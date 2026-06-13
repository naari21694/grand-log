# Reel → Recipe pipeline (v0.1 — core)

Share an Instagram recipe reel → exact ingredients/measurements extracted → auto-scaled
1/2/4/6/10 in Mealie. This is the **core single-reel pipeline**; the Telegram bot + queue +
backlog backfill layer on top of it next. Design + decisions: `../reel-pipeline-blueprint.md`.

```
download (yt-dlp→gallery-dl) → transcribe (whisper) → brain text (claude -p)
  → [if a quantity is missing] frames (ffmpeg) → brain vision (Gemini free)
  → Mealie  (or --dry-run: write JSON)
```

Everything is a swappable adapter — flip the brain or transcriber with one line in `.env`.

## Test it on Windows today — three tiers

**Tier 0 — extraction only (no Mealie, no Gemini key needed):**
```powershell
cd reel-pipeline
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
winget install Gyan.FFmpeg          # if ffmpeg isn't on PATH
copy .env.example .env              # defaults are fine for this tier
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
```
→ writes `work/last_recipe.json` — the full structured recipe (exact measurements, grams,
`scaling_notes`, per-serving nutrition, confidence). Uses `claude -p` for the brain (your
Claude Code CLI). First run downloads the Whisper model (~1.5 GB).

> Instagram blocks most logged-out downloads. Set `YTDLP_COOKIES_BROWSER=chrome` (or your
> browser) in `.env`, logged into a **throwaway** IG account.

**Tier 1 — add on-screen-quantity reading (free):**
Get a free key at aistudio.google.com → put it in `.env` as `GEMINI_API_KEY`. Now any reel
that *shows* a quantity it never says gets filled from the frames.

**Tier 2 — real cookbook (point at Mealie):**
Run Mealie (Docker) and create an API token (User → Profile → API Tokens). Put `MEALIE_URL`
+ `MEALIE_TOKEN` in `.env`, drop `--dry-run` → the recipe lands in Mealie; open its PWA,
slide servings to 1/2/4/6/10.

```yaml
# docker-compose.yml (Mealie, arm64 + amd64)
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
| `TRANSCRIBE_BACKEND` | `faster_whisper` (dev/Windows) or `whisper_cpp` (ARM prod) |
| `YTDLP_COOKIES_BROWSER` | browser to pull IG cookies from (throwaway account) |
| `MEALIE_URL` / `MEALIE_TOKEN` | leave URL empty to force dry-run |

## Layout
```
pipeline/config.py      env config            pipeline/brain.py    claude_p + gemini adapters
pipeline/schema.py      recipe schema+prompts pipeline/mealie.py   two-step create + image
pipeline/download.py    yt-dlp → gallery-dl   pipeline/process.py  orchestrate one reel (CLI)
pipeline/transcribe.py  whisper backends      pipeline/frames.py   ffmpeg scene-frames
```

## Next increments
1. Telegram bot (long-poll, 🍳 button) + SQLite job queue + worker.
2. Backlog backfill: IG data-export `saved_*.json` → queue (Collection name = route).
3. Japan/Home systems: new schema + Google Sheets/Maps connector (reuses everything above).
