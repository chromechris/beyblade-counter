r"""Publish the pages in wiki/ to the GitHub wiki of chromechris/beyblade-counter.

    python tools/publish_wiki.py

GitHub creates a repository's wiki only after its first page is made in the browser. If the
clone below fails, open https://github.com/chromechris/beyblade-counter/wiki, click
"Create the first page", save it with any content, and run this script again.

wiki/ in the main repository is the source of truth: every *.md there replaces the wiki's
pages (so edits made in GitHub's wiki editor are overwritten). Links written as
"[text](Page.md)" become "[text](Page)", which is how wiki pages link to each other.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "wiki"
REMOTE = "https://github.com/chromechris/beyblade-counter.wiki.git"


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="beywiki-"))
    dst = tmp / "w"
    r = subprocess.run(["git", "clone", "-q", REMOTE, str(dst)], capture_output=True, text=True)
    if r.returncode:
        sys.exit("Could not clone the wiki repository. Create its first page in the browser\n"
                 "(https://github.com/chromechris/beyblade-counter/wiki -> Create the first page)\n"
                 "and run this again.\n" + r.stderr.strip())
    for old in dst.glob("*.md"):
        old.unlink()
    pages = sorted(SRC.glob("*.md"))
    for f in pages:
        text = f.read_text(encoding="utf-8")
        text = re.sub(r"\]\(([A-Za-z0-9_-]+)\.md\)", r"](\1)", text)
        (dst / f.name).write_text(text, encoding="utf-8", newline="\n")
    subprocess.run(["git", "add", "-A"], cwd=dst, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=dst).returncode == 0:
        print("wiki already up to date")
    else:
        subprocess.run(["git", "commit", "-q", "-m", "Update wiki from wiki/ in the main repository"], cwd=dst, check=True)
        subprocess.run(["git", "push", "-q"], cwd=dst, check=True)
        print(f"published {len(pages)} pages to {REMOTE}")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
