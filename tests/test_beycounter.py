import json
from pathlib import Path

import pytest

from beycounter.collection import Collection
from beycounter.database import load
from beycounter.engine import evaluate, rank_counters, type_advantage


@pytest.fixture(scope="module")
def db():
    return load()


def test_database_has_official_lines(db):
    lines = {m.line for m in db.models.values()}
    assert {"BX", "UX", "CX"} <= lines
    assert len(db.models) > 200
    assert all(m.type in {"Attack", "Defense", "Stamina", "Balance"} for m in db.models.values())


def test_published_totals_match_official_example(db):
    # Published stats: DranBuster 70/20/10 + 1-60 17/9/4 + Accel 40/10/10, dash 40, burst 80
    t = db.totals(db.get("DranBuster 1-60A"))
    assert (t.attack, t.defense, t.stamina) == (127, 39, 24)
    assert (t.dash, t.burst_resistance) == (40, 80)
    assert not t.estimated


def test_lookup_by_hasbro_name_and_alias(db):
    assert db.get("Buster Dran 1-60A").id == "DranBuster 1-60A"
    assert db.get("Soar Phoenix 9-60GF").id == "PhoenixWing 9-60GF"
    assert db.get("dran buster") is None            # ambiguous: several DranBuster releases
    assert len(db.search("dran buster")) > 1
    assert any(m.id == "WizardRod 5-70DB" for m in db.search("wizard rod"))
    assert db.get("Courage Dran S 6-60V").id == "DranBrave S6-60V"


def test_type_triangle():
    assert type_advantage("Attack", "Stamina") == 1
    assert type_advantage("Stamina", "Defense") == 1
    assert type_advantage("Defense", "Attack") == 1
    assert type_advantage("Stamina", "Attack") == -1
    assert type_advantage("Balance", "Attack") == 0


def test_counter_depends_on_opponent(db):
    attack_opp = db.get("DranBuster 1-60A")        # Attack type
    stamina_opp = db.get("WizardRod 5-70DB")       # Stamina type
    top_vs_attack = rank_counters(db, attack_opp, top=5)
    top_vs_stamina = rank_counters(db, stamina_opp, top=5)
    assert [r.candidate.id for r in top_vs_attack] != [r.candidate.id for r in top_vs_stamina]
    # The official triangle should show up in the recommendations.
    assert any(r.candidate.type == "Defense" for r in top_vs_attack)
    assert any(r.candidate.type == "Attack" for r in top_vs_stamina)


def test_score_is_antisymmetric_ish(db):
    a, b = db.get("DranBuster 1-60A"), db.get("WizardRod 5-70DB")
    ab, ba = evaluate(db, a, b), evaluate(db, b, a)
    assert 0 <= ab.score <= 100 and 0 <= ba.score <= 100
    assert abs((ab.score + ba.score) - 100) < 1.0
    assert ab.explain()


def test_custom_combo_and_collection(db, tmp_path):
    path = tmp_path / "col.json"
    col = Collection(db, path)
    assert col.add(db.get("DranBuster 1-60A"))
    assert not col.add(db.get("DranBuster 1-60A"))  # duplicate
    custom = db.make_custom("Phoenix Wing", "9-60", "GF")
    assert custom.custom and custom.type == "Attack"
    assert db.totals(custom).attack > 100
    assert col.add(custom)
    assert len(col.models()) == 2
    # persisted and reloaded
    col2 = Collection(db, path)
    assert {m.id for m in col2.models()} == {"DranBuster 1-60A", custom.id}
    best = rank_counters(db, db.get("WizardRod 5-70DB"), col2.models(), top=0)
    assert len(best) == 2
    assert col2.remove("DranBuster 1-60A").id == "DranBuster 1-60A"
    assert len(Collection(db, path).models()) == 1
    assert json.loads(path.read_text(encoding="utf-8"))["entries"]


def test_custom_line_custom_combo(db):
    m = db.make_custom("Brave", "6-60", "V", assist="Slash", lock_chip="Dran")
    official = db.get("DranBrave S6-60V")
    assert db.totals(m).as_dict() == db.totals(official).as_dict()
