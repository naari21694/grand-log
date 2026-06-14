"""Process one reel end to end, route it, and record it for search and resurfacing.

The bot and the backfill call process_one(url, bucket). It is caption-first: it reads the
caption only (no video download, no Whisper), and downloads the video and transcribes it
only when the caption alone is too thin to trust (CAPTURE_MODE=auto). caption never downloads;
full always downloads. The bucket picks the schema and the destination. Every filed item is
recorded in the store, so /search and /digest can find it later.

    python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
    python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --bucket place
    python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --no-video
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


def process_one(url: str, bucket: str = "recipe", dry_run: bool = False, mode: str | None = None) -> dict:
    mode = mode or config.CAPTURE_MODE
    print(f"🏴‍☠️  {NAMES.get(bucket, 'Grand Log')} · {bucket} · {mode}")
    extract = {"place": brain.extract_place, "home": brain.extract_home}.get(bucket, brain.extract_text)
    media, record = _gather(url, bucket, mode, extract)

    if bucket == "place":
        record = _finish_place(url, media, record)
    elif bucket == "home":
        record = _finish_home(url, media, record)
    else:
        record = _finish_recipe(url, media, record, dry_run)

    card = _card(record, bucket)
    record["_card"] = card
    store.save(bucket=bucket, title=card["title"], summary=card["summary"], link=card["link"],
               thumb=card["thumb"], text=json.dumps(record, ensure_ascii=False), source_url=url)
    return record


def _gather(url: str, bucket: str, mode: str, extract) -> tuple:
    """Caption-first extraction. Downloads the video and transcribes only when needed.
    Returns (media, record). media.video is '' when the caption alone was enough."""
    if mode == "full":
        return _full(url, extract)
    try:
        meta = download.fetch_meta(url)
    except Exception as exc:
        if mode == "caption":
            raise
        print(f"   caption fetch failed ({exc}); downloading the video")
        return _full(url, extract)
    print(f"   caption {len(meta.caption)} chars · @{meta.handle or '?'} (no video)")
    record = extract(meta.caption, "", url, meta.handle)
    if mode == "caption" or not _thin(record, bucket):
        return meta, record
    print("   caption is thin; escalating to the video (download + transcript)")
    return _full(url, extract)


def _full(url: str, extract) -> tuple:
    media = download.fetch(url)
    print(f"   caption {len(media.caption)} chars · @{media.handle or '?'}")
    transcript = transcribe.run(media.video)
    print(f"   transcript {len(transcript)} chars")
    return media, extract(media.caption, transcript, url, media.handle)


def _thin(record: dict, bucket: str) -> bool:
    """Is the caption-only extraction too weak to trust, so we should read the video?"""
    if not isinstance(record, dict) or record.get("confidence") == "low":
        return True
    if bucket == "recipe":
        return (not record.get("ingredients") or not record.get("instructions")
                or bool(record.get("missing_quantities")))
    if bucket == "place":
        return not record.get("name")
    if bucket == "home":
        return not record.get("item")
    return False


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


def _finish_recipe(url: str, media, recipe: dict, dry_run: bool) -> dict:
    missing = recipe.get("missing_quantities") or []
    if missing and media.video and brain.vision_available():
        print(f"   vision: reading on-screen quantities for {missing}")
        recipe = brain.extract_vision(frames.sample(media.video), recipe, missing)
    recipe["_source_url"] = url
    recipe["_thumb"] = (frames.grab_one(media.video) or "") if media.video else ""

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


def _finish_place(url: str, media, place: dict) -> dict:
    place["_source_url"] = url
    if not place.get("lat") and place.get("name"):
        query = " ".join(p for p in (place.get("name"), place.get("city"), place.get("country")) if p)
        coords = geocode.lookup(query)
        if coords:
            place["lat"], place["lng"] = coords
    places.append(place)
    place["_thumb"] = (frames.grab_one(media.video) or "") if media.video else ""
    maps_q = urllib.parse.quote_plus(
        " ".join(p for p in (place.get("name"), place.get("city"), place.get("country")) if p))
    place["_link"] = f"https://www.google.com/maps/search/?api=1&query={maps_q}" if maps_q else ""
    where = place.get("region") or place.get("city") or "?"
    pinned = "pinned" if place.get("lat") else "saved (no coords)"
    print(f"🗾  Log Pose {pinned}: {place.get('name')} ({where})")
    return place


def _finish_home(url: str, media, item: dict) -> dict:
    item["_source_url"] = url
    home.append(item)
    item["_thumb"] = (frames.grab_one(media.video) or "") if media.video else ""
    item["_link"] = item.get("link", "")
    print(f"🏠  Going Merry saved: {item.get('item')} ({item.get('room') or item.get('category') or '?'})")
    return item


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Reel to a crew destination")
    ap.add_argument("url")
    ap.add_argument("--bucket", default="recipe", choices=list(BUCKETS))
    ap.add_argument("--dry-run", action="store_true", help="recipe only: write JSON, don't post to Mealie")
    ap.add_argument("--mode", choices=["auto", "caption", "full"], default=config.CAPTURE_MODE,
                    help="auto: caption first, fetch video only if thin; caption: never; full: always")
    ap.add_argument("--no-video", action="store_true", help="caption only, never download the video")
    a = ap.parse_args()
    _banner()
    process_one(a.url, a.bucket, a.dry_run, "caption" if a.no_video else a.mode)
