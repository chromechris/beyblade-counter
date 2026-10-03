"""Matchup engine: which Beyblade is the most effective counter to another.

The score is built only from published information:

1. Type triangle (official): Attack beats Stamina, Stamina beats Defense,
   Defense beats Attack.  Balance is neutral.
2. Published stat totals, compared the way a battle is actually decided:
     * Knock-out  : my Attack (+ a Dash bonus for Xtreme Dash) vs. their Defense,
                    adjusted by the weight difference (heavier beys are harder
                    to move and hit harder).
     * Burst      : my Attack vs. their Burst Resistance.
     * Spin finish: my Stamina vs. their Stamina.
   Each path is turned into a 0..1 "pressure" with a logistic curve, for both
   beys.  A bey is a good counter when its best win path is strong AND the
   opponent's best path against it is weak.

The result is a 0-100 score (roughly a win likelihood) plus a plain-English
explanation, so the recommendation can be checked against the numbers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .database import Database, Model, Totals

BEATS = {"Attack": "Stamina", "Stamina": "Defense", "Defense": "Attack"}

# Tuning constants (stat totals range roughly: attack 40-140, defense 20-110,
# stamina 15-110, dash 10-45, burst resistance 10-80, weight 35-55 g).
KO_SCALE = 25.0
BURST_SCALE = 30.0
SPIN_SCALE = 20.0
DASH_WEIGHT = 0.25        # attack bonus per Dash point on the knock-out path
WEIGHT_PER_GRAM = 2.0     # knock-out margin points per gram of weight difference
TYPE_BONUS = 1.1          # logit bonus for a favourable type matchup
MARGIN_GAIN = 3.0         # logit gain on (my pressure - their pressure)


def _sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def type_advantage(mine: str, theirs: str) -> int:
    """+1 if `mine` beats `theirs`, -1 if it loses, 0 if neutral."""
    if BEATS.get(mine) == theirs:
        return 1
    if BEATS.get(theirs) == mine:
        return -1
    return 0


@dataclass(frozen=True)
class Pressure:
    ko: float
    burst: float
    spin: float

    @property
    def best(self) -> float:
        return max(self.ko, self.burst, self.spin)

    @property
    def best_path(self) -> str:
        return max((self.ko, "knock-out"), (self.burst, "burst"), (self.spin, "spin finish"))[1]

    @property
    def combined(self) -> float:
        return 0.65 * self.best + 0.35 * (self.ko + self.burst + self.spin) / 3


def pressure(me: Totals, them: Totals) -> Pressure:
    """How strongly `me` threatens `them` on each win path (0..1 each)."""
    ko_margin = (me.attack + DASH_WEIGHT * me.dash) - them.defense \
        + WEIGHT_PER_GRAM * (me.weight_g - them.weight_g) - 15.0
    burst_margin = me.attack - them.burst_resistance - 25.0
    spin_margin = me.stamina - them.stamina
    return Pressure(_sig(ko_margin / KO_SCALE), _sig(burst_margin / BURST_SCALE), _sig(spin_margin / SPIN_SCALE))


@dataclass
class Matchup:
    candidate: Model
    opponent: Model
    cand_totals: Totals
    opp_totals: Totals
    offense: Pressure      # candidate threatening the opponent
    threat: Pressure       # opponent threatening the candidate
    type_adv: int
    score: float           # 0..100

    @property
    def verdict(self) -> str:
        if self.score >= 70:
            return "strong counter"
        if self.score >= 55:
            return "favourable"
        if self.score >= 45:
            return "even"
        if self.score >= 30:
            return "unfavourable"
        return "bad matchup"

    def explain(self) -> list[str]:
        c, o = self.cand_totals, self.opp_totals
        cm, om = self.candidate, self.opponent
        notes = []
        if self.type_adv > 0:
            notes.append(f"Type edge: {cm.type} beats {om.type} (official type triangle).")
        elif self.type_adv < 0:
            notes.append(f"Type disadvantage: {om.type} beats {cm.type} (official type triangle).")
        else:
            notes.append(f"Neutral typing: {cm.type} vs {om.type}.")
        path = self.offense.best_path
        if path == "knock-out":
            notes.append(f"Best win path: knock-out - attack {c.attack:.0f} (+dash {c.dash:.0f}) vs their defense "
                         f"{o.defense:.0f}, weight {c.weight_g:.1f} g vs {o.weight_g:.1f} g "
                         f"({self.offense.ko:.0%} pressure).")
        elif path == "burst":
            notes.append(f"Best win path: burst - attack {c.attack:.0f} vs their burst resistance "
                         f"{o.burst_resistance:.0f} ({self.offense.burst:.0%} pressure).")
        else:
            notes.append(f"Best win path: spin finish - stamina {c.stamina:.0f} vs their {o.stamina:.0f} "
                         f"({self.offense.spin:.0%} pressure).")
        tp = self.threat.best_path
        if tp == "knock-out":
            notes.append(f"Their main threat: knock-out - their attack {o.attack:.0f} vs your defense "
                         f"{c.defense:.0f} ({self.threat.ko:.0%}).")
        elif tp == "burst":
            notes.append(f"Their main threat: burst - their attack {o.attack:.0f} vs your burst resistance "
                         f"{c.burst_resistance:.0f} ({self.threat.burst:.0%}).")
        else:
            notes.append(f"Their main threat: outspinning you - stamina {o.stamina:.0f} vs your "
                         f"{c.stamina:.0f} ({self.threat.spin:.0%}).")
        if c.estimated or o.estimated:
            notes.append("Note: some part stats are not published yet and were estimated from type averages.")
        return notes


def evaluate(db: Database, candidate: Model, opponent: Model) -> Matchup:
    ct, ot = db.totals(candidate), db.totals(opponent)
    off = pressure(ct, ot)
    thr = pressure(ot, ct)
    adv = type_advantage(candidate.type, opponent.type)
    logit = MARGIN_GAIN * (off.combined - thr.combined) + TYPE_BONUS * adv
    return Matchup(candidate, opponent, ct, ot, off, thr, adv, round(100 * _sig(logit), 1))


def rank_counters(db: Database, opponent: Model, candidates: list[Model] | None = None,
                  top: int = 5, exclude_self: bool = True) -> list[Matchup]:
    """Rank `candidates` (default: every official model) against `opponent`."""
    if candidates is None:
        candidates = list(db.models.values())
    results = []
    for c in candidates:
        if exclude_self and not c.custom and c.id == opponent.id:
            continue
        results.append(evaluate(db, c, opponent))
    results.sort(key=lambda m: (-m.score, m.candidate.name))
    return results[:top] if top else results
