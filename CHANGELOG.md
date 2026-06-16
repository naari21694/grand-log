# Changelog

All notable changes to Grand Log are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims for
[semantic versioning](https://semver.org/spec/v2.0.0.html). Grand Log is alpha, so minor
versions may still change behavior.

## [Unreleased]

### Security
- The brain no longer puts the API key in a request URL. The Gemini call passed the key as a `?key=` query parameter, so a request error (a 503 was observed in testing) leaked the full key into the error message and logs. The key now travels in the `x-goog-api-key` header, so it can never reach a URL.

### Fixed
- Transient brain-provider errors (5xx, 429, network blips) now retry with a short backoff instead of crashing the reel. Applies to the Gemini and OpenAI text and vision calls.

## [0.4.0] - 2026-06-15

### Added
- GPU transcription: faster-whisper auto-detects an NVIDIA GPU (`WHISPER_DEVICE=auto`) and runs on CUDA, much faster than CPU, with the Windows cuDNN/cuBLAS libraries loaded automatically. Force with `WHISPER_DEVICE=cpu|cuda`.
- Groq Whisper backend (`TRANSCRIBE_BACKEND=groq`): free, fast cloud transcription that runs off the local machine.
- `cookies.txt` support: a Netscape cookies file (default `work/cookies.txt`) is auto-detected and takes precedence over browser cookies, which sidesteps the Windows DPAPI browser-cookie failure.
- Full-frame vision for every crew: the vision pass now reads all on-screen text (names, addresses, prices, dimensions, quantities, steps) for recipe, place, and home. Places and home previously read no frames at all.
- `KEEP_MEDIA` (default true): keep the downloaded video, frames, and thumbnail as a local archive; set false to delete them after extraction and save disk.
- Setup wizard: `python -m pipeline.setup` prompts for your brain provider and key, writes `.env`, and runs the doctor.
- Worker retry-with-backoff and dead-letter (`WORKER_MAX_ATTEMPTS`): a transient Instagram or network blip requeues with exponential backoff instead of dropping a reel.
- Offline saved-export backfill: `python -m pipeline.backfill <export.json> --run` ingests your Instagram `saved_collections.json` / `saved_posts.json` straight from the captions, auto-routed (a Collection-name keyword for free, otherwise the brain classifies once per collection); recipe/place/home get full extraction, everything else is indexed as a searchable `saved` item. Resumable (skips already-saved URLs), throttled (`BACKFILL_SLEEP`); thin or caption-less items are flagged in `work/needs_video.jsonl` for a later video pass. `--limit` runs a safe slice; a no-flag run previews counts and routing.
- Dashboard: a `Saved` filter chip and icon for generically-indexed items.
- Docs: a "Choose your host" matrix and a first-class personal-computer host guide (Windows/macOS/Linux), so any user finds their setup path in seconds.

### Changed
- Mode-aware doctor: ffmpeg is required only for `CAPTURE_MODE=full`; in auto and caption modes it is advisory.
- `.env.example`: browser cookies are off by default (drop a `cookies.txt` instead), and transcription auto-detects the GPU. Defaults lead, overrides are documented inline.

### Fixed
- The backfill parser now reads the current nested Instagram export format (a list of collections with `label_values` holding the name, captions, and URLs). The previous parser matched only the older dict shape and silently fell back to a URL regex, which lost every collection's routing.
- Instagram cookie loading on Windows: a `cookies.txt` file is used in preference to the browser-cookie path, which fails with a DPAPI decrypt error.

## [0.3.0] - 2026-06-14

### Added
- Local recipe cookbook: on the dry-run or no-Mealie path, recipes are appended to `work/recipes.json` (the full list) and `work/recipes.csv` (a summary), so they accumulate. Mealie stays the rich destination.
- Release automation: pushing a `v*` tag builds and pushes a multi-arch image to GHCR and creates a GitHub Release with notes and the source archives (see RELEASING.md).
- `IDEAS.md`, a tracked list of considered improvements, kept out of the README.

### Changed
- README restructured to be grounded and navigable: a "what it supports now" section, a requirements-and-where-to-get-them table, a credits section, and a docs nav. Removed the ASCII art; the test-count badge is now the live CI badge.

### Fixed
- Recipes were silently lost without Mealie: the dry-run path overwrote `work/last_recipe.json` on every run. It now also appends to the cookbook, so nothing is lost.

## [0.2.0] - 2026-06-14

### Added
- Provider-agnostic brain: one schema-locked extraction call against Gemini (free tier), any
  OpenAI-compatible endpoint (OpenAI, OpenRouter, Groq, Together, local Ollama), or Anthropic.
  A validate-and-repair loop checks required fields and enum values and runs one repair pass,
  so the output stays schema-valid even on a small free model.
- Caption-first tiered capture (`CAPTURE_MODE` = auto, caption, full). `auto` reads the caption
  with no download and no Whisper, and fetches the video and transcribes only when the caption
  is thin. `--no-video` forces caption-only for one run.
- Security defaults: the Telegram bot answers only allow-listed chats (`ALLOWED_CHAT_IDS`), only
  known video hosts are downloadable (SSRF guard), and the dashboard binds `127.0.0.1` with an
  optional token.
- `python -m pipeline.doctor` preflight check.
- Onboarding and deploy: `scripts/install.sh` and `install.ps1`, one-click templates for Railway,
  Fly, and Render, and synthetic Instagram export plus routes samples for testing backfill.
- Documentation: docs/INSTALL.md, docs/CONFIGURATION.md, docs/DEPLOY.md, and a docs index.

### Changed
- Default brain is Gemini (free tier). The agentic `claude_p` CLI path was removed.
- `places` and `home` read `WORKDIR` at call time, consistent with `process` and `frames`.

### Security
- Model output is treated as untrusted and validated against the schema; SQLite access stays
  parameterized; secrets live only in a git-ignored `.env`.

## [0.1.0] - 2026-06-13

### Added
- Baratie recipe pipeline: download, transcribe, extract, scale, and write to Mealie, with
  structured ingredients, per-serving nutrition, and non-linear scaling notes.
- Den Den Mushi Telegram bot, the resumable SQLite job queue, and the worker.
- Log Pose places (GeoJSON and CSV) and Going Merry home vault (CSV and JSON).
- Instagram backfill, the saved-items store, `/search`, `/digest`, and the tile dashboard.
- Community kit: AGPL-3.0 plus commercial dual license, CLA, governance ladder, security
  policy, issue and PR templates, and CI.

[0.4.0]: https://github.com/naari21694/grand-log/releases/tag/v0.4.0
[0.3.0]: https://github.com/naari21694/grand-log/releases/tag/v0.3.0
