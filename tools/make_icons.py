"""Generate the Beytelligence app icons (PWA, Android/iOS, Windows .ico) from a product photo.

Usage: python tools/make_icons.py [photo]   (default: web/img/models/DranSword_3-60F.png)

Writes web/icons/ (icon-192/512/1024.png, apple-touch-icon.png, favicon.png, app.ico) and the
source images @capacitor/assets wants in mobile/assets/ (icon.png, icon-only.png, icon-foreground.png,
icon-background.png, splash.png, splash-dark.png). The photo sits inside a targeting reticle.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "icons"
ASSETS = ROOT / "mobile" / "assets"
BG_TOP, BG_BOTTOM = (16, 22, 32), (7, 10, 15)
GREEN, AMBER = (70, 227, 154), (245, 185, 66)


def knock_out_white(img: Image.Image, threshold: int = 238) -> Image.Image:
    """Make the (near) white studio background transparent."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r >= threshold and g >= threshold and b >= threshold:
                px[x, y] = (r, g, b, 0)
    return img


def gradient(size: int) -> Image.Image:
    bg = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(bg)
    for y in range(size):
        t = y / max(1, size - 1)
        col = tuple(int(BG_TOP[i] * (1 - t) + BG_BOTTOM[i] * t) for i in range(3)) + (255,)
        d.line([(0, y), (size, y)], fill=col)
    return bg


def subject(photo: Image.Image, size: int) -> Image.Image:
    """Transparent layer: the photo inside a targeting reticle (ring, ticks, corner brackets)."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    p = photo.copy()
    inner = int(size * 0.66)
    p.thumbnail((inner, inner), Image.LANCZOS)
    layer.alpha_composite(p, ((size - p.width) // 2, (size - p.height) // 2))
    d = ImageDraw.Draw(layer)
    c, w = size // 2, max(2, size // 80)
    r = int(size * 0.415)
    d.ellipse([c - r, c - r, c + r, c + r], outline=GREEN + (235,), width=w)
    r2 = int(size * 0.375)
    d.ellipse([c - r2, c - r2, c + r2, c + r2], outline=GREEN + (70,), width=max(1, w // 2))
    tick = int(size * 0.05)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.line([(c + dx * (r - tick), c + dy * (r - tick)), (c + dx * (r + tick), c + dy * (r + tick))], fill=GREEN + (235,), width=w)
    m, L = int(size * 0.045), int(size * 0.09)
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        x = m if sx == 1 else size - 1 - m
        y = m if sy == 1 else size - 1 - m
        d.line([(x, y), (x + sx * L, y)], fill=AMBER + (235,), width=w)
        d.line([(x, y), (x, y + sy * L)], fill=AMBER + (235,), width=w)
    return layer


def make_icon(photo: Image.Image, size: int, rounded: bool) -> Image.Image:
    icon = gradient(size)
    icon.alpha_composite(subject(photo, size))
    if rounded:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
        icon.putalpha(mask)
    return icon


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "web" / "img" / "models" / "DranSword_3-60F.png"
    photo = knock_out_white(Image.open(src))
    bbox = photo.getbbox()
    if bbox:
        photo = photo.crop(bbox)
    OUT.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    # square (maskable-safe) versions for Android / PWA, rounded for Apple & favicon
    make_icon(photo, 1024, False).save(OUT / "icon-1024.png")
    make_icon(photo, 512, False).save(OUT / "icon-512.png")
    make_icon(photo, 192, False).save(OUT / "icon-192.png")
    make_icon(photo, 180, False).save(OUT / "apple-touch-icon.png")
    make_icon(photo, 64, True).save(OUT / "favicon.png")
    make_icon(photo, 256, True).save(OUT / "app.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    # Capacitor sources (npx @capacitor/assets generate --android)
    full = make_icon(photo, 1024, False)
    full.save(ASSETS / "icon.png")
    full.save(ASSETS / "icon-only.png")
    gradient(1024).save(ASSETS / "icon-background.png")
    fg = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))          # adaptive icon: keep inside the 66% safe zone
    s = subject(photo, 1024).resize((660, 660), Image.LANCZOS)
    fg.alpha_composite(s, (182, 182))
    fg.save(ASSETS / "icon-foreground.png")
    for name in ("splash.png", "splash-dark.png"):
        sp = gradient(2732)
        s = subject(photo, 1024).resize((900, 900), Image.LANCZOS)
        sp.alpha_composite(s, ((2732 - 900) // 2, (2732 - 900) // 2))
        sp.save(ASSETS / name)
    print("icons written to", OUT, "and", ASSETS)


if __name__ == "__main__":
    main()
