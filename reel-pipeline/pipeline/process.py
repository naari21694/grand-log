"""Process one reel end to end, route it, and record it for search and resurfacing.

The bot and the backfill call process_one(url, bucket). Everything up to the brain is
shared; the bucket picks the schema and the destination. Every filed item is also recorded
in the store, so /search and /digest can find it later. The rich result lives in the
best-of-breed destination (Mealie, a map, a vault); the store is the unified index.

    python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
    python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --bucket place
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse

from . import brain, config, download, frames, geocode, home, mealie, places, store, transcribe
from .routing import BUCKETS, NAMES

try:
    sys.stdout.reconfigure(encoding="utf-8")  # keep emoji safe on Windows consoles
except Exception:
    pass

# Side-view straw hat with Luffy's red band, slightly levitating over a faint shadow.
_COLORS = {"y": "\033[93m", "r": "\033[91m", "d": "\033[90m", "": ""}
_HAT = [
    ("y", "          .-~~~~~~~-."),
    ("y", "        .'           '."),
    ("y", "       /               \\"),
    ("y", "      /                 \\"),
    ("r", "   ,--===================--,"),
    ("y", "  /                         \\"),
    ("y", "  '.,_____________________,.'"),
    ("", ""),
    ("d", "      '-.._______..-'"),
]


def _banner() -> None:
    """Print the straw hat: yellow hat, red band, faint shadow, floating. Plain if not a tty or NO_COLOR."""
    color = sys.stdout.isatty() and not os.getenv("NO_COLOR")
    reset = "\033[0m"
    for tag, line in _HAT:
        print(f"{_COLORS[tag]}{line}{reset}" if (color and tag) else line)
    print()


def process_one(url: str, bucket: str = "recipe", dry_run: bool = False) -> dict:
    print(f"🏴‍☠️  {NAMES.get(bucket, 'Grand Log')} · {bucket}")
    print(f"   download  {url}")
    media = download.fetch(url)
    print(f"   caption {len(media.caption)} chars · @{media.handle or '?'}")
    transcript = transcribe.run(media.video)
    print(f"   transcript {len(transcript)} chars")

    if bucket == "place":
        record = _process_place(url, media, transcript)
    elif bucket == "home":
        record = _process_home(url, media, transcript)
    else:
        record = _process_recipe(url, media, transcript, dry_run)

    card = _card(record, bucket)
    record["_card"] = card
    store.save(bucket=bucket, title=card["title"], summary=card["summary"], link=card["link"],
               thumb=card["thumb"], text=json.dumps(record, ensure_ascii=False), source_url=url)
    return record


def _card(record: dict, bucket: str) -> dict:
    """The one-card view: a title, a one-line summary, a link to the real destination, a thumbnail."""
    title = record.get("title") or record.get("name") or record.get("item") or "Saved"
    if bucket == "recipe":
        summary = f"serves {record.get('base_servings', '?')}, {len(record.get('ingredients', []))} ingredients"
    elif bucket == "place":
        summary = ", ".join(x for x in (record.get("category"), record.get("region") or record.get("city")) if x)
    else:
        summary = ", ".join(x for x in (record.get("category"), record.get("room")) if x)
    return {"title": title, "summary": summary,
            "link": record.get("_link", ""), "thumb": record.get("_thumb", "")}


def _process_recipe(url: str, media, transcript: str, dry_run: bool) -> dict:
    recipe = brain.extract_text(media.caption, transcript, url, media.handle)
    missing = recipe.get("missing_quantities") or []
    if missing and brain.vision_available():
        print(f"   vision: reading on-screen quantities for {missing}")
        recipe = brain.extract_vision(frames.sample(media.video), recipe, missing)
    recipe["_source_url"] = url
    recipe["_thumb"] = frames.grab_one(media.video) or ""

    if dry_run or not config.MEALIE_URL:
        out = config.WORKDIR / "last_recipe.json"
        out.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")
        recipe["_link"] = ""
        print(f"\U0001f4dd  dry-run, recipe written to {out}")
        print(f"   {recipe.get('title')} · serves {recipe.get('base_servings')} · "
              f"{len(recipe.get('ingredients', []))} ingredients · confidence {recipe.get('confidence')}")
        return recipe

    slug = mealie.upsert(recipe, image_path=recipe["_thumb"] or None)
    recipe["_link"] = f"{config.MEALIE_URL}/g/home/r/{slug}"
    print(f"✅  Mealie: {recipe['_link']}")
    return recipe


def _process_place(url: str, media, transcript: str) -> dict:
    place = brain.extract_place(media.caption, transcript, url, media.handle)
    place["_source_url"] = url
    if not place.get("lat") and place.get("name"):
        query = " ".join(p for p in (place.get("name"), place.get("city"), place.get("country")) if p)
        coords = geocode.lookup(query)
        if coords:
            place["lat"], place["lng"] = coords
    places.append(place)
    place["_thumb"] = frames.grab_one(media.video) or ""
    maps_q = urllib.parse.quote_plus(
        " ".join(p for p in (place.get("name"), place.get("city"), place.get("country")) if p))
    place["_link"] = f"https://www.google.com/maps/search/?api=1&query={maps_q}" if maps_q else ""
    where = place.get("region") or place.get("city") or "?"
    pinned = "pinned" if place.get("lat") else "saved (no coords)"
    print(f"🗾  Log Pose {pinned}: {place.get('name')} ({where})")
    return place


def _process_home(url: str, media, transcript: str) -> dict:
    item = brain.extract_home(media.caption, transcript, url, media.handle)
    item["_source_url"] = url
    home.append(item)
    item["_thumb"] = frames.grab_one(media.video) or ""
    item["_link"] = item.get("link", "")
    print(f"🏠  Going Merry saved: {item.get('item')} ({item.get('room') or item.get('category') or '?'})")
    return item


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Reel to a crew destination")
    ap.add_argument("url")
    ap.add_argument("--bucket", default="recipe", choices=list(BUCKETS))
    ap.add_argument("--dry-run", action="store_true", help="recipe only: write JSON, don't post to Mealie")
    a = ap.parse_args()
    _banner()
    process_one(a.url, a.bucket, a.dry_run)
