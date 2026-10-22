# Using Beytelligence

Beytelligence has three screens, numbered like steps in a file: **01 Target analysis**, **02 My arsenal** and **03 Dossiers**. The screens are identical in the web app, the Android app and the Windows app.

## 01 Target analysis

1. Type the opponent's Beyblade in the **Identify the target** box. Takara Tomy names (*Dran Buster*), Hasbro names (*Buster Dran*), product codes (*UX-01*) and partial names all match. Use the arrow keys and Enter, or tap a result.
2. The **Subject file** shows the target's photo, type and **Threat profile**: its Attack, Defense, Stamina, Dash and Burst Resistance totals and its weight. **Full dossier** opens its components; **New target** clears it.
3. **Recommended assets** lists the best counters, ranked. Switch the pool between **All known models** and **My arsenal**, and filter by line (BX, UX, CX, Hasbro), by type, and by how many to show.

### Reading an assessment card

Each card is one candidate against the current target.

- **Ring and number**: the assessment score from 0 to 100. Above 55 is in your favour, above 70 is a strong counter.
- **Stamp**: the verdict band.

| Score | Stamp |
| --- | --- |
| 70 to 100 | Strong counter |
| 55 to 69 | Favourable |
| 45 to 54 | Even |
| 30 to 44 | Unfavourable |
| 0 to 29 | Bad matchup |

- **Field notes** explain the number: the type matchup (official triangle), your best **attack vector** (knock-out, burst or spin finish, with the stats behind it and the pressure it generates), and the opponent's main **threat** against you. A note says so when any part's stats were estimated.

Tap a card to open its dossier, from which you can **Set as target** (to see who counters *it*) or **Add to arsenal**.

## 02 My arsenal

Log the Beyblades you own so Target analysis can pick the best counter you actually have.

- **Log an asset**: type a name and pick it. Cards show the asset's stats; the **x** removes it.
- **Assemble a custom combo**: pick a blade, ratchet and bit (for Custom Line, a main blade, assist blade, optional second assist blade and lock chip). The stat totals update live; **Add to arsenal** saves the combo under its generated name, for example *PhoenixWing 9-60GF*.
- **Export JSON** writes your arsenal to a file; **Import JSON** merges a file into it. The file format is the same as the Python command line's collection file, so it moves between the apps, the web app and the CLI.
- **Wipe arsenal** removes everything after a confirmation.

The arsenal is stored on the device only. See the install pages for where each platform keeps it.

## 03 Dossiers

Every model in the database, with photo, type and stats. Filter by name, line and type. Open a dossier to see each component with its published numbers (and weight), aliases and release information, then **Set as target** or **Add to arsenal** from there.

## Keyboard and gestures

- Arrow keys move through search matches, **Enter** picks, **Esc** closes a dossier.
- On phones the three tabs sit in one row under the header; everything else scrolls.

## Status line

The header's status line (*online · 248 subject files · 260 component records*) confirms the database loaded. "Uplink failed" means the page was opened as a plain file instead of over HTTP; see [Troubleshooting and FAQ](Troubleshooting-and-FAQ.md).
