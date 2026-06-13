from pipeline import store, web


def _fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_DB", tmp_path / "items.db")
    store.init_db()


def test_items_payload_lists_saved(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    store.save(bucket="recipe", title="Miso", summary="serves 2", link="http://x", thumb="t.jpg")
    payload = web._items_payload()
    assert payload[0]["title"] == "Miso"
    assert payload[0]["crew"] == "Baratie"
    assert payload[0]["has_thumb"] is True


def test_items_payload_search(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    store.save(bucket="place", title="Ichiran", text="tonkotsu ramen")
    assert web._items_payload("tonkotsu")
    assert web._items_payload("nope") == []


def test_page_is_self_contained():
    assert "Grand Log" in web._PAGE
    assert "/api/items" in web._PAGE
