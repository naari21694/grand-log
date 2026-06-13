import json

from pipeline import backfill


def test_parse_saved_posts_shape(tmp_path):
    data = {"saved_saved_media": [
        {"title": "chef", "string_map_data": {"Saved on": {"href": "https://www.instagram.com/reel/AAA/"}}},
        {"title": "chef", "string_map_data": {"Saved on": {"href": "https://www.instagram.com/reel/BBB/"}}},
    ]}
    path = tmp_path / "saved_posts.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    items = backfill.parse(str(path))
    assert ("https://www.instagram.com/reel/AAA/", "recipe") in items
    assert len(items) == 2


def test_parse_collections_routes_by_name(tmp_path):
    data = {"saved_collections": [
        {"title": "Travel 2026", "string_list_data": [{"href": "https://www.instagram.com/reel/CCC/"}]},
    ]}
    path = tmp_path / "saved_collections.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert backfill.parse(str(path)) == [("https://www.instagram.com/reel/CCC/", "place")]


def test_parse_falls_back_to_regex(tmp_path):
    path = tmp_path / "weird.json"
    path.write_text('{"x": "see https://www.instagram.com/reel/DDD/ now"}', encoding="utf-8")
    items = backfill.parse(str(path))
    assert ("https://www.instagram.com/reel/DDD/", "recipe") in items


def test_force_bucket_overrides_routing(tmp_path):
    data = {"saved_collections": [
        {"title": "Anywhere", "string_list_data": [{"href": "https://www.instagram.com/reel/EEE/"}]},
    ]}
    path = tmp_path / "c.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert backfill.parse(str(path), force="home") == [("https://www.instagram.com/reel/EEE/", "home")]
