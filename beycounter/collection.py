"""The user's own Beyblade collection, saved as JSON."""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from .database import Database, Model

DEFAULT_PATH = Path(os.environ.get("BEYCOUNTER_COLLECTION", Path.home() / ".beycounter" / "collection.json"))


class Collection:
    def __init__(self, db: Database, path: Path | str = DEFAULT_PATH):
        self.db = db
        self.path = Path(path)
        self.entries: list[dict] = []   # {"model": id} or {"custom": {...model fields...}}
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                self.entries = json.load(f).get("entries", [])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"entries": self.entries}, f, indent=1, ensure_ascii=False)

    # ---------------------------------------------------------------- content
    def models(self) -> list[Model]:
        out = []
        for e in self.entries:
            if "model" in e:
                m = self.db.models.get(e["model"])
                if m is not None:
                    out.append(m)
            elif "custom" in e:
                c = dict(e["custom"])
                c["aliases"] = tuple(c.get("aliases") or ())
                out.append(Model(**c))
        return out

    def ids(self) -> set[str]:
        return {m.id for m in self.models()}

    def add(self, model: Model) -> bool:
        """Add a model (official or custom). Returns False if already present."""
        if model.id in self.ids():
            return False
        if model.custom:
            d = asdict(model)
            d["aliases"] = list(d["aliases"])
            self.entries.append({"custom": d})
        else:
            self.entries.append({"model": model.id})
        self.save()
        return True

    def remove(self, text: str) -> Model | None:
        """Remove by exact id/name, or by unique fuzzy match among owned models."""
        target = None
        for m in self.models():
            if text.lower() in {m.id.lower(), m.name.lower(), (m.hasbro_name or "").lower()}:
                target = m
                break
        if target is None:
            hits = [m for m in self.models() if text.lower() in m.name.lower()
                    or text.lower() in (m.hasbro_name or "").lower()]
            if len(hits) == 1:
                target = hits[0]
        if target is None:
            return None
        self.entries = [e for e in self.entries
                        if e.get("model") != target.id and e.get("custom", {}).get("id") != target.id]
        self.save()
        return target

    def clear(self) -> None:
        self.entries = []
        self.save()
