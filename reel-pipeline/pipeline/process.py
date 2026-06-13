"""Process one reel end to end and route it to the right crew member.

The Telegram bot and the backfill both call process_one(url, bucket). Everything up to the
brain is shared; the bucket picks the schema and the destination.

    python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
    python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --bucket japan
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import brain, config, download, frames, geocode, home, mealie, places, transcribe

# Grand Log suite, each bucket is a One Piece artifact.
NAMES = {"recipe": "Baratie", "japan": "Log Pose", "home": "Going Merry"}

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

    if bucket == "japan":
        return _process_place(url, media, transcript)
    if bucket == "home":
        return _process_home(url, media, transcript)
    return _process_recipe(url, media, transcript, dry_run)


def _process_recipe(url: str, media, transcript: str, dry_run: bool) -> dict:
    recipe = brain.extract_text(media.caption, transcript, url, media.handle)
    missing = recipe.get("missing_quantities") or []
    if missing and brain.vision_available():
        print(f"   vision: reading on-screen quantities for {missing}")
        recipe = brain.extract_vision(frames.sample(media.video), recipe, missing)
    recipe["_source_url"] = url

    if dry_run or not config.MEALIE_URL:
        out = config.WORKDIR / "last_recipe.json"
        out.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\U0001f4dd  dry-run, recipe written to {out}")
        print(f"   {recipe.get('title')} · serves {recipe.get('base_servings')} · "
              f"{len(recipe.get('ingredients', []))} ingredients · confidence {recipe.get('confidence')}")
        return recipe

    slug = mealie.upsert(recipe, image_path=frames.grab_one(media.video))
    print(f"✅  Mealie: {config.MEALIE_URL}/g/home/r/{slug}")
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
    where = place.get("region") or place.get("city") or "?"
    pinned = "pinned" if place.get("lat") else "saved (no coords)"
    print(f"🗾  Log Pose {pinned}: {place.get('name')} ({where})")
    return place


def _process_home(url: str, media, transcript: str) -> dict:
    item = brain.extract_home(media.caption, transcript, url, media.handle)
    item["_source_url"] = url
    home.append(item)
    print(f"🏠  Going Merry saved: {item.get('item')} ({item.get('room') or item.get('category') or '?'})")
    return item


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Reel to a crew destination")
    ap.add_argument("url")
    ap.add_argument("--bucket", default="recipe", choices=["recipe", "japan", "home"])
    ap.add_argument("--dry-run", action="store_true", help="recipe only: write JSON, don't post to Mealie")
    a = ap.parse_args()
    _banner()
    process_one(a.url, a.bucket, a.dry_run)
