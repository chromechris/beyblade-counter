"""Build the Windows desktop executable with PyInstaller.

    python tools/build_desktop.py            ->  dist/Spintelligence.exe

Requires:  pip install pyinstaller pywebview
The .exe bundles the whole web/ folder (UI, database copy, photos). The user's
collection is stored in %APPDATA%\\BeybladeCounter so it survives updates.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON = ROOT / "web" / "icons" / "app.ico"


def main() -> None:
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    (ROOT / "dist").mkdir(exist_ok=True)           # dist/ also holds the Android APK copy: only replace the exe
    for old in ("Spintelligence.exe", "Spintelligence"):
        (ROOT / "dist" / old).unlink(missing_ok=True)
    cmd = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--onefile", "--windowed", "--name", "Spintelligence",
        "--add-data", f"{ROOT / 'web'}{';' if sys.platform == 'win32' else ':'}web",
        "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        "--hidden-import", "clr", "--hidden-import", "clr_loader",
    ]
    if ICON.exists():
        cmd += ["--icon", str(ICON)]
    cmd.append(str(ROOT / "desktop.py"))
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)
    exe = ROOT / "dist" / ("Spintelligence.exe" if sys.platform == "win32" else "Spintelligence")
    print(f"\nbuilt {exe} ({exe.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
