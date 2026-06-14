"""Going Merry destination: append home and build-together ideas to a vault you import.

  work/home.csv    one row per item (room, category, store, link, ...); import into a sheet or Notion
  work/home.json   the same items as a JSON list

A richer vault connector (a live sheet or Notion API) is a tracked follow-up. These files
need no account.
"""
from __future__ import annotations

import csv
import json

from . import config

_FIELDS = ["item", "category", "room", "price", "store", "link", "dimensions",
           "color", "why", "source_url", "creator"]


def _csv_path():
    return config.WORKDIR / "home.csv"


def _json_path():
    return config.WORKDIR / "home.json"


def _row(item: dict) -> dict:
    return {field: item.get("_source_url" if field == "source_url" else field, "") for field in _FIELDS}


def append(item: dict) -> None:
    """Append one item to both the CSV and the JSON list."""
    _append_csv(item)
    _append_json(item)


def _append_csv(item: dict) -> None:
    path = _csv_path()
    new_file = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(_row(item))


def _append_json(item: dict) -> None:
    path = _json_path()
    items = []
    if path.exists():
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            items = []
    items.append(_row(item))
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
