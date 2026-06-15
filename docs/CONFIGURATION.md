# Configuration

This is the complete settings reference for Grand Log. Every setting is read from the environment, normally through a `.env` file. Copy `reel-pipeline/.env.example` to `reel-pipeline/.env`, fill in the values, then run `python -m pipeline.doctor` to confirm everything is in place.

Grand Log is alpha. Pick the provider whose key you already have, point a few variables at it, and you have a working brain.

## Instagram cookies

Instagram's login wall blocks downloads, so a cookie from a throwaway account is needed to fetch a reel. The default path works on Windows: export a Netscape-format `cookies.txt` and drop it at `work/cookies.txt`. Grand Log auto-detects it, and a `cookies.txt` takes precedence over the browser-cookie path, which sidesteps the Windows DPAPI browser-cookie decrypt failure. Point `YTDLP_COOKIES_FILE` elsewhere only if your file lives outside `work/`.

To pull cookies straight from a logged-in browser profile instead, override with `YTDLP_COOKIES_BROWSER` (for example `chrome`). Note this path is broken on Windows because of DPAPI, so prefer `cookies.txt` there.

| Setting | Default | Notes |
| --- | --- | --- |
| `YTDLP_COOKIES_FILE` | (empty) | Path to a Netscape `cookies.txt`. `work/cookies.txt` is auto-detected; set this only to point elsewhere. Takes precedence over `YTDLP_COOKIES_BROWSER`. |
| `YTDLP_COOKIES_BROWSER` | (empty) | Browser profile to pull cookies from (for example `chrome`). Broken on Windows (DPAPI); use `cookies.txt` there. |

## Capture mode

`CAPTURE_MODE` decides how much of a reel Grand Log reads.

- `auto` (default): read the caption first with no download. Download the video and run Whisper only when the caption alone is too thin to trust (for a recipe that means missing ingredients or instructions, flagged missing quantities, or low confidence). This is the fast, cheap default, and it skips Whisper entirely for reels whose value is in the caption.
- `caption`: never download the video. Fastest and lightest, but it misses reels where the recipe is only spoken in the audio or only shown on screen. The CLI flag `--no-video` sets this for a single run.
- `full`: always download and transcribe, then run the on-screen vision pass when a quantity is missing. Highest fidelity, heaviest.

```bash
CAPTURE_MODE=auto
```

### Keep the downloaded media

`KEEP_MEDIA` defaults to `true`, so the downloaded video, sampled frames, and thumbnail stay in your `WORKDIR` as a local archive after extraction. Set it `false` to delete them once extraction finishes and reclaim disk.

```bash
KEEP_MEDIA=true
```

## The brain

The brain makes one schema-locked extraction call against whatever LLM you point it at. You pick one provider with `BRAIN_PROVIDER` (`gemini`, `openai`, or `anthropic`) and supply that provider's key. The other provider settings are ignored.

```bash
# pick ONE provider and bring your own key
BRAIN_PROVIDER=gemini
```

### gemini

The free starting point. Gemini's free tier covers both the text extraction and the on-screen vision pass from a single key, which is why it is the default.

| Setting | Default | Notes |
| --- | --- | --- |
| `GEMINI_API_KEY` | (empty) | Get a free key at [aistudio.google.com](https://aistudio.google.com). |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Does text and vision from the one key. |

```bash
BRAIN_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.5-flash
```

### openai (any OpenAI-compatible endpoint)

The `openai` provider talks to any OpenAI-compatible `/chat/completions` endpoint. That includes OpenAI itself, OpenRouter, Groq, and a local Ollama. You set three values: the key, the base URL, and the model. A key is required only when the base URL points at OpenAI itself (`api.openai.com`); a local Ollama needs no key.

| Endpoint | `OPENAI_BASE_URL` | `OPENAI_MODEL` | Key needed |
| --- | --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` | Yes |
| OpenRouter | `https://openrouter.ai/api/v1` | `google/gemini-2.5-flash` | Yes |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | Yes |
| Ollama (local) | `http://localhost:11434/v1` | `llama3.1` | No |

```bash
BRAIN_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

| Setting | Default | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | (empty) | Required for OpenAI; optional for endpoints that do not check it, such as a local Ollama. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | The OpenAI-compatible endpoint. A trailing slash is trimmed. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Any model the endpoint serves. |

### anthropic

Uses the official `anthropic` SDK, which ships in `requirements.txt`. Haiku is the cheapest reliable extraction model. Move up to Sonnet or Opus for harder reels where the text is thin and most of the detail is on screen.

| Setting | Default | Notes |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | (empty) | Get a key at [console.anthropic.com](https://console.anthropic.com). |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Cheapest reliable extraction model; set Sonnet or Opus for harder reels. |

```bash
BRAIN_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-haiku-4-5
```

If the `anthropic` SDK is not installed, install it with `pip install anthropic`. The doctor checks for both the key and the SDK when `BRAIN_PROVIDER=anthropic`.

## Which model should I pick

Pricing changes often, so this table is by budget and intent, not by price. Check each provider's current pricing page before you commit.

| Budget | Pick | How to set it |
| --- | --- | --- |
| Free | Gemini Flash free tier, or Groq's free Llama | `BRAIN_PROVIDER=gemini` with `GEMINI_MODEL=gemini-2.5-flash`, or `BRAIN_PROVIDER=openai` with the Groq base URL and `llama-3.3-70b-versatile` |
| Pennies and reliable | Claude Haiku 4.5, or a small OpenAI model | `BRAIN_PROVIDER=anthropic` with `ANTHROPIC_MODEL=claude-haiku-4-5`, or `BRAIN_PROVIDER=openai` with `OPENAI_MODEL=gpt-4o-mini` |
| Highest fidelity for hard reels | Claude Sonnet 4.6 or Opus 4.8, or a large GPT | `BRAIN_PROVIDER=anthropic` with `ANTHROPIC_MODEL=claude-sonnet-4-6` or `claude-opus-4-8`, or `BRAIN_PROVIDER=openai` with a large GPT model |

Current Anthropic model ids you can name: `claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-opus-4-8`. For live pricing, see each provider:

- Gemini: [aistudio.google.com](https://aistudio.google.com)
- OpenAI: [openai.com/api](https://openai.com/api)
- Groq: [groq.com](https://groq.com)
- Anthropic: [console.anthropic.com](https://console.anthropic.com)

The live extraction path is not benchmarked, so treat these as starting points and try a few reels on your own content before deciding.

## How quality stays high on any model

Two mechanisms keep a small or free model honest.

### Validate and repair

After the model returns its JSON, the brain checks it against the schema before trusting it. The check is cheap and concrete: every required field must be present and non-empty, and any field with a fixed set of allowed values (an enum) must hold one of those values. If the JSON passes, it is used as is.

If it fails, the brain runs one repair pass. It sends the model back the same prompt plus the exact list of problems it found (for example, "missing required field 'title'", or a field set to a value that is not in the allowed list) and asks for corrected JSON that keeps every good field. The repaired result is used if it now passes. If the repair pass itself errors out, the first best-effort extraction is kept rather than lost. The result is that even a small free model lands a complete, schema-valid record.

### On-screen vision pass

Many reels put quantities and steps on screen rather than in the caption or voice-over. After the text extraction, the brain can run a vision pass over sampled frames to fill in what was only shown visually. `BRAIN_VISION` controls it:

| `BRAIN_VISION` | Behavior |
| --- | --- |
| `auto` (default) | Picks the first provider you have a key for, in the order gemini, openai, anthropic. If none has a key, vision is off. |
| `gemini` | Use Gemini for vision (needs `GEMINI_API_KEY`). |
| `openai` | Use the OpenAI-compatible endpoint for vision (needs `OPENAI_API_KEY`). |
| `anthropic` | Use Anthropic for vision (needs `ANTHROPIC_API_KEY`). |
| `none` | No vision pass; text-only extraction. |

If a named provider has no key, the vision pass falls back to off rather than erroring. If the vision pass fails at runtime, the text-only recipe is kept.

## Transcription

Grand Log transcribes the reel's audio before the brain reads it. The default just works: faster-whisper runs locally and auto-detects an NVIDIA GPU, falling back to CPU when there is none. You only touch these settings to change where or how transcription runs.

```bash
TRANSCRIBE_BACKEND=faster_whisper
WHISPER_DEVICE=auto
WHISPER_MODEL=large-v3-turbo
```

### Device and compute

With `WHISPER_DEVICE=auto` (the default), faster-whisper detects an NVIDIA GPU and runs on CUDA, which is much faster than CPU. On Windows the cuDNN and cuBLAS libraries are loaded for you. Override the choice when you want to force one path:

- `WHISPER_DEVICE=cuda` forces the GPU.
- `WHISPER_DEVICE=cpu` forces CPU, useful when the GPU is busy or the CUDA libraries are missing.

`WHISPER_COMPUTE` sets the precision. Leave it blank and Grand Log picks a sensible default per device: `int8_float16` on GPU, `int8` on CPU. Set it only to override that choice (for example `float16` or `float32`).

### Backend

`TRANSCRIBE_BACKEND` selects the engine. The default `faster_whisper` is pip-only and cross-platform, the best choice on Windows and for development. Two overrides:

- `groq`: free, fast cloud Whisper that runs off your local machine. Set `TRANSCRIBE_BACKEND=groq` and a `GROQ_API_KEY` from [console.groq.com](https://console.groq.com). `GROQ_WHISPER_MODEL` defaults to `whisper-large-v3-turbo`.
- `whisper_cpp`: a binary, best on an ARM box such as a Raspberry Pi or the Oracle free tier. Point `WHISPER_CPP_BIN` at the binary and `WHISPER_CPP_MODEL` at the model file.

| Setting | Default | Notes |
| --- | --- | --- |
| `TRANSCRIBE_BACKEND` | `faster_whisper` | `faster_whisper` (local), `groq` (free cloud), or `whisper_cpp` (ARM). |
| `WHISPER_DEVICE` | `auto` | `auto` detects an NVIDIA GPU; force with `cpu` or `cuda`. |
| `WHISPER_COMPUTE` | (empty) | Precision; blank means `int8_float16` on GPU, `int8` on CPU. |
| `WHISPER_MODEL` | `large-v3-turbo` | The faster-whisper model to load. |
| `GROQ_API_KEY` | (empty) | Key for the `groq` backend, from [console.groq.com](https://console.groq.com). |
| `GROQ_WHISPER_MODEL` | `whisper-large-v3-turbo` | Groq Whisper model, used when `TRANSCRIBE_BACKEND=groq`. |
| `WHISPER_CPP_BIN` | (empty) | Path to the `whisper.cpp` binary, used when `TRANSCRIBE_BACKEND=whisper_cpp`. |
| `WHISPER_CPP_MODEL` | (empty) | Path to the `whisper.cpp` model file, used when `TRANSCRIBE_BACKEND=whisper_cpp`. |

## Destination (Mealie)

Recipes are written to a [Mealie](https://mealie.io) cookbook.

| Setting | Default | Notes |
| --- | --- | --- |
| `MEALIE_URL` | (empty) | Your Mealie base URL. A trailing slash is trimmed. |
| `MEALIE_TOKEN` | (empty) | A Mealie API token. |

Leaving `MEALIE_URL` empty (or using `--dry-run`) skips Mealie and writes recipes to a local cookbook instead: `work/recipes.json` (the full list) and `work/recipes.csv` (a summary). Recipes accumulate, so nothing is lost; this is the zero-setup default while you are trying things out. The doctor pings Mealie only if `MEALIE_URL` is set, and treats it as advisory.

```bash
MEALIE_URL=https://mealie.example.com
MEALIE_TOKEN=your-token-here
```

## Routing

A saved reel carries the name of the Instagram Collection it was saved to. Routing maps that Collection name to one of three buckets:

| Bucket key | Crew name | What goes here |
| --- | --- | --- |
| `recipe` | Baratie | Cooking reels; routed to Mealie. |
| `place` | Log Pose | Places to visit; routed to map pins. |
| `home` | Going Merry | Home and decor ideas; routed to the ideas vault. |

A Collection name routes to a bucket if it contains any of that bucket's keywords. The defaults are:

| Bucket | Default keywords |
| --- | --- |
| `place` | travel, trip, place, city, vacation, holiday, destination, explore, itinerary, wanderlust, sightseeing, tour |
| `home` | home, decor, furnitur, house, interior, apartment, build, room |
| `recipe` | recipe, food, cook, meal, kitchen, baking, eat |

Buckets are checked in the order `place`, `home`, `recipe`. Anything that matches no keyword falls back to `recipe`.

### Override the keywords

You can change the keyword lists without touching code by dropping a `routes.json` in your `WORKDIR` (which defaults to `./work`). A starter file ships at `reel-pipeline/examples/routes.json`. Copy it to `work/routes.json` and edit it.

```bash
cp reel-pipeline/examples/routes.json work/routes.json
```

The file maps each bucket to its keyword list. The shipped example:

```json
{
  "place": ["travel", "trip", "japan", "city", "vacation", "itinerary"],
  "home": ["home", "decor", "furniture", "interior", "apartment"],
  "recipe": ["recipe", "food", "cook", "meal", "baking"]
}
```

Any bucket you list replaces that bucket's default keyword list. A bucket you leave out keeps its defaults.

## Worker

The worker drains the SQLite job queue. The default handles a flaky network for you: a transient Instagram or network blip requeues the reel with exponential backoff instead of dropping it, and a job is dead-lettered only after `WORKER_MAX_ATTEMPTS` tries.

| Setting | Default | Notes |
| --- | --- | --- |
| `WORKER_MAX_ATTEMPTS` | `3` | Tries before a job is dead-lettered. Raise it for a flakier connection; lower it to fail fast. |

```bash
WORKER_MAX_ATTEMPTS=3
```

## Security

Grand Log ships locked down. These settings are how it stays that way. See [SECURITY.md](../SECURITY.md) for the full hardening checklist.

### Bot access control

The Telegram bot is gated to its owner so a stranger who finds it cannot spend your API budget.

| Setting | Default | Notes |
| --- | --- | --- |
| `ALLOWED_CHAT_IDS` | (empty) | Comma- or space-separated Telegram chat ids allowed to drive the bot. With none set and `ALLOW_ALL_CHATS` off, the bot replies with your chat id and refuses to process anything until you add it. Message the bot once to learn your id, then paste it here. |
| `ALLOW_ALL_CHATS` | `false` | Set `true` only if you knowingly want the bot open to anyone. |

### Download allow-list (SSRF guard)

Only allow-listed hosts are ever downloaded. A crafted link to an internal address or a `file://` target is refused at both the bot and the downloader.

| Setting | Default | Notes |
| --- | --- | --- |
| `ALLOWED_HOSTS` | (empty) | Comma- or space-separated hosts that a reel may come from. Empty falls back to the safe default list. A host matches if it equals an allowed host or is a subdomain of one. |

When `ALLOWED_HOSTS` is empty, the default list is: `instagram.com`, `tiktok.com`, `youtube.com`, `youtu.be`, `facebook.com`, `fb.watch`, `pinterest.com`, `pin.it`.

### Dashboard

The tile dashboard (`python -m pipeline.web`) binds localhost by default. Expose it only through a tunnel, and gate it with a token when you do.

| Setting | Default | Notes |
| --- | --- | --- |
| `DASHBOARD_HOST` | `127.0.0.1` | Bind address. The localhost default keeps the dashboard private. Change it only behind a tunnel. |
| `DASHBOARD_PORT` | `8080` | Bind port. |
| `DASHBOARD_TOKEN` | (empty) | Optional `?token=...` gate. Set it when you expose the dashboard through a tunnel. |
| `WEBAPP_URL` | (empty) | The public https URL of the dashboard. Setting it enables the `/dashboard` Mini App button in the bot. |

Run `python -m pipeline.doctor` to confirm the access-control and brain settings are in place before you go live.

## Full environment-variable reference

Every variable, its meaning, and its default. Defaults are taken from `pipeline/config.py` and `.env.example`.

| Variable | Meaning | Default |
| --- | --- | --- |
| `WORKDIR` | Working directory for downloads, the store, the queue, and `routes.json`. | `./work` |
| `FFMPEG` | ffmpeg command or path. | `ffmpeg` |
| `YTDLP_COOKIES_FILE` | Path to a Netscape `cookies.txt`. `work/cookies.txt` is auto-detected; takes precedence over the browser-cookie path. Use a throwaway Instagram account. | (empty) |
| `YTDLP_COOKIES_BROWSER` | Browser to pull Instagram login cookies from (for example `chrome`). Broken on Windows (DPAPI); use `cookies.txt` there. | (empty) |
| `CAPTURE_MODE` | How much of the reel to read: `auto` (caption first, video only if thin), `caption` (never download), or `full` (always). | `auto` |
| `KEEP_MEDIA` | Keep the downloaded video, frames, and thumbnail as a local archive; `false` deletes them after extraction. | `true` |
| `TRANSCRIBE_BACKEND` | Transcription backend: `faster_whisper` (local), `groq` (free cloud), or `whisper_cpp` (ARM). | `faster_whisper` |
| `WHISPER_DEVICE` | faster-whisper device: `auto` detects an NVIDIA GPU; force with `cpu` or `cuda`. | `auto` |
| `WHISPER_COMPUTE` | faster-whisper precision; blank means `int8_float16` on GPU, `int8` on CPU. | (empty) |
| `WHISPER_MODEL` | faster-whisper model to load. | `large-v3-turbo` |
| `GROQ_API_KEY` | Key for the `groq` backend, from console.groq.com. | (empty) |
| `GROQ_WHISPER_MODEL` | Groq Whisper model (groq backend). | `whisper-large-v3-turbo` |
| `WHISPER_CPP_BIN` | Path to the `whisper.cpp` binary (whisper_cpp backend). | (empty) |
| `WHISPER_CPP_MODEL` | Path to the `whisper.cpp` model file (whisper_cpp backend). | (empty) |
| `BRAIN_PROVIDER` | Text extraction provider: `gemini`, `openai`, or `anthropic`. | `gemini` |
| `BRAIN_VISION` | On-screen vision pass: `auto`, `gemini`, `openai`, `anthropic`, or `none`. | `auto` |
| `GEMINI_API_KEY` | Gemini key from aistudio.google.com. | (empty) |
| `GEMINI_MODEL` | Gemini model (text and vision). | `gemini-2.5-flash` |
| `OPENAI_API_KEY` | Key for the OpenAI-compatible endpoint; not needed for endpoints that do not check it (such as local Ollama). | (empty) |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint base URL; trailing slash trimmed. | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Model served by the endpoint. | `gpt-4o-mini` |
| `ANTHROPIC_API_KEY` | Anthropic key from console.anthropic.com. | (empty) |
| `ANTHROPIC_MODEL` | Anthropic model. | `claude-haiku-4-5` |
| `MEALIE_URL` | Mealie base URL; trailing slash trimmed. Empty forces dry-run. | (empty) |
| `MEALIE_TOKEN` | Mealie API token. | (empty) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather; needed to run the bot. | (empty) |
| `WORKER_MAX_ATTEMPTS` | Worker retries before a job is dead-lettered, with exponential backoff. | `3` |
| `ALLOWED_CHAT_IDS` | Telegram chat ids allowed to drive the bot (comma- or space-separated). | (empty) |
| `ALLOW_ALL_CHATS` | Open the bot to any chat. | `false` |
| `ALLOWED_HOSTS` | Hosts a reel may be downloaded from (comma- or space-separated). Empty uses the default list. | (empty) |
| `WEBAPP_URL` | Public https URL of the dashboard; enables the `/dashboard` Mini App button. | (empty) |
| `DASHBOARD_HOST` | Dashboard bind address. | `127.0.0.1` |
| `DASHBOARD_PORT` | Dashboard bind port. | `8080` |
| `DASHBOARD_TOKEN` | Optional `?token=...` gate for the dashboard. | (empty) |
