# Building from source

Everything is built from one repository: https://github.com/chromechris/beyblade-counter. The web app in `web/` is the core; the Android and Windows apps wrap it.

## Prerequisites

| For | Needs |
| --- | --- |
| Web app, CLI, tests | Python 3.10 or later (no packages) |
| Database rebuild | Python; internet for a fresh scrape, none with `--offline` |
| Icons | `pip install Pillow` |
| Windows exe | `pip install pyinstaller pywebview` |
| Android APK | Node 20+, JDK 21, Android SDK (platform 35, build-tools 34+) |
| iOS app | A Mac with Xcode (see below) |

```bash
git clone https://github.com/chromechris/beyblade-counter.git
cd beyblade-counter
python -m pytest            # 8 tests
python serve.py             # opens http://localhost:8792/web/
```

## Web app

`web/` is plain HTML, CSS and JavaScript with no build step. `python serve.py` serves the project folder (the app must be served over HTTP; opening `index.html` as a file blocks the database fetch). The service worker also registers on `localhost`, so offline behaviour can be tested by loading the page once, stopping the server and reloading.

Pushing to `main` publishes `web/` to GitHub Pages through `.github/workflows/pages.yml`.

## Database, photos, icons

```bash
python tools/build_database.py            # scrape the Beyblade Wiki -> beycounter/data + web/data
python tools/build_database.py --offline  # rebuild from the cached pages in tools/cache/
python tools/fetch_images.py              # download product and part photos into web/img/
python tools/make_icons.py                # web/icons/ and mobile/assets/ from a product photo
```

## Windows exe

```bash
pip install pyinstaller pywebview
python tools/build_desktop.py             # -> dist/Spintelligence.exe (about 29 MB)
```

`desktop.py` runs the same window from source. The exe bundles the whole `web/` folder and serves it to a WebView2 window from a local port; the arsenal is kept in `%APPDATA%\BeybladeCounter`.

## Android APK

```bash
cd mobile
npm install
npm run android                           # -> android/app/build/outputs/apk/debug/app-debug.apk and dist/Spintelligence-debug.apk
npm run android:install                   # same, then adb install -r and launch on the connected phone
```

`npm run android` runs `tools/build_android.py`, which copies `web/` into `mobile/www`, runs `npx cap sync android` and `gradlew assembleDebug`. It finds JDK 21 and the SDK on its own (`C:\Program Files\Java\jdk-21`, `%LOCALAPPDATA%\Android\Sdk`; override with `BEYCOUNTER_JDK` and `ANDROID_HOME`) and rewrites `mobile/android/local.properties`.

Things that go wrong, and why:

- **Wrong JDK.** Gradle 8.11 (Capacitor 7) needs JDK 17 to 23 and compiles for Java 21. Android Studio's bundled JDK 25 and Corretto 17 both fail; JDK 21 works.
- **"The filename, directory name, or volume label syntax is incorrect"** at configuration time: `local.properties` is a Java properties file, so a raw Windows path (`C:\Users\...`) loses its backslashes. Use forward slashes; the build script does.
- **`gradlew.bat` not recognised** when the shell has `NoDefaultCurrentDirectoryInExePath` set: call it by full path.
- **Status bar overlaps the header on Android 15.** Keep `android.adjustMarginsForEdgeToEdge: "auto"` in `capacitor.config.json` and the dark `windowBackground` in `AppTheme.NoActionBar` if you regenerate the Android project.

Opening `mobile/android` in Android Studio also works (Build, Build APK(s)) once its Gradle JDK is set to 21.

### Play Store bundle

```bash
npm run android:release                   # -> dist/Spintelligence-release.aab (+ a signed release .apk)
```

Release builds are signed with the upload keystore named in `mobile/android/keystore.properties` (git-ignored, next to the keystore itself). Keep both backed up: Google Play cannot replace a lost upload key. Bump `versionCode` in `mobile/android/app/build.gradle` before each upload. The listing text and the console form answers are in `store/play-listing.md`.

## iOS (on a Mac)

```bash
cd mobile
npm install
python ../tools/sync_mobile.py
npx cap add ios
npx @capacitor/assets generate --ios
npx cap sync ios
npx cap open ios                          # Xcode: pick your team, build, run on the phone
```

A free Apple ID signs the app for your own phone (re-sign every 7 days); TestFlight and the App Store need a paid developer account. Until then, iPhones use the web app.

## Keeping the engine in sync

`beycounter/engine.py` (Python) and the engine section of `web/app.js` implement the same model with the same constants. Change both, run `python -m pytest`, and check a known matchup in the web app.
