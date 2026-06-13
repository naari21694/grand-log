"""Write the recipe into Mealie: two-step create (POST name -> slug, PATCH body), then image.

Ingredients are stored STRUCTURALLY (quantity + unit + food) so Mealie's serving-scaler
renders 1/2/4/6/10. scaling_notes + confidence go into recipe notes; nutrition is per-serving.
"""
from __future__ import annotations

import requests

from . import config


def _iso(mins) -> str | None:
    return f"PT{int(mins)}M" if mins else None


def _to_payload(r: dict) -> dict:
    ings = []
    for i in r.get("ingredients", []):
        ing = {"quantity": i.get("quantity") or 0,
               "food": {"name": i.get("food", "")},
               "note": i.get("note", "")}
        if i.get("unit"):
            ing["unit"] = {"name": i["unit"]}
        ings.append(ing)

    notes = []
    if r.get("scaling_notes"):
        notes.append({"title": "Scaling (1 to 10 people)", "text": r["scaling_notes"]})
    if r.get("confidence"):
        notes.append({"title": f"Extraction confidence: {r['confidence']}",
                      "text": r.get("confidence_notes", "")})

    n = r.get("nutrition_per_serving") or {}
    nutrition = {k: str(v) for k, v in {
        "calories": n.get("calories"), "proteinContent": n.get("protein_g"),
        "fatContent": n.get("fat_g"), "carbohydrateContent": n.get("carbs_g"),
        "fiberContent": n.get("fiber_g"), "sodiumContent": n.get("sodium_mg"),
        "sugarContent": n.get("sugar_g")}.items() if v is not None}

    servings = r.get("base_servings") or 2
    payload = {
        "description": r.get("description", ""),
        "recipeServings": servings,
        "recipeYieldQuantity": servings,
        "recipeYield": "servings",
        "recipeIngredient": ings,
        "recipeInstructions": [{"text": s} for s in r.get("instructions", [])],
        "tags": [{"name": t} for t in r.get("tags", [])],
        "recipeCategory": [{"name": r["cuisine"]}] if r.get("cuisine") else [],
        "tools": [{"name": t} for t in r.get("equipment", [])],
        "orgURL": r.get("_source_url", ""),
        "notes": notes,
    }
    for key, val in {"totalTime": _iso(r.get("total_time_min")),
                     "prepTime": _iso(r.get("prep_time_min")),
                     "performTime": _iso(r.get("cook_time_min"))}.items():
        if val:
            payload[key] = val
    if nutrition:
        payload["nutrition"] = nutrition
    return payload


def upsert(recipe: dict, image_path: str | None = None) -> str:
    h = {"Authorization": f"Bearer {config.MEALIE_TOKEN}"}
    slug = requests.post(f"{config.MEALIE_URL}/api/recipes",
                         json={"name": recipe.get("title", "Untitled reel recipe")},
                         headers=h, timeout=60).json()
    if isinstance(slug, dict):
        slug = slug.get("slug") or slug.get("id")

    requests.patch(f"{config.MEALIE_URL}/api/recipes/{slug}",
                   json=_to_payload(recipe), headers=h, timeout=60).raise_for_status()

    if image_path:
        with open(image_path, "rb") as fh:
            requests.put(f"{config.MEALIE_URL}/api/recipes/{slug}/image",
                         files={"image": ("thumb.jpg", fh, "image/jpeg")},
                         data={"extension": "jpg"}, headers=h, timeout=60)
    return slug
