"""Process one reel end to end. The Telegram bot + queue (next increment) just call process_one().

    python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
"""
from __future__ import annotations
import argparse
import json
import sys

from . import brain, config, download, frames, mealie, transcribe

# Grand Log suite — each bucket is a One Piece artifact.
NAMES = {"recipe": "Baratie", "japan": "Log Pose", "home": "Going Merry"}

try:
    sys.stdout.reconfigure(encoding="utf-8")  # keep emoji safe on Windows consoles
except Exception:
    pass


def process_one(url: str, bucket: str = "recipe", dry_run: bool = False) -> dict:
    print(f"🏴‍☠️  {NAMES.get(bucket, 'Grand Log')} · {bucket}")
    print(f"⤵  download  {url}")
    media = download.fetch(url)
    print(f"   caption {len(media.caption)} chars · @{media.handle or '?'}")

    transcript = transcribe.run(media.video)
    print(f"   transcript {len(transcript)} chars")

    recipe = brain.extract_text(media.caption, transcript, url, media.handle)
    missing = recipe.get("missing_quantities") or []
    if missing and brain.vision_available():
        print(f"   vision: reading on-screen quantities for {missing}")
        recipe = brain.extract_vision(frames.sample(media.video), recipe, missing)
    recipe["_source_url"] = url

    if dry_run or not config.MEALIE_URL:
        out = config.WORKDIR / "last_recipe.json"
        out.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\U0001f4dd  dry-run — recipe written to {out}")
        print(f"   {recipe.get('title')} · serves {recipe.get('base_servings')} · "
              f"{len(recipe.get('ingredients', []))} ingredients · confidence {recipe.get('confidence')}")
        return recipe

    slug = mealie.upsert(recipe, image_path=frames.grab_one(media.video))
    print(f"✅  Mealie: {config.MEALIE_URL}/g/home/r/{slug}")
    return recipe


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Reel -> recipe")
    ap.add_argument("url")
    ap.add_argument("--bucket", default="recipe")
    ap.add_argument("--dry-run", action="store_true", help="extract only; write JSON, don't post to Mealie")
    a = ap.parse_args()
    process_one(a.url, a.bucket, a.dry_run)
