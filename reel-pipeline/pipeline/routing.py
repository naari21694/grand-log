"""Buckets, crew names, and Collection-name routing, in one place.

Bucket keys are plain generic nouns (recipe, place, home). The crew names are the brand
layer on top, mapped here. Routing keywords default here and can be overridden without
touching code by dropping a routes.json in WORKDIR (or next to .env), for example:

    { "place": ["travel", "trip", "city"], "home": ["home", "decor"] }
"""
from __future__ import annotations

import json

from . import config

# bucket key -> crew name (the brand layer; the only proper nouns that carry personality)
NAMES = {"recipe": "Baratie", "place": "Log Pose", "home": "Going Merry"}
BUCKETS = tuple(NAMES)

# bucket -> keywords that route a saved-Collection name to it. Generic, no personal specifics.
DEFAULT_ROUTES = {
    "place": ["travel", "trip", "place", "city", "vacation", "holiday",
              "destination", "explore", "itinerary", "wanderlust", "sightseeing", "tour"],
    "home": ["home", "decor", "furnitur", "house", "interior", "apartment", "build", "room"],
    "recipe": ["recipe", "food", "cook", "meal", "kitchen", "baking", "eat"],
}

_OVERRIDE = config.WORKDIR / "routes.json"


def routes() -> dict:
    """Default routes, overridden by routes.json if present, so the lists stay editable."""
    table = {bucket: list(keys) for bucket, keys in DEFAULT_ROUTES.items()}
    if _OVERRIDE.exists():
        try:
            for bucket, keys in json.loads(_OVERRIDE.read_text(encoding="utf-8")).items():
                table[bucket] = list(keys)
        except Exception:
            pass
    return table


def route(collection_name: str, default: str = "recipe") -> str:
    """Map a saved-Collection name to a bucket by keyword, falling back to default."""
    name = (collection_name or "").lower()
    table = routes()
    for bucket in ("place", "home", "recipe"):
        if any(key in name for key in table.get(bucket, [])):
            return bucket
    return default
