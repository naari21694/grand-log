import json

from pipeline import routing


def test_route_matches_keywords():
    assert routing.route("My Recipes") == "recipe"
    assert routing.route("Travel ideas") == "place"
    assert routing.route("Home decor") == "home"
    assert routing.route("misc", default="recipe") == "recipe"


def test_routes_json_override(tmp_path, monkeypatch):
    override = tmp_path / "routes.json"
    override.write_text(json.dumps({"home": ["gadget"]}), encoding="utf-8")
    monkeypatch.setattr(routing, "_OVERRIDE", override)
    assert routing.route("cool gadget thing") == "home"


def test_buckets_are_generic():
    assert routing.BUCKETS == ("recipe", "place", "home")
    assert "japan" not in routing.BUCKETS
