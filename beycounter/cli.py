"""Command line interface.

    python -m beycounter                         interactive menu
    python -m beycounter counter "Dran Buster"   best counters from the whole database
    python -m beycounter counter "Dran Buster" --mine     best counter from MY collection
    python -m beycounter versus "Wizard Rod" "Dran Buster"
    python -m beycounter show "Dran Buster 1-60A"
    python -m beycounter search wizard
    python -m beycounter list --type Stamina --line UX
    python -m beycounter mine list | add NAME... | remove NAME | clear
    python -m beycounter mine add-custom --blade "Phoenix Wing" --ratchet 9-60 --bit GF
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .collection import DEFAULT_PATH, Collection
from .database import Database, Model, load
from .engine import Matchup, evaluate, rank_counters


# ------------------------------------------------------------------ helpers
def fmt_model_line(db: Database, m: Model) -> str:
    code = f"[{m.product_code}] " if m.product_code else ""
    return f"{code}{m.display_name}  ({m.type})"


def print_model(db: Database, m: Model) -> None:
    t = db.totals(m)
    print(f"{m.display_name}")
    print(f"  type: {m.type}   spin: {m.spin or '?'}   system: {m.system or '?'}"
          f"   code: {m.product_code or '-'}   released (JP): {m.release_jp or '-'}")
    if m.aliases:
        print(f"  also known as: {', '.join(m.aliases)}")
    print(f"  parts: {m.parts_summary(db)}")
    print(f"  totals: attack {t.attack:.0f}  defense {t.defense:.0f}  stamina {t.stamina:.0f}"
          f"  dash {t.dash:.0f}  burst res. {t.burst_resistance:.0f}  weight {t.weight_g:.1f} g"
          + ("  (some stats estimated)" if t.estimated else ""))


def print_ranking(db: Database, opponent: Model, results: list[Matchup], detail: int = 3) -> None:
    ot = db.totals(opponent)
    print(f"\nOpponent: {opponent.display_name} ({opponent.type})  "
          f"atk {ot.attack:.0f} / def {ot.defense:.0f} / sta {ot.stamina:.0f} / "
          f"dash {ot.dash:.0f} / burst {ot.burst_resistance:.0f} / {ot.weight_g:.1f} g")
    if not results:
        print("  (no candidates)")
        return
    print(f"\n{'#':>2}  {'score':>5}  {'verdict':<15} {'type':<8} model")
    for i, r in enumerate(results, 1):
        print(f"{i:>2}  {r.score:>5.1f}  {r.verdict:<15} {r.candidate.type:<8} {r.candidate.display_name}")
    for r in results[:detail]:
        c = r.cand_totals
        print(f"\n-> {r.candidate.display_name}  [{r.score:.1f}, {r.verdict}]")
        print(f"   atk {c.attack:.0f} / def {c.defense:.0f} / sta {c.stamina:.0f} / dash {c.dash:.0f}"
              f" / burst {c.burst_resistance:.0f} / {c.weight_g:.1f} g   parts: {r.candidate.parts_summary(db)}")
        for n in r.explain():
            print(f"   - {n}")


def resolve(db: Database, text: str, pool: list[Model] | None = None, interactive: bool = False) -> Model | None:
    """Turn user text into one model; ask to disambiguate when interactive."""
    if pool is not None:
        exact = [m for m in pool if text.lower() in {m.id.lower(), m.name.lower(), (m.hasbro_name or "").lower()}]
        hits = exact or [m for m in pool if text.lower() in m.name.lower()
                         or text.lower() in (m.hasbro_name or "").lower()]
    else:
        m = db.get(text)
        if m is not None:
            return m
        hits = db.search(text)
    if not hits:
        print(f"No model matches {text!r}. Try `search` with part of the name (e.g. 'wizard').")
        return None
    if len(hits) == 1:
        return hits[0]
    if not interactive:
        print(f"{text!r} is ambiguous. Did you mean:")
        for m in hits[:15]:
            print(f"   {fmt_model_line(db, m)}")
        return None
    print(f"Matches for {text!r}:")
    for i, m in enumerate(hits[:15], 1):
        print(f"  {i:>2}. {fmt_model_line(db, m)}")
    choice = input("Pick a number (blank to cancel): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(hits[:15]):
        return hits[int(choice) - 1]
    return None


# ----------------------------------------------------------------- commands
def cmd_counter(db: Database, col: Collection, args) -> int:
    opp = resolve(db, args.opponent)
    if opp is None:
        return 1
    if args.mine:
        pool = col.models()
        if not pool:
            print(f"Your collection is empty (file: {col.path}). Add beys with `mine add NAME`.")
            return 1
    else:
        pool = db.all_models(line=args.line, mtype=args.type)
    results = rank_counters(db, opp, pool, top=args.top)
    print_ranking(db, opp, results, detail=args.detail)
    return 0


def cmd_versus(db: Database, col: Collection, args) -> int:
    a = resolve(db, args.mine_bey)
    b = resolve(db, args.opponent)
    if a is None or b is None:
        return 1
    r = evaluate(db, a, b)
    print_ranking(db, b, [r], detail=1)
    back = evaluate(db, b, a)
    print(f"\n(reverse view: {b.display_name} vs {a.display_name} scores {back.score:.1f})")
    return 0


def cmd_show(db: Database, col: Collection, args) -> int:
    m = resolve(db, args.model)
    if m is None:
        return 1
    print_model(db, m)
    return 0


def cmd_search(db: Database, col: Collection, args) -> int:
    hits = db.search(" ".join(args.text), limit=30)
    if not hits:
        print("No matches.")
        return 1
    for m in hits:
        print(f"  {fmt_model_line(db, m)}")
    return 0


def cmd_list(db: Database, col: Collection, args) -> int:
    ms = db.all_models(line=args.line, mtype=args.type)
    for m in ms:
        t = db.totals(m)
        print(f"  {fmt_model_line(db, m):<60} atk {t.attack:>3.0f} def {t.defense:>3.0f} sta {t.stamina:>3.0f}")
    print(f"{len(ms)} models")
    return 0


def cmd_mine(db: Database, col: Collection, args) -> int:
    sub = args.mine_cmd
    if sub == "list":
        ms = col.models()
        if not ms:
            print(f"Collection is empty. (file: {col.path})")
            return 0
        for m in ms:
            t = db.totals(m)
            print(f"  {fmt_model_line(db, m):<60} atk {t.attack:>3.0f} def {t.defense:>3.0f} sta {t.stamina:>3.0f}")
        print(f"{len(ms)} beys in your collection  (file: {col.path})")
        return 0
    if sub == "add":
        rc = 0
        for name in args.names:
            m = resolve(db, name)
            if m is None:
                rc = 1
                continue
            print(("added: " if col.add(m) else "already in collection: ") + m.display_name)
        return rc
    if sub == "add-custom":
        try:
            m = db.make_custom(args.blade, args.ratchet, args.bit, assist=args.assist,
                               assist2=args.assist2, lock_chip=args.lock_chip, name=args.name)
        except ValueError as e:
            print(f"error: {e}")
            return 1
        print(("added custom combo: " if col.add(m) else "already in collection: ") + m.display_name)
        print_model(db, m)
        return 0
    if sub == "remove":
        m = col.remove(args.name)
        if m is None:
            print(f"Not in your collection: {args.name!r}")
            return 1
        print(f"removed: {m.display_name}")
        return 0
    if sub == "clear":
        col.clear()
        print("collection cleared")
        return 0
    return 1


# -------------------------------------------------------------- interactive
def interactive(db: Database, col: Collection) -> int:
    print(f"Beyblade X Counter Picker v{__version__} - {len(db.models)} official models, "
          f"{len(db.parts)} parts (stats: Takara Tomy / Hasbro via Beyblade Wiki)")
    menu = (
        "\n 1) Best counter to an opponent (whole database)"
        "\n 2) Best counter from MY collection"
        "\n 3) Head-to-head: my bey vs opponent"
        "\n 4) My collection: list / add / remove"
        "\n 5) Look up a model (stats and parts)"
        "\n 0) Quit"
    )
    while True:
        print(menu)
        try:
            choice = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if choice == "0" or choice.lower() in {"q", "quit", "exit"}:
            return 0
        if choice in {"1", "2"}:
            opp = resolve(db, input("Opponent's Beyblade: ").strip(), interactive=True)
            if opp is None:
                continue
            pool = col.models() if choice == "2" else None
            if choice == "2" and not pool:
                print("Your collection is empty - add beys with option 4 first.")
                continue
            print_ranking(db, opp, rank_counters(db, opp, pool, top=5 if choice == "1" else 0))
        elif choice == "3":
            pool = col.models() or None
            a = resolve(db, input("Your Beyblade: ").strip(), pool=pool, interactive=True)
            if a is None:
                continue
            b = resolve(db, input("Opponent's Beyblade: ").strip(), interactive=True)
            if b is None:
                continue
            print_ranking(db, b, [evaluate(db, a, b)], detail=1)
        elif choice == "4":
            ms = col.models()
            print(f"\nYour collection ({len(ms)}):" if ms else "\nYour collection is empty.")
            for m in ms:
                print(f"   {fmt_model_line(db, m)}")
            act = input("add / remove / custom / back? ").strip().lower()
            if act.startswith("a"):
                m = resolve(db, input("Model to add: ").strip(), interactive=True)
                if m is not None:
                    print(("added: " if col.add(m) else "already there: ") + m.display_name)
            elif act.startswith("r"):
                m = resolve(db, input("Model to remove: ").strip(), pool=ms, interactive=True)
                if m is not None and col.remove(m.id):
                    print(f"removed: {m.display_name}")
            elif act.startswith("c"):
                blade = input("Blade (or Custom Line main blade): ").strip()
                assist = input("Assist blade(s) for Custom Line, e.g. 'Slash' or 'Turn,Quell' (blank if none): ").strip()
                lock = input("Lock chip (blank if none): ").strip() or None
                ratchet = input("Ratchet, e.g. 9-60: ").strip()
                bit = input("Bit, e.g. GF or Gear Flat: ").strip()
                a1, _, a2 = assist.partition(",")
                try:
                    m = db.make_custom(blade, ratchet, bit, assist=a1 or None, assist2=a2 or None, lock_chip=lock)
                except ValueError as e:
                    print(f"error: {e}")
                    continue
                print(("added custom combo: " if col.add(m) else "already there: ") + m.display_name)
                print_model(db, m)
        elif choice == "5":
            m = resolve(db, input("Model name: ").strip(), interactive=True)
            if m is not None:
                print()
                print_model(db, m)
        else:
            print("Please choose 0-5.")


# ------------------------------------------------------------------ parser
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="beycounter", description="Beyblade X counter picker")
    p.add_argument("--collection", default=str(DEFAULT_PATH), help="path of your collection JSON")
    p.add_argument("--version", action="version", version=f"beycounter {__version__}")
    sp = p.add_subparsers(dest="cmd")

    c = sp.add_parser("counter", help="rank the best counters to an opponent")
    c.add_argument("opponent")
    c.add_argument("--mine", action="store_true", help="only consider my collection")
    c.add_argument("--top", type=int, default=5)
    c.add_argument("--detail", type=int, default=3, help="how many results to explain")
    c.add_argument("--line", help="BX / UX / CX / Hasbro")
    c.add_argument("--type", help="Attack / Defense / Stamina / Balance")
    c.set_defaults(func=cmd_counter)

    v = sp.add_parser("versus", help="head to head")
    v.add_argument("mine_bey")
    v.add_argument("opponent")
    v.set_defaults(func=cmd_versus)

    s = sp.add_parser("show", help="show a model's parts and stat totals")
    s.add_argument("model")
    s.set_defaults(func=cmd_show)

    se = sp.add_parser("search", help="search models by name")
    se.add_argument("text", nargs="+")
    se.set_defaults(func=cmd_search)

    li = sp.add_parser("list", help="list official models")
    li.add_argument("--line")
    li.add_argument("--type")
    li.set_defaults(func=cmd_list)

    m = sp.add_parser("mine", help="manage my collection")
    ms = m.add_subparsers(dest="mine_cmd", required=True)
    ms.add_parser("list")
    a = ms.add_parser("add")
    a.add_argument("names", nargs="+")
    r = ms.add_parser("remove")
    r.add_argument("name")
    ms.add_parser("clear")
    cu = ms.add_parser("add-custom", help="add a custom part combination")
    cu.add_argument("--blade", required=True, help="Blade, or Custom Line main blade")
    cu.add_argument("--ratchet", required=True)
    cu.add_argument("--bit", required=True)
    cu.add_argument("--assist", help="Custom Line assist blade")
    cu.add_argument("--assist2", help="second assist blade")
    cu.add_argument("--lock-chip", dest="lock_chip")
    cu.add_argument("--name")
    m.set_defaults(func=cmd_mine)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db = load()
    col = Collection(db, args.collection)
    if args.cmd is None:
        return interactive(db, col)
    return args.func(db, col, args)


if __name__ == "__main__":
    sys.exit(main())
