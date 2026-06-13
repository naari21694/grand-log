import json

from pipeline import schema


def test_schema_hint_is_valid_json():
    json.loads(schema.SCHEMA_HINT)


def test_recipe_schema_lists_required_fields():
    required = schema.RECIPE_SCHEMA["required"]
    for field in ("title", "base_servings", "ingredients", "instructions"):
        assert field in required


def test_text_prompt_formats_with_all_keys():
    out = schema.TEXT_PROMPT.format(url="u", handle="h", caption="c", transcript="t")
    assert "TRANSCRIPT" in out and "u" in out


def test_vision_prompt_formats_with_all_keys():
    out = schema.VISION_PROMPT.format(recipe_json="{}", missing="salt", schema_hint="{}")
    assert "salt" in out


def test_place_schema_lists_required_fields():
    assert "name" in schema.PLACE_SCHEMA["required"]
    assert "category" in schema.PLACE_SCHEMA["required"]


def test_place_schema_hint_is_valid_json():
    json.loads(schema.PLACE_SCHEMA_HINT)


def test_place_prompt_formats_with_all_keys():
    out = schema.PLACE_PROMPT.format(url="u", handle="h", caption="c", transcript="t")
    assert "category" in out
