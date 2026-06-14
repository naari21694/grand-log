<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a2980,100:26d0ce&height=200&section=header&text=Grand%20Log&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=38" width="100%" alt="Grand Log"/>

### Turn the Instagram reels you save and forget into a cookbook, a map, and a vault.

Share a reel to a Telegram bot. A small crew pulls out the value and files it where you will use it: a recipe you can cook, a place on your map, an idea in your vault. Self-hosted, free, and runs on any OS, triggered from any phone.

![license](https://img.shields.io/badge/license-AGPL--3.0-blue?style=flat-square)
![status](https://img.shields.io/badge/status-alpha-yellow?style=flat-square)
[![version](https://img.shields.io/badge/version-0.2.0-blue?style=flat-square)](CHANGELOG.md)
![python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![tests](https://img.shields.io/badge/tests-73%20passing-brightgreen?style=flat-square)
![code style: ruff](https://img.shields.io/badge/style-ruff-D7FF64?style=flat-square)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-ff69b4?style=flat-square)](CODE_OF_CONDUCT.md)

**[Install](docs/INSTALL.md)  ·  [Configure](docs/CONFIGURATION.md)  ·  [Deploy](docs/DEPLOY.md)  ·  [Architecture](ARCHITECTURE.md)  ·  [Security](SECURITY.md)  ·  [Ideas](IDEAS.md)  ·  [Changelog](CHANGELOG.md)  ·  [Contribute](CONTRIBUTING.md)**

</div>

---

## The problem

You save hundreds of reels: a recipe you meant to cook, a restaurant you meant to try, a shelf you meant to build. They sit in a folder you never reopen. Saving is easy. The hard part, pulling the value out and filing it somewhere you will actually reach for, is the part nobody does. Grand Log is that missing step.

## How it works

```mermaid
flowchart LR
    A([Share a reel]) --> B[Den Den Mushi<br/>Telegram bot]
    B --> C[read caption,<br/>and video if needed]
    C --> D[Brain<br/>extract and structure]
    D --> E{route}
    E --> F[Baratie<br/>cookbook]
    E --> G[Log Pose<br/>map and sheet]
    E --> H[Going Merry<br/>vault]
```

One share, zero typing. The phone never does the heavy work. Everything runs on your own box, with your own keys, and nothing phones home.

## The crew

| | Tool | What it does | Status |
|---|---|---|---|
| 🍳 | **Baratie** | Recipes into a Mealie cookbook, with exact measurements auto-scaled for 1, 2, 4, 6, 10 people | built |
| 🗾 | **Log Pose** | Places into map pins (GeoJSON) plus a region-grouped sheet (CSV) | built |
| 🏠 | **Going Merry** | Home and build-together ideas into a vault (CSV and JSON) | built |
| 🐌 | **Den Den Mushi** | The Telegram bot you share reels to. Any phone, zero install, identical on iOS and Android | built |

Crew names are an affectionate One Piece homage. The bucket keys underneath are plain: `recipe`, `place`, `home`.

## What it supports right now

- **AI brains: any key you already have**, through three adapters. Gemini (free tier), any OpenAI-compatible API (OpenAI, OpenRouter, Groq, Together, DeepSeek, or local Ollama), and Anthropic. A validate-and-repair step keeps the output schema-valid even on a small free model.
- **Three capture modes** (`CAPTURE_MODE`): `auto` reads the caption first and only downloads the video and runs Whisper when the caption is thin; `caption` never downloads; `full` always does.
- **Destinations:** recipes to Mealie (in dry-run, the structured recipe is written to a file), places to GeoJSON plus CSV for Google My Maps and a sheet, home items to CSV plus JSON for a sheet or Notion.
- **Multilingual** transcription (auto-detected: English, Japanese, Hindi, and more).
- **Any OS** via Python or a Docker image you build, and **any phone** via the Telegram bot.
- **Source:** Instagram reels and posts today. The downloader (yt-dlp) and the host allow-list already cover TikTok and YouTube, not yet tested end to end.
- **Project:** 20 small Python modules, 73 passing tests, ruff-clean, v0.2.0, AGPL-3.0.

## Baratie: a recipe engine, not a bookmark

- **Exact measurements** from the caption, the audio, and the on-screen text. The vision pass reads quantities that flash on screen and are never spoken.
- **Real scaling.** Ingredients land as structured `quantity + unit + food`, so Mealie's slider renders any serving count, and Baratie adds the part a slider cannot: the non-linear notes for salt, spice, leavening, cook time, and pan size when you change the batch.
- **Canonical grams plus dual units, per-serving nutrition, tags, and a confidence flag** on anything the reel left ambiguous.

## Quick start

```bash
cd reel-pipeline
python -m venv .venv && . .venv/bin/activate      # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt                    # plus install ffmpeg
cp .env.example .env                               # add a free Gemini key (aistudio.google.com)
python -m pipeline.doctor                          # checks ffmpeg, your key, and access control
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --no-video --dry-run
```

That extracts from the caption alone (no download, no Whisper) and writes the structured result to `work/`. Drop `--no-video` to let it read the video when the caption is thin. Add `MEALIE_URL` and `MEALIE_TOKEN` and drop `--dry-run` to land recipes in a real cookbook. The step-by-step guide is [docs/INSTALL.md](docs/INSTALL.md); every setting is in [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Requirements and where to get them

| Need | What it is | Where to get it | Required? |
|---|---|---|---|
| Python 3.10+ | the runtime | [python.org](https://www.python.org/downloads/) | yes |
| ffmpeg | audio and frame extraction | [ffmpeg.org](https://ffmpeg.org/download.html) (Windows: `winget install Gyan.FFmpeg`) | for `auto`/`full` mode; not for caption-only |
| An AI key | the brain | [Gemini](https://aistudio.google.com/) (free), or [OpenAI](https://platform.openai.com/), [OpenRouter](https://openrouter.ai/), [Groq](https://console.groq.com/), [Anthropic](https://console.anthropic.com/), or local [Ollama](https://ollama.com/) | yes, or run Ollama for none |
| Telegram bot token | the share front door | [@BotFather](https://t.me/BotFather) | for the bot; not for the CLI |
| Mealie | the recipe cookbook | [mealie-recipes/mealie](https://github.com/mealie-recipes/mealie) | optional; in dry-run the recipe is written to a file instead |
| Cloudflare Tunnel | expose Mealie and the dashboard safely | [Cloudflare Zero Trust](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) | optional |
| Instagram cookies | downloads behind the login wall | a throwaway account, exported `cookies.txt` | only if a download is blocked |

## Then it gets out of your way

Capture is one front door; what you save fans out to the tool built for it, and one hub indexes all of it.

- **A rich card the moment you share:** thumbnail, title, a one-line summary, and an Open button to the destination.
- **`/search`** across everything you ever saved.
- **`/digest`** resurfaces a few saves to revisit, because a save that never resurfaces is a save you lost.
- **A tile dashboard** of every save, in any phone browser or as a Telegram Mini App.

The design behind this is in [docs/research-oss-android-apps.md](docs/research-oss-android-apps.md).

## Yours, and only yours

- **No telemetry, no analytics, it never phones home.** See [PRIVACY.md](PRIVACY.md). You choose which AI provider sees your reels, or run Ollama so nothing leaves your machine.
- Everything runs on your infrastructure with your keys. Secrets live in a git-ignored `.env`.
- **Locked down by default:** the bot answers only your own Telegram chat, only known video hosts are downloaded (SSRF guard), and the dashboard binds to localhost. Run `python -m pipeline.doctor` to confirm. Full checklist in [SECURITY.md](SECURITY.md).
- Supply-chain workflows: CodeQL scanning, OpenSSF Scorecard, and Dependabot.

## Honest positioning

Grand Log is not the first to turn a reel into a recipe, a save into a map pin, or a post into an AI vault. Those exist, as SaaS (ReciMe, Triply, Preplo) and as open source, the closest being [`pickeld/social_recipes`](https://github.com/pickeld/social_recipes), [`Peter-SB/n8n-ai-instagram-scraper`](https://github.com/Peter-SB/n8n-ai-instagram-scraper), and [Karakeep](https://github.com/karakeep-app/karakeep). What we have not found elsewhere: one self-hosted pipeline, on your own AI credits, fanning out to purpose-built destinations, with disciplined recipe scaling and resurfacing, plus a backfill that re-files your whole Instagram history using your saved Collection names as the router.

## Status and ideas

What is built is in the table above and in the [CHANGELOG](CHANGELOG.md). What we are thinking about next (caption-first onboarding wins, a prebuilt image, auto-router, resurfacing reminders, more platforms, new buckets) lives in [IDEAS.md](IDEAS.md), kept separate so this README stays a map, not a list of promises.

## Credits

Grand Log is assembly, not invention. It stands on these projects, each invoked as a separate tool, never bundled or modified:

- **Download:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense), [gallery-dl](https://github.com/mikf/gallery-dl) (GPL-2.0)
- **Media and audio:** [FFmpeg](https://ffmpeg.org) (LGPL/GPL), [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT), [whisper.cpp](https://github.com/ggml-org/whisper.cpp) (MIT), [OpenAI Whisper](https://github.com/openai/whisper) (MIT)
- **Bot and runtime:** [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) (LGPL-3.0), [requests](https://github.com/psf/requests) (Apache-2.0), [python-dotenv](https://github.com/theskumar/python-dotenv) (BSD-3), [anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) (MIT)
- **Destinations:** [Mealie](https://github.com/mealie-recipes/mealie) (AGPL-3.0), [Tandoor](https://github.com/TandoorRecipes/recipes) (AGPL-3.0)
- **AI providers:** Google Gemini, OpenAI, Anthropic, and OpenAI-compatible hosts (OpenRouter, Groq, Together) and local Ollama, used with your own keys.
- **Geocoding:** [OpenStreetMap Nominatim](https://nominatim.org/).
- **README visuals:** [capsule-render](https://github.com/kyechan99/capsule-render), [contrib.rocks](https://contrib.rocks), [star-history](https://star-history.com).

Prior art that shaped the honest positioning is credited above. The crew names are a fan homage to One Piece (© Oda, Shueisha, Toei), used as codenames, not trademark claims.

## Contributing

Anyone can contribute by fork and pull request. Trusted contributors climb a transparent, rules-based ladder (Contributor, Triager, Reviewer, Maintainer). Start with [ARCHITECTURE.md](ARCHITECTURE.md), then [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md). Be kind: [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Open source under [AGPL-3.0](LICENSE): free to use, modify, self-host, and build on, as long as your version stays open too. A commercial or closed-source product on top needs a separate commercial license, see [LICENSING.md](LICENSING.md).

---

<div align="center">

### Contributors
<a href="https://github.com/naari21694/grand-log/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=naari21694/grand-log" alt="contributors"/>
</a>

### Star history
[![Star History Chart](https://api.star-history.com/svg?repos=naari21694/grand-log&type=Date)](https://star-history.com/#naari21694/grand-log&Date)

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:26d0ce,100:1a2980&height=110&section=footer" width="100%" alt=""/>

</div>
