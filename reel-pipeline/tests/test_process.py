from pipeline import process
from pipeline.download import Media


def _patch_stages(monkeypatch, tmp_path, recipe):
    monkeypatch.setattr(process.config, "WORKDIR", tmp_path)
    monkeypatch.setattr(process.config, "MEALIE_URL", "")
    monkeypatch.setattr(process.download, "fetch", lambda url: Media(video="v.mp4", caption="cap", handle="chef"))
    monkeypatch.setattr(process.transcribe, "run", lambda video: "transcript")
    monkeypatch.setattr(process.brain, "extract_text", lambda *a, **k: dict(recipe))


def test_dry_run_writes_json_and_returns_recipe(tmp_path, monkeypatch):
    recipe = {"title": "Miso Soup", "base_servings": 2, "ingredients": [], "instructions": []}
    _patch_stages(monkeypatch, tmp_path, recipe)
    monkeypatch.setattr(process.brain, "vision_available", lambda: False)
    out = process.process_one("https://x/reel/1/", "recipe", dry_run=True)
    assert out["title"] == "Miso Soup"
    assert (tmp_path / "last_recipe.json").exists()


def test_vision_escalates_when_a_quantity_is_missing(tmp_path, monkeypatch):
    recipe = {"title": "X", "base_servings": 2, "ingredients": [], "instructions": [],
              "missing_quantities": ["salt"]}
    _patch_stages(monkeypatch, tmp_path, recipe)
    monkeypatch.setattr(process.brain, "vision_available", lambda: True)
    monkeypatch.setattr(process.frames, "sample", lambda video: ["f1.jpg"])
    seen = {}

    def fake_vision(frames, current, missing):
        seen["missing"] = missing
        current["missing_quantities"] = []
        return current

    monkeypatch.setattr(process.brain, "extract_vision", fake_vision)
    process.process_one("https://x/reel/1/", "recipe", dry_run=True)
    assert seen["missing"] == ["salt"]


def test_vision_skipped_when_unavailable(tmp_path, monkeypatch):
    recipe = {"title": "X", "base_servings": 2, "ingredients": [], "instructions": [],
              "missing_quantities": ["salt"]}
    _patch_stages(monkeypatch, tmp_path, recipe)
    monkeypatch.setattr(process.brain, "vision_available", lambda: False)
    called = {"vision": False}
    monkeypatch.setattr(process.brain, "extract_vision",
                        lambda *a, **k: called.__setitem__("vision", True))
    process.process_one("https://x/reel/1/", "recipe", dry_run=True)
    assert called["vision"] is False


def test_japan_bucket_routes_to_place_and_geocodes(tmp_path, monkeypatch):
    place = {"name": "Ichiran", "category": "food", "region": "Tokyo"}
    monkeypatch.setattr(process.download, "fetch", lambda url: Media(video="v.mp4", caption="cap", handle="chef"))
    monkeypatch.setattr(process.transcribe, "run", lambda video: "t")
    monkeypatch.setattr(process.brain, "extract_place", lambda *a, **k: dict(place))
    monkeypatch.setattr(process.geocode, "lookup", lambda query: (35.0, 139.0))
    written = {}
    monkeypatch.setattr(process.places, "append", lambda p: written.update(p))
    out = process.process_one("https://x/reel/1/", "japan")
    assert out["name"] == "Ichiran"
    assert out["lat"] == 35.0 and out["lng"] == 139.0
    assert written["name"] == "Ichiran"
