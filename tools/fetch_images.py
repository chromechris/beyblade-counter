"""Download product / part thumbnails referenced by beyblade_x.json into web/img/.

Usage:  python tools/fetch_images.py [--width 360] [--workers 4]

Image files come from the Beyblade Wiki (https://beyblade.fandom.com). They are
product photos / renders used for identification in this personal tool.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://beyblade.fandom.com/api.php"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "beycounter" / "data" / "beyblade_x.json"
IMG_DIR = ROOT / "web" / "img"
UA = {"User-Agent": "beycounter-image-fetch/0.1"}


def local_name(wiki_name: str) -> str:
    """Same sanitising rule as web/app.js localImage()."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", wiki_name)


def call(**params):
    params["format"] = "json"
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def thumb_urls(names: list[str], width: int) -> dict[str, str]:
    out: dict[str, str] = {}
    for i in range(0, len(names), 50):
        batch = names[i:i + 50]
        d = call(action="query", prop="imageinfo", iiprop="url", iiurlwidth=width,
                 titles="|".join("File:" + n for n in batch))
        normalised = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
        for pg in d["query"]["pages"].values():
            title = pg.get("title", "")
            orig = normalised.get(title, title)
            orig = re.sub(r"^File:", "", orig)
            info = (pg.get("imageinfo") or [{}])[0]
            url = info.get("thumburl") or info.get("url")
            if url:
                out[orig] = url
                # the API may normalise "Foo bar.png" -> "Foo_bar.png"; map both
                out[orig.replace("_", " ")] = url
        print(f"  resolved {min(i + 50, len(names))}/{len(names)}", file=sys.stderr)
        time.sleep(0.5)
    return out


def download(url: str, dest: Path) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        return "cached"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        dest.write_bytes(data)
        return "ok"
    except Exception as e:  # noqa: BLE001
        return f"fail ({e})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=360)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    data = json.load(open(DATA, encoding="utf-8"))
    # one wiki file can be used both as a product photo and as a part image
    wanted: dict[str, set[Path]] = {}
    for m in data["models"]:
        if m.get("image"):
            wanted.setdefault(m["image"], set()).add(IMG_DIR / "models" / local_name(m["image"]))
    for p in data["parts"]:
        if p.get("image"):
            wanted.setdefault(p["image"], set()).add(IMG_DIR / "parts" / local_name(p["image"]))
    for d in {v.parent for vs in wanted.values() for v in vs}:
        d.mkdir(parents=True, exist_ok=True)
    todo: dict[str, Path] = {}
    copies = 0
    for n, dests in wanted.items():
        have = [d for d in dests if d.exists() and d.stat().st_size > 0]
        for d in dests:
            if d.exists() and d.stat().st_size > 0:
                continue
            if have:  # already downloaded for the other folder: copy it
                d.write_bytes(have[0].read_bytes())
                copies += 1
            else:
                todo[n] = d
    print(f"{len(wanted)} images referenced, {copies} copied, {len(todo)} to download", file=sys.stderr)
    if not todo:
        return
    urls = thumb_urls(sorted(todo), args.width)
    missing = [n for n in todo if n not in urls]
    jobs = [(urls[n], todo[n]) for n in todo if n in urls]
    results = {"ok": 0, "cached": 0, "fail": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for status in ex.map(lambda j: download(*j), jobs):
            results[status.split(" ")[0]] += 1
    for n, d in todo.items():  # mirror into any sibling destinations
        for other in wanted[n]:
            if other != d and d.exists() and not other.exists():
                other.write_bytes(d.read_bytes())
    print(f"downloaded {results['ok']}, cached {results['cached']}, failed {results['fail']}, "
          f"no url for {len(missing)}", file=sys.stderr)
    for n in missing[:30]:
        print("  no url:", n, file=sys.stderr)


if __name__ == "__main__":
    main()
