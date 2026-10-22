# How the assessment works

The score is built only from published information: the official type triangle and the stat numbers printed on each part. The same model runs in the app (`web/app.js`) and in the Python engine (`beycounter/engine.py`), and every recommendation prints the numbers it used.

## 1. Stat totals

A combo's totals follow the official stat sheet:

- **Attack, Defense, Stamina** = sum over the blade-side parts (blade, or lock chip + main blade + assist blades) + ratchet + bit.
- **Dash** and **Burst Resistance** come from the bit only.
- **Weight** = sum of all parts.

Example: DranBuster 1-60A = 70 + 17 + 40 = **127** attack, 20 + 9 + 10 = **39** defense, 10 + 4 + 10 = **24** stamina, dash **40**, burst resistance **80**, 45.1 g.

## 2. Three ways to win

For a candidate **C** against the target **O**, the engine measures how much pressure C puts on O along each way a battle is decided, and the same in the other direction.

| Win path | Margin (C pressing O) |
| --- | --- |
| Knock-out | (C.attack + 0.25 × C.dash) − O.defense + 2.0 × (C.weight − O.weight) − 15 |
| Burst | C.attack − O.burst_resistance − 25 |
| Spin finish | C.stamina − O.stamina |

Each margin is divided by a scale (25 for knock-out, 30 for burst, 20 for spin) and passed through a logistic curve, giving a pressure between 0 and 1. The field notes show these as percentages: "spin finish, stamina 63 vs their 24 (88% pressure)".

A bey's **combined pressure** is mostly its best path, with a smaller share for the average of all three:

```
combined = 0.65 × best + 0.35 × (ko + burst + spin) / 3
```

## 3. Type triangle

Attack beats Stamina, Stamina beats Defense, Defense beats Attack; Balance is neutral. `type_edge` is +1 when C's type beats O's, −1 when it loses, 0 otherwise.

## 4. Score

```
score = 100 × sigmoid( 3.0 × (combined_C − combined_O) + 1.1 × type_edge )
```

| Score | Verdict |
| --- | --- |
| 70 to 100 | Strong counter |
| 55 to 69 | Favourable |
| 45 to 54 | Even |
| 30 to 44 | Unfavourable |
| 0 to 29 | Bad matchup |

Candidates are ranked by score; ties break alphabetically.

## 5. Estimated stats

Seven parts have no published numbers yet. They get the average of published parts of the same kind and type, and any assessment that depends on them is marked **partly estimated**.

## 6. What the score is not

The published stats are comparison labels from the manufacturer, not measurements. The score says which numbers favour which bey; it does not know your launch, the stadium, or how worn a part is. Treat 70+ as "the numbers are clearly on your side", not as a 70 % chance of winning.

## Constants

| Constant | Value | Role |
| --- | --- | --- |
| KO_SCALE | 25 | logistic scale for the knock-out margin |
| BURST_SCALE | 30 | logistic scale for the burst margin |
| SPIN_SCALE | 20 | logistic scale for the spin margin |
| DASH_WEIGHT | 0.25 | attack bonus per Dash point on the knock-out path |
| WEIGHT_PER_GRAM | 2.0 | knock-out margin per gram of weight difference |
| TYPE_BONUS | 1.1 | logit bonus for a favourable type matchup |
| MARGIN_GAIN | 3.0 | logit gain on the pressure difference |

They live at the top of `beycounter/engine.py` and in the `K` object in `web/app.js`; change both to keep the app and the CLI in step.
