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

_FIELDS = ["name", "category", "region", "city", "country", "price", "why",
           "lat", "lng", "source_url", "creator"]


def _csv_path():
    return config.WORKDIR / "places.csv"


def _geojson_path():
    return config.WORKDIR / "places.geojson"


def _row(place: dict) -> dict:
    return {field: place.get("_source_url" if field == "source_url" else field, "") for field in _FIELDS}


def append(place: dict) -> None:
    """Append one place to both the CSV and the GeoJSON."""
    _append_csv(place)
    _append_geojson(place)


def _append_csv(place: dict) -> None:
    path = _csv_path()
    new_file = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(_row(place))


def _append_geojson(place: dict) -> None:
    path = _geojson_path()
    collection = {"type": "FeatureCollection", "features": []}
    if path.exists():
        try:
            collection = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            collection = {"type": "FeatureCollection", "features": []}
    feature = {"type": "Feature", "properties": _row(place), "geometry": None}
    if place.get("lat") and place.get("lng"):
        feature["geometry"] = {"type": "Point", "coordinates": [place["lng"], place["lat"]]}
    collection["features"].append(feature)
    path.write_text(json.dumps(collection, indent=2, ensure_ascii=False), encoding="utf-8")


def _has_point(feature: dict) -> bool:
    geom = feature.get("geometry")
    return bool(geom and geom.get("type") == "Point"
                and isinstance(geom.get("coordinates"), list) and len(geom["coordinates"]) >= 2)


def regeocode_missing(limit: int = 0) -> tuple[int, int]:
    """Re-geocode places that still have no point, in place. Returns (recovered, remaining).

    Reuses the accuracy-first geocoder, so a name that OpenStreetMap could not place earlier
    gets another, country-constrained try (handy after coverage improves, or for the deferred
    image posts). Resumable: it only touches features that are still unpinned.
    """
    from . import geocode
    path = _geojson_path()
    if not path.exists():
        return (0, 0)
    collection = json.loads(path.read_text(encoding="utf-8"))
    features = collection.get("features", [])
    todo = [f for f in features if not _has_point(f) and (f.get("properties") or {}).get("name")]
    if limit:
        todo = todo[:limit]
    recovered = 0
    for feature in todo:
        prop = feature["properties"]
        hit = geocode.locate(prop.get("name"), prop.get("city", ""), prop.get("country", ""),
                             prop.get("category", ""))
        if hit:
            feature["geometry"] = {"type": "Point", "coordinates": [hit["lng"], hit["lat"]]}
            prop["lat"], prop["lng"] = hit["lat"], hit["lng"]
            recovered += 1
    if recovered:
        path.write_text(json.dumps(collection, indent=2, ensure_ascii=False), encoding="utf-8")
    remaining = sum(1 for f in features if not _has_point(f))
    return (recovered, remaining)
