"""Live end-to-end smoke test: the real brain, real routing, real destinations.

Unlike tests/ (which mocks the brain), this exercises the actual extraction through
whatever BRAIN_PROVIDER is configured (gemini by default). It stubs only the two stages
that need outside credentials or large models: the Instagram download and the whisper
transcription. Everything after the brain is real: routing, geocoding, the destination
files, the store index, and the card.

    python -m tools.smoke_live

Needs: a key for the configured brain provider (for the gemini default, GEMINI_API_KEY). No
IG cookies, no Mealie, no Telegram token. Geocoding hits free Nominatim; a network miss
degrades to "saved without coords" and the test still passes.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from pipeline import brain, config, download, process, store, transcribe

# Synthetic reels with enough detail for a real extraction. The recipe deliberately
# leaves the salt amount unspoken to exercise the missing_quantities path.
RECIPE = (
    "@tokyo_home_kitchen Classic miso soup for 2. Caption: dashi 500ml, 2 tbsp miso paste, "
    "150g silken tofu cubed, 1 stalk spring onion sliced, a handful of wakame. Add salt to taste.",
    "Bring the dashi to a gentle simmer, do not boil. Whisk in the miso through a strainer. "
    "Add the tofu and wakame, warm for two minutes, finish with spring onion and a little salt.",
)
PLACE = (
    "@ramen_japan Ichiran Shibuya is the one tonkotsu bowl you cannot skip in Tokyo. "
    "Solo booths, order by ticket machine, customise richness and spice.",
    "We waited twenty minutes, worth every second. It sits right by Shibuya crossing in Tokyo, Japan.",
)
HOME = (
    "@small_space_living This boucle sofa transformed our living room. The Söderhamn from IKEA, "
    "about 699 dollars, 2.3m wide, oatmeal colour.",
    "It is deep enough to nap on and the cover comes off to wash, which sold us.",
)


def _run(bucket: str, caption: str, transcript: str) -> dict:
    download.fetch = lambda url, _cap=caption, _h="creator": download.Media(
        video=str(config.WORKDIR / "nonexistent.mp4"), caption=_cap, handle=_h)
    transcribe.run = lambda video, _t=transcript: _t
    url = f"https://www.instagram.com/reel/SMOKE_{bucket}/"
    return process.process_one(url, bucket, dry_run=(bucket == "recipe"), mode="full")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="grandlog_smoke_"))
    config.WORKDIR = tmp
    process.config.WORKDIR = tmp
    store._DB = tmp / "items.db"
    config.MEALIE_URL = ""
    process.config.MEALIE_URL = ""

    print(f"brain: provider={config.BRAIN_PROVIDER} vision_available={brain.vision_available()}")
    print(f"workdir: {tmp}\n")

    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" :: {detail}" if detail else ""))
        if not ok:
            failures.append(label)

    # --- Recipe (Baratie), dry-run, real brain ---
    print("RECIPE -> Baratie")
    r = _run("recipe", *RECIPE)
    check("title extracted", bool(r.get("title")), r.get("title", ""))
    check("base_servings present", isinstance(r.get("base_servings"), int), str(r.get("base_servings")))
    check("ingredients found", len(r.get("ingredients", [])) >= 3, f"{len(r.get('ingredients', []))} ingredients")
    check("dry-run JSON written", (tmp / "last_recipe.json").exists())
    check("card summary built", "ingredients" in r["_card"]["summary"], r["_card"]["summary"])
    check("indexed in store", bool(store.search("miso")), "searchable by 'miso'")

    # --- Place (Log Pose), real brain + real geocode ---
    print("\nPLACE -> Log Pose")
    p = _run("place", *PLACE)
    check("name extracted", bool(p.get("name")), p.get("name", ""))
    check("category in enum", p.get("category") in
          {"food", "see", "do", "buy", "try", "stay", "other"}, str(p.get("category")))
    check("places.geojson written", (tmp / "places.geojson").exists())
    check("places.csv written", (tmp / "places.csv").exists())
    check("maps link built", "google.com/maps" in p["_card"]["link"])
    geocoded = bool(p.get("lat"))
    check("geocoded (or gracefully skipped)", True, "pinned" if geocoded else "no coords (network or miss)")

    # --- Home (Going Merry), real brain ---
    print("\nHOME -> Going Merry")
    h = _run("home", *HOME)
    check("item extracted", bool(h.get("item")), h.get("item", ""))
    check("category in enum", h.get("category") in
          {"furniture", "decor", "material", "appliance", "lighting", "idea", "other"}, str(h.get("category")))
    check("home.csv written", (tmp / "home.csv").exists())
    check("home.json written", (tmp / "home.json").exists())

    # --- Store: all three filed, searchable ---
    print("\nSTORE (the unified index)")
    recent = store.recent(10)
    check("all three buckets indexed", {row["bucket"] for row in recent} == {"recipe", "place", "home"},
          str(sorted({row["bucket"] for row in recent})))
    check("digest sample works", len(store.sample(3)) >= 1)

    print()
    if failures:
        print(f"RESULT: {len(failures)} check(s) FAILED: {failures}")
        return 1
    print("RESULT: all live end-to-end checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
