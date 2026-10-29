"""Desktop app: the web UI in a native window (pywebview + WebView2).

Run from source:   python desktop.py
Build an .exe:     python tools/build_desktop.py   ->  dist/Spintelligence.exe
"""
from __future__ import annotations

import functools
import http.server
import os
import sys
import threading
from pathlib import Path

import webview

APP_NAME = "Spintelligence"


def resource_root() -> Path:
    """Project root when run from source, the PyInstaller bundle dir when frozen."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def user_data_dir() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    d = base / "BeybladeCounter"   # kept from the first release so an existing collection survives the rename
    d.mkdir(parents=True, exist_ok=True)
    return d


def start_server(root: Path) -> int:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # silence request logging
            pass

    handler = functools.partial(Quiet, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd.server_address[1]


def main() -> None:
    port = start_server(resource_root())
    webview.create_window(APP_NAME, f"http://127.0.0.1:{port}/web/",
                          width=1280, height=860, min_size=(400, 600))
    # private_mode=False + storage_path keep the collection (localStorage) between runs
    webview.start(private_mode=False, storage_path=str(user_data_dir()))


if __name__ == "__main__":
    main()
