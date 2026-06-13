"""Backfill: load your Instagram data export and queue everything you saved.

Saved Collection names become the router when present: recipes go to Baratie, Japan and
travel to Log Pose, home to Going Merry. Anything unmatched uses --default.

  python -m pipeline.backfill saved_posts.json
  python -m pipeline.backfill saved_collections.json --run     # also process now, no Telegram
  python -m pipeline.backfill saved_posts.json --bucket recipe  # force one bucket

Get the export from Instagram: Accounts Center, Your information and permissions,
Download your information, JSON format.

NOTE: parsing matches the commonly seen saved_posts.json shape (saved_saved_media,
string_map_data["Saved on"]["href"]) and the saved_collections shape. Instagram changes
this format over time, so there is a regex fallback that grabs any instagram.com URL.
This is INFERENCE, NOT VERIFIED against a live export in this build. Check your own file
and adjust _extract if a key differs.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from . import queue
from .process import process_one

_BUCKETS = ("recipe", "japan", "home")
_ROUTES = [
    ("japan", ("japan", "travel", "trip", "tokyo", "osaka", "kyoto", "place", "itinerary")),
    ("home", ("home", "decor", "furnitur", "house", "interior", "apartment", "build")),
    ("recipe", ("recipe", "food", "cook", "meal", "kitchen", "baking", "eat")),
]
_IG_URL = re.compile(r"https?://(?:www\.)?instagram\.com/[^\s\"']+")


def route(collection_name: str, default: str = "recipe") -> str:
    """Map a saved-Collection name to a bucket by keyword, falling back to default."""
    name = (collection_name or "").lower()
    for bucket, keys in _ROUTES:
        if any(key in name for key in keys):
            return bucket
    return default


def _extract(data: object) -> list[tuple[str, str]]:
    """Pull (url, collection_name) pairs from the parsed export, best effort."""
    pairs: list[tuple[str, str]] = []
    if not isinstance(data, dict):
        return pairs
    for entry in data.get("saved_saved_media", []) or []:
        href = ((entry.get("string_map_data") or {}).get("Saved on") or {}).get("href")
        if href:
            pairs.append((href, ""))  # saved_posts.json carries no collection name
    for coll in data.get("saved_collections", []) or []:
        name = coll.get("title", "")
        for link in coll.get("string_list_data", []) or []:
            if link.get("href"):
                pairs.append((link["href"], name))
    return pairs


def parse(export_path: str, default: str = "recipe", force: str | None = None) -> list[tuple[str, str]]:
    """Return a de-duplicated [(url, bucket)] from an Instagram saved export (JSON)."""
    text = Path(export_path).read_text(encoding="utf-8")
    pairs = _extract(json.loads(text))
    if not pairs:  # fallback: any instagram URL anywhere in the file
        pairs = [(url, "") for url in dict.fromkeys(_IG_URL.findall(text))]

    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for url, name in pairs:
        if url in seen:
            continue
        seen.add(url)
        out.append((url, force or route(name, default)))
    return out


def _drain() -> int:
    """Process every pending job now, synchronously. Recipe bucket only for the moment."""
    done = 0
    while True:
        job = queue.claim_next()
        if job is None:
            return done
        if job["bucket"] != "recipe":
            queue.mark_failed(job["id"], "bucket not aboard yet")
            continue
        try:
            recipe = process_one(job["url"], job["bucket"], False)
            queue.mark_done(job["id"], recipe.get("title", ""))
            done += 1
        except Exception as exc:
            queue.mark_failed(job["id"], str(exc))


def main() -> None:
    ap = argparse.ArgumentParser(description="Queue your saved Instagram reels from a data export.")
    ap.add_argument("export", help="path to saved_posts.json or saved_collections.json")
    ap.add_argument("--default", default="recipe", choices=_BUCKETS, help="bucket for unmatched items")
    ap.add_argument("--bucket", choices=_BUCKETS, help="force every item to this bucket")
    ap.add_argument("--run", action="store_true", help="also process the queue now, no Telegram needed")
    args = ap.parse_args()

    queue.init_db()
    items = parse(args.export, default=args.default, force=args.bucket)
    for url, bucket in items:
        queue.enqueue(url, bucket, 0)  # chat_id 0: no Telegram reply for backfill jobs

    counts: dict[str, int] = {}
    for _, bucket in items:
        counts[bucket] = counts.get(bucket, 0) + 1
    print(f"queued {len(items)} saved reels: {counts}")

    if args.run:
        print(f"processed {_drain()} reels")


if __name__ == "__main__":
    main()
