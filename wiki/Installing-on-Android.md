# Installing on Android

The Android app is a single file, `Spintelligence-debug.apk` (about 20 MB). It contains the whole app, the database and all 369 photos, so it works with no connection at all.

## Requirements

- Android 6.0 (Marshmallow) or later. Tested on Android 15.
- About 60 MB of free space after installation.
- No Google account, no Play Store, no permissions beyond network access (which the app only uses for the wiki link in the footer).

## Get the APK

Build outputs are not stored in the repository. Get the file from whoever built it (it lands in `dist/Spintelligence-debug.apk` after `npm run android`), from the repository's Releases page when a release is published, or build it yourself: see [Building from source](Building-from-source.md).

## Install

1. Copy the APK to the phone: USB cable, Google Drive, email attachment or a chat message to yourself all work.
2. Open the **Files** app, find the APK and tap it.
3. Android asks to allow installs from this source (Files, Drive, Gmail...). Tap **Settings**, switch **Allow from this source** on, and go back. This is asked once per source app.
4. Tap **Install**. If Google Play Protect warns that the app is from an unknown developer, choose **More details** and **Install anyway**. The warning appears because the APK is signed with a development key, not because of its contents; the source is open.
5. Tap **Open**. Spintelligence appears in the app drawer with the reticle icon.

## Update

Install the new APK over the old one. The package name (`com.chromechris.spintelligence`) stays the same, so the installation is an upgrade and your arsenal is kept. (The pre-release build named Beytelligence used a different package name; it is a separate app, so export its arsenal and import it into Spintelligence.)

One exception: if the new APK was built on a different computer, its development signing key differs and Android refuses the upgrade with "App not installed". Export your arsenal first (My arsenal, **Export JSON**), uninstall the old app, install the new one and import the file.

## Where your data lives

The arsenal is stored in the app's private storage (the WebView's local storage). It survives updates and reboots, and it is removed when the app is uninstalled or when you clear the app's data in Android settings. **Export JSON** writes a backup to the Downloads folder; **Import JSON** reads it back on any device, including the Windows app and the web app.

## Uninstall

Long-press the icon and choose **Uninstall**, or use Settings, Apps, Spintelligence, Uninstall.

## See also

- [Using Spintelligence](Using-Spintelligence.md)
- [Troubleshooting and FAQ](Troubleshooting-and-FAQ.md)
