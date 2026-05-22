"""一键启动前后端开发服务器 — 后端先启动，前端紧随，并行等待就绪"""

import os
import signal
import socket
import subprocess
import sys
import time

from app.core.config import settings

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

BACKEND_HOST = settings.SERVER_HOST
BACKEND_PORT = settings.SERVER_PORT
FRONTEND_PORT = 5173


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


def start():
    backend_proc = None
    frontend_proc = None

    try:
        # ── 1. 先启动后端（子进程，非阻塞） ──
        if _port_in_use(BACKEND_PORT):
            print(f"[run] Backend already running on http://{BACKEND_HOST}:{BACKEND_PORT}")
        else:
            cmd = [sys.executable, "-m", "uvicorn", "app.main:app",
                   "--host", BACKEND_HOST, "--port", str(BACKEND_PORT)]
            if settings.DEBUG:
                cmd.extend(["--reload", "--reload-exclude", "uploads/*",
                            "--reload-exclude", "db/*",
                            "--reload-exclude", "*.db*",
                            "--reload-exclude", "*.bin"])
            backend_proc = subprocess.Popen(
                cmd,
                cwd=ROOT_DIR,
                stdout=subprocess.DEVNULL,
                stderr=None,
            )
            print(f"[run] Backend starting (PID: {backend_proc.pid})...")

        # ── 2. 紧随启动前端 ──
        if not os.path.exists(os.path.join(FRONTEND_DIR, "package.json")):
            print("[run] Frontend package.json not found, skipping frontend.")
        elif _port_in_use(FRONTEND_PORT):
            print(f"[run] Frontend already running on http://localhost:{FRONTEND_PORT}")
        else:
            npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
            frontend_proc = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=FRONTEND_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"[run] Frontend starting (PID: {frontend_proc.pid})...")

        # ── 3. 并行等待两者就绪 ──
        backend_ok = _wait_port(BACKEND_PORT, timeout=15)
        frontend_ok = _wait_port(FRONTEND_PORT, timeout=30)

        if backend_ok:
            print(f"[run] Backend ready  → http://{BACKEND_HOST}:{BACKEND_PORT}")
        else:
            print(f"[run] WARNING: Backend may still be starting")
        if frontend_ok:
            print(f"[run] Frontend ready → http://localhost:{FRONTEND_PORT}")
        else:
            print(f"[run] WARNING: Frontend may still be starting, check http://localhost:{FRONTEND_PORT}")

        print("[run] Both servers running. Press Ctrl+C to stop.")

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
