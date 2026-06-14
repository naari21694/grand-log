"""Unit tests for the local cookbook: recipes accumulate (never overwritten), with a CSV summary."""
import json

from pipeline import recipes

RECIPE = {"title": "Miso Soup", "cuisine": "Japanese", "base_servings": 2,
          "ingredients": [{"food": "miso"}, {"food": "tofu"}], "tags": ["soup"],
          "confidence": "high", "_source_url": "https://x/reel/1/", "_card": {"x": 1}}


def _redirect(tmp_path, monkeypatch):
    monkeypatch.setattr(recipes.config, "WORKDIR", tmp_path)


def test_append_writes_json_list_without_card(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    recipes.append(RECIPE)
    items = json.loads((tmp_path / "recipes.json").read_text(encoding="utf-8"))
    assert items[0]["title"] == "Miso Soup"
    assert "_card" not in items[0]  # the derived card is stripped from the stored record


def test_two_recipes_accumulate(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    recipes.append(RECIPE)
    recipes.append({**RECIPE, "title": "Ramen"})
    items = json.loads((tmp_path / "recipes.json").read_text(encoding="utf-8"))
    assert [r["title"] for r in items] == ["Miso Soup", "Ramen"]  # the bug was overwriting


def test_csv_summary_has_header_and_row(tmp_path, monkeypatch):
    _redirect(tmp_path, monkeypatch)
    recipes.append(RECIPE)
    text = (tmp_path / "recipes.csv").read_text(encoding="utf-8")
    assert "title" in text.splitlines()[0]
    assert "Miso Soup" in text
