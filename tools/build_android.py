r"""Build the Android debug APK (Capacitor + Gradle).

    python tools/build_android.py            ->  mobile/android/app/build/outputs/apk/debug/app-debug.apk
    python tools/build_android.py --install  ->  ... then `adb install -r` on the connected phone / emulator

What it does:
  1. copies web/ into mobile/www            (tools/sync_mobile.py)
  2. `npx cap sync android`                  (www -> android/app/src/main/assets/public)
  3. `gradlew assembleDebug`                 with JDK 21 and the Android SDK forced, whatever
                                             JAVA_HOME / ANDROID_HOME say in this shell

Why the forcing: Gradle 8.11 (Capacitor 7) needs JDK 17..23 to run, and Capacitor 7 compiles
with Java 21, so JDK 21 is the one that works. Android Studio's bundled JBR (JDK 25) and
Corretto 17 both fail. The SDK path is written to android/local.properties with forward
slashes: a Java .properties file treats "\" as an escape, so a raw Windows path such as
C:\Users\... is read as C:Users... and the Android plugin dies with
"The filename, directory name, or volume label syntax is incorrect".
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOBILE = ROOT / "mobile"
ANDROID = MOBILE / "android"
APK = ANDROID / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
WIN = sys.platform == "win32"

JDK_CANDIDATES = [
    os.environ.get("BEYCOUNTER_JDK"),
    r"C:\Program Files\Java\jdk-21",
    r"C:\Program Files\Eclipse Adoptium\jdk-21",
    r"C:\Program Files\Microsoft\jdk-21",
    "/usr/lib/jvm/java-21-openjdk-amd64",
    "/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home",
]
SDK_CANDIDATES = [
    os.environ.get("ANDROID_HOME"),
    os.environ.get("ANDROID_SDK_ROOT"),
    str(Path.home() / "AppData" / "Local" / "Android" / "Sdk"),
    str(Path.home() / "Android" / "Sdk"),
    str(Path.home() / "Library" / "Android" / "sdk"),
]


def java_major(home: str) -> int | None:
    exe = Path(home) / "bin" / ("java.exe" if WIN else "java")
    if not exe.exists():
        return None
    out = subprocess.run([str(exe), "-version"], capture_output=True, text=True).stderr
    try:
        ver = out.split('"')[1]  # e.g. 21.0.9 or 1.8.0_401
        major = int(ver.split(".")[0])
        return 8 if major == 1 else major
    except (IndexError, ValueError):
        return None


def find_jdk() -> str:
    for c in [os.environ.get("JAVA_HOME")] + JDK_CANDIDATES:
        if c and java_major(c) == 21:
            return c
    # any 17..23 would run Gradle 8.11, but Capacitor 7 compiles for Java 21: prefer exactly 21
    for c in [os.environ.get("JAVA_HOME")] + JDK_CANDIDATES:
        if c and (java_major(c) or 0) in (22, 23):
            return c
    sys.exit("No JDK 21 found. Install one (https://adoptium.net) or set BEYCOUNTER_JDK=<path to the JDK>.")


def find_sdk() -> str:
    for c in SDK_CANDIDATES:
        if c and (Path(c) / "platform-tools").exists():
            return c
    sys.exit("Android SDK not found. Install it with Android Studio or set ANDROID_HOME.")


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    print("$", " ".join(cmd), f"   (in {cwd})")
    subprocess.run(cmd, cwd=cwd, env=env, check=True, shell=WIN)


def main() -> None:
    jdk, sdk = find_jdk(), find_sdk()
    env = dict(os.environ, JAVA_HOME=jdk, ANDROID_HOME=sdk, ANDROID_SDK_ROOT=sdk)
    env["PATH"] = os.pathsep.join([str(Path(jdk) / "bin"), str(Path(sdk) / "platform-tools"), env.get("PATH", "")])
    print(f"JDK: {jdk}\nSDK: {sdk}")

    # forward slashes: safe in a Java .properties file on every OS
    (ANDROID / "local.properties").write_text(f"sdk.dir={Path(sdk).as_posix()}\n", encoding="utf-8")

    run([sys.executable, str(ROOT / "tools" / "sync_mobile.py")], MOBILE, env)
    npx = "npx.cmd" if WIN else "npx"
    run([npx, "cap", "sync", "android"], MOBILE, env)
    gradlew = str(ANDROID / ("gradlew.bat" if WIN else "gradlew"))  # full path: cmd may not search "."
    run([gradlew, "assembleDebug", "--no-daemon"], ANDROID, env)

    if not APK.exists():
        sys.exit("gradle finished but the APK is missing")
    print(f"\nbuilt {APK} ({APK.stat().st_size / 1e6:.1f} MB)")
    copy = ROOT / "dist" / "BeyCounter-debug.apk"   # next to the Windows exe, easy to find / send to a phone
    copy.parent.mkdir(exist_ok=True)
    shutil.copy2(APK, copy)
    print(f"copied to {copy}")

    if "--install" in sys.argv:
        adb = shutil.which("adb", path=env["PATH"]) or "adb"
        run([adb, "install", "-r", str(APK)], ANDROID, env)
        run([adb, "shell", "monkey", "-p", "app.beycounter", "-c", "android.intent.category.LAUNCHER", "1"], ANDROID, env)


if __name__ == "__main__":
    main()
