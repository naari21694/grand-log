import json

from pipeline import places

PLACE = {
    "name": "Ichiran", "category": "food", "region": "Tokyo", "city": "Tokyo",
    "country": "Japan", "price": "1000 yen", "why": "tonkotsu ramen",
    "lat": 35.0, "lng": 139.0, "creator": "foodie", "_source_url": "https://x/reel/1/",
}


def _redirect(tmp_path, monkeypatch):
    monkeypatch.setattr(places, "_GEOJSON", tmp_path / "places.geojson")
    monkeypatch.setattr(places, "_CSV", tmp_path / "places.csv")


def test_append_writes_geojson_point(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    places.append(PLACE)
    collection = json.loads((tmp_path / "places.geojson").read_text(encoding="utf-8"))
    assert collection["type"] == "FeatureCollection"
    feature = collection["features"][0]
    assert feature["geometry"]["coordinates"] == [139.0, 35.0]
    assert feature["properties"]["name"] == "Ichiran"
    assert feature["properties"]["source_url"] == "https://x/reel/1/"


def test_append_csv_has_header_and_row(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    places.append(PLACE)
    text = (tmp_path / "places.csv").read_text(encoding="utf-8")
    assert "name" in text.splitlines()[0]
    assert "Ichiran" in text


def test_append_two_places_accumulate(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    places.append(PLACE)
    places.append({**PLACE, "name": "Senso-ji", "category": "see"})
    collection = json.loads((tmp_path / "places.geojson").read_text(encoding="utf-8"))
    assert len(collection["features"]) == 2


def test_append_without_coords_leaves_geometry_null(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    no_coords = {k: v for k, v in PLACE.items() if k not in ("lat", "lng")}
    places.append(no_coords)
    collection = json.loads((tmp_path / "places.geojson").read_text(encoding="utf-8"))
    assert collection["features"][0]["geometry"] is None
