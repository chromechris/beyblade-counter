# Google Play listing: Spintelligence

Everything the Play Console asks for, ready to paste. Assets: `store/feature-graphic.png` (1024x500),
`store/icon-512.png`, phone screenshots in `store/screenshots/` (1080x2400). Upload file:
`dist/Spintelligence-release.aab` (built by `npm run android:release`).

## App details

| Field | Value |
| --- | --- |
| App name | Spintelligence |
| Default language | English (United States) |
| App or game | App |
| Free or paid | Free |
| Category | Tools |
| Package name (permanent) | com.chromechris.spintelligence |
| Privacy policy URL | https://chromechris.github.io/beyblade-counter/privacy.html |
| Website | https://chromechris.github.io/beyblade-counter/ |
| Contact email | (your developer account email) |

## Store listing text

**Short description** (80 characters max, 72 used):

```
Unofficial Beyblade X counter picker. Study the target, pick the counter.
```

**Full description** (4000 characters max):

```
Spintelligence studies the Beyblade X you are about to face and tells you which model is the most effective counter, using only the stat numbers printed on each part. Log the Beyblades you own and it picks the best counter from your own arsenal.

HOW IT WORKS
• 01 Target analysis: search any Beyblade X by its Takara Tomy or Hasbro name, product code or part of the name. Its subject file shows the photo, type and threat profile (Attack, Defense, Stamina, Dash, Burst Resistance, weight).
• Recommended assets: every known model ranked against the target, with an assessment score, a verdict stamp (strong counter, favourable, even, unfavourable, bad matchup) and field notes that explain the number: type advantage, your best attack vector and the opponent's main threat.
• 02 My arsenal: add the models you own or assemble a custom combo (blade, ratchet, bit, or Custom Line main blade, assist blades and lock chip) with live stat totals. Switch the finder to "My arsenal" to see the best counter you actually have. Export and import your arsenal as a file.
• 03 Dossiers: 248 official models and 260 parts across the BX, UX and CX lines and Hasbro releases, each with its published numbers, aliases and release information.

THE MODEL
Stat totals follow the official stat sheet. For every candidate the app scores the three ways a battle ends (knock-out, burst, spin finish) in both directions, adds the official type triangle (Attack beats Stamina, Stamina beats Defense, Defense beats Attack) and reports a 0–100 assessment. It compares published numbers only; launch skill, stadium and part wear are not in the file.

PRIVATE BY DESIGN
No account, no ads, no analytics, no server. The database and every photo are inside the app, so it works fully offline, and your arsenal never leaves your device.

UNOFFICIAL FAN-MADE TOOL
Spintelligence is an independent fan project. It is not affiliated with, endorsed by or sponsored by Takara Tomy, Hasbro or the Beyblade franchise. Beyblade and Beyblade X are trademarks of their respective owners. Product names and photos are used only to identify the parts. Stats are the values published by Takara Tomy / Hasbro as transcribed by the Beyblade Wiki (CC BY-SA). Source code: github.com/chromechris/beyblade-counter
```

## Graphics

| Asset | Requirement | File |
| --- | --- | --- |
| App icon | 512x512 PNG, 32-bit, under 1 MB | `store/icon-512.png` |
| Feature graphic | 1024x500 PNG or JPEG | `store/feature-graphic.png` |
| Phone screenshots | 2 to 8, 16:9 or 9:16, 320 to 3840 px | `store/screenshots/` |
| 7-inch / 10-inch tablet screenshots | optional unless you want tablet promotion | capture from a tablet emulator if wanted |

## Policy forms (App content section)

| Form | Answer |
| --- | --- |
| Privacy policy | https://chromechris.github.io/beyblade-counter/privacy.html |
| Ads | No, the app does not contain ads |
| App access | All functionality is available without special access (no login) |
| Content rating (IARC questionnaire) | Category: Utility / Productivity / Reference. No violence, sexual content, language, controlled substances, gambling, user interaction, personal info sharing, location sharing or purchases. Expected rating: Everyone |
| Target audience and content | Target age groups: 13 and over (not designed for children). The app does not unintentionally appeal to children in a way that triggers the Families policy; if the review disagrees, the Families program is still passable because there are no ads, purchases or data collection |
| News app | No |
| COVID-19 contact tracing / status | No |
| Data safety | Does the app collect or share user data: **No**. No data collected, no data shared, no data encrypted in transit (none leaves the device), users can delete all data by uninstalling or clearing data. No third-party SDKs |
| Government app | No |
| Financial features | None |
| Health | Not a health app |
| Advertising ID | The app does not use the advertising ID |

## Release notes (first release)

```
First release of Spintelligence: Beyblade X counter picker with 248 official models, offline database and photos, your own arsenal, custom combos, export/import. Unofficial fan-made tool.
```

## Before every upload

1. Bump `versionCode` (and `versionName`) in `mobile/android/app/build.gradle`.
2. `npm run android:release` in `mobile/`.
3. Upload `dist/Spintelligence-release.aab` to the chosen track (Internal testing first, then Closed testing for the 14-day requirement, then Production).
4. Keep `mobile/android/release.keystore` and `keystore.properties` backed up somewhere safe: Google Play cannot replace a lost upload key, and Play App Signing takes over the final signing key on the first upload.
