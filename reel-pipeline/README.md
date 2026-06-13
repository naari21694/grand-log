# Reel to Recipe pipeline (v0.1, core)

Share an Instagram recipe reel, get the exact ingredients and measurements, auto-scaled for 1, 2, 4, 6, 10 in Mealie. This is the core single-reel pipeline. The Telegram bot, the queue, and the backlog backfill layer on top of it next. Design and decisions live in `../reel-pipeline-blueprint.md`.

```
download (yt-dlp, gallery-dl fallback)
  then transcribe (whisper)
  then brain text (claude -p)
  then, if a quantity is missing, sample frames (ffmpeg) and brain vision (Gemini free)
  then write to Mealie, or with --dry-run write the JSON
```

Every stage is a swappable adapter. Flip the brain or the transcriber with one line in `.env`.

## Test it on Windows today, three tiers

**Tier 0, extraction only (no Mealie, no Gemini key):**
```powershell
cd reel-pipeline
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
winget install Gyan.FFmpeg          # if ffmpeg is not on PATH
copy .env.example .env              # defaults are fine for this tier
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
```
This writes `work/last_recipe.json`, the full structured recipe (exact measurements, grams, `scaling_notes`, per-serving nutrition, confidence). It uses `claude -p` for the brain (your Claude Code CLI). The first run downloads the Whisper model (about 1.5 GB).

> Instagram blocks most logged-out downloads. Set `YTDLP_COOKIES_BROWSER=chrome` (or your browser) in `.env`, logged into a throwaway IG account.

**Tier 1, add on-screen-quantity reading (free):**
Get a free key at aistudio.google.com, put it in `.env` as `GEMINI_API_KEY`. Now any reel that shows a quantity it never says gets filled from the frames.

**Tier 2, real cookbook (point at Mealie):**
Run Mealie (Docker) and create an API token (User, Profile, API Tokens). Put `MEALIE_URL` and `MEALIE_TOKEN` in `.env`, drop `--dry-run`, and the recipe lands in Mealie. Open its PWA, slide servings to 1, 2, 4, 6, 10.

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
| Var | Meaning |
|---|---|
| `BRAIN_TEXT` | `claude_p` (Max credit) or `gemini` |
| `BRAIN_VISION` | `gemini` (free tier) or `none` |
| `TRANSCRIBE_BACKEND` | `faster_whisper` (dev, Windows) or `whisper_cpp` (ARM prod) |
| `YTDLP_COOKIES_BROWSER` | browser to pull IG cookies from (throwaway account) |
| `MEALIE_URL`, `MEALIE_TOKEN` | leave the URL empty to force dry-run |

## Layout
```
pipeline/config.py      env config            pipeline/brain.py    claude_p and gemini adapters
pipeline/schema.py      recipe schema, prompts pipeline/mealie.py   two-step create and image
pipeline/download.py    yt-dlp, gallery-dl    pipeline/process.py  orchestrate one reel (CLI)
pipeline/transcribe.py  whisper backends      pipeline/frames.py   ffmpeg scene-frames
```

## Den Den Mushi (the Telegram bot)
Share a reel to the bot, tap a crew button, and it queues and files the reel, then replies in the chat.
```bash
# get a bot token from @BotFather, put it in .env as TELEGRAM_BOT_TOKEN
python -m pipeline.bot          # long-polling, no public URL needed
# or, on any OS with Docker:
docker compose up -d
```
Jobs land in a SQLite queue (`work/queue.db`) so they survive a restart. A background worker runs the same pipeline and reports back. Baratie (recipes) is live; Log Pose and Going Merry reply that they are not aboard yet.

## Next increments
1. Backlog backfill: IG data-export `saved_*.json` into the queue (Collection name sets the route).
2. Japan and Home systems: a new schema plus a Google Sheets or Maps connector (reuses everything above).
