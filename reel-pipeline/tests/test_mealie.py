from pipeline import mealie

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
