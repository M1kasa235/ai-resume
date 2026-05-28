"""一键启动前后端开发服务器 — 后端 health 就绪后再启动前端"""

import os
import signal
import socket
import subprocess
import sys
import time

from app.core.config import settings
from app.core.startup_health import wait_for_health

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

BACKEND_HOST = settings.SERVER_HOST
BACKEND_PORT = settings.SERVER_PORT
FRONTEND_PORT = 5173
BACKEND_HEALTH_TIMEOUT = 120.0


def _port_in_use(port: int) -> bool:
    """检查端口是否已被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def _wait_port(port: int, timeout: float) -> bool:
    """轮询等待端口就绪，返回是否成功"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_in_use(port):
            return True
        time.sleep(0.3)
    return False


def _kill(proc, name: str):
    """安全终止子进程"""
    if not proc or proc.poll() is not None:
        return
    print(f"[run] Stopping {name} (PID: {proc.pid})...")
    sig = signal.CTRL_BREAK_EVENT if sys.platform == "win32" else signal.SIGTERM
    proc.send_signal(sig)
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print(f"[run] {name} stopped.")


def _find_listening_pid(port: int) -> int | None:
    """Return PID listening on localhost:port (Windows netstat)."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    needle = f":{port}"
    for line in result.stdout.splitlines():
        if needle not in line or "LISTENING" not in line:
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            return int(parts[-1])
        except ValueError:
            continue
    return None


def _kill_pid(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False)
    else:
        subprocess.run(["kill", "-9", str(pid)], check=False)


def start():
    backend_proc = None
    frontend_proc = None

    try:
        backend_already_running = _port_in_use(BACKEND_PORT)

        # ── 1. 先启动后端 ──
        if backend_already_running and settings.DEBUG:
            stale_pid = _find_listening_pid(BACKEND_PORT)
            if stale_pid:
                print(
                    f"[run] Stopping stale backend on port {BACKEND_PORT} (PID: {stale_pid})..."
                )
                _kill_pid(stale_pid)
                time.sleep(1)
                backend_already_running = _port_in_use(BACKEND_PORT)

        if backend_already_running:
            print(
                f"[run] WARNING: Port {BACKEND_PORT} still in use — "
                f"stop the old backend manually, then re-run."
            )
            print(f"[run] Verify fix: http://{BACKEND_HOST}:{BACKEND_PORT}/health")
            print("[run] Expected: {\"checkpointer\": \"AsyncSqliteSaver\"}")
        else:
            cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                BACKEND_HOST,
                "--port",
                str(BACKEND_PORT),
            ]
            if settings.DEBUG:
                # Windows: avoid `dir/*` globs — uvicorn/click expands them into extra CLI args.
                cmd.extend(
                    [
                        "--reload",
                        "--reload-dir",
                        "app",
                        "--reload-exclude",
                        "db",
                        "--reload-exclude",
                        "uploads",
                        "--reload-exclude",
                        "*.db",
                        "--reload-exclude",
                        "*.db-shm",
                        "--reload-exclude",
                        "*.db-wal",
                        "--reload-exclude",
                        "*.bin",
                    ]
                )
            backend_proc = subprocess.Popen(
                cmd,
                cwd=ROOT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=None,
            )
            print(f"[run] Backend starting (PID: {backend_proc.pid})...")

        # ── 2. 等待后端 /health 就绪（端口监听 ≠ 应用可用） ──
        print(f"[run] Waiting for backend health (timeout {int(BACKEND_HEALTH_TIMEOUT)}s)...")
        backend_ok = wait_for_health(
            BACKEND_HOST,
            BACKEND_PORT,
            timeout=BACKEND_HEALTH_TIMEOUT,
        )
        if backend_ok:
            print(f"[run] Backend ready  → http://{BACKEND_HOST}:{BACKEND_PORT}")
        else:
            print("[run] WARNING: Backend health check timed out; frontend may show errors")

        # ── 3. 后端就绪后再启动前端 ──
        if not os.path.exists(os.path.join(FRONTEND_DIR, "package.json")):
            print("[run] Frontend package.json not found, skipping frontend.")
        elif _port_in_use(FRONTEND_PORT):
            print(
                f"[run] WARNING: Port {FRONTEND_PORT} already in use — "
                f"stop the old frontend first, then re-run."
            )
            print(f"[run] Try: http://localhost:{FRONTEND_PORT} (may be a stale process)")
        else:
            npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
            frontend_proc = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=FRONTEND_DIR,
            )
            print(f"[run] Frontend starting (PID: {frontend_proc.pid})...")

        frontend_ok = _wait_port(FRONTEND_PORT, timeout=60)
        if frontend_ok:
            print(f"[run] Frontend ready → http://localhost:{FRONTEND_PORT}")
        else:
            print(f"[run] WARNING: Frontend may still be starting, check http://localhost:{FRONTEND_PORT}")

        print("[run] Dev servers running. Press Ctrl+C to stop.")

        # ── 4. 保活：监控任一子进程退出 ──
        while True:
            if backend_proc and backend_proc.poll() is not None:
                print("[run] Backend exited unexpectedly")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print("[run] Frontend exited unexpectedly")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[run] Shutting down...")
    finally:
        _kill(backend_proc, "backend")
        _kill(frontend_proc, "frontend")


if __name__ == "__main__":
    start()
