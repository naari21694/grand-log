from pipeline import process, store
from pipeline.download import Media


def _base_patch(monkeypatch, tmp_path):
    monkeypatch.setattr(process.config, "WORKDIR", tmp_path)
    monkeypatch.setattr(process.config, "MEALIE_URL", "")
    monkeypatch.setattr(process.store, "_DB", tmp_path / "items.db")
    monkeypatch.setattr(process.download, "fetch",
                        lambda url: Media(video="v.mp4", caption="cap", handle="chef"))
    monkeypatch.setattr(process.download, "fetch_meta",
                        lambda url: Media(video="", caption="cap", handle="chef"))
    monkeypatch.setattr(process.transcribe, "run", lambda video: "transcript")
    monkeypatch.setattr(process.frames, "grab_one", lambda video: "")


def test_dry_run_writes_json_and_returns_recipe(tmp_path, monkeypatch):
    _base_patch(monkeypatch, tmp_path)
    recipe = {"title": "Miso Soup", "base_servings": 2, "ingredients": [], "instructions": []}
    monkeypatch.setattr(process.brain, "extract_text", lambda *a, **k: dict(recipe))
    monkeypatch.setattr(process.brain, "vision_available", lambda: False)
    out = process.process_one("https://x/reel/1/", "recipe", dry_run=True)
    assert out["title"] == "Miso Soup"
    assert (tmp_path / "last_recipe.json").exists()
    assert (tmp_path / "recipes.json").exists()  # the persistent local cookbook
    assert out["_card"]["title"] == "Miso Soup"


def test_process_records_item_to_store(tmp_path, monkeypatch):
    _base_patch(monkeypatch, tmp_path)
    monkeypatch.setattr(process.brain, "extract_text",
                        lambda *a, **k: {"title": "Findable Dish", "base_servings": 2,
                                         "ingredients": [], "instructions": []})
    monkeypatch.setattr(process.brain, "vision_available", lambda: False)
    process.process_one("https://x/reel/1/", "recipe", dry_run=True)
    assert store.search("Findable")[0]["title"] == "Findable Dish"


def test_vision_escalates_when_a_quantity_is_missing(tmp_path, monkeypatch):
    _base_patch(monkeypatch, tmp_path)
    recipe = {"title": "X", "base_servings": 2, "ingredients": [], "instructions": [],
              "missing_quantities": ["salt"]}
    monkeypatch.setattr(process.brain, "extract_text", lambda *a, **k: dict(recipe))
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
    _base_patch(monkeypatch, tmp_path)
    recipe = {"title": "X", "base_servings": 2, "ingredients": [], "instructions": [],
              "missing_quantities": ["salt"]}
    monkeypatch.setattr(process.brain, "extract_text", lambda *a, **k: dict(recipe))
    monkeypatch.setattr(process.brain, "vision_available", lambda: False)
    called = {"vision": False}
    monkeypatch.setattr(process.brain, "extract_vision",
                        lambda *a, **k: called.__setitem__("vision", True))
    process.process_one("https://x/reel/1/", "recipe", dry_run=True)
    assert called["vision"] is False


def test_place_bucket_routes_and_geocodes(tmp_path, monkeypatch):
    _base_patch(monkeypatch, tmp_path)
    place = {"name": "Ichiran", "category": "food", "region": "Tokyo"}
    monkeypatch.setattr(process.brain, "extract_place", lambda *a, **k: dict(place))
    monkeypatch.setattr(process.geocode, "lookup", lambda query: (35.0, 139.0))
    written = {}
    monkeypatch.setattr(process.places, "append", lambda p: written.update(p))
    out = process.process_one("https://x/reel/1/", "place")
    assert out["name"] == "Ichiran"
    assert out["lat"] == 35.0 and out["lng"] == 139.0
    assert written["name"] == "Ichiran"
    assert "google.com/maps" in out["_card"]["link"]


def test_home_bucket_routes_to_vault(tmp_path, monkeypatch):
    _base_patch(monkeypatch, tmp_path)
    item = {"item": "Sofa", "category": "furniture", "room": "living"}
    monkeypatch.setattr(process.brain, "extract_home", lambda *a, **k: dict(item))
    written = {}
    monkeypatch.setattr(process.home, "append", lambda i: written.update(i))
    out = process.process_one("https://x/reel/1/", "home")
    assert out["item"] == "Sofa"
    assert written["item"] == "Sofa"


def _track_full(monkeypatch):
    """Replace the full download with a tracker so a test can assert whether the video was fetched."""
    fetched = {"full": False}
    monkeypatch.setattr(process.download, "fetch",
                        lambda url: fetched.__setitem__("full", True) or Media("v.mp4", "cap", "chef"))
    monkeypatch.setattr(process.brain, "vision_available", lambda: False)
    return fetched


def test_caption_only_skips_video_when_complete(tmp_path, monkeypatch):
    _base_patch(monkeypatch, tmp_path)
    fetched = _track_full(monkeypatch)
    complete = {"title": "Caption Dish", "base_servings": 2,
                "ingredients": [{"food": "rice"}], "instructions": ["cook"], "confidence": "high"}
    monkeypatch.setattr(process.brain, "extract_text", lambda *a, **k: dict(complete))
    out = process.process_one("https://x/reel/1/", "recipe", dry_run=True, mode="auto")
    assert out["title"] == "Caption Dish"
    assert fetched["full"] is False  # a complete caption never downloads the video


def test_escalates_to_video_when_caption_thin(tmp_path, monkeypatch):
    _base_patch(monkeypatch, tmp_path)
    fetched = _track_full(monkeypatch)
    thin = {"title": "X", "base_servings": 2, "ingredients": [], "instructions": []}
    monkeypatch.setattr(process.brain, "extract_text", lambda *a, **k: dict(thin))
    process.process_one("https://x/reel/1/", "recipe", dry_run=True, mode="auto")
    assert fetched["full"] is True  # a thin caption forces the video download


def test_caption_mode_never_downloads(tmp_path, monkeypatch):
    _base_patch(monkeypatch, tmp_path)
    fetched = _track_full(monkeypatch)
    thin = {"title": "X", "base_servings": 2, "ingredients": [], "instructions": []}
    monkeypatch.setattr(process.brain, "extract_text", lambda *a, **k: dict(thin))
    process.process_one("https://x/reel/1/", "recipe", dry_run=True, mode="caption")
    assert fetched["full"] is False  # caption mode never escalates, even when thin
