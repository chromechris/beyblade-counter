"""Build beycounter/data/beyblade_x.json from the Beyblade Wiki (CC BY-SA).

Usage:  python tools/build_database.py [--cache DIR] [--offline]

Sources (all from https://beyblade.fandom.com via the MediaWiki API):
  * Category:Blades / Ratchets / Bits / Lock_Chips / Main_Blades / Assist_Blades
    -> {{Part Infobox}} with the official published stats
       (AttackStat, DefenseStat, StaminaStat, DashStat, BurstResistanceStat, Weight)
  * Category:Beyblade_X_Beyblades -> {{Beyblade Infobox}} of each official product
  * "==Products==" sections of every part page -> extra official combos (random
    boosters, sets, Hasbro releases) that have no page of their own.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from pathlib import Path

API = "https://beyblade.fandom.com/api.php"
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "beycounter" / "data" / "beyblade_x.json"
PART_CATS = ["Blades", "Ratchets", "Bits", "Lock_Chips", "Main_Blades", "Assist_Blades"]
X_SYSTEMS = {"Basic Line", "Unique Line", "Custom Line"}


# ----------------------------------------------------------------- wiki access
def call(**params):
    params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "beycounter-db-builder/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def members(cat: str) -> list[str]:
    out, cont = [], {}
    while True:
        d = call(action="query", list="categorymembers", cmtitle="Category:" + cat, cmlimit=500, **cont)
        out += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" not in d:
            return out
        cont = {"cmcontinue": d["continue"]["cmcontinue"]}


def fetch_pages(titles: list[str]) -> dict[str, str | None]:
    raw: dict[str, str | None] = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        d = call(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(batch))
        for pg in d["query"]["pages"].values():
            revs = pg.get("revisions")
            raw[pg["title"]] = revs[0]["slots"]["main"]["*"] if revs else None
        print(f"  fetched {i + len(batch)}/{len(titles)}", file=sys.stderr)
        time.sleep(1)
    return raw


def cached(cache: Path, name: str, producer, offline: bool):
    f = cache / name
    if f.exists():
        return json.load(open(f, encoding="utf-8"))
    if offline:
        raise SystemExit(f"offline and no cache file {f}")
    data = producer()
    cache.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(f, "w", encoding="utf-8"), ensure_ascii=False)
    return data


# ------------------------------------------------------------- wikitext parse
def infobox(text: str, name: str) -> dict | None:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    i = text.find("{{" + name)
    if i < 0:
        return None
    depth, j = 0, i
    while j < len(text):
        if text.startswith("{{", j):
            depth += 1
            j += 2
            continue
        if text.startswith("}}", j):
            depth -= 1
            j += 2
            if depth == 0:
                break
            continue
        j += 1
    body = text[i + 2:j - 2]
    parts, buf, depth, k = [], "", 0, 0
    while k < len(body):
        two = body[k:k + 2]
        if two in ("{{", "[["):
            depth += 1
            buf += two
            k += 2
            continue
        if two in ("}}", "]]"):
            depth -= 1
            buf += two
            k += 2
            continue
        if body[k] == "|" and depth == 0:
            parts.append(buf)
            buf = ""
            k += 1
            continue
        buf += body[k]
        k += 1
    parts.append(buf)
    fields = {}
    for p in parts[1:]:
        if "=" in p:
            key, val = p.split("=", 1)
            fields[key.strip()] = val.strip()
    return fields


def clean(v: str | None) -> str | None:
    if v is None:
        return None
    v = re.sub(r"<!--.*?-->", "", v, flags=re.S)
    v = re.sub(r"<ref[^>]*>.*?</ref>", "", v, flags=re.S)
    v = re.sub(r"<ref[^>]*/>", "", v)
    v = re.sub(r"\{\{Ruby\|([^|}]*)\|[^}]*\}\}", r"\1", v)
    v = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", v)
    v = re.sub(r"'''?", "", v)
    return v.strip()


def first_num(v: str | None) -> float | None:
    v = clean(v)
    if not v:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", v)
    return float(m.group()) if m else None


def lines(v: str | None) -> list[str]:
    v = clean(v)
    if not v:
        return []
    return [x.strip() for x in re.split(r"<br\s*/?>", v) if x.strip()]


def first_line(v: str | None) -> str | None:
    ls = lines(v)
    return ls[0] if ls else None


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def image_name(v: str | None) -> str | None:
    """First image file name of an infobox Image / Image1 field (plain or <gallery>)."""
    if not v:
        return None
    v = re.sub(r"<!--.*?-->", "", v, flags=re.S)
    m = re.search(r"<gallery[^>]*>\s*([^\n|]+)", v)
    name = m.group(1) if m else re.split(r"<br\s*/?>|\n", v.strip())[0]
    name = re.sub(r"^\[\[", "", name.strip())
    name = re.sub(r"^(File|Image):", "", name, flags=re.I).split("|")[0].strip()
    return name if re.search(r"\.(png|jpe?g|gif|webp)$", name, re.I) else None


# ---------------------------------------------------------------------- parts
def parse_parts(raw: dict[str, str | None]) -> list[dict]:
    parts = []
    for title, text in raw.items():
        cls, name = title.split(" - ", 1)
        ib = infobox(text or "", "Part Infobox")
        if ib is None:
            continue
        system = first_line(ib.get("System"))
        if system not in X_SYSTEMS:
            continue  # Beyblade Burst parts share the wiki categories
        parts.append({
            "id": title,
            "name": clean(ib.get("Name")) or name,
            "classification": clean(ib.get("Classification")) or cls,
            "type": first_line(ib.get("Type")),
            "spin": first_line(ib.get("SpinDirection")),
            "system": system,
            "aka": clean(ib.get("AKA")),
            "product_code": first_line(ib.get("ProductCode")),
            "release_jp": first_line(ib.get("ReleaseJP")),
            "weight_g": first_num(ib.get("Weight")),
            "attack": first_num(ib.get("AttackStat")),
            "defense": first_num(ib.get("DefenseStat")),
            "stamina": first_num(ib.get("StaminaStat")),
            "dash": first_num(ib.get("DashStat")),
            "burst_resistance": first_num(ib.get("BurstResistanceStat")),
            "height": first_num(ib.get("HeightStat")),
            "estimated": first_num(ib.get("AttackStat")) is None and cls != "Lock Chip",
            "image": image_name(ib.get("Image")),
        })
    return parts


class PartIndex:
    def __init__(self, parts: list[dict]):
        self.parts = parts
        self.by_cls: dict[str, list[dict]] = {}
        for p in parts:
            self.by_cls.setdefault(p["classification"], []).append(p)
        # abbreviation maps
        self.bit_abbr: dict[str, dict] = {}
        for p in self.by_cls.get("Bit", []):
            for a in self._akas(p):
                if re.fullmatch(r"[A-Za-z]{1,3}", a):
                    self.bit_abbr.setdefault(a.upper(), p)
        self.assist_abbr: dict[str, dict] = {}
        for p in self.by_cls.get("Assist Blade", []):
            self.assist_abbr.setdefault(p["name"][0].upper(), p)
            for a in self._akas(p):
                if re.fullmatch(r"[A-Z]{1,2}", a):
                    self.assist_abbr.setdefault(a, p)

    @staticmethod
    def _akas(p: dict) -> list[str]:
        out = []
        for a in re.split(r"<br\s*/?>|,|/", p.get("aka") or ""):
            a = re.sub(r"\(.*?\)", "", a).strip()
            if a:
                out.append(a)
        return out

    def find(self, cls: str, text: str | None) -> dict | None:
        t = norm(text)
        if not t:
            return None
        cands = self.by_cls.get(cls, [])
        for p in cands:
            if t == norm(p["name"]) or t == norm(p["id"]):
                return p
        for p in cands:
            if any(t == norm(a) for a in self._akas(p)):
                return p
        # Hasbro naming reverses word order: "Sword Dran" == "DranSword"
        for p in cands:
            words = re.findall(r"[A-Z][a-z]+", p["name"])
            if len(words) == 2 and t == norm(words[1] + words[0]):
                return p
        return None

    def split_bits(self, letters: str) -> dict | None:
        return self.bit_abbr.get(letters.upper())

    def split_assists(self, letters: str) -> list[dict] | None:
        out = []
        for ch in letters:
            p = self.assist_abbr.get(ch)
            if p is None:
                return None
            out.append(p)
        return out


# --------------------------------------------------------------------- models
NAME_RE = re.compile(r"^(?P<base>.+?)\s+(?P<assist>[A-Z]{0,2})\s?(?P<ratchet>(?:\d|M)-\d\d)\s?(?P<bit>[A-Za-z]{1,3})$")


def line_of(code: str | None) -> str | None:
    if not code:
        return None
    m = re.match(r"(BX|UX|CX)-", code)
    if m:
        return m.group(1)
    if re.match(r"[A-Z]\d{4}", code):
        return "Hasbro"
    return None


def model_from_product_page(title: str, text: str, idx: PartIndex, log: list) -> dict | None:
    ib = infobox(text, "Beyblade Infobox")
    if ib is None:
        return None
    parts: dict[str, str] = {}
    if first_line(ib.get("BladeX")) or first_line(ib.get("Blade")):
        b = idx.find("Blade", first_line(ib.get("BladeX")) or first_line(ib.get("Blade")))
        if b is None:
            log.append(f"product {title}: unknown blade {ib.get('BladeX')!r}")
            return None
        parts["blade"] = b["id"]
        btype = b["type"]
    else:
        mb = idx.find("Main Blade", first_line(ib.get("MainBlade")))
        if mb is None:
            log.append(f"product {title}: unknown main blade {ib.get('MainBlade')!r}")
            return None
        parts["main_blade"] = mb["id"]
        btype = mb["type"]
        lc = idx.find("Lock Chip", first_line(ib.get("LockChip")))
        if lc is not None:
            parts["lock_chip"] = lc["id"]
        abs_ = [x for x in re.split(r"<br\s*/?>|,|/|\+", clean(ib.get("AssistBlade")) or "") if x.strip()]
        if first_line(ib.get("AssistBlade2")):
            abs_.append(first_line(ib.get("AssistBlade2")))
        for i, a in enumerate(abs_):
            ab = idx.find("Assist Blade", a)
            if ab is None:
                log.append(f"product {title}: unknown assist blade {a!r}")
                return None
            parts["assist_blade" if i == 0 else "assist_blade_2"] = ab["id"]
    r = idx.find("Ratchet", first_line(ib.get("Ratchet")))
    bit = idx.find("Bit", first_line(ib.get("Bit")))
    if r is None or bit is None:
        log.append(f"product {title}: unknown ratchet/bit {ib.get('Ratchet')!r} {ib.get('Bit')!r}")
        return None
    parts["ratchet"] = r["id"]
    parts["bit"] = bit["id"]
    code = first_line(ib.get("ProductCode"))
    code = re.sub(r"\s*\(.*?\)\s*", "", code).strip() if code else None
    akas = [re.sub(r"\s*\(.*?\)\s*", "", a).strip() for a in lines(ib.get("AKA"))]
    hasbro = next((a for a, raw_a in zip(akas, lines(ib.get("AKA"))) if "Hasbro" in raw_a), None)
    return {
        "id": title,
        "name": title,
        "type": first_line(ib.get("Type")) or btype or "Balance",
        "spin": first_line(ib.get("SpinDirection")),
        "system": first_line(ib.get("System")),
        "line": line_of(code),
        "product_code": code,
        "hasbro_name": hasbro,
        "release_jp": first_line(ib.get("ReleaseJP")) or first_line(ib.get("ReleaseUS")),
        "parts": parts,
        "aliases": [a for a in akas if a and a != title],
        "source": "wiki product page",
        "image": image_name(ib.get("Image1")) or image_name(ib.get("Image")),
    }


def models_from_part_lists(raw_parts: dict[str, str | None], idx: PartIndex, log: list) -> list[dict]:
    """Parse '* BX-14 [[Random Booster Vol. 1]] - 03: [[DranSword 3-80B]]' lines."""
    link_re = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
    code_re = re.compile(r"^\*+\s*([A-Z]{1,2}-?\d{2,4}|[A-Z]\d{4})\b")
    out: list[dict] = []
    for pid, text in raw_parts.items():
        if not text:
            continue
        cls = pid.split(" - ")[0]
        if cls not in ("Blade", "Main Blade"):
            continue
        anchor = idx.find(cls, pid.split(" - ", 1)[1]) or next((p for p in idx.parts if p["id"] == pid), None)
        if anchor is None:
            continue
        m = re.search(r"==\s*Products\s*==(.*?)(?:\n==[^=]|\Z)", text, flags=re.S)
        if not m:
            continue
        brand = "Takara Tomy"
        for line in m.group(1).splitlines():
            if re.match(r"\s*===\s*Hasbro", line):
                brand = "Hasbro"
            elif re.match(r"\s*===", line):
                brand = "Takara Tomy"
            if not line.strip().startswith("*"):
                continue
            cm = code_re.match(line.strip())
            code = cm.group(1) if cm else None
            for name in link_re.findall(line):
                name = name.strip()
                nm = NAME_RE.match(name)
                if not nm:
                    continue
                parts: dict[str, str] = {}
                if cls == "Blade":
                    parts["blade"] = anchor["id"]
                    btype = anchor["type"]
                else:
                    parts["main_blade"] = anchor["id"]
                    btype = anchor["type"]
                    base = nm.group("base").replace(" ", "")
                    mbn = anchor["name"]
                    lc_name = None
                    if base.endswith(mbn):
                        lc_name = base[: -len(mbn)]
                    elif base.startswith(mbn):  # Hasbro order "Courage Dran"
                        lc_name = base[len(mbn):]
                    lc = idx.find("Lock Chip", lc_name)
                    if lc is not None:
                        parts["lock_chip"] = lc["id"]
                    assists = idx.split_assists(nm.group("assist")) if nm.group("assist") else None
                    if not assists:
                        log.append(f"{pid}: cannot resolve assist blade(s) in {name!r}")
                        continue
                    parts["assist_blade"] = assists[0]["id"]
                    if len(assists) > 1:
                        parts["assist_blade_2"] = assists[1]["id"]
                r = idx.find("Ratchet", nm.group("ratchet"))
                bit = idx.split_bits(nm.group("bit"))
                if r is None or bit is None:
                    log.append(f"{pid}: cannot resolve ratchet/bit in {name!r}")
                    continue
                parts["ratchet"] = r["id"]
                parts["bit"] = bit["id"]
                mtype = bit["type"] or btype or "Balance"
                if bit["type"] == "Balance" and btype:
                    mtype = btype
                out.append({
                    "id": name, "name": name, "type": mtype, "spin": anchor["spin"],
                    "system": anchor["system"], "line": line_of(code), "product_code": code,
                    "hasbro_name": name if brand == "Hasbro" else None,
                    "release_jp": None, "parts": parts, "aliases": [],
                    "source": f"listed on {pid}", "image": None,
                })
    return out


def part_key(parts: dict) -> tuple:
    # Lock Chips carry no combat stats, so a combo is the same bey with or without one listed.
    return tuple(sorted((k, v) for k, v in parts.items() if k != "lock_chip"))


SYSTEM_LINE = {"Basic Line": "BX", "Unique Line": "UX", "Custom Line": "CX"}


def merge_models(primary: list[dict], extra: list[dict]) -> list[dict]:
    """Dedupe by part set. Product pages win; Hasbro names become aliases."""
    by_key: "OrderedDict[tuple, dict]" = OrderedDict()
    # Takara Tomy pages first so their names become the primary ids
    ordered = sorted(primary, key=lambda m: m["line"] == "Hasbro") + extra
    for m in ordered:
        k = part_key(m["parts"])
        if k not in by_key:
            by_key[k] = m
            continue
        base = by_key[k]
        if m["line"] == "Hasbro" and not base.get("hasbro_name"):
            base["hasbro_name"] = m["hasbro_name"] or m["name"]
        elif m["hasbro_name"] and not base.get("hasbro_name"):
            base["hasbro_name"] = m["hasbro_name"]
        for alias in [m["name"], *m.get("aliases", [])]:
            if alias != base["name"] and alias not in base["aliases"] and alias != base.get("hasbro_name"):
                base["aliases"].append(alias)
        if not base.get("product_code") and m.get("product_code"):
            base["product_code"] = m["product_code"]
            base["line"] = m["line"]
        if not base.get("release_jp") and m.get("release_jp"):
            base["release_jp"] = m["release_jp"]
        if not base.get("image") and m.get("image"):
            base["image"] = m["image"]
    # A Takara Tomy-style name should be the primary id when the page title was Hasbro's
    for m in by_key.values():
        m["aliases"] = sorted(set(a for a in m["aliases"] if a != m["name"]))
        if not m.get("line"):
            m["line"] = SYSTEM_LINE.get(m.get("system") or "")
    return list(by_key.values())


# ----------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(HERE / "cache"))
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    cache = Path(args.cache)

    print("parts...", file=sys.stderr)
    part_titles = cached(cache, "part_titles.json",
                         lambda: [t for c in PART_CATS for t in members(c)], args.offline)
    raw_parts = cached(cache, "raw_parts.json", lambda: fetch_pages(part_titles), args.offline)
    parts = parse_parts(raw_parts)
    idx = PartIndex(parts)

    print("products...", file=sys.stderr)
    prod_titles = cached(cache, "product_titles.json", lambda: members("Beyblade_X_Beyblades"), args.offline)
    raw_products = cached(cache, "raw_products.json", lambda: fetch_pages(prod_titles), args.offline)

    log: list[str] = []
    primary = [m for t, txt in raw_products.items() if txt and (m := model_from_product_page(t, txt, idx, log))]
    extra = models_from_part_lists(raw_parts, idx, log)
    models = merge_models(primary, extra)
    models.sort(key=lambda m: ((m["line"] or "zz"), m["product_code"] or "zz", m["name"]))

    data = {
        "meta": {
            "generation": "Beyblade X",
            "source": "Beyblade Wiki (https://beyblade.fandom.com), CC BY-SA 3.0; stats as published by Takara Tomy / Hasbro",
            "generated": dt.date.today().isoformat(),
            "stat_model": {
                "attack/defense/stamina": "sum of blade-side parts + ratchet + bit",
                "dash/burst_resistance": "from the bit only",
                "type_triangle": "Attack beats Stamina, Stamina beats Defense, Defense beats Attack; Balance is neutral",
            },
            "counts": {"parts": len(parts), "models": len(models)},
        },
        "parts": parts,
        "models": models,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # the web / desktop / mobile apps use a self-contained copy inside web/
    web_copy = HERE.parent / "web" / "data" / "beyblade_x.json"
    web_copy.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(web_copy, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {args.out}: {len(parts)} parts, {len(models)} models "
          f"({len(primary)} from product pages, {len(extra)} listed combos before merge)", file=sys.stderr)
    if log:
        print(f"{len(log)} unresolved entries:", file=sys.stderr)
        for l in sorted(set(log)):
            print("  -", l, file=sys.stderr)


if __name__ == "__main__":
    main()
