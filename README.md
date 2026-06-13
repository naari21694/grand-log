<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a2980,100:26d0ce&height=210&section=header&text=Grand%20Log&fontSize=82&fontColor=ffffff&animation=fadeIn&fontAlignY=38" width="100%" alt="Grand Log"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3500&pause=800&center=true&width=720&color=26D0CE&lines=Share+a+reel.+Forget+it.;Grand+Log+files+the+treasure.;Recipes+become+a+cookbook.;Places+become+your+map.;Ideas+become+a+vault.)](https://github.com/naari21694/grand-log)

**Every reel you save is an island you meant to visit. Grand Log is your Log Pose. It records the treasure and points you back to it.**

![license](https://img.shields.io/badge/license-AGPL--3.0-blue?style=flat-square)
![commercial](https://img.shields.io/badge/commercial%20use-license%20required-orange?style=flat-square)
![status](https://img.shields.io/badge/status-alpha-yellow?style=flat-square)
![python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![code style: ruff](https://img.shields.io/badge/style-ruff-D7FF64?style=flat-square)
![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-ff69b4?style=flat-square)](CODE_OF_CONDUCT.md)

</div>

---

Grand Log turns the Instagram reels you save and forget into organized, permanent, usable knowledge. Share a reel, and a small crew of tools pulls out the value and files it where it belongs: a recipe you can actually cook, a place you can actually navigate to, an idea for the home you are actually building. Self-hosted, free, privacy-first, and designed to run on any OS and be triggered from any phone.

## ⚓ The problem

You save hundreds of reels into a folder you never reopen. Saving is easy. Pulling out the value and filing it is the hard part nobody does. Grand Log is that missing pipeline.

## 🧭 How it works

```mermaid
flowchart LR
    A([📱 Share a reel]) --> B[🐌 Den Den Mushi<br/>Telegram bot]
    B --> C[grab, transcribe,<br/>read on-screen text]
    C --> D[🧠 Brain<br/>extract and structure]
    D --> E{route}
    E --> F[🍳 Baratie<br/>cookbook]
    E --> G[🗾 Log Pose<br/>map and sheet]
    E --> H[🏠 Going Merry<br/>vault]
```

## 🐉 The crew

| | Tool | What it does | Status |
|---|---|---|---|
| 🍳 | **Baratie** | Recipes into a Mealie cookbook with exact measurements, auto-scaled for 1, 2, 4, 6, 10 people | building |
| 🗾 | **Log Pose** | Places into Google Maps pins plus a region-grouped sheet | planned |
| 🏠 | **Going Merry** | Home and build-together ideas into an organized vault | planned |
| 🐌 | **Den Den Mushi** | The Telegram bot you share reels to (any phone, zero install) | planned |

## 🍳 Baratie, the recipe engine (built)

- Exact ingredients and measurements from the caption, the audio, and the on-screen text. The vision pass reads quantities that are shown but never said.
- Canonical grams plus dual units, per-serving nutrition, tags, and confidence flags.
- Precision scaling: linear for bulk, plus the non-linear notes a slider cannot compute (salt, spice, leavening, cook time, pan size).
- Multilingual: English, Japanese, Hindi, and more.
- Swappable adapters: brain (`claude -p` or Gemini), transcriber (faster-whisper or whisper.cpp), destination.

The app lives in [`reel-pipeline/`](reel-pipeline/). See its [README](reel-pipeline/README.md) to run it.

## 🚀 Quick start

```bash
cd reel-pipeline
python -m venv .venv && . .venv/bin/activate      # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt                    # plus install ffmpeg
cp .env.example .env
python -m pipeline.process "https://www.instagram.com/reel/XXXX/" --dry-run
```

This writes `work/last_recipe.json`, the full structured recipe. Add a Gemini key to read on-screen quantities. Add `MEALIE_URL` and `MEALIE_TOKEN`, drop `--dry-run`, and it lands in a real cookbook.

<details>
<summary>📦 <b>Install on any OS, trigger from any phone, upgrade in one command</b></summary>

<br>

- **Any OS.** A multi-arch Docker image runs identically on Linux, macOS, Windows, and Raspberry Pi. The CLI image works today (`docker run grand-log "<reel>" --dry-run`). The one-command `docker compose up -d` service ships with Den Den Mushi.
- **Any phone.** The trigger is a Telegram bot. Nothing to install, identical on iOS, Android, and web. Your phone never runs the heavy work.
- **One-click cloud.** Deploy buttons for Railway, Render, and Fly are on the roadmap.
- **One-command upgrade.** `docker compose pull && docker compose up -d`, or automatic with Watchtower.

</details>

## 🔐 Security and privacy

- No telemetry. No analytics. It never phones home. See [PRIVACY.md](PRIVACY.md).
- Everything runs on your infrastructure with your keys. Secrets live in a git-ignored `.env`, never in the repo.
- Supply-chain hardened: CodeQL scanning, OpenSSF Scorecard, Dependabot, signed releases, least-privilege CI. See [SECURITY.md](SECURITY.md).

## 🧱 Design philosophy

- **Free-first.** $0 wherever possible: free-tier cloud, your own LLM credits, OSS everywhere.
- **Lean.** If 10 lines do the job as well as 200, write 10.
- **Swappable.** Every stage is an adapter. Change vendors with one env var.
- **Capture must end in action.** A recipe you cook, a pin you follow, a home you build. Never a prettier hoard.

## 🧭 Prior art and honest positioning

Grand Log is not a new idea, and pretending otherwise would be dishonest. Reel-to-recipe, saved-posts-to-map, and save-everything-to-AI-vault all already exist, as SaaS (ReciMe, Triply, Preplo) and as open source. The closest cousins: [`pickeld/social_recipes`](https://github.com/pickeld/social_recipes), [`Peter-SB/n8n-ai-instagram-scraper`](https://github.com/Peter-SB/n8n-ai-instagram-scraper), and [Karakeep](https://github.com/karakeep-app/karakeep). What Grand Log adds is the assembly: one self-hosted pipeline on your own LLM credits, fanning out to purpose-built destinations, with disciplined recipe scaling, plus a backfill that re-files your whole Instagram history using your saved Collection names as the router. That last mechanic is the one we have not found anywhere else.

## 🙏 Standing on giants

All invoked as separate tools, never bundled or modified:
[yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense), [gallery-dl](https://github.com/mikf/gallery-dl) (GPL-2.0), [FFmpeg](https://ffmpeg.org) (LGPL/GPL), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [whisper.cpp](https://github.com/ggml-org/whisper.cpp), [OpenAI Whisper](https://github.com/openai/whisper) (MIT), [Mealie](https://github.com/mealie-recipes/mealie), [Tandoor](https://github.com/TandoorRecipes/recipes) (AGPL), [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) (LGPL), Claude, and Gemini.

## 🤝 Contributing

Grand Log wants a real crew. Anyone can contribute via fork and pull request. Trusted contributors climb a transparent, rules-based ladder (Contributor, Triager, Reviewer, Maintainer) with measurable promotion criteria. See [GOVERNANCE.md](GOVERNANCE.md) and [CONTRIBUTING.md](CONTRIBUTING.md). Be kind: [Code of Conduct](CODE_OF_CONDUCT.md).

## 🗓️ Roadmap

- [x] **Baratie** core pipeline (single-reel, dry-run testable)
- [ ] **Den Den Mushi**: Telegram bot plus queue (share and forget), plus Docker compose for any-OS install
- [ ] Backlog backfill from your Instagram data export (saved Collections become routes)
- [ ] **Log Pose** and **Going Merry**
- [ ] Auto-router (one share, zero taps), resurfacing reminders, more platforms (TikTok, Shorts)

## 📜 License

Open source under [AGPL-3.0](LICENSE): free to use, modify, self-host, and build on, forever, as long as your version stays open too. Building a commercial or closed-source product on it needs a separate commercial license, see [LICENSING.md](LICENSING.md). Dual-licensing keeps Grand Log free and community-driven while ensuring anyone who profits from it gives back.

> "Grand Log" is the brand. The crew (Baratie, Log Pose, Den Den Mushi, Going Merry) are an affectionate fan homage to One Piece (© Oda, Shueisha, Toei). They are codenames, not trademark claims.

---

<div align="center">

### Contributors
<a href="https://github.com/naari21694/grand-log/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=naari21694/grand-log" alt="contributors"/>
</a>

### Star history
[![Star History Chart](https://api.star-history.com/svg?repos=naari21694/grand-log&type=Date)](https://star-history.com/#naari21694/grand-log&Date)

<br>

**Free to use. Free to build on. Open forever. Profit from it, give back.** 🏴‍☠️

*The One Piece was the meals we cooked and the homes we built along the way.*

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:26d0ce,100:1a2980&height=120&section=footer" width="100%" alt=""/>

</div>
