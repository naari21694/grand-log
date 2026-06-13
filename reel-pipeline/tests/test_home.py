import json

from pipeline import home

ITEM = {
    "item": "Walnut shelf", "category": "furniture", "room": "living", "price": "200 USD",
    "store": "IKEA", "link": "https://shop/x", "dimensions": "80x30cm", "color": "walnut",
    "why": "fits the alcove", "creator": "decorpro", "_source_url": "https://x/reel/1/",
}


def _redirect(tmp_path, monkeypatch):
    monkeypatch.setattr(home, "_CSV", tmp_path / "home.csv")
    monkeypatch.setattr(home, "_JSON", tmp_path / "home.json")


def test_append_writes_csv_header_and_row(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    home.append(ITEM)
    text = (tmp_path / "home.csv").read_text(encoding="utf-8")
    assert "item" in text.splitlines()[0]
    assert "Walnut shelf" in text


def test_append_writes_json_list_with_source_url(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    home.append(ITEM)
    items = json.loads((tmp_path / "home.json").read_text(encoding="utf-8"))
    assert items[0]["item"] == "Walnut shelf"
    assert items[0]["source_url"] == "https://x/reel/1/"


def test_append_two_items_accumulate(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    home.append(ITEM)
    home.append({**ITEM, "item": "Floor lamp", "category": "lighting"})
    items = json.loads((tmp_path / "home.json").read_text(encoding="utf-8"))
    assert len(items) == 2
