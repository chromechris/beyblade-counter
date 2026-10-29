"""Produce the single-file pages used to publish the web app as a private claude.ai artifact.

    python tools/build_artifact.py OUTDIR

Writes OUTDIR/index.html (body of web/index.html with style.css and app.js inlined, no html/head/body
wrappers: the artifact host adds its own skeleton) and OUTDIR/privacy.html (a complete page with the
stylesheet inlined). Photos, the database and icons are published alongside from web/ as they are.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


def body_of(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    return m.group(1) if m else html


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    css = (WEB / "style.css").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    index = (WEB / "index.html").read_text(encoding="utf-8")
    body = body_of(index).replace('<script src="app.js"></script>', "")
    page = (
        "<title>Spintelligence</title>\n"
        '<meta name="claude:viewport-fit-sides" content="cover">\n'
        '<link rel="icon" type="image/png" href="icons/favicon.png">\n'
        f"<style>\n{css}\n</style>\n"
        f"{body.strip()}\n"
        f"<script>\n{js}\n</script>\n"
    )
    (out / "index.html").write_text(page, encoding="utf-8")
    privacy = (WEB / "privacy.html").read_text(encoding="utf-8")
    privacy = privacy.replace('<link rel="stylesheet" href="style.css">', f"<style>\n{css}\n</style>")
    (out / "privacy.html").write_text(privacy, encoding="utf-8")
    print("wrote", out / "index.html", "and", out / "privacy.html")


if __name__ == "__main__":
    main()
