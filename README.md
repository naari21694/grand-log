<div align="center">

# 🏴‍☠️ Grand Log

**Every reel you save is an island you meant to visit.**
**Grand Log is your Log Pose — it records the treasure and points you back to it.**

![status](https://img.shields.io/badge/status-alpha-orange)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-AGPL--3.0-blue)
![commercial](https://img.shields.io/badge/commercial%20use-license%20required-orange)
![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen)

</div>

---

Grand Log turns the Instagram reels you save and forget into **organized, permanent, _actionable_** knowledge. Share a reel; a small crew of tools extracts the value and files it where it belongs — a recipe you can actually cook, a place you can actually navigate to, an idea for the home you're actually building.

## ⚓ The problem

You save hundreds of reels — recipes, restaurants, trips, home ideas — into a folder you never reopen. Saving is easy. **Extracting the value and filing it** is the hard part nobody does. Grand Log is that missing pipeline.

## 🧭 How it works

```
                    ┌─ caption (yt-dlp)
share a reel        ├─ speech  (whisper)  ─┐
   │                └─ on-screen text ─────┤
   ▼                   (ffmpeg frames)     ▼
📱 Den Den Mushi ─────────────────────▶  🧠 brain  ──▶  structured record  ──▶  route
   (Telegram bot)                       (LLM)                                    │
                                                  ┌──────────────┬───────────────┤
                                                  ▼              ▼               ▼
                                              🍳 Baratie     🗾 Log Pose     🏠 Going Merry
                                              (cookbook)     (map + sheet)   (home vault)
```

## 🐉 The crew

| | Tool | What it does | Status |
|---|---|---|---|
| 🍳 | **Baratie** | Recipes → a Mealie cookbook with exact measurements, auto-scaled for 1/2/4/6/10 | 🔨 building |
| 🗾 | **Log Pose** | Places → Google Maps pins + a region-grouped sheet | 🗺️ planned |
| 🏠 | **Going Merry** | Home & build-together ideas → an organized vault | 🗺️ planned |
| 📱 | **Den Den Mushi** | The Telegram bot you share reels to | 🗺️ planned |

## 🍳 Baratie — the recipe engine (what's built)

- **Exact** ingredients & measurements from **caption + audio + on-screen text** (vision reads quantities that are shown but never said)
- Canonical **grams** + dual units
- **God-tier scaling** — linear for bulk *plus* the non-linear notes a serving-slider can't compute: salt/spice/seasoning, leavening, cook time, pan size
- Per-serving nutrition, tags, and **confidence flags** where the source was ambiguous
- **Multilingual** — English / 日本語 / हिन्दी / …
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
→ writes the full structured recipe to `work/last_recipe.json`. Add a Gemini key to read on-screen quantities; add `MEALIE_URL`/`MEALIE_TOKEN` and drop `--dry-run` to land it in a real cookbook.

## 🧱 Design philosophy

- **Free-first** — $0 wherever possible (free-tier cloud, your existing LLM credits, OSS everywhere)
- **Lean** — if 10 lines do it as well as 200, write 10
- **Swappable** — every stage is an adapter; change vendors with one env var
- **Runs anywhere** — a $0 always-on box with a public endpoint, triggered from your phone
- **Capture must end in action** — a recipe you cook, a pin you follow, a home you build — never a prettier hoard

## 🗓️ Roadmap

- [x] **Baratie** core pipeline (single-reel, dry-run testable)
- [ ] **Den Den Mushi** — Telegram bot + queue (share-and-forget)
- [ ] Backlog backfill from your Instagram data export (saved Collections → routes)
- [ ] **Log Pose** & **Going Merry**

## ⚠️ Responsible use

Grand Log is a **personal, educational** tool. It downloads content you already have access to, for your **own offline use** — respect each platform's Terms of Service, don't redistribute downloaded media, and use a throwaway account for cookies. Downloader reliability (yt-dlp ↔ Instagram) is best-effort; platforms break it periodically.

## 🧭 Prior art & honest positioning

Grand Log isn't a new idea, and pretending otherwise would be dishonest. Reel → recipe, saved-posts → map, and save-everything → AI vault all already exist — as SaaS (ReciMe, Triply, Preplo, Nutrola…) and as open source. The closest open-source cousins:

- [`pickeld/social_recipes`](https://github.com/pickeld/social_recipes) — Whisper + vision-frame OCR + yt-dlp → Mealie/Tandoor. Nearly identical to Baratie.
- [`Peter-SB/n8n-ai-instagram-scraper`](https://github.com/Peter-SB/n8n-ai-instagram-scraper) — reel → Whisper → LLM → bucket-categorize → Sheets. The "one pipeline, many buckets" router.
- [Karakeep](https://github.com/karakeep-app/karakeep) — self-hosted, AI-tagged save-everything vault.

**What Grand Log adds** isn't a capability nobody has — it's the *assembly*: one self-hosted pipeline on **your own** LLM credits at ~zero marginal cost, fanning out to **purpose-built destinations** (Mealie, Google Maps, a vault) instead of a walled-garden app, with disciplined grams-canonical + non-linear recipe scaling, and a **backfill that re-files your whole Instagram history using your saved Collection names as the router** — the one mechanic we haven't found elsewhere.

## 🙏 Standing on giants

Grand Log is glue around extraordinary open-source work — all invoked as separate tools/services, never bundled or modified:

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense) · [gallery-dl](https://github.com/mikf/gallery-dl) (GPL-2.0) — download
- [FFmpeg](https://ffmpeg.org) (LGPL/GPL) — audio + frame extraction
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [whisper.cpp](https://github.com/ggml-org/whisper.cpp) · [OpenAI Whisper](https://github.com/openai/whisper) (all MIT) — transcription
- [Mealie](https://github.com/mealie-recipes/mealie) · [Tandoor](https://github.com/TandoorRecipes/recipes) (AGPL) — the cookbook Baratie writes to
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) (LGPL-3.0) — Den Den Mushi
- Claude (Anthropic) & Gemini (Google) — the brain

## 📜 License

Grand Log is **open source under [AGPL-3.0](LICENSE)** — free to use, modify, self-host, and build on, forever, as long as your version stays open too. The community owns the journey.

**Building a commercial or closed-source product on it?** That needs a separate **commercial license** — see [LICENSING.md](LICENSING.md). Dual-licensing keeps Grand Log free and community-driven while ensuring anyone who *capitalizes* on it gives back. Contributions are welcomed under a lightweight CLA.

> *"Grand Log" is the brand; the crew (Baratie, Log Pose, Den Den Mushi, Going Merry) are an affectionate fan homage to One Piece (© Oda / Shueisha / Toei) — codenames, not trademark claims.*

<div align="center">

**Free to use. Free to build on. Open forever. Capitalize on it → give back.** 🏴‍☠️

*The One Piece was the meals we cooked and the homes we built along the way.*

</div>
