# Installing on Windows

The Windows app is a single file, `Beytelligence.exe` (about 29 MB). There is nothing to install: run it and the app opens in its own window. It needs no Python and no internet connection.

## Requirements

- Windows 10 or 11, 64-bit.
- The Microsoft Edge **WebView2** runtime. Windows 11 ships with it, and almost every Windows 10 PC has it through Microsoft Edge. If the window opens blank, install the Evergreen runtime from https://developer.microsoft.com/microsoft-edge/webview2/ and start the app again.

## Get the file

Build outputs are not stored in the repository. Get `Beytelligence.exe` from whoever built it (it lands in `dist/` after `python tools/build_desktop.py`), from the repository's Releases page when a release is published, or build it yourself: see [Building from source](Building-from-source.md).

## First run

1. Double-click `Beytelligence.exe`. The first start takes a few seconds while the single file unpacks itself; later starts are faster.
2. SmartScreen may show **"Windows protected your PC"** because the file is not code-signed. Click **More info**, then **Run anyway**. This happens once per download location.
3. Some antivirus products flag any PyInstaller-packed program as suspicious. The source is open and the build is reproducible; add an exception if your product blocks the file.

The app opens at 1280 x 860 and can be resized down to 400 x 600. Close it like any window; there is no background process.

## Where your data lives

The arsenal is stored in `%APPDATA%\BeybladeCounter` (the folder name is kept from the first release so earlier collections carry over). It survives replacing the exe. To reset the app, close it and delete that folder. **Export JSON** saves a backup wherever you choose; **Import JSON** reads it back on any platform.

## Update

Replace `Beytelligence.exe` with the new file. Nothing else changes and your arsenal stays.

## Portable use

The exe can live on a USB stick, but the data folder is per Windows user profile, not next to the exe. Export your arsenal if you move between PCs.

## See also

- [Using Beytelligence](Using-Beytelligence.md)
- [Troubleshooting and FAQ](Troubleshooting-and-FAQ.md)
