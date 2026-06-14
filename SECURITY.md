# Security Policy

## Supported versions
The latest `main` is supported. This is an early-stage project, so pin a commit or tag if you need stability.

| Version | Supported |
| ------- | --------- |
| `main`  | yes |
| older   | no |

## Reporting a vulnerability
Please do not report security issues through public issues, discussions, or PRs.

Use GitHub's private [Report a vulnerability](https://github.com/naari21694/grand-log/security/advisories/new) button, or email vnarendrakumar21694@gmail.com with the subject "Grand Log security". Include impact, the affected stage (download, transcribe, brain, destination), repro steps, and the version or commit.

We aim to acknowledge within a few days, and will keep you posted through to a fix and coordinated disclosure.

## Notes
- Grand Log runs on your own infrastructure with your own keys and cookies. Keep your `.env` private (it is gitignored). See [PRIVACY.md](PRIVACY.md).
- The downloaders (yt-dlp, gallery-dl) fetch from third-party sites. Treat all downloaded content as untrusted input.
- Hardening in place: CodeQL scanning, OpenSSF Scorecard, Dependabot, secret scanning with push protection, least-privilege CI, pinned third-party actions.

## Self-hosting securely (hardening checklist)
Grand Log ships locked down by default. The controls below are how it stays that way.

- **Lock the bot to you.** Set `ALLOWED_CHAT_IDS` to your own Telegram chat id. With no id set, the bot replies with your id and refuses to process any message, so a stranger who finds the bot cannot spend your API budget. Only set `ALLOW_ALL_CHATS=true` if you knowingly want it open.
- **Download allow-list (SSRF guard).** Only the hosts in `ALLOWED_HOSTS` (default: Instagram, TikTok, YouTube, and similar) are ever downloaded. A crafted link to an internal or `file://` address is refused at both the bot and the downloader.
- **Dashboard stays private.** `python -m pipeline.web` binds `127.0.0.1` by default. Expose it only through a tunnel (Cloudflare Tunnel + Access), and set `DASHBOARD_TOKEN` so the URL needs `?token=...`.
- **Model output is untrusted.** Reel captions and transcripts can carry injection attempts. The brain only ever emits schema-validated JSON, and nothing downstream executes model text or builds SQL or shell from it (the store and queue use parameterized SQLite).
- **Secrets.** Keys live only in `.env` (gitignored). Use a throwaway Instagram account for cookies, scope each API key minimally, and rotate on exposure. Never commit `.env` or anything under `work/`.
- **Containers.** The image runs as a non-root user with a real ffmpeg binary. Keep `work/` and the model cache on mounted volumes, not in the image.

Run `python -m pipeline.doctor` to confirm the access-control and brain settings are in place before you go live.
