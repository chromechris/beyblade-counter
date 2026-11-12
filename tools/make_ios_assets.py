"""Copy the app icon and splash screen into the iOS Xcode project.

    python tools/make_ios_assets.py

Sources are the Capacitor asset files that tools/make_icons.py writes to mobile/assets/.
Apple rejects an App Store icon with an alpha channel, so the icon is flattened to RGB.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "mobile" / "assets"
XCASSETS = ROOT / "mobile" / "ios" / "App" / "App" / "Assets.xcassets"
BG = (7, 10, 15)  # #070a0f, the app background


def flatten(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    base = Image.new("RGBA", img.size, BG + (255,))
    base.alpha_composite(img)
    return base.convert("RGB")


def main() -> None:
    icon = flatten(ASSETS / "icon.png").resize((1024, 1024), Image.LANCZOS)
    icon.save(XCASSETS / "AppIcon.appiconset" / "AppIcon-512@2x.png")
    splash = flatten(ASSETS / "splash-dark.png").resize((2732, 2732), Image.LANCZOS)
    for name in ("splash-2732x2732.png", "splash-2732x2732-1.png", "splash-2732x2732-2.png"):
        splash.save(XCASSETS / "Splash.imageset" / name)
    print("iOS icon and splash written to", XCASSETS)


if __name__ == "__main__":
    main()
