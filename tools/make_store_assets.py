"""Play Store listing assets: the 1024x500 feature graphic and a copy of the 512x512 icon.

    python tools/make_store_assets.py      ->  store/feature-graphic.png, store/icon-512.png

Screenshots go in store/screenshots/ (1080x2400 phone captures work as they are).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_icons import GREEN, AMBER, knock_out_white, subject  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "store"
BG_TOP, BG_BOTTOM = (16, 22, 32), (7, 10, 15)
INK, MUTED = (223, 231, 241), (138, 153, 173)


def font(names: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for n in names:
        p = Path("C:/Windows/Fonts") / n
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def feature_graphic(photo: Image.Image) -> Image.Image:
    W, H = 1024, 500
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(BG_TOP[i] * (1 - t) + BG_BOTTOM[i] * t) for i in range(3)) + (255,))
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # faint console grid, alpha-blended
    g = ImageDraw.Draw(grid)
    for x in range(0, W, 32):
        g.line([(x, 0), (x, H)], fill=(255, 255, 255, 12))
    for y in range(0, H, 32):
        g.line([(0, y), (W, y)], fill=(255, 255, 255, 12))
    img.alpha_composite(grid)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 26], fill=AMBER + (255,))  # classification bar
    bar_font = font(["consolab.ttf", "consola.ttf"], 13)
    d.text((24, 6), "TOP SECRET  //  SPINTELLIGENCE  //  FIELD INTELLIGENCE SYSTEM  //  BLADER EYES ONLY", font=bar_font, fill=(26, 18, 0))
    icon = subject(photo, 380)
    img.alpha_composite(icon, (44, 72))
    title = font(["segoeuib.ttf", "arialbd.ttf"], 58)
    d.text((452, 150), "SPINTELLIGENCE", font=title, fill=INK)
    sub = font(["segoeui.ttf", "arial.ttf"], 27)
    d.text((456, 226), "Study the target. Pick the counter.", font=sub, fill=INK)
    mono = font(["consola.ttf"], 17)
    d.text((458, 282), "BEYBLADE X COUNTER PICKER  ·  WORKS OFFLINE", font=mono, fill=GREEN)
    small = font(["consola.ttf"], 13)
    d.text((458, 326), "Unofficial fan-made tool. Not affiliated with Takara Tomy or Hasbro.", font=small, fill=MUTED)
    d.text((458, 346), "Beyblade and Beyblade X are trademarks of their respective owners.", font=small, fill=MUTED)
    # corner brackets, as on the icon
    m, L, w = 14, 40, 3
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        x = m if sx == 1 else W - 1 - m
        y = 26 + m if sy == 1 else H - 1 - m
        d.line([(x, y), (x + sx * L, y)], fill=AMBER + (255,), width=w)
        d.line([(x, y), (x, y + sy * L)], fill=AMBER + (255,), width=w)
    return img


def main() -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / "screenshots").mkdir(exist_ok=True)
    src = ROOT / "web" / "img" / "models" / "DranSword_3-60F.png"
    photo = knock_out_white(Image.open(src))
    bbox = photo.getbbox()
    if bbox:
        photo = photo.crop(bbox)
    feature_graphic(photo).convert("RGB").save(OUT / "feature-graphic.png")
    shutil.copy2(ROOT / "web" / "icons" / "icon-512.png", OUT / "icon-512.png")
    print("written", OUT / "feature-graphic.png", "and", OUT / "icon-512.png")


if __name__ == "__main__":
    main()
