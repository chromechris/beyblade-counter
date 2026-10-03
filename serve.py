"""Serve the web UI locally:  python serve.py [port]   (default 8792)

Opens http://localhost:<port>/web/ in your browser. Ctrl+C stops it.
"""
import functools
import http.server
import sys
import threading
import webbrowser
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8792
ROOT = Path(__file__).resolve().parent


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):  # keep the console clean
        if "404" in (args[1] if len(args) > 1 else ""):
            super().log_message(fmt, *args)


def main() -> None:
    handler = functools.partial(Quiet, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}/web/"
        print(f"Beyblade X Counter Picker -> {url}   (Ctrl+C to stop)")
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
