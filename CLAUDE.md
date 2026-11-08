# Spintelligence: project guide for agents

Read this first. It is the hand-off for anyone (human or agent) picking the project up cold.
Last updated 2026-11-07.

## What this is

Spintelligence is a **Beyblade X counter picker**: you name the opponent's Beyblade and it ranks every
official model (or only the ones you own) by how well it counters that opponent, using nothing but the
Attack / Defense / Stamina / Dash / Burst-Resistance / weight values Takara Tomy and Hasbro print on the
parts. The UI is themed as a classified "field intelligence" console (subject files, threat profiles,
assessment stamps, field notes). It is an **unofficial fan-made tool**: not affiliated with Takara Tomy,
Hasbro or the Beyblade franchise; that notice must stay in the app footer, the About dialog, the README,
the wiki, the store listing and the whitepaper.

One web core (`web/`, plain HTML/CSS/JS, no build step) is shipped four ways:

| Deliverable | Where | How it is built | Status (2026-11-07) |
| --- | --- | --- | --- |
| Web app / PWA | https://chromechris.github.io/beyblade-counter/ | push to `main` -> `.github/workflows/pages.yml` publishes `web/` | live, installable, offline after first visit |
| Android debug APK | `dist/Spintelligence-debug.apk` | `cd mobile && npm run android` (= `python tools/build_android.py`) | verified on an Android 15 emulator offline |
| Android Play bundle | `dist/Spintelligence-release.aab` (+ signed `.apk`) | `npm run android:release` (= `build_android.py --release`) | built and signed; **not uploaded**, see Play section |
| Windows exe | `dist/Spintelligence.exe` | `python tools/build_desktop.py` (PyInstaller + pywebview/WebView2) | built |
| Python engine + CLI | `beycounter/` | `python -m beycounter ...`, tests `python -m pytest` (8) | same model as the web app |
| iOS | `mobile/` (Capacitor) | `npx cap add ios` on a Mac; no Mac available | iPhone uses the PWA |

Docs: `README.md` (user-facing), `wiki/` (nine pages, source of the GitHub wiki), `store/play-listing.md`
(Play Console text and form answers), and a whitepaper that lives as a Claude Doc (link in the agent memory
for this project; export to PDF from there). `dist/` and all build outputs are git-ignored; binaries exist
only on this PC.

## Naming history (do not "fix" these)

- Working title "Beyblade X Counter Picker" (2026-10-03) -> "Beytelligence" (10-03) -> **"Spintelligence"**
  (10-28, to keep the trademark out of the app name).
- GitHub repo stayed `chromechris/beyblade-counter`; Python package stayed `beycounter`.
- Android package is `com.chromechris.spintelligence` (permanent once on Play). The earlier debug app
  `app.beycounter` is a different app; its arsenal does not carry over except via Export/Import JSON.
- Windows data folder stayed `%APPDATA%\BeybladeCounter` so earlier collections survive.

## Repository layout

```
beycounter/        Python engine (engine.py = scoring model), database loader, collection, CLI, data/beyblade_x.json
web/               index.html, app.js (same model as engine.py, UI), style.css (theme), sw.js (offline cache),
                   manifest.webmanifest, privacy.html, data/beyblade_x.json, img/ (369 photos), icons/
mobile/            Capacitor 7 project: capacitor.config.json, android/ (generated project, committed), assets/ (icon sources)
                   android/keystore.properties + release.keystore = upload key, GIT-IGNORED, never commit or print
store/             Play listing text, feature-graphic.png, icon-512.png, screenshots/ (git-ignored)
tools/             build_database.py (wiki scrape -> JSON, --offline uses tools/cache), fetch_images.py, make_icons.py,
                   make_store_assets.py, build_desktop.py, build_android.py, sync_mobile.py, build_artifact.py, publish_wiki.py
wiki/              documentation pages; tools/publish_wiki.py pushes them to the GitHub wiki
tests/             pytest for engine + database
.github/           Pages deployment workflow (runs on pushes that touch web/)
.claude/launch.json  dev server entry "beyblade" = python serve.py 8792 -> http://localhost:8792/web/
```

## How it works (the parts an agent must not break)

- **Data**: 248 models, 260 parts, scraped from the Beyblade Wiki (CC BY-SA) by `tools/build_database.py`;
  the JSON is copied into `web/data/`. Seven parts have no published stats and are estimated from averages
  (the UI says "partly estimated"). Seven referenced photos are missing (placeholder shown).
- **Model** (identical in `beycounter/engine.py` and the `K` constants + `pressure()`/`evaluate()` in
  `web/app.js`; change both): totals per the official stat sheet; three win paths (knock-out, burst, spin
  finish) each a logistic of a margin (scales 25/30/20, dash x0.25, 2.0 per gram); combined = 0.65 x best +
  0.35 x mean; score = 100 x sigmoid(3.0 x (P_C - P_O) + 1.1 x type_edge); bands 70/55/45/30.
- **Offline**: the web app's `sw.js` precaches the shell + database and, after `app.js` posts the photo
  list, all photos. Bump `SHELL_VERSION` in `sw.js` when the precache list changes. The service worker is
  skipped inside Capacitor (`window.Capacitor`) and registers on localhost for testing.
- **Mobile**: `tools/sync_mobile.py` copies `web/` -> `mobile/www` (minus `sw.js`); `npx cap sync android`
  copies that into `android/app/src/main/assets/public`. Android 15 edge-to-edge is handled by
  `adjustMarginsForEdgeToEdge: "auto"` in `capacitor.config.json` plus the dark `windowBackground` in
  `android/app/src/main/res/values/styles.xml`; keep both if the project is regenerated.
- **Release signing**: `android/app/build.gradle` reads `keystore.properties` if present and signs release
  builds with it. Bump `versionCode` before every Play upload.
- **Desktop**: `desktop.py` serves `web/` on 127.0.0.1 and opens a pywebview window; PyInstaller bundles it.

## Toolchain that is known to work on this PC

JDK 21 at `C:\Program Files\Java\jdk-21` (Corretto 17 is too old, Android Studio's JDK 25 too new),
Android SDK at `%LOCALAPPDATA%\Android\Sdk` (platforms 35 and 36, build-tools 36), Node 22, Python 3.10
with PyInstaller, pywebview, Pillow, pytest. `build_android.py` forces the JDK and SDK itself. The emulator
`Medium_Phone_API_35` exists for install tests (`emulator -avd Medium_Phone_API_35 -no-window ...`).

## Gotchas already paid for

- `mobile/android/local.properties` must use forward slashes; a raw `C:\Users\...` path dies in the Java
  properties parser with "The filename, directory name, or volume label syntax is incorrect".
- This PC sets `NoDefaultCurrentDirectoryInExePath=1`: call `gradlew.bat` by full path.
- Windows paths inside Python docstrings need `r"""`.
- Very long shell heredocs get mangled by the agent tooling; write big files with a file-writing tool or run
  a script file instead.
- GitHub creates a repo wiki only after a first page is made in the browser; until then
  `tools/publish_wiki.py` cannot push (as of 2026-11-07 that click is still pending).
- Google Play personal accounts need a closed test (12 testers, 14 days) before production.

## Rules from the owner

- Never stop processes by scanning for `python.exe` or similar; only by a PID you started or an exact name.
- Ask before creating or pushing repositories or publishing anything new (a release, a store listing, a
  public page). Routine commits to this repo for requested work are fine.
- Keep README, wiki, store listing and the whitepaper consistent whenever behaviour, names or builds change.
- The keystore and its passwords stay out of git and out of chat.

## Open items

- Google Play: developer account, closed test, upload of `dist/Spintelligence-release.aab` (listing text and
  form answers are ready in `store/play-listing.md`; privacy policy at
  https://chromechris.github.io/beyblade-counter/privacy.html).
- GitHub wiki: owner clicks "Create the first page", then `python tools/publish_wiki.py`.
- Optional: GitHub Release with the APK and exe attached; a LICENSE file; the 7 missing photos; code
  signing for the Windows exe; native iOS build when a Mac is available.
