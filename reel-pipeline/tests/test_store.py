from pipeline import store


def _fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_DB", tmp_path / "items.db")
    store.init_db()


def test_save_then_search_finds_it(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    store.save(bucket="recipe", title="Miso Salmon", text="miso salmon glaze")
    rows = store.search("salmon")
    assert rows and rows[0]["title"] == "Miso Salmon"


def test_search_matches_body_text_and_misses_cleanly(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    store.save(bucket="japan", title="Ichiran", text="best tonkotsu ramen in Tokyo")
    assert store.search("tonkotsu")
    assert store.search("nothing-here-at-all") == []


def test_recent_returns_newest_first(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    store.save(bucket="recipe", title="A")
    store.save(bucket="recipe", title="B")
    assert store.recent(2)[0]["title"] == "B"


def test_sample_is_bounded(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    for i in range(10):
        store.save(bucket="home", title=f"item{i}")
    assert len(store.sample(3)) == 3


def test_get_returns_row_or_none(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    item_id = store.save(bucket="recipe", title="X")
    assert store.get(item_id)["title"] == "X"
    assert store.get(999999) is None
