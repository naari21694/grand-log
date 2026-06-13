<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a2980,100:26d0ce&height=210&section=header&text=Grand%20Log&fontSize=82&fontColor=ffffff&animation=fadeIn&fontAlignY=38" width="100%" alt="Grand Log"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3500&pause=800&center=true&width=720&color=26D0CE&lines=Share+a+reel.+Forget+it.;Grand+Log+files+the+treasure.;Recipes+%E2%86%92+a+cookbook.;Places+%E2%86%92+your+map.;Ideas+%E2%86%92+a+vault.)](https://github.com/naari21694/grand-log)

**Every reel you save is an island you meant to visit. Grand Log is your Log Pose — it records the treasure and points you back to it.**

![license](https://img.shields.io/badge/license-AGPL--3.0-blue?style=flat-square)
![commercial](https://img.shields.io/badge/commercial%20use-license%20required-orange?style=flat-square)
![status](https://img.shields.io/badge/status-alpha-yellow?style=flat-square)
![python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![code style: ruff](https://img.shields.io/badge/style-ruff-D7FF64?style=flat-square)
![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-ff69b4?style=flat-square)](CODE_OF_CONDUCT.md)

</div>

---

Grand Log turns the Instagram reels you save and forget into **organized, permanent, _actionable_** knowledge. Share a reel; a small crew of tools extracts the value and files it where it belongs — a recipe you can actually cook, a place you can actually navigate to, an idea for the home you're actually building. **Self-hosted, free, privacy-first, and designed to run on any OS and be triggered from any phone.**

## ⚓ The problem

You save hundreds of reels into a folder you never reopen. Saving is easy. **Extracting the value and filing it** is the hard part nobody does. Grand Log is that missing pipeline.

## 🧭 How it works

```mermaid
flowchart LR
    A([📱 Share a reel]) --> B[🐌 Den Den Mushi<br/>Telegram bot]
    B --> C[grab · transcribe<br/>· read on-screen text]
    C --> D[🧠 Brain<br/>extract + structure]
    D --> E{route}
    E --> F[🍳 Baratie<br/>cookbook]
    E --> G[🗾 Log Pose<br/>map + sheet]
    E --> H[🏠 Going Merry<br/>vault]
```

## 🐉 The crew

| | Tool | What it does | Status |
|---|---|---|---|
| 🍳 | **Baratie** | Recipes → a Mealie cookbook with exact measurements, auto-scaled 1/2/4/6/10 | 🔨 building |
| 🗾 | **Log Pose** | Places → Google Maps pins + a region-grouped sheet | 🗺️ planned |
| 🏠 | **Going Merry** | Home & build-together ideas → an organized vault | 🗺️ planned |
| 🐌 | **Den Den Mushi** | The Telegram bot you share reels to (any phone, zero install) | 🗺️ planned |

## 🍳 Baratie — the recipe engine (built)

- **Exact** ingredients & measurements from **caption + audio + on-screen text** (vision reads quantities shown but never said)
- Canonical **grams** + dual units · per-serving nutrition · tags · **confidence flags**
- **Precision scaling** — linear for bulk *plus* the non-linear notes a slider can't compute (salt/spice/leavening, cook time, pan size)
- **Multilingual** (English / 日本語 / हिन्दी / …)
- Fully **swappable adapters**: brain (`claude -p` ↔ Gemini) · transcriber (faster-whisper ↔ whisper.cpp) · destination

The app lives in [`reel-pipeline/`](reel-pipeline/) — see its [README](reel-pipeline/README.md) to run it.

## 🚀 Quick start

```bash
cd reel-pipeline
python -m venv .venv && . .venv/bin/activate      # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt                    # + install ffmpeg
cp .env.example .env
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
```

<details>
<summary>📦 <b>Install on any OS · trigger from any phone · upgrade in one command</b></summary>

<br>

- **Any OS** — a multi-arch Docker image runs identically on Linux/macOS/Windows/Raspberry Pi. The CLI image works today (`docker run grand-log "<reel>" --dry-run`); the one-command `docker compose up -d` service ships with Den Den Mushi.
- **Any phone** — the trigger is a **Telegram bot**: nothing to install, identical on iOS/Android/web. Your phone never runs the heavy lifting.
- **One-click cloud** — deploy buttons for Railway / Render / Fly are on the roadmap so you don't even need your own box.
- **One-command upgrade** — `docker compose pull && docker compose up -d` (or fully automatic via Watchtower).

</details>

## 🔐 Security & privacy

- **No telemetry. No analytics. It never phones home.** See [PRIVACY.md](PRIVACY.md).
- Everything runs on **your** infrastructure with **your** keys; secrets live in a git-ignored `.env`, never in the repo.
- Supply-chain hardened: CodeQL scanning, OpenSSF Scorecard, Dependabot, signed releases, least-privilege CI. See [SECURITY.md](SECURITY.md).

## 🧱 Design philosophy

- **Free-first** — $0 wherever possible (free-tier cloud, your own LLM credits, OSS everywhere)
- **Lean** — if 10 lines do it as well as 200, write 10
- **Swappable** — every stage is an adapter; change vendors with one env var
- **Capture must end in action** — a recipe you cook, a pin you follow, a home you build — never a prettier hoard

## 🧭 Prior art & honest positioning

Grand Log isn't a new idea, and pretending otherwise would be dishonest. Reel → recipe, saved-posts → map, and save-everything → AI vault all already exist — as SaaS (ReciMe, Triply, Preplo…) and open source. Closest cousins: [`pickeld/social_recipes`](https://github.com/pickeld/social_recipes), [`Peter-SB/n8n-ai-instagram-scraper`](https://github.com/Peter-SB/n8n-ai-instagram-scraper), [Karakeep](https://github.com/karakeep-app/karakeep). **What Grand Log adds** is the *assembly*: one self-hosted pipeline on **your own** LLM credits, fanning out to **purpose-built destinations** with disciplined recipe scaling, plus a **backfill that re-files your whole Instagram history using your saved Collection names as the router** — the one mechanic we haven't found elsewhere.

## 🙏 Standing on giants

All invoked as separate tools, never bundled or modified:
[yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense) · [gallery-dl](https://github.com/mikf/gallery-dl) (GPL-2.0) · [FFmpeg](https://ffmpeg.org) (LGPL/GPL) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [whisper.cpp](https://github.com/ggml-org/whisper.cpp) · [OpenAI Whisper](https://github.com/openai/whisper) (MIT) · [Mealie](https://github.com/mealie-recipes/mealie) · [Tandoor](https://github.com/TandoorRecipes/recipes) (AGPL) · [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) (LGPL) · Claude & Gemini.

## 🤝 Contributing

Grand Log wants a real crew. Anyone can contribute via fork → PR; trusted contributors climb a transparent, **rules-based ladder** (Contributor → Triager → Reviewer → Maintainer) with measurable promotion criteria — see [GOVERNANCE.md](GOVERNANCE.md) and [CONTRIBUTING.md](CONTRIBUTING.md). Be kind: [Code of Conduct](CODE_OF_CONDUCT.md).

## 🗓️ Roadmap

- [x] **Baratie** core pipeline (single-reel, dry-run testable)
- [ ] **Den Den Mushi** — Telegram bot + queue (share-and-forget) + Docker/compose for any-OS install
- [ ] Backlog backfill from your Instagram data export (saved Collections → routes)
- [ ] **Log Pose** & **Going Merry**
- [ ] Auto-router (one share, zero taps) · resurfacing reminders · more platforms (TikTok/Shorts)

## 📜 License

**Open source under [AGPL-3.0](LICENSE)** — free to use, modify, self-host, and build on, forever, as long as your version stays open too. **Building a commercial or closed-source product on it?** That needs a separate commercial license — see [LICENSING.md](LICENSING.md). Dual-licensing keeps Grand Log free and community-driven while ensuring anyone who *capitalizes* on it gives back.

> *"Grand Log" is the brand; the crew (Baratie, Log Pose, Den Den Mushi, Going Merry) are an affectionate fan homage to One Piece (© Oda / Shueisha / Toei) — codenames, not trademark claims.*

---

<div align="center">

### Contributors
<a href="https://github.com/naari21694/grand-log/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=naari21694/grand-log" alt="contributors"/>
</a>

### Star history
[![Star History Chart](https://api.star-history.com/svg?repos=naari21694/grand-log&type=Date)](https://star-history.com/#naari21694/grand-log&Date)

<br>

**Free to use. Free to build on. Open forever. Capitalize on it → give back.** 🏴‍☠️

*The One Piece was the meals we cooked and the homes we built along the way.*

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:26d0ce,100:1a2980&height=120&section=footer" width="100%" alt=""/>

</div>
