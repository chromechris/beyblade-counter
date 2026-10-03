"""Load the official Beyblade X database and compute combo stat totals.

Stat model (official Takara Tomy / Hasbro published stats):
  * Attack, Defense, Stamina are published per part and summed across the
    blade-side parts (Blade, or Main Blade + Assist Blade(s) for Custom Line),
    the Ratchet and the Bit.
  * Dash and Burst Resistance are published for the Bit only.
  * Weight is the sum of part weights (grams).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_PATH = Path(__file__).with_name("data") / "beyblade_x.json"

TYPES = ("Attack", "Defense", "Stamina", "Balance")
BLADE_SLOTS = ("blade", "lock_chip", "main_blade", "assist_blade", "assist_blade_2")
PART_SLOTS = BLADE_SLOTS + ("ratchet", "bit")


@dataclass(frozen=True)
class Part:
    id: str
    name: str
    classification: str
    type: str | None = None
    spin: str | None = None
    system: str | None = None
    aka: str | None = None
    product_code: str | None = None
    release_jp: str | None = None
    weight_g: float | None = None
    attack: float | None = None
    defense: float | None = None
    stamina: float | None = None
    dash: float | None = None
    burst_resistance: float | None = None
    height: float | None = None
    estimated: bool = False
    image: str | None = None  # wiki image file name (see tools/fetch_images.py)


@dataclass(frozen=True)
class Totals:
    attack: float
    defense: float
    stamina: float
    dash: float
    burst_resistance: float
    weight_g: float
    estimated: bool  # True if any part stat had to be estimated

    def as_dict(self) -> dict:
        return {
            "attack": self.attack, "defense": self.defense, "stamina": self.stamina,
            "dash": self.dash, "burst_resistance": self.burst_resistance,
            "weight_g": round(self.weight_g, 1), "estimated": self.estimated,
        }


@dataclass(frozen=True)
class Model:
    """An official product combo (e.g. 'DranSword 3-60F') or a custom combo."""
    id: str
    name: str
    type: str
    spin: str | None = None
    system: str | None = None
    line: str | None = None
    product_code: str | None = None
    hasbro_name: str | None = None
    release_jp: str | None = None
    parts: dict = field(default_factory=dict)  # slot -> part id
    aliases: tuple = ()
    source: str | None = None
    custom: bool = False
    image: str | None = None

    @property
    def display_name(self) -> str:
        if self.hasbro_name and self.hasbro_name != self.name:
            return f"{self.name} / {self.hasbro_name}"
        return self.name

    def parts_summary(self, db: "Database") -> str:
        bits = []
        for slot in PART_SLOTS:
            pid = self.parts.get(slot)
            if pid and pid in db.parts:
                p = db.parts[pid]
                bits.append(f"{p.classification} {p.name}")
        return " + ".join(bits)


def _norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


class Database:
    def __init__(self, path: Path | str = DATA_PATH):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.meta: dict = data.get("meta", {})
        self.parts: dict[str, Part] = {p["id"]: Part(**p) for p in data["parts"]}
        self.models: dict[str, Model] = {}
        for m in data["models"]:
            m = dict(m)
            m["aliases"] = tuple(m.get("aliases") or ())
            self.models[m["id"]] = Model(**m)
        self._type_avgs = self._compute_type_averages()

    # ------------------------------------------------------------------ parts
    def parts_of(self, classification: str) -> list[Part]:
        return [p for p in self.parts.values() if p.classification == classification]

    @staticmethod
    def _akas(p: Part) -> list[str]:
        out = []
        for a in re.split(r"<br\s*/?>|,|/", p.aka or ""):
            a = re.sub(r"\(.*?\)", "", a).strip()
            if a:
                out.append(a)
        return out

    def find_part(self, classification: str, text: str | None) -> Part | None:
        """Find a part by name, abbreviation (AKA) or id, case/space-insensitive."""
        t = _norm(text)
        if not t:
            return None
        cands = self.parts_of(classification)
        for p in cands:  # exact id / name / aka
            if t in {_norm(p.id), _norm(p.name)} or t in {_norm(a) for a in self._akas(p)}:
                return p
        for p in cands:  # Hasbro word order: "Sword Dran" == "DranSword"
            words = re.findall(r"[A-Z][a-z]+", p.name)
            if len(words) == 2 and t == _norm(words[1] + words[0]):
                return p
        for p in cands:  # prefix / contains
            if _norm(p.name).startswith(t):
                return p
        for p in cands:
            if t in _norm(p.name):
                return p
        return None

    def _compute_type_averages(self) -> dict:
        """Average published stats per (classification, type) for estimating gaps."""
        sums: dict[tuple, list] = {}
        for p in self.parts.values():
            if p.attack is None:
                continue
            for key in ((p.classification, p.type), (p.classification, None)):
                acc = sums.setdefault(key, [0, 0, 0, 0, 0, 0, 0])
                acc[0] += 1
                acc[1] += p.attack or 0
                acc[2] += p.defense or 0
                acc[3] += p.stamina or 0
                acc[4] += p.dash or 0
                acc[5] += p.burst_resistance or 0
                acc[6] += p.weight_g or 0
        return {k: tuple(v[i] / v[0] for i in range(1, 7)) for k, v in sums.items() if v[0]}

    def part_stats(self, part: Part) -> tuple[float, float, float, float, float, float, bool]:
        """(attack, defense, stamina, dash, burst, weight, estimated) with gaps filled."""
        if part.classification == "Lock Chip":
            # Lock Chips carry no published combat stats; they only add weight.
            return 0.0, 0.0, 0.0, 0.0, 0.0, part.weight_g or 1.7, part.weight_g is None
        avg = self._type_avgs.get((part.classification, part.type)) or \
            self._type_avgs.get((part.classification, None)) or (0, 0, 0, 0, 0, 0)
        vals, est = [], False
        is_bit = part.classification == "Bit"
        for i, v in enumerate((part.attack, part.defense, part.stamina, part.dash,
                               part.burst_resistance, part.weight_g)):
            if v is None:
                if i in (3, 4) and not is_bit:
                    v = 0.0  # Dash / Burst Resistance are only published for Bits
                else:
                    est = True
                    v = avg[i]
            vals.append(float(v))
        return vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], (est or part.estimated)

    def totals(self, model: Model) -> Totals:
        atk = dfn = sta = wt = 0.0
        dash = burst = 0.0
        est = False
        for slot, pid in model.parts.items():
            part = self.parts.get(pid)
            if part is None:
                raise KeyError(f"{model.id}: unknown part {pid!r} in slot {slot}")
            a, d, s, da, b, w, e = self.part_stats(part)
            est = est or e
            atk += a
            dfn += d
            sta += s
            wt += w
            if slot == "bit":
                dash, burst = da, b
        return Totals(atk, dfn, sta, dash, burst, wt, est)

    # ----------------------------------------------------------------- models
    def search(self, text: str, limit: int = 15) -> list[Model]:
        """Rank models by how well `text` matches name / Hasbro name / aliases / code."""
        t = _norm(text)
        if not t:
            return []
        words = [_norm(w) for w in re.split(r"\s+", text) if _norm(w)]
        scored = []
        for m in self.models.values():
            names = [m.name, m.hasbro_name or "", *m.aliases, m.product_code or ""]
            best = 0
            for n in names:
                nn = _norm(n)
                if not nn:
                    continue
                if nn == t:
                    best = max(best, 100)
                elif nn.startswith(t):
                    best = max(best, 80)
                elif t in nn:
                    best = max(best, 60)
                elif words and all(w in nn for w in words):
                    best = max(best, 50)
            if best:
                scored.append((best, m.name, m))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [m for _, _, m in scored[:limit]]

    def get(self, text: str) -> Model | None:
        """Exact lookup by id, name, Hasbro name or alias; else the unique search hit."""
        t = _norm(text)
        for m in self.models.values():
            if t in {_norm(m.id), _norm(m.name), _norm(m.hasbro_name), *(_norm(a) for a in m.aliases)}:
                return m
        hits = self.search(text, limit=2)
        return hits[0] if len(hits) == 1 else None

    def make_custom(self, blade: str, ratchet: str, bit: str,
                    assist: str | None = None, assist2: str | None = None,
                    lock_chip: str | None = None, name: str | None = None) -> Model:
        """Build a custom combo from part names (a Basic/Unique Line blade, or a
        Custom Line main blade + assist blade(s) + optional lock chip)."""
        parts: dict[str, str] = {}
        bl = self.find_part("Blade", blade)
        mb = None
        if bl is not None:
            parts["blade"] = bl.id
            btype, head = bl.type, bl
        else:
            mb = self.find_part("Main Blade", blade)
            if mb is None:
                raise ValueError(f"Unknown blade: {blade!r}")
            ab = self.find_part("Assist Blade", assist)
            if ab is None:
                raise ValueError(f"Custom Line main blade {mb.name!r} needs an assist blade (e.g. Slash)")
            parts["main_blade"] = mb.id
            parts["assist_blade"] = ab.id
            ab2 = self.find_part("Assist Blade", assist2)
            if ab2 is not None:
                parts["assist_blade_2"] = ab2.id
            lc = self.find_part("Lock Chip", lock_chip)
            if lc is not None:
                parts["lock_chip"] = lc.id
            btype, head = mb.type, mb
        r = self.find_part("Ratchet", ratchet)
        if r is None:
            raise ValueError(f"Unknown ratchet: {ratchet!r}")
        b = self.find_part("Bit", bit)
        if b is None:
            raise ValueError(f"Unknown bit: {bit!r}")
        parts["ratchet"] = r.id
        parts["bit"] = b.id
        # Official convention: the Bit sets the combo's type unless it is a
        # Balance bit, in which case the blade's type is used.
        mtype = b.type or btype or "Balance"
        if b.type == "Balance" and btype:
            mtype = btype
        bit_abbr = self._akas(b)[0] if self._akas(b) else b.name
        if bl is not None:
            base = bl.name
        else:
            lc_name = self.parts[parts["lock_chip"]].name if "lock_chip" in parts else ""
            ab_letters = "".join(self.parts[parts[s]].name[0] for s in ("assist_blade", "assist_blade_2") if s in parts)
            base = f"{lc_name}{mb.name} {ab_letters}"
        mid = name or f"{base}{'' if base.endswith(' ') else ' '}{r.name}{bit_abbr}".replace("  ", " ")
        return Model(id=mid, name=mid, type=mtype, spin=head.spin, system=head.system,
                     line="Custom", parts=parts, custom=True, source="custom combo")

    def all_models(self, line: str | None = None, mtype: str | None = None) -> list[Model]:
        out = []
        for m in self.models.values():
            if line and (m.line or "").lower() != line.lower():
                continue
            if mtype and m.type.lower() != mtype.lower():
                continue
            out.append(m)
        return sorted(out, key=lambda m: (m.line or "", m.product_code or "", m.name))


def load(path: Path | str = DATA_PATH) -> Database:
    return Database(path)
