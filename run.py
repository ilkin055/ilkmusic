"""Tətbiqi işə salır və ayrıca app pəncərəsində açır.

Masaüstü qısayolu və portativ paketin ilkmusic.exe-si bunu pythonw.exe ilə (konsol pəncərəsi olmadan) işə salır.
Pəncərə Chrome/Edge-in "app" rejimində açılır: ünvan sətri və tablar olmadan, adi proqram kimi.
Pəncərə bağlananda server özü dayanır.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.request
import webbrowser
import winreg
from pathlib import Path

HOST = "127.0.0.1"
# Telefon ev Wi-Fi-ı ilə qoşula bilsin deyə server bütün şəbəkə kartlarında dinləyir.
# Şəbəkədən gələn sorğuları app/main.py gizli açarla yoxlayır.
BIND_HOST = "0.0.0.0"
PORTS = range(8000, 8011)
LOG_PATH = Path(tempfile.gettempdir()) / "ilkmusic.log"
APP_WINDOW_SIZE = "1280,860"
APP_BROWSERS = ("chrome.exe", "msedge.exe")  # Edge Windows 10/11-də həmişə var


def _app_browser() -> str | None:
    """Chrome və ya Edge-in yolu: Windows-un "App Paths" qeydindən, tapılmasa standart yerlərdən."""
    for exe in APP_BROWSERS:
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}") as key:
                    path = winreg.QueryValue(key, None).strip('"')
            except OSError:
                continue
            if path and os.path.exists(path):
                return path
    program_dirs = [os.environ.get(v, "") for v in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")]
    candidates = [
        os.path.join(base, *parts)
        for base in program_dirs
        for parts in (("Google", "Chrome", "Application", "chrome.exe"), ("Microsoft", "Edge", "Application", "msedge.exe"))
    ]
    return next((p for p in candidates if os.path.exists(p)), None)


def _open_app_window(url: str) -> None:
    browser = _app_browser()
    if browser:
        subprocess.Popen([browser, f"--app={url}", f"--window-size={APP_WINDOW_SIZE}"])
    else:
        webbrowser.open(url)  # Chrome/Edge yoxdursa, adi brauzer tabında


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
            print(f"Tətbiq artıq işləyir, pəncərəsi açılır: http://localhost:{port}")
            _open_app_window(f"http://localhost:{port}")
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
    server = uvicorn.Server(uvicorn.Config(app_module.app, host=BIND_HOST, port=port))
    app_module.shutdown_hook = lambda: setattr(server, "should_exit", True)
    threading.Timer(1.5, _open_app_window, args=[url]).start()
    server.run()


if __name__ == "__main__":
    run()
