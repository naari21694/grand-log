# Grand Log: Getting Started

Grand Log is an open-source, self-hosted pipeline that turns the Instagram reels you save into things you can actually use. Share a reel and the value gets extracted and filed: a recipe with exact measurements in your Mealie cookbook (Baratie), a pin on your map (Log Pose), or a home idea in your vault (Going Merry). You drive it all from a Telegram bot (Den Den Mushi). It is alpha software, so expect rough edges.

There are three ways to run it:

1. **One-click cloud.** Deploy the bot to a host and let it run. See [DEPLOY.md](DEPLOY.md).
2. **Docker.** One container for the bot, good on any OS or a small always-on box. Covered below.
3. **Local.** Run it on your own computer with a Python virtualenv or Docker Desktop. Good for trying it out, and a valid always-on personal host in its own right (see [Your own computer](DEPLOY.md#your-own-computer-a-personal-always-on-host)). Covered below.

For the full menu of hosts (your own computer, a home server or Pi, Oracle, Railway, Render, Fly) and how to keep each one running, see [Choose your host](DEPLOY.md#choose-your-host).

Every setting lives in one `.env` file. This guide shows the minimal path; for the full list of options and the complete brain provider matrix, see [CONFIGURATION.md](CONFIGURATION.md).

## 1. Prerequisites

You need two things on your machine before anything else.

**Python 3.10 or newer.** Check with `python --version` (or `python3 --version`).

**A real ffmpeg binary.** This is the actual ffmpeg program, not the `pip install ffmpeg` package, which does not work. yt-dlp and Whisper both need it.

```bash
# Linux (Debian/Ubuntu)
sudo apt install ffmpeg
```

```bash
# macOS (Homebrew)
brew install ffmpeg
```

```powershell
# Windows
winget install Gyan.FFmpeg
```

After installing on Windows, open a new terminal so `ffmpeg` is on PATH.

**A free brain key.** The "brain" is the model that reads the caption and transcript and turns them into structured JSON. The easy start is Google's Gemini free tier: get a key at [aistudio.google.com](https://aistudio.google.com). One Gemini key powers both the text extraction and the on-screen vision pass. Other providers (any OpenAI-compatible API, or the official Anthropic API) are listed in [CONFIGURATION.md](CONFIGURATION.md).

## 2. Local install

Pick your platform. Each has a one-liner installer and a manual fallback. Both install into `reel-pipeline/`.

### Windows

One-liner (run from the repo root):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

It warns if ffmpeg is missing, creates the virtualenv, installs the requirements, copies `.env.example` to `.env` if you do not have one yet, and runs the doctor at the end.

### Linux and macOS

One-liner (run from the repo root):

```bash
bash scripts/install.sh
```

Same steps as the Windows script: ffmpeg warning, virtualenv, requirements, `.env` from the template, then the doctor.

### Manual fallback (any OS)

If you would rather do it by hand, or the script fails:

```bash
cd reel-pipeline
python -m venv .venv

# activate the venv:
. .venv/bin/activate              # Linux/macOS
# .\.venv\Scripts\Activate.ps1    # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
```

The first time you run an extraction, the pipeline downloads the Whisper transcription model (about 1.5 GB). That happens once and is cached for every run after.

**Transcription just works.** It auto-detects an NVIDIA GPU and runs on it (much faster), and falls back to CPU when there is none. No setting is required. On Windows with an NVIDIA GPU, if the GPU run cannot find the CUDA libraries, install them once into your virtualenv:

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

Override: to transcribe in the cloud off your own machine, set `TRANSCRIBE_BACKEND=groq` in `.env` for free, fast Whisper. That needs a `GROQ_API_KEY` from [console.groq.com](https://console.groq.com).

**The easy way to create `.env`.** Instead of copying the template by hand, run the setup wizard. It prompts for your brain provider and key, writes `.env`, and runs the doctor at the end:

```bash
python -m pipeline.setup
```

## 3. Configure the brain

Open `reel-pipeline/.env` and set the provider plus its matching key. The minimal Gemini case is two lines:

```ini
BRAIN_PROVIDER=gemini
GEMINI_API_KEY=your-key-from-aistudio
```

`GEMINI_MODEL` defaults to `gemini-2.5-flash`, and `BRAIN_VISION=auto` lets the same key read quantities shown on screen but never spoken. To use an OpenAI-compatible endpoint (OpenAI, OpenRouter, Groq, Together, local Ollama) or the official Anthropic API instead, see the provider matrix in [CONFIGURATION.md](CONFIGURATION.md).

## 4. Check your setup

Run the doctor. It tells you exactly what is in place and what is missing before you try to process anything.

```bash
python -m pipeline.doctor
```

Each line is one check, marked `[OK ]` or `[XX]`:

- **`ffmpeg on PATH`** (required): the ffmpeg binary was found. If this fails, go back to Prerequisites.
- **`brain: gemini key`** (required, for the Gemini provider): `GEMINI_API_KEY` is set. For the openai provider the line is `brain: openai-compatible`; for anthropic you get two lines, `brain: anthropic key` and `brain: anthropic SDK`.
- **`work/ writable`** (required): the `work/` output folder can be written to.
- **`bot access control`** (advisory): the bot is locked to you. Empty until you set `ALLOWED_CHAT_IDS` (see step 7).
- **`telegram token (optional)`** (advisory): `TELEGRAM_BOT_TOKEN` is set. Needed only to run the bot.
- **`mealie reachable (optional)`** (advisory): shown only if `MEALIE_URL` is set, and reports whether Mealie answers.

The three required checks gate the exit code. When they all pass you see "All required checks passed." The advisory lines are fine to leave failing until you want the bot or a Mealie destination.

## 5. Your first extraction (no Mealie needed)

You can extract a reel and see the result without any destination set up. Start with the fastest path, caption-only, which matches the README quickstart:

```bash
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --no-video --dry-run
```

What the two flags do:

- `--no-video` reads only the caption. No download, no Whisper, so it is the fastest path and needs no ffmpeg and no Instagram cookies. Drop it to let the pipeline download the video and run Whisper (and the on-screen vision pass) when the caption alone is too thin. That fuller run is the `auto` default; see [CONFIGURATION.md](CONFIGURATION.md#capture-mode).
- `--dry-run` skips any Mealie destination and writes to a local cookbook instead.

Either way it runs the brain and appends the recipe to your local cookbook: `work/recipes.json` (the full list) plus a `recipes.csv` summary. It also writes the latest result to `work/last_recipe.json`. Open either to see what the brain pulled out: measurements, a confidence flag, and more.

**Instagram cookies note.** Instagram blocks most logged-out downloads behind a login wall. To get past it, log into Instagram with a throwaway account, never your main one, and give the downloader its cookies.

The easy path, which works on Windows: export a `cookies.txt` (Netscape format) for that throwaway account and drop it at `work/cookies.txt`. It is auto-detected, so no `.env` change is needed. To point at a different location, set `YTDLP_COOKIES_FILE` in `.env`.

The browser-cookie path is an override and is broken on Windows (it fails with a DPAPI decrypt error), so prefer the `cookies.txt` file there. On Linux or macOS you can instead pull cookies straight from a logged-in browser profile:

```ini
YTDLP_COOKIES_BROWSER=chrome
```

Use whatever browser holds the throwaway login (`chrome`, `firefox`, and so on). With neither set, the downloader tries without cookies, which often fails.

## 6. Run the bot (Den Den Mushi)

The bot is how you drive Grand Log from your phone: share a reel to it, tap a crew button, and it files the reel.

First, get a bot token. Message [@BotFather](https://t.me/BotFather) on Telegram, create a bot, and copy the token it gives you. Put it in `.env`:

```ini
TELEGRAM_BOT_TOKEN=your-token-from-botfather
```

Then run it:

```bash
python -m pipeline.bot
```

It uses long-polling, so no public URL is needed.

**The security claim flow (read this).** The bot refuses to serve strangers, and the lock is not automatic, you have to claim it. Here is exactly what happens:

1. You start the bot with no `ALLOWED_CHAT_IDS` set.
2. You message the bot. Because your chat is not on the allow-list, the bot does not process the reel. Instead it replies with your numeric chat id.
3. You copy that id into `.env`:

   ```ini
   ALLOWED_CHAT_IDS=123456789
   ```

4. You restart the bot. Now it serves you, and only you.

This is the lock that keeps strangers from sharing reels to your bot and spending your brain key. Until you set `ALLOWED_CHAT_IDS` (or deliberately flip `ALLOW_ALL_CHATS=true`, which you should not do for a public bot), every unknown chat gets the same "here is your id, add it to allow yourself" reply and nothing is processed.

## 7. The dashboard

The dashboard is a tile grid of everything you have saved, searchable and filterable by crew, each tile opening into its real destination.

```bash
python -m pipeline.web
```

Then open [http://127.0.0.1:8080](http://127.0.0.1:8080).

It binds localhost (`127.0.0.1`) by default, so it is reachable only from your own machine. To open it to the wider internet (for example, as a Telegram Mini App), put it behind an HTTPS tunnel and set `DASHBOARD_TOKEN`; see [CONFIGURATION.md](CONFIGURATION.md).

## 8. Backfill your saved history

Backfill takes a saved-collections export and routes each reel to the right crew. Start with the bundled sample so you can watch routing work before touching your real data:

```bash
python -m pipeline.backfill examples/saved_collections.sample.json
```

That queues the sample reels (queue only, nothing is processed yet) and shows how collection titles like "Recipes", "Japan Travel", and "Home Decor" route to the recipe, place, and home crews.

When you are ready for your real history, export it from Instagram (Accounts Center, then "Your information and permissions", then "Download your information", and choose JSON). Point the same command at that file:

```bash
python -m pipeline.backfill path/to/saved_posts.json
```

The parser matches the common export shape with a regex fallback, so check it against your own file in case a key differs.

For a full backlog, the Gemini free tier (about 20 requests a day) is too small. Because the brain is provider-agnostic, point `BRAIN_PROVIDER` at a higher-limit option for the backfill and keep Gemini for live shares: Groq (free, fast), a local Ollama (free, unlimited), or a Gemini key with billing (about a dollar for the whole backlog). Set `BACKFILL_SLEEP` to match the provider's rate limit; the run is resumable, so you can stop and restart anytime.

## 9. Run with Docker

Docker is the simplest way to keep the bot running on any OS or a small always-on box. The `compose.yaml` ships a single long-running bot service.

```bash
cd reel-pipeline
cp .env.example .env        # set TELEGRAM_BOT_TOKEN, plus your brain and Mealie keys
docker compose up -d
```

The container mounts `./work` for output and keeps the Whisper model in a named cache volume, so the 1.5 GB download happens once. The image installs a real ffmpeg binary for you.

To run a single extraction in a container instead of the long-running bot:

```bash
docker build -t grand-log reel-pipeline/
docker run --rm -v "$PWD/work:/app/work" grand-log "https://www.instagram.com/reel/XXXX/" --dry-run
```

## 10. Troubleshooting

Full problem-cause-fix list: [TROUBLESHOOTING.md](TROUBLESHOOTING.md). The two you are most likely to hit first:

**ffmpeg not found.** The doctor's `ffmpeg on PATH` check fails. Install the real binary (see Prerequisites), then open a new terminal so PATH is refreshed. The `pip install ffmpeg` package is not the same thing and will not work. Caption-only runs (`--no-video`) do not need ffmpeg at all.

**Instagram login wall.** Downloads fail or return nothing because Instagram blocks logged-out access. Export a `cookies.txt` from a throwaway Instagram account and drop it at `work/cookies.txt`, which is auto-detected and is the path that works on Windows (see step 5). Do not use your main account.

For GPU and CUDA libraries, the Windows browser-cookie (DPAPI) failure, brain auth errors, the Anthropic SDK, the bot "Locked, your chat id is X" claim flow, and the Telegram-unreachable case, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
