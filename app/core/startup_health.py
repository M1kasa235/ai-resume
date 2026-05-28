"""Poll backend /health until ready."""

from __future__ import annotations

import time
import urllib.error
import urllib.request


def wait_for_health(
    host: str,
    port: int,
    *,
    timeout: float = 120.0,
    interval: float = 0.5,
) -> bool:
    """Return True when GET /health responds with HTTP 200."""
    url = f"http://{host}:{port}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(interval)
    return False
