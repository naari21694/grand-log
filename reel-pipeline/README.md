# Grand Log pipeline (developer guide)

This is the module-level guide for working inside the `pipeline` package. A new user should start at the project [README](../README.md) and the [install guide](../docs/INSTALL.md), not here.

The single-reel core, the Telegram bot (Den Den Mushi), the SQLite queue, the backfill, and the tile dashboard all live in this directory. The module map is in [`../ARCHITECTURE.md`](../ARCHITECTURE.md); every setting is in [`../docs/CONFIGURATION.md`](../docs/CONFIGURATION.md). This file covers the per-module CLI commands and how to run the package directly.

```text
download (yt-dlp, gallery-dl fallback)
  then transcribe (whisper)
  then brain (Gemini, free): caption and transcript become structured JSON
  then sample frames (ffmpeg) and read all on-screen text (Gemini vision)
  then write to the destination, or with --dry-run write the JSON
```

Every stage is a swappable adapter. Flip the brain or the transcriber with one line in `.env`.

## Run one reel from the CLI
From inside `reel-pipeline/` with the venv active and `.env` written (see the [install guide](../docs/INSTALL.md)):
```powershell
python -m pipeline.doctor          # confirms ffmpeg, your brain key, and access control
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
```
`--dry-run` appends the recipe to your local cookbook (`work/recipes.json`, plus a `recipes.csv` summary) instead of writing to Mealie. The first run that touches video downloads the Whisper model (about 1.5 GB).

To point at a real Mealie, run it (Docker) and create an API token (User, Profile, API Tokens), put `MEALIE_URL` and `MEALIE_TOKEN` in `.env`, and drop `--dry-run`:

```yaml
# mealie.compose.yaml (a separate service you run, not this repo's shipped compose.yaml)
services:
  mealie:
    image: ghcr.io/mealie-recipes/mealie:latest
    ports: ["9925:9000"]
    environment: { BASE_URL: "http://localhost:9925", ALLOW_SIGNUP: "false" }
    volumes: ["./mealie-data:/app/data"]
    restart: unless-stopped
```

> Instagram cookies (dev note): Instagram blocks most logged-out downloads. The path that works on Windows is a Netscape `cookies.txt` from a throwaway IG account dropped at `work/cookies.txt` (auto-detected; point elsewhere with `YTDLP_COOKIES_FILE`). The browser path (`YTDLP_COOKIES_BROWSER`) is an override and is broken on Windows (DPAPI).

## Layout
The full module map, grouped by layer, is in [`../ARCHITECTURE.md`](../ARCHITECTURE.md). In short: entrypoints (`process`, `bot`, `web`, `backfill`, `doctor`), core (`config`, `routing`, `schema`, `security`), stages (`download`, `transcribe`, `frames`), extract (`brain`, `geocode`), destinations (`mealie`, `places`, `home`, `recipes`), and data (`queue`, `store`).

## Den Den Mushi (the Telegram bot)
Share a reel to the bot, tap a crew button (Baratie, Log Pose, Going Merry), and it files the reel, then replies with a card: the thumbnail, the title, a one-line summary, and an Open button to the real destination.
```bash
# get a bot token from @BotFather, put it in .env as TELEGRAM_BOT_TOKEN
# the bot is locked to you: message it once, it replies with your chat id, add it as
# ALLOWED_CHAT_IDS in .env, restart. See ../SECURITY.md for the full hardening checklist.
python -m pipeline.bot          # long-polling, no public URL needed
# or, on any OS with Docker:
docker compose up -d
```
Two commands turn the chat into your hub: `/search <term>` finds anything you have saved, and `/digest` resurfaces a few items to revisit. Jobs land in a SQLite queue (`work/queue.db`) so they survive a restart, and every filed item is indexed in `work/items.db` for search.

## Dashboard (tile view)
A clean tile grid of everything you saved, searchable and filterable by crew, each tile opening into its real destination. Works in any phone browser, and as a Telegram Mini App.
```bash
python -m pipeline.web            # then open http://localhost:8080
```
To open it from the bot with `/dashboard`, expose it over HTTPS (a tunnel) and set `WEBAPP_URL` in `.env`. No extra dependencies; it reads the same `work/items.db`.

## Backfill your whole saved list (offline)
Export from Instagram (Accounts Center, Your information and permissions, Download your information, choose JSON). The `saved_collections.json` and `saved_posts.json` files already carry each item's URL, caption, and Collection name, so the backfill reads them directly: no Instagram fetch, no cookies, no Whisper.
```bash
python -m pipeline.backfill saved_collections.json                  # preview: counts and routing
python -m pipeline.backfill saved_collections.json --run --limit 20 # a safe first slice
python -m pipeline.backfill saved_collections.json --run            # full run (resumable)
```
Each item is auto-routed: a Collection name with a clear keyword routes for free, otherwise the brain classifies it once per collection. Recipe, place, and home get full extraction from the caption; everything else (art, books, memes) is indexed as a searchable `saved` item, so nothing is lost. An item with no caption, or whose extraction is thin, is recorded in `work/needs_video.jsonl` for a later video pass on a host where Instagram cookies work.

The run is resumable (it skips any URL already saved), so you can stop and restart it, or spread it across sessions to stay under a free-tier daily limit. Set `BACKFILL_SLEEP` to pause between AI calls. Routing keywords are editable without touching code: drop a `work/routes.json` like `{ "place": ["travel", "trip"], "home": ["decor"] }`.

## Log Pose (places)
Share a travel reel and pick Log Pose, or run it directly:
```bash
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --bucket place
```
It extracts the place, geocodes it free via OpenStreetMap, and appends to `work/places.geojson` and `work/places.csv`. Import the GeoJSON into Google My Maps for pins, or the CSV into a sheet for region panels. A live Sheets and My Maps API connector is a tracked follow-up.

## Going Merry (home ideas)
Share a home or build-together reel and pick Going Merry, or run it directly:
```bash
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --bucket home
```
It extracts the item (what, room, price, store, link, dimensions, why) and appends to `work/home.csv` and `work/home.json`. Import the CSV into a sheet or Notion for your vault.

## Tests
```bash
pip install pytest requests
pytest -q
```
The network and model stages are monkeypatched, so the suite runs fast with no external services.

## Next increments
Considered improvements are tracked in [`../IDEAS.md`](../IDEAS.md).
