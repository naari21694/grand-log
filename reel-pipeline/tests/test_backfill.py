import json

from pipeline import backfill


def _collection(name, items):
    """Build a collection in the current export shape: a name plus nested URL/Caption items."""
    inner = [{"dict": [{"label": "URL", "href": url}, {"label": "Caption", "value": cap}]}
             for url, cap in items]
    return {"label_values": [{"label": "Name", "value": name}, {"dict": inner}]}


def test_parse_export_new_format(tmp_path):
    data = [_collection("Burger Recipes", [
        ("https://www.instagram.com/p/AAA/", "smash burger with secret sauce"),
        ("https://www.instagram.com/p/BBB/", "double cheeseburger"),
    ])]
    path = tmp_path / "saved_collections.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    records = backfill.parse_export(str(path))
    assert records == [
        ("https://www.instagram.com/p/AAA/", "smash burger with secret sauce", "Burger Recipes"),
        ("https://www.instagram.com/p/BBB/", "double cheeseburger", "Burger Recipes"),
    ]


def test_parse_export_saved_posts_format(tmp_path):
    data = [{"label_values": [
        {"label": "URL", "href": "https://www.instagram.com/p/CCC/"},
        {"label": "Caption", "value": "a watercolour painting"},
    ]}]
    path = tmp_path / "saved_posts.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert backfill.parse_export(str(path)) == [
        ("https://www.instagram.com/p/CCC/", "a watercolour painting", "")]


def test_parse_export_old_dict_format(tmp_path):
    data = {"saved_collections": [
        {"title": "Travel 2026", "string_list_data": [{"href": "https://www.instagram.com/reel/DDD/"}]},
    ]}
    path = tmp_path / "saved_collections.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert backfill.parse_export(str(path)) == [
        ("https://www.instagram.com/reel/DDD/", "", "Travel 2026")]


def test_parse_export_dedup_and_regex_fallback(tmp_path):
    path = tmp_path / "weird.json"
    path.write_text('{"x": "see https://www.instagram.com/reel/EEE/ and '
                    'https://www.instagram.com/reel/EEE/ once"}', encoding="utf-8")
    assert backfill.parse_export(str(path)) == [("https://www.instagram.com/reel/EEE/", "", "")]


def test_route_item_keyword_wins_without_a_call(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("should not classify when the name keyword matches")
    monkeypatch.setattr(backfill.brain, "classify", boom)
    assert backfill.route_item("any caption", "Travel 2026", {}) == ("place", False)


def test_route_item_classifies_once_per_collection(monkeypatch):
    calls = []
    monkeypatch.setattr(backfill.brain, "classify",
                        lambda caption, name="": calls.append(name) or "recipe")
    cache: dict = {}
    assert backfill.route_item("a smoothie", "Smoothies", cache) == ("recipe", True)
    assert backfill.route_item("another smoothie", "Smoothies", cache) == ("recipe", False)
    assert calls == ["Smoothies"]  # classified once, then served from cache


def test_route_item_without_caption_defaults_to_saved():
    assert backfill.route_item("", "Random Stuff", {}) == ("saved", False)


def test_ingest_routes_indexes_and_skips(tmp_path, monkeypatch):
    data = [
        _collection("Recipes", [("https://www.instagram.com/p/R1/", "pasta recipe")]),
        _collection("Anime", [("https://www.instagram.com/p/A1/", "cool clip")]),
        _collection("Recipes", [("https://www.instagram.com/p/R2/", "already have this")]),
    ]
    path = tmp_path / "saved_collections.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    saved: list[dict] = []
    monkeypatch.setattr(backfill.config, "WORKDIR", tmp_path)
    monkeypatch.setattr(backfill.store, "exists", lambda url: url.endswith("/R2/"))  # one already done
    monkeypatch.setattr(backfill.store, "save", lambda **kw: saved.append(kw))
    monkeypatch.setattr(backfill.brain, "classify", lambda caption, name="": "saved")
    monkeypatch.setattr(backfill, "process_one", lambda url, bucket, caption=None: {
        "confidence": "high", "ingredients": ["x"], "instructions": ["y"], "_card": {"title": "t"}})

    counts = backfill.ingest(str(path))
    assert counts.get("recipe") == 1          # R1 routed by the "Recipes" keyword
    assert counts.get("saved") == 1           # A1 auto-classified to generic, indexed
    assert counts.get("skipped") == 1         # R2 already in the store
    assert any(kw["bucket"] == "saved" for kw in saved)
