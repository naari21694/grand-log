# Troubleshooting

When something does not work, start here. Each entry is a symptom, its cause, and the fix.
Most setup problems show up in the doctor first, so run it before anything else:

```bash
python -m pipeline.doctor
```

For the full settings reference see [CONFIGURATION.md](CONFIGURATION.md). Back to the docs
index: [README.md](README.md).

## Setup

### ffmpeg not found

The doctor's `ffmpeg on PATH` check fails, or an extraction errors when it falls back to video.

Cause: the real ffmpeg binary is not installed or not on PATH. The `pip install ffmpeg` package is
a different thing and does not work.

Fix: install the real binary, then open a new terminal so PATH is refreshed.

```bash
sudo apt install ffmpeg          # Linux (Debian/Ubuntu)
brew install ffmpeg              # macOS (Homebrew)
winget install Gyan.FFmpeg       # Windows
```

Caption-only runs (`--no-video`, or `CAPTURE_MODE=caption`) never download a video, so they do not
need ffmpeg. You only need it for `auto` and `full` mode.

### Python too old

An install or import fails on a syntax or version error.

Cause: Grand Log targets Python 3.10 or newer.

Fix: check with `python --version` (or `python3 --version`) and upgrade if it is below 3.10.

### work/ not writable

The doctor's `work/ writable` check fails.

Cause: the `work/` output folder cannot be written to. On a server this is usually a missing or
non-persistent volume mount.

Fix: make sure `work/` exists and is writable. Under Docker, mount a persistent volume at
`/app/work` (see [DEPLOY.md](DEPLOY.md)); without it, the queue and index reset on every restart.

## Capture and download

### Instagram login wall

Downloads fail or return nothing.

Cause: Instagram blocks most logged-out downloads behind a login wall, so the downloader needs a
logged-in cookie to fetch a reel.

Fix: log into Instagram with a throwaway account, never your main one, export a Netscape-format
`cookies.txt` for it, and drop it at `work/cookies.txt`. It is auto-detected, so no `.env` change is
needed. To point at a different location, set `YTDLP_COOKIES_FILE`. Caption-only mode reads the
caption without a download, so for many reels the login wall does not matter at all.

### Windows browser-cookie (DPAPI) failure

The `YTDLP_COOKIES_BROWSER` path fails on Windows with a DPAPI decrypt error.

Cause: yt-dlp cannot read Chrome's cookie store on Windows because of DPAPI encryption.

Fix: use the `cookies.txt` file path instead (above). It works everywhere and takes precedence over
the browser-cookie path. The `YTDLP_COOKIES_BROWSER=chrome` override is for Linux and macOS only.
Running under Docker also sidesteps the quirk, since the container is Linux.

### Throttled after a burst

Image posts (`/p/` links) start failing after a run of successful downloads.

Cause: Instagram rate-limits an account that pulls many posts quickly. This is a throttle, not a
code error.

Fix: slow down and retry later. Space out large backfills rather than processing everything at once.
The worker already requeues transient failures with backoff (`WORKER_MAX_ATTEMPTS`).

## Transcription and GPU

### CUDA libraries not found on Windows

Transcription cannot start on the GPU and reports missing CUDA libraries, even though an NVIDIA GPU
is present.

Cause: the cuDNN and cuBLAS libraries are not in the virtualenv.

Fix: install them once into your active virtualenv.

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

If you would rather not run on the GPU, force CPU with `WHISPER_DEVICE=cpu`, or move transcription
off your machine with `TRANSCRIBE_BACKEND=groq` (free cloud Whisper; needs a `GROQ_API_KEY`).

### Transcription is slow

A full-mode run takes a long time.

Cause: it is running on CPU. A CPU-only laptop is slow at Whisper.

Fix: transcription auto-detects an NVIDIA GPU and uses it when present. With no GPU, set
`TRANSCRIBE_BACKEND=groq` to move it to free cloud Whisper, or stay in caption-first mode so most
reels skip Whisper entirely.

### Model download on first run

The first extraction pauses for a large download.

Cause: faster-whisper fetches the Whisper model (about 1.5 GB) the first time it runs.

Fix: nothing to do. It downloads once and is cached for every run after. Under Docker the model is
kept in a named cache volume so it is not re-downloaded across restarts.

## Brain

### Brain key or auth error

Extraction fails with an authentication or key error.

Cause: the provider and key in `.env` do not match, or the key is missing or wrong.

Fix: confirm `BRAIN_PROVIDER` and the matching key. For Gemini that is `BRAIN_PROVIDER=gemini` and a
filled-in `GEMINI_API_KEY`. Run `python -m pipeline.doctor` and confirm the brain line reads `[OK ]`.
The provider matrix for OpenAI-compatible endpoints and Anthropic is in [CONFIGURATION.md](CONFIGURATION.md#the-brain).

### Anthropic SDK missing

The doctor's `brain: anthropic SDK` line fails when `BRAIN_PROVIDER=anthropic`.

Cause: the `anthropic` SDK is not installed. It ships in `requirements.txt` and is imported only when
you use that provider.

Fix: a normal `pip install -r requirements.txt` covers it. If the line still fails, run
`pip install anthropic` in your active virtualenv.

## Bot

### "Locked, your chat id is X"

You message the bot and it replies with your numeric chat id instead of processing the reel.

Cause: this is expected, not a bug. The bot is owner-locked and the lock is not automatic, you claim
it. Until your chat is on the allow-list, every unknown chat gets the same reply and nothing is
processed. This is what stops a stranger from spending your brain key.

Fix: copy the id it gave you into `.env`, then restart the bot.

```ini
ALLOWED_CHAT_IDS=123456789
```

Now it serves you, and only you. Do not set `ALLOW_ALL_CHATS=true` for a public bot.

### Bot times out on start (Telegram unreachable)

The bot starts but cannot reach Telegram and times out.

Cause: some networks and ISPs block Telegram. The bot dials out to Telegram over long-polling, so if
that path is blocked it cannot connect.

Fix: confirm the host can reach Telegram (try it from another network, or use a VPN or a cloud host).
This is a network reachability problem, not a Grand Log error. A cloud host (see
[DEPLOY.md](DEPLOY.md)) avoids it entirely.

### No bot token

The bot will not start, or the doctor's `telegram token (optional)` line is empty.

Cause: `TELEGRAM_BOT_TOKEN` is not set.

Fix: message [@BotFather](https://t.me/BotFather), create a bot, and put the token in `.env` as
`TELEGRAM_BOT_TOKEN`. You only need this to run the bot; the CLI works without it.

## Dashboard

### Dashboard not reachable from another device

The dashboard works on the host but not from your phone or another machine.

Cause: it binds localhost (`127.0.0.1`) by default, so it is reachable only from the host. This is
the secure default.

Fix: do not open a raw port. Put it behind an HTTPS tunnel (for example a Cloudflare Tunnel), set
`DASHBOARD_TOKEN` so the URL requires `?token=...`, and set `WEBAPP_URL` to enable the `/dashboard`
Mini App button. See [DEPLOY.md](DEPLOY.md#optional-exposing-the-mealie-pwa-or-the-dashboard).
