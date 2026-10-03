# Beytelligence

*Beyblade X counter intelligence.* Beytelligence studies the Beyblade you are
about to face and tells you which model is the most effective counter, using
only the official published part stats. It also keeps your own arsenal and
picks the best bey *you own* for any target. The UI is styled as a classified
field-intelligence console: subject files, threat profiles, assessment stamps
and field notes - because the way to beat an opponent is to study it first.

Live web app (installable on iPhone / Android, works offline):
**https://chromechris.github.io/beyblade-counter/**

No third-party packages are needed (Python 3.10+).

## Web UI (recommended)

```bash
cd Beyblade_Counter
python serve.py
```

This opens `http://localhost:8792/web/` in your browser:

* **01 Target analysis** - type the target's Beyblade (Takara Tomy or Hasbro
  name), get its subject file (photo, threat profile) and the ranked
  counter-assets, each with an assessment ring, a verdict stamp and the field
  notes behind the pick. Switch the pool to *My arsenal* to rank only the
  Beyblades you own; filter by line (BX / UX / CX / Hasbro) or type.
* **02 My arsenal** - log official models by name, or assemble a custom combo
  (Blade + Ratchet + Bit, or a Custom Line main blade + assist blade + lock
  chip) with live stat totals. Export / import it as JSON (same format as the
  CLI collection file).
* **03 Dossiers** - every model with photos; open any file for its components,
  each part's published numbers, aliases and release info.

The arsenal is kept in the browser's local storage. Photos live in
`web/img/` (run `python tools/fetch_images.py` to download them again).

## Windows desktop app (.exe)

`dist/Beytelligence.exe` is a single-file desktop program: double-click it and
the same UI opens in its own window (it uses the WebView2 engine that ships
with Windows 10/11). No Python needed on the target PC. The arsenal is saved
in `%APPDATA%\BeybladeCounter`, so it survives updates of the exe.

Rebuild it after changing the web app or the database:

```bash
pip install pyinstaller pywebview
python tools/build_desktop.py        # -> dist/Beytelligence.exe (~30 MB)
```

`python desktop.py` runs the same window straight from source.

## Android app (.apk)

`mobile/` is a [Capacitor](https://capacitorjs.com) project that wraps the web
app in a native shell. The built debug APK is at
`mobile/android/app/build/outputs/apk/debug/app-debug.apk` (a copy lands in
`dist/BeyCounter-debug.apk` next to the Windows exe). Copy it to the
phone (USB, Drive, email...), open it and allow "install from unknown sources"
once. It runs fully offline: the database and every photo are inside the APK,
and the collection is kept in the app's own storage (use Export to back it up).

Rebuild after changing the web app or the database (needs Node 20+, JDK 21 and
the Android SDK; the first build downloads Gradle and the Android plugins):

```bash
cd mobile
npm install
npm run android              # = python ../tools/build_android.py
npm run android:install      # same, then installs + launches it on the connected phone / emulator
```

`tools/build_android.py` copies `web/` into `mobile/www` (without `sw.js`),
runs `npx cap sync android` and `gradlew assembleDebug`. It picks the JDK and
the SDK itself (JDK 21 in `C:\Program Files\Java\jdk-21`, SDK in
`%LOCALAPPDATA%\Android\Sdk`; override with `BEYCOUNTER_JDK` / `ANDROID_HOME`)
and rewrites `mobile/android/local.properties` each time.

Things that bit once, so you do not have to find them again:

* Gradle 8.11 (Capacitor 7) runs on JDK 17-23 and compiles for Java 21, so
  Android Studio's bundled JDK 25 and Corretto 17 both fail. JDK 21 works.
* `local.properties` is a Java *properties* file, where `\` is an escape
  character: a raw `C:\Users\...` path becomes `C:Users...` and the build dies
  with *"The filename, directory name, or volume label syntax is incorrect"*.
  Write the path with forward slashes (the build script does).
* Opening `mobile/android` in Android Studio also works (Build > Build APK(s),
  or Run on an emulator) once its Gradle JDK is set to JDK 21.
* Android 15 draws apps edge-to-edge (under the status bar). `capacitor.config.json`
  sets `android.adjustMarginsForEdgeToEdge: "auto"` and `AppTheme.NoActionBar` in
  `mobile/android/app/src/main/res/values/styles.xml` paints the bands behind the
  system bars dark; keep both if you regenerate the Android project.

To put it on the Play Store you would need a release keystore and a Google
Play developer account; the debug APK is for your own devices.

## iPhone / iPad

An iOS app can only be compiled on a Mac with Xcode, which cannot be done from
Windows. Two options:

### Install it as a web app (no Mac needed)

The site is an installable web app (PWA). It needs to be served over HTTPS:

1. Publish `web/` on any static host. This repository does it with GitHub
   Pages: the workflow in `.github/workflows/pages.yml` publishes `web/` on
   every push to `main` (Pages source: *GitHub Actions*), and the app lives at
   https://chromechris.github.io/beyblade-counter/ .
2. On the iPhone open that URL in Safari, tap *Share* -> *Add to Home Screen*.
   It gets its own icon, opens full-screen (notch and home bar handled) and the
   service worker keeps the app, the database and all 369 photos on the phone:
   the first visit shows "Ready for offline use" once the photos are saved.
   On Android, Chrome offers *Install app* for the same URL.

Updates: push a new version; the installed app refreshes itself the next time
it is opened online. Bump `SHELL_VERSION` in `web/sw.js` when you change the
list of files it pre-caches. To try the offline behaviour on the PC, run
`python serve.py` (the service worker also registers on `localhost`), load the
page once, stop the server and reload.

### Native build on a Mac

```bash
cd mobile
npm install
python ../tools/sync_mobile.py
npx cap add ios          # creates mobile/ios from capacitor.config.json
npx cap sync ios
npx cap open ios         # opens the project in Xcode: pick your team, build, run on the phone
```

The app id (`app.beycounter`), name, colours and the icon source
(`mobile/assets/`) are already configured; run
`npx @capacitor/assets generate --ios` after `cap add ios` to create the icon
set. A free Apple ID can sign the app for your own phone (re-sign every 7 days);
TestFlight / App Store need a paid developer account.

## Command line

```bash
cd Beyblade_Counter
python -m beycounter                 # interactive menu
```

Or use direct commands:

```bash
python -m beycounter counter "DranBuster 1-60A"              # top 5 counters from the whole database
python -m beycounter counter "Wizard Rod 5-70DB" --top 10    # more results
python -m beycounter counter "Soar Phoenix 9-60GF" --line BX # only Takara Tomy BX releases
python -m beycounter mine add "WizardRod 5-70DB" "PhoenixWing 9-60GF" "KnightShield 3-80N"
python -m beycounter mine add-custom --blade "Phoenix Wing" --ratchet 9-60 --bit GF
python -m beycounter counter "DranBuster 1-60A" --mine       # best counter from MY collection
python -m beycounter versus "WizardRod 5-70DB" "DranBuster 1-60A"
python -m beycounter show "DranBrave S6-60V"
python -m beycounter search wizard
python -m beycounter list --type Defense --line UX
```

Hasbro names work too (`Buster Dran 1-60A`, `Soar Phoenix 9-60GF`), as do
partial names: an ambiguous name lists the matching releases so you can pick one.

Your collection is saved to `~/.beycounter/collection.json`
(override with `--collection PATH` or the `BEYCOUNTER_COLLECTION` env var).

## What is in the database

`beycounter/data/beyblade_x.json` - built by `tools/build_database.py` from the
[Beyblade Wiki](https://beyblade.fandom.com) (CC BY-SA), which transcribes the
stats printed by Takara Tomy / Hasbro:

* **260 parts**: every Blade, Ratchet, Bit, Lock Chip, Main Blade and Assist Blade
  of the Basic (BX), Unique (UX) and Custom (CX) lines, with the published
  Attack / Defense / Stamina values, Dash and Burst Resistance (Bits), and weight.
* **~245 official models**: every product combo with a wiki page plus every combo
  listed in a part's "Products" section (random boosters, sets, Hasbro
  releases and collaborations). Same combo released under two names is one
  model with the other names as aliases.

A handful of very new parts have no published numbers yet; their stats are
estimated from the averages of parts of the same class and type, and any
recommendation that relies on them says so.

Re-run `python tools/build_database.py` to refresh from the wiki
(`--offline` uses the cached pages in `tools/cache/`).

## How the counter score works (`beycounter/engine.py`)

Stat totals follow the official stat sheet: Attack, Defense and Stamina are the
sum of blade-side parts + ratchet + bit; Dash and Burst Resistance come from the
bit. Example: DranBuster 1-60A = 70+17+40 attack, 20+9+10 defense, 10+4+10
stamina, dash 40, burst resistance 80.

For a candidate **C** against opponent **O** the engine scores the three ways a
battle is actually won, in both directions:

| win path    | pressure of C on O                                              |
|-------------|-----------------------------------------------------------------|
| knock-out   | C.attack + 0.25 x C.dash  vs  O.defense, adjusted by weight difference |
| burst       | C.attack  vs  O.burst_resistance                                |
| spin finish | C.stamina  vs  O.stamina                                        |

Each margin goes through a logistic curve (0..1). C's "pressure" is mostly its
best path, with a smaller share for the average of all three. The score is

```
score = 100 * sigmoid( 3.0 * (pressure_C - pressure_O) + 1.1 * type_edge )
```

where `type_edge` is +1 / 0 / -1 from the official type triangle
(Attack beats Stamina, Stamina beats Defense, Defense beats Attack; Balance is
neutral). A score above 55 is favourable, above 70 a strong counter. Every
recommendation prints the numbers behind it so you can sanity-check it.

Published stats are comparison labels, not odds: launch skill, stadium and part
wear are not in the numbers.

## Tests

```bash
python -m pytest
```

## Layout

```
beycounter/
  database.py    load JSON, part lookup, stat totals, custom combos
  engine.py      matchup model + explanations
  collection.py  your collection (JSON on disk)
  cli.py         commands + interactive menu
  data/beyblade_x.json
tools/build_database.py   wiki scraper / database builder (+ cache/)
tools/fetch_images.py     downloads the product / part photos into web/img/
tools/make_icons.py       app icons (web/icons/, mobile/assets/) from a product photo, with the reticle
tools/build_desktop.py    Windows .exe (PyInstaller + pywebview)
tools/build_android.py    Android .apk (Capacitor + Gradle); tools/sync_mobile.py copies web/ -> mobile/www
web/                      the browser UI: index.html, app.js, style.css, data/, img/, icons/, sw.js, manifest
mobile/                   Capacitor project (android/ generated; ios/ is created on a Mac)
.github/workflows/pages.yml   publishes web/ to GitHub Pages
tests/test_beycounter.py
```
