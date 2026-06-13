"""Log Pose destination: append places to local files you import into Maps and a sheet.

  work/places.geojson   FeatureCollection of points; import into Google My Maps
  work/places.csv       one row per place (region, category, ...); import into Sheets or My Maps

A live Google Sheets and My Maps API connector is a tracked follow-up. These files need no
account and import in two clicks.
"""
from __future__ import annotations

import csv
import json

from . import config

_GEOJSON = config.WORKDIR / "places.geojson"
_CSV = config.WORKDIR / "places.csv"
_FIELDS = ["name", "category", "region", "city", "country", "price", "why",
           "lat", "lng", "source_url", "creator"]


def _row(place: dict) -> dict:
    return {field: place.get("_source_url" if field == "source_url" else field, "") for field in _FIELDS}


def append(place: dict) -> None:
    """Append one place to both the CSV and the GeoJSON."""
    _append_csv(place)
    _append_geojson(place)


def _append_csv(place: dict) -> None:
    new_file = not _CSV.exists()
    with open(_CSV, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(_row(place))


def _append_geojson(place: dict) -> None:
    collection = {"type": "FeatureCollection", "features": []}
    if _GEOJSON.exists():
        try:
            collection = json.loads(_GEOJSON.read_text(encoding="utf-8"))
        except Exception:
            collection = {"type": "FeatureCollection", "features": []}
    feature = {"type": "Feature", "properties": _row(place), "geometry": None}
    if place.get("lat") and place.get("lng"):
        feature["geometry"] = {"type": "Point", "coordinates": [place["lng"], place["lat"]]}
    collection["features"].append(feature)
    _GEOJSON.write_text(json.dumps(collection, indent=2, ensure_ascii=False), encoding="utf-8")
