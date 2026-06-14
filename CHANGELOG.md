# Changelog

All notable changes to Grand Log are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims for
[semantic versioning](https://semver.org/spec/v2.0.0.html). Grand Log is alpha, so minor
versions may still change behavior.

## [Unreleased]

### Added
- Offline saved-export backfill: `python -m pipeline.backfill <export.json> --run` ingests your Instagram `saved_collections.json` / `saved_posts.json` straight from the captions in the export, with no Instagram fetch, no cookies, and no Whisper. Each item is auto-routed (a Collection-name keyword for free, otherwise the brain classifies once per collection); recipe, place, and home get full extraction, and everything else is indexed as a searchable `saved` item. The run is resumable (skips already-saved URLs) and throttled (`BACKFILL_SLEEP`); items with no caption or a thin extraction are flagged in `work/needs_video.jsonl` for a later video pass. `--limit` runs a safe first slice, and a no-flag run previews counts and routing.
- Dashboard: a `Saved` filter chip and icon for generically-indexed items.

### Fixed
- The backfill parser now reads the current nested Instagram export format (a list of collections with `label_values` holding the name, captions, and URLs). The previous parser matched only the older dict shape and silently fell back to a URL regex, which lost every collection's routing.

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

[0.3.0]: https://github.com/naari21694/grand-log/releases/tag/v0.3.0
