# Troubleshooting and FAQ

## Android

**"App not installed" when updating.** The new APK was signed with a different development key (built on another PC). Export your arsenal, uninstall the old app, install the new one, import the file.

**Play Protect says the app is from an unknown developer.** Expected for a sideloaded debug build. Choose *More details*, then *Install anyway*.

**The install button is greyed out.** Another app is drawing over the screen (a screen filter, a chat bubble). Close it and try again.

**Photos show a grey placeholder.** Seven models have no photo in the database yet; everything else is bundled in the APK. If every photo is missing, the APK was built from an incomplete `web/img/` folder: run `python tools/fetch_images.py` and rebuild.

## Windows

**"Windows protected your PC".** The exe is not code-signed. *More info*, then *Run anyway*.

**The window opens but stays blank.** The WebView2 runtime is missing. Install the Evergreen runtime from Microsoft and start the app again.

**Antivirus quarantines the file.** PyInstaller-packed programs trigger heuristics in some products. Restore it and add an exception, or build the exe yourself from the source.

**First start is slow.** The single-file exe unpacks to a temporary folder on each start; a few seconds is normal.

## Web app

**No "Offline cache secured" toast.** The service worker only runs over HTTPS (or on `localhost`). Also give the first visit a few seconds online while the photos download.

**Safari lost my arsenal.** Safari can clear a site's data after a few weeks without use when the page is not installed on the home screen. Install it (Share, Add to Home Screen) and keep an export.

**"Uplink failed" in the header.** The page was opened as a file instead of over HTTP. Run `python serve.py` or use the hosted URL.

## Data

**Where is my arsenal?** Android: the app's private storage. Windows: `%APPDATA%\BeybladeCounter`. Web: the browser's local storage for the site. In all cases *Export JSON* makes a portable copy and *Import JSON* restores it anywhere, including the Python CLI.

**How do I reset everything?** Android: Settings, Apps, Spintelligence, Clear data. Windows: delete `%APPDATA%\BeybladeCounter`. Web: clear the site's data, or use *Wipe arsenal*.

**Can two devices share one arsenal?** Not automatically; there is no account or sync. Export on one, import on the other.

## The model

**Is the score a win probability?** No. It compares published numbers only. Treat 70+ as "the numbers are clearly on your side". See [How the assessment works](How-the-assessment-works.md).

**Why does a Balance type never get a type bonus?** Balance is neutral on the official triangle, so its edge is always 0; it wins or loses on the stat paths alone.

**A part shows "partly estimated".** Its stats have not been published; the app uses the average of similar parts and says so.

**A Beyblade is missing.** The database follows the Beyblade Wiki's part and product pages. Rebuild it with `python tools/build_database.py` after the wiki is updated, or add a custom combo from its parts in *My arsenal*.
