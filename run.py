"""Tətbiqi işə salır və brauzerdə açır.

Masaüstü qısayolu və portativ paketin ilkmusic.exe-si bunu pythonw.exe ilə (konsol pəncərəsi olmadan) işə salır.
Brauzerdə tətbiq səhifəsi qalmayanda server özü dayanır.
"""

import json
import socket
import sys
import tempfile
import threading
import urllib.request
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORTS = range(8000, 8011)
LOG_PATH = Path(tempfile.gettempdir()) / "ilkmusic.log"


def _port_state(port: int) -> str:
    """"free" (boş), "ilkmusic" (tətbiq artıq işləyir) və ya "busy" (port başqa proqramdadır)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        if sock.connect_ex((HOST, port)) != 0:
            return "free"
    try:
        request = urllib.request.Request(f"http://{HOST}:{port}/api/heartbeat", method="POST")
        with urllib.request.urlopen(request, timeout=2) as response:
            return "ilkmusic" if json.load(response).get("app") == "ilkmusic" else "busy"
    except Exception:
        return "busy"


def _log_to_file(mode: str) -> None:
    # pythonw.exe ilə konsol yoxdur, ona görə loglar fayla yazılır.
    if sys.stdout is None or sys.stderr is None:
        sys.stdout = sys.stderr = open(LOG_PATH, mode, encoding="utf-8", buffering=1)


def run() -> None:
    for port in PORTS:
        state = _port_state(port)
        if state == "ilkmusic":
            print(f"Tətbiq artıq işləyir, brauzerdə açılır: http://localhost:{port}")
            webbrowser.open(f"http://localhost:{port}")
            return
        if state == "free":
            break
    else:
        _log_to_file("a")  # işləyən serverin logunu silməmək üçün sona əlavə edirik
        print(f"{PORTS.start}–{PORTS.stop - 1} portlarının hamısı başqa proqramlar tərəfindən istifadə olunur.")
        return

    _log_to_file("w")
    import uvicorn

    import app.main as app_module

    url = f"http://localhost:{port}"
    server = uvicorn.Server(uvicorn.Config(app_module.app, host=HOST, port=port))
    app_module.shutdown_hook = lambda: setattr(server, "should_exit", True)
    threading.Timer(1.5, webbrowser.open, args=[url]).start()
    server.run()


if __name__ == "__main__":
    run()
