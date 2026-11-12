# Apple App Store: Spintelligence

Everything App Store Connect asks for, plus the one-time setup for the cloud build. The iOS app is the
Capacitor project in `mobile/ios/`; it is built and uploaded by `.github/workflows/ios.yml` on a GitHub
macOS runner (no Mac needed). Screenshots: `node tools/make_ios_screenshots.mjs` -> `store/screenshots-ios/`
(1320 x 2868, the 6.9" iPhone size App Store Connect requires). The app is iPhone-only, so no iPad screenshots.

## One-time setup (owner)

1. **App record**: App Store Connect -> Apps -> "+" -> New App.
   Platform iOS, name `Spintelligence`, primary language English (U.S.), bundle ID
   `com.chromechris.spintelligence` (register it first under Certificates, Identifiers & Profiles ->
   Identifiers if it is not in the list), SKU `spintelligence`, full access.
2. **API key**: App Store Connect -> Users and Access -> Integrations -> App Store Connect API ->
   Team Keys -> "+". Name `GitHub Actions`, access **Admin** (needed for automatic signing). Download the
   `.p8` file (only possible once) and note the Key ID and the Issuer ID shown above the list.
3. **Team ID**: developer.apple.com -> Account -> Membership details -> Team ID.
4. **GitHub secrets**: github.com/chromechris/beyblade-counter -> Settings -> Secrets and variables ->
   Actions -> New repository secret, four times:
   `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8` (open the .p8 in Notepad, paste the whole text including
   the BEGIN/END lines), `APPLE_TEAM_ID`. Keep the .p8 file somewhere safe and never commit it.

## Building

GitHub -> Actions -> "iOS build" -> Run workflow.
- `upload` off: compile check for the Simulator (no secrets needed).
- `upload` on: signed build uploaded to App Store Connect. The build number is the workflow run number;
  the version is `MARKETING_VERSION` (1.0.0) in `mobile/ios/App/App.xcodeproj/project.pbxproj`.
  After 5-30 minutes it shows under TestFlight; add yourself as an internal tester and install it with
  the TestFlight app on the iPhone.

## App information

| Field | Value |
| --- | --- |
| Name | Spintelligence |
| Subtitle (30 max) | Spin battle counter picker |
| Primary category | Utilities |
| Secondary category | Reference |
| Price | Free |
| Privacy policy URL | https://chromechris.github.io/beyblade-counter/privacy.html |
| Support URL | https://github.com/chromechris/beyblade-counter |
| Marketing URL | https://chromechris.github.io/beyblade-counter/ |
| Copyright | 2026 chromechris (owner: use the name you want shown) |
| Content rights | "Does your app contain, show, or access third-party content?" -> **Yes** (product names and photos used to identify parts; stats transcribed by the Beyblade Wiki under CC BY-SA). Apple then asks you to confirm you have the rights to use it: that statement is the owner's call |

**Promotional text** (170 max):

```
Name the Beyblade X you are about to face and get the counter that beats it, from every official model or from the ones you own. Works fully offline.
```

**Keywords** (100 max; no trademarks, Apple rejects other brands in keywords):

```
spinning top,counter,battle,stats,matchup,arsenal,combo,blader,stamina,attack,defense,picker
```

**Description**: same text as the full description in `store/play-listing.md` (it fits Apple's 4000
characters and already carries the unofficial fan-made notice).

## Age rating

All questionnaire answers "None" / "No" (no violence, mature themes, gambling, contests, web browsing,
user-generated content, messaging). Expected rating: 4+.

## App Privacy

Data collection: **No, we do not collect data from this app.** (No account, no analytics, no ads, no
network calls except loading the bundled pages; the arsenal stays in local storage on the device.)

## App Review notes

```
Spintelligence is an unofficial, free fan tool for the Beyblade X spinning-top game. It needs no account and works fully offline: the database of official part stats and the product photos are bundled in the app.
How to try it: on "Target analysis" type a name such as "Dran Buster" and pick it; the app ranks every model by how well it counters that target and explains each score. "My arsenal" lets you log the tops you own (or assemble a custom combo) so the ranking can use only those. "Dossiers" lists every model with its stats.
Product names and photos are used only to identify the parts; the app states on its About screen, footer and in this listing that it is not affiliated with Takara Tomy, Hasbro or the Beyblade franchise.
```

## Before every upload

1. Change `MARKETING_VERSION` for a new version (the build number rises by itself with each run).
2. Run the workflow with `upload` on.
3. In App Store Connect select the new build on the version page, then "Add for Review" / "Submit".
