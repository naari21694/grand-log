"""Baratie's local cookbook: append recipes to files you keep even without Mealie.

  work/recipes.json   the full structured recipes, a JSON list (browse or re-import)
  work/recipes.csv    one summary row per recipe (title, servings, time, ...) for a sheet

Used on the dry-run / no-Mealie path so a recipe is never lost. Mealie stays the rich
destination; this is the zero-setup fallback. Paths are read at call time from WORKDIR.
"""
from __future__ import annotations

import csv
import json

from . import config

_FIELDS = ["title", "cuisine", "base_servings", "total_time_min", "ingredients",
           "tags", "confidence", "source_url", "creator"]


def _csv_path():
    return config.WORKDIR / "recipes.csv"


def _json_path():
    return config.WORKDIR / "recipes.json"


def _summary(recipe: dict) -> dict:
    return {
        "title": recipe.get("title", ""),
        "cuisine": recipe.get("cuisine", ""),
        "base_servings": recipe.get("base_servings", ""),
        "total_time_min": recipe.get("total_time_min", ""),
        "ingredients": len(recipe.get("ingredients", []) or []),
        "tags": ", ".join(recipe.get("tags", []) or []),
        "confidence": recipe.get("confidence", ""),
        "source_url": recipe.get("_source_url", ""),
        "creator": recipe.get("creator", ""),
    }


def append(recipe: dict) -> None:
    """Append one recipe to the JSON cookbook and the CSV summary."""
    _append_csv(recipe)
    _append_json(recipe)


def _append_csv(recipe: dict) -> None:
    path = _csv_path()
    new_file = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(_summary(recipe))


def _append_json(recipe: dict) -> None:
    path = _json_path()
    items = []
    if path.exists():
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            items = []
    items.append({k: v for k, v in recipe.items() if k != "_card"})
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
