# 🍳 Grand Log pipeline

Share an Instagram reel and the value gets extracted and filed: a recipe with exact measurements auto-scaled for 1, 2, 4, 6, 10 in Mealie, a place on your map, or a home idea in your vault. The single-reel core, the Telegram bot (Den Den Mushi), the SQLite queue, the backfill, and the tile dashboard all live here. The module map is in [`../ARCHITECTURE.md`](../ARCHITECTURE.md).

```text
download (yt-dlp, gallery-dl fallback)
  then transcribe (whisper)
  then brain (Gemini, free): caption and transcript become structured JSON
  then, if a quantity is missing, sample frames (ffmpeg) and read them (Gemini vision)
  then write to the destination, or with --dry-run write the JSON
```

Every stage is a swappable adapter. Flip the brain or the transcriber with one line in `.env`.

## Run it on Windows today, two tiers

**Tier 0, extraction (free).** Get a free key at aistudio.google.com and put it in `.env` as `GEMINI_API_KEY`. One key powers both the text extraction and the on-screen vision pass.
```powershell
cd reel-pipeline
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
winget install Gyan.FFmpeg          # if ffmpeg is not on PATH
copy .env.example .env              # set GEMINI_API_KEY
python -m pipeline.doctor          # confirms ffmpeg, your brain key, and access control
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
```
This appends the recipe to your local cookbook (`work/recipes.json`, plus a `recipes.csv` summary) and writes `work/last_recipe.json` (the latest), the full structured recipe: exact measurements, grams, `scaling_notes`, per-serving nutrition, and a confidence flag. The vision pass reads quantities shown on screen but never spoken, using the same free key. The first run downloads the Whisper model (about 1.5 GB).

> Instagram blocks most logged-out downloads. Set `YTDLP_COOKIES_BROWSER=chrome` (or your browser) in `.env`, logged into a throwaway IG account.

**Tier 1, real cookbook (point at Mealie).** Run Mealie (Docker) and create an API token (User, Profile, API Tokens). Put `MEALIE_URL` and `MEALIE_TOKEN` in `.env`, drop `--dry-run`, and the recipe lands in Mealie. Open its PWA and slide servings to 1, 2, 4, 6, 10.

```yaml
# docker-compose.yml (Mealie, arm64 and amd64)
services:
  mealie:
    image: ghcr.io/mealie-recipes/mealie:latest
    ports: ["9925:9000"]
    environment: { BASE_URL: "http://localhost:9925", ALLOW_SIGNUP: "false" }
    volumes: ["./mealie-data:/app/data"]
    restart: unless-stopped
```

## Config (`.env`)
The full provider matrix, model picks, and every setting are in [../docs/CONFIGURATION.md](../docs/CONFIGURATION.md). The essentials:

| Var | Meaning |
|---|---|
| `CAPTURE_MODE` | `auto` (caption first, fetch the video only if the caption is thin), `caption` (never), or `full` (always) |
| `BRAIN_PROVIDER` | `gemini` (free), `openai` (OpenAI/OpenRouter/Groq/Ollama), or `anthropic` |
| `GEMINI_API_KEY` | free Gemini key from aistudio.google.com (or set the OPENAI_* / ANTHROPIC_* keys instead) |
| `BRAIN_VISION` | on-screen quantity reader: `auto`, `gemini`, `openai`, `anthropic`, or `none` |
| `TRANSCRIBE_BACKEND` | `faster_whisper` (dev, Windows) or `whisper_cpp` (ARM prod) |
| `YTDLP_COOKIES_BROWSER` | browser to pull IG cookies from (throwaway account) |
| `MEALIE_URL`, `MEALIE_TOKEN` | leave the URL empty to force dry-run |
| `ALLOWED_CHAT_IDS` | lock the bot to your Telegram chat id (the bot tells you yours on first message) |

## Layout
The full module map, grouped by layer, is in [`../ARCHITECTURE.md`](../ARCHITECTURE.md). In short: entrypoints (`process`, `bot`, `web`, `backfill`, `doctor`), core (`config`, `routing`, `schema`, `security`), stages (`download`, `transcribe`, `frames`), extract (`brain`, `geocode`), destinations (`mealie`, `places`, `home`, `recipes`), and data (`queue`, `store`).

## 🐌 Den Den Mushi (the Telegram bot)
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

## 🗺️ Dashboard (tile view)
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

## 🗾 Log Pose (places)
Share a travel reel and pick Log Pose, or run it directly:
```bash
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --bucket place
```
It extracts the place, geocodes it free via OpenStreetMap, and appends to `work/places.geojson` and `work/places.csv`. Import the GeoJSON into Google My Maps for pins, or the CSV into a sheet for region panels. A live Sheets and My Maps API connector is a tracked follow-up.

## 🏠 Going Merry (home ideas)
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
