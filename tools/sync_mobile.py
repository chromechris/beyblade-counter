"""Copy the web app into mobile/www (Capacitor's webDir).

    python tools/sync_mobile.py

Run it after changing anything in web/ (then `npx cap sync` inside mobile/).
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web"
DST = ROOT / "mobile" / "www"


def main() -> None:
    shutil.rmtree(DST, ignore_errors=True)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("sw.js"))  # Capacitor serves locally; no service worker needed
    n = sum(1 for _ in DST.rglob("*") if _.is_file())
    print(f"copied {n} files to {DST}")


if __name__ == "__main__":
    main()
