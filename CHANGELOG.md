# Changelog

All notable changes to Grand Log are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims for
[semantic versioning](https://semver.org/spec/v2.0.0.html). Grand Log is alpha, so minor
versions may still change behavior.

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

[0.2.0]: https://github.com/naari21694/grand-log/releases/tag/v0.2.0
[0.1.0]: https://github.com/naari21694/grand-log/releases/tag/v0.1.0
