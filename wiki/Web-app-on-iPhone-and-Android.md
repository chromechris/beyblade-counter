# Web app on iPhone and Android

The web app at **https://chromechris.github.io/beyblade-counter/** is the same Beytelligence as the Android and Windows apps, served over HTTPS. It installs to the home screen without an app store and works offline after the first visit. On iPhone this is the way to run Beytelligence, since a native iOS build needs a Mac to compile.

## iPhone and iPad

1. Open the URL in **Safari** (other browsers on iOS cannot install web apps).
2. Tap the **Share** button, then **Add to Home Screen**, then **Add**.
3. Open Beytelligence from the home screen. It runs full-screen with its own icon.
4. Leave it open for a few seconds on first use. When the toast **"Offline cache secured: 369 photos saved on this device"** appears, everything is on the phone and the app works in airplane mode.

## Android (web version)

Open the URL in Chrome and choose **Install app** from the menu (or tap the install banner). The native APK ([Installing on Android](Installing-on-Android.md)) does the same job without needing the first online visit.

## Desktop browsers

Chrome and Edge offer **Install Beytelligence** in the address bar. The Windows exe ([Installing on Windows](Installing-on-Windows.md)) is the alternative when you prefer a plain program.

## Updates

Push a new version to the site and the installed app picks it up the next time it is opened online. No reinstall is needed.

## Storage notes

- The arsenal is stored in the browser's local storage for that site. Clearing site data removes it, so use **Export JSON** for a backup.
- Safari can discard a site's stored data after a few weeks without use when the site is *not* on the home screen. Installed home-screen apps keep their data.
- The offline cache (app shell, database, photos) takes about 14 MB.
