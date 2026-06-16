import pytest
import requests
from pipeline import config, mealie

RECIPE = {
    "title": "Test", "description": "d", "cuisine": "Japanese", "tags": ["vegetarian"],
    "base_servings": 4, "total_time_min": 40, "prep_time_min": 15, "cook_time_min": 25,
    "ingredients": [
        {"quantity": 2, "unit": "cup", "food": "flour", "note": "sifted"},
        {"quantity": 0, "unit": "", "food": "salt", "note": "to taste"},
    ],
    "instructions": ["Mix", "Bake"],
    "equipment": ["bowl"],
    "nutrition_per_serving": {"calories": 200, "protein_g": 5},
    "scaling_notes": "salt to taste when scaling",
    "confidence": "high", "confidence_notes": "clear",
    "_source_url": "https://example.com/reel",
}


def test_payload_maps_core_fields():
    payload = mealie._to_payload(RECIPE)
    assert payload["recipeServings"] == 4
    assert payload["totalTime"] == "PT40M"
    assert payload["orgURL"] == "https://example.com/reel"
    assert {"name": "Japanese"} in payload["recipeCategory"]
    assert {"name": "vegetarian"} in payload["tags"]


def test_payload_ingredients_structure():
    payload = mealie._to_payload(RECIPE)
    flour = payload["recipeIngredient"][0]
    assert flour["quantity"] == 2
    assert flour["unit"] == {"name": "cup"}
    assert flour["food"] == {"name": "flour"}
    salt = payload["recipeIngredient"][1]
    assert "unit" not in salt  # an empty unit is omitted, not sent as null


def test_payload_notes_carry_scaling_and_confidence():
    titles = [note["title"] for note in mealie._to_payload(RECIPE)["notes"]]
    assert any("Scaling" in title for title in titles)
    assert any("confidence" in title.lower() for title in titles)


def test_iso_duration():
    assert mealie._iso(40) == "PT40M"
    assert mealie._iso(0) is None


class _Resp:
    def __init__(self, code=200, body="slug-123", text=""):
        self.status_code = code
        self._body = body
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} from Mealie")

    def json(self):
        return self._body


def _set_mealie(monkeypatch):
    monkeypatch.setattr(config, "MEALIE_URL", "https://mealie.local")
    monkeypatch.setattr(config, "MEALIE_TOKEN", "tok")


def test_upsert_raises_when_create_status_is_error(monkeypatch):
    """A 401/5xx on create must raise via raise_for_status, never parse an error body into a slug."""
    _set_mealie(monkeypatch)

    def fail_post(*a, **k):
        return _Resp(code=401, body={"detail": "bad token"}, text="unauthorized")

    monkeypatch.setattr(mealie.requests, "post", fail_post)
    with pytest.raises(requests.HTTPError):
        mealie.upsert({"title": "X"})


def test_upsert_raises_when_create_returns_no_slug(monkeypatch):
    """A 200 create whose body carries no usable slug is a hard error, not a junk URL."""
    _set_mealie(monkeypatch)
    monkeypatch.setattr(mealie.requests, "post",
                        lambda *a, **k: _Resp(code=200, body={"message": "ok"}, text="{}"))
    with pytest.raises(RuntimeError, match="slug"):
        mealie.upsert({"title": "X"})


def test_upsert_happy_path_returns_slug(monkeypatch, tmp_path):
    """Create yields a slug, then PATCH and the image PUT both succeed."""
    _set_mealie(monkeypatch)
    seen = {}

    def fake_post(url, **k):
        seen["post"] = url
        return _Resp(code=201, body={"slug": "miso-soup"})

    def fake_patch(url, **k):
        seen["patch"] = url
        return _Resp(code=200, body={})

    def fake_put(url, **k):
        seen["put"] = url
        return _Resp(code=200, body={})

    monkeypatch.setattr(mealie.requests, "post", fake_post)
    monkeypatch.setattr(mealie.requests, "patch", fake_patch)
    monkeypatch.setattr(mealie.requests, "put", fake_put)

    img = tmp_path / "thumb.jpg"
    img.write_bytes(b"jpegbytes")

    assert mealie.upsert(RECIPE, image_path=str(img)) == "miso-soup"
    assert seen["post"].endswith("/api/recipes")
    assert seen["patch"].endswith("/api/recipes/miso-soup")
    assert seen["put"].endswith("/api/recipes/miso-soup/image")
