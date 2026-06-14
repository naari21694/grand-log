"""Backfill: ingest your Instagram saved export, offline.

Instagram lets you download your own data (Accounts Center > Your information and permissions >
Download your information > select JSON). The `saved_collections.json` and `saved_posts.json`
files carry, for each saved item, its URL, its caption, and (for collections) your Collection
name. This reads them directly, so the bulk backfill needs no Instagram fetch, no cookies, and
no Whisper.

Each item is auto-routed: recipe, place, and home get full extraction from the caption; anything
else (art, memes, books) is indexed as a searchable saved item, so nothing is lost. An item whose
caption is missing, or whose extraction comes back thin, is recorded in `work/needs_video.jsonl`
for a later, richer video pass on a host where Instagram cookies work.

    python -m pipeline.backfill saved_collections.json                  # preview: counts + routing
    python -m pipeline.backfill saved_collections.json --run --limit 20 # a safe first slice
    python -m pipeline.backfill saved_collections.json --run            # full run (resumable)

The run is resumable: it skips any URL already in the store, so you can stop and restart it, or
run it across several sessions to stay inside a free-tier daily limit. Set BACKFILL_SLEEP to pause
between AI calls.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path

from . import brain, config, routing, store
from .process import _thin, process_one

_IG_URL = re.compile(r"https?://(?:www\.)?instagram\.com/[^\s\"']+")
_CREW = ("recipe", "place", "home")  # the buckets that have a rich extractor and a destination


# ---------------- parse the export ----------------
def _walk_items(node):
    """Yield (url, caption) for every saved item anywhere in a nested label_values structure."""
    if isinstance(node, list):
        labels = {e["label"]: e for e in node if isinstance(e, dict) and "label" in e}
        if "URL" in labels:
            url = labels["URL"].get("href") or labels["URL"].get("value")
            if url:
                yield url, (labels.get("Caption") or {}).get("value", "")
        for child in node:
            yield from _walk_items(child)
    elif isinstance(node, dict):
        for value in node.values():
            yield from _walk_items(value)


def _collection_name(entry: dict) -> str:
    for field in entry.get("label_values") or []:
        if isinstance(field, dict) and field.get("label") == "Name":
            return field.get("value", "")
    return ""


def parse_export(path: str) -> list[tuple[str, str, str]]:
    """Return deduplicated (url, caption, collection_name) from a saved-data export.

    Handles the current nested list format and the older dict format, and falls back to a plain
    URL scan (captions and names lost) if a file matches neither.
    """
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    records: list[tuple[str, str, str]] = []

    if isinstance(data, list):  # current format: a list of collections or saved posts
        for entry in data:
            if not isinstance(entry, dict):
                continue
            name = _collection_name(entry)
            for url, caption in _walk_items(entry):
                records.append((url, caption, name))
    elif isinstance(data, dict):  # older export format
        for entry in data.get("saved_saved_media", []) or []:
            href = ((entry.get("string_map_data") or {}).get("Saved on") or {}).get("href")
            if href:
                records.append((href, "", ""))
        for coll in data.get("saved_collections", []) or []:
            name = coll.get("title", "")
            for link in coll.get("string_list_data", []) or []:
                if link.get("href"):
                    records.append((link["href"], "", name))

    if not records:  # last resort: any Instagram URL in the file
        records = [(url, "", "") for url in dict.fromkeys(_IG_URL.findall(text))]

    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for url, caption, name in records:
        if url in seen:
            continue
        seen.add(url)
        out.append((url, caption, name))
    return out


# ---------------- route (dynamic) ----------------
def route_item(caption: str, name: str, cache: dict) -> tuple[str, bool]:
    """Decide the bucket. A clear Collection-name keyword wins for free; otherwise the brain
    classifies once per collection (cached) from the caption. Returns (bucket, classified).

    Raises if the classify call fails (for example a rate limit), so the caller can defer the
    item and retry it on the next, resumable run rather than misfiling it.
    """
    keyword = routing.route(name, "")  # "" default tells us when the name did not match a bucket
    if keyword:
        return keyword, False
    if name and name in cache:
        return cache[name], False
    if caption:
        bucket = brain.classify(caption, name)  # may raise on an API or rate-limit error
        if name:
            cache[name] = bucket
        return bucket, True
    return "saved", False


# ---------------- index / flag ----------------
def _index_generic(url: str, caption: str, name: str) -> None:
    """Index a non-crew item so the whole library is searchable, with no AI call."""
    first_line = caption.strip().splitlines()[0].strip() if caption.strip() else ""
    title = first_line[:80] or "Saved"
    store.save(bucket="saved", title=title, summary=name, link=url, text=caption, source_url=url)


def _flag_needs_video(url: str, bucket: str, name: str) -> None:
    """Record an item for the later video pass (download + transcript + on-screen text)."""
    line = json.dumps({"url": url, "bucket": bucket, "collection": name}, ensure_ascii=False)
    with open(config.WORKDIR / "needs_video.jsonl", "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


# ---------------- ingest ----------------
def ingest(path: str, limit: int = 0) -> dict:
    """Ingest the export offline. Resumable (skips already-saved URLs) and throttled."""
    records = parse_export(path)
    if limit:
        records = records[:limit]
    total = len(records)
    counts: Counter = Counter()
    cache: dict = {}  # collection name -> bucket, so each collection is classified at most once
    print(f"ingesting {total} items from {Path(path).name} (resumable; already-saved are skipped)")

    for i, (url, caption, name) in enumerate(records, 1):
        if store.exists(url):
            counts["skipped"] += 1
        else:
            try:
                bucket, used_brain = route_item(caption, name, cache)
                if bucket in _CREW and caption:
                    record = process_one(url, bucket, caption=caption)
                    counts[bucket] += 1
                    if _thin(record, bucket):
                        _flag_needs_video(url, bucket, name)
                        counts["needs_video"] += 1
                    used_brain = True
                else:
                    _index_generic(url, caption, name)
                    counts["saved"] += 1
                    if bucket in _CREW:  # a crew item we could only reach through the video
                        _flag_needs_video(url, bucket, name)
                        counts["needs_video"] += 1
                if used_brain and config.BACKFILL_SLEEP:
                    time.sleep(config.BACKFILL_SLEEP)
            except Exception as exc:
                counts["deferred"] += 1  # not stored, so the next resumable run retries it
                print(f"   ~ {url[:55]} deferred: {str(exc)[:90]}")
        if i % 25 == 0 or i == total:
            print(f"   {i}/{total}  {dict(counts)}")
    return dict(counts)


def preview(path: str) -> None:
    """Cheap, no-AI summary: how many items, how many have captions, keyword routing so far."""
    records = parse_export(path)
    with_caption = sum(1 for _, caption, _ in records if caption)
    keyword = Counter(routing.route(name, "") or "auto-classify" for _, _, name in records)
    print(f"{len(records)} items in {Path(path).name}, {with_caption} with a caption in the export")
    print(f"keyword routing: {dict(keyword)}")
    print("(items shown as auto-classify are routed by the brain at --run; the rest are free)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest your Instagram saved export, offline.")
    ap.add_argument("export", help="path to saved_collections.json or saved_posts.json")
    ap.add_argument("--run", action="store_true", help="ingest (without it, just preview)")
    ap.add_argument("--limit", type=int, default=0, help="process only the first N items (a safe test)")
    args = ap.parse_args()

    if not args.run:
        preview(args.export)
        print("\nAdd --run to ingest. Try --run --limit 20 first to see it end to end.")
        return

    counts = ingest(args.export, args.limit)
    print(f"\ndone: {counts}")
    print("recipes in work/recipes.json, places in work/places.geojson, home in work/home.csv;")
    print("everything is searchable via the bot /search and the dashboard.")
    if counts.get("needs_video"):
        print(f"{counts['needs_video']} items flagged in work/needs_video.jsonl for the video pass.")


if __name__ == "__main__":
    main()
