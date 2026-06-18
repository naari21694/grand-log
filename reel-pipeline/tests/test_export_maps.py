import csv
import io
import json
import xml.etree.ElementTree as ET
import zipfile

from pipeline import export_maps


def _pt(name, cat="cafe", lat=35.0, lng=139.0, **extra):
    return {"type": "Feature",
            "properties": {"name": name, "category": cat, **extra},
            "geometry": {"type": "Point", "coordinates": [lng, lat]}}


def _write(tmp_path, features):
    (tmp_path / "places.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")


def test_to_csv_has_header_and_one_row_per_place():
    rows = list(csv.reader(io.StringIO(export_maps.to_csv([_pt("A"), _pt("B")]))))
    assert rows[0][0] == "Name" and "Latitude" in rows[0]
    assert len(rows) == 3  # header + two


def test_to_kml_is_wellformed_and_groups_by_category():
    kml = export_maps.to_kml([_pt("A", "cafe"), _pt("B", "cafe"), _pt("C", "bar")])
    root = ET.fromstring(kml)
    placemarks = [e for e in root.iter() if e.tag.endswith("}Placemark")]
    folders = [e for e in root.iter() if e.tag.endswith("}Folder")]
    assert len(placemarks) == 3 and len(folders) == 2


def test_export_writes_all_formats(tmp_path):
    _write(tmp_path, [_pt("A"), _pt("B")])
    written = export_maps.export(workdir=tmp_path, formats=("all",))
    assert written["count"] == 2
    for name in ("places.kml", "places.kmz", "places.csv", "unmapped.csv"):
        assert (tmp_path / "maps" / name).exists()
    with zipfile.ZipFile(tmp_path / "maps" / "places.kmz") as z:
        assert "doc.kml" in z.namelist()


def test_export_format_selector_writes_only_requested(tmp_path):
    _write(tmp_path, [_pt("A")])
    export_maps.export(workdir=tmp_path, formats=("csv",))
    assert (tmp_path / "maps" / "places.csv").exists()
    assert not (tmp_path / "maps" / "places.kml").exists()


def test_export_excludes_null_geometry_and_review_flag(tmp_path):
    feats = [_pt("Good"),
             {"type": "Feature", "properties": {"name": "NoGeom", "category": "cafe"},
              "geometry": None},
             _pt("Flagged", loc_flag="country_mismatch_review")]
    _write(tmp_path, feats)
    written = export_maps.export(workdir=tmp_path, formats=("csv",))
    assert written["count"] == 1
    unmapped = list(csv.reader(io.StringIO(
        (tmp_path / "maps" / "unmapped.csv").read_text(encoding="utf-8"))))
    assert len(unmapped) == 3  # header + the two excluded


def test_export_missing_geojson_is_safe(tmp_path):
    written = export_maps.export(workdir=tmp_path, formats=("all",))
    assert written["count"] == 0
    assert (tmp_path / "maps" / "places.kml").exists()


def test_refresh_swallows_errors(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("x")
    monkeypatch.setattr(export_maps, "export", boom)
    export_maps.refresh()  # must not raise
