# Security Policy

## Supported versions
The latest `main` is supported. This is an early-stage project — pin a commit/tag if you need stability.

| Version | Supported |
| ------- | --------- |
| `main`  | ✅ |
| older   | ❌ |

## Reporting a vulnerability
**Please do not report security issues through public issues, discussions, or PRs.**

Use GitHub's private **[Report a vulnerability](https://github.com/naari21694/grand-log/security/advisories/new)** button (Private Vulnerability Reporting), or email **vnarendrakumar21694@gmail.com** with subject `Grand Log security`. Include impact, affected stage (download / transcribe / brain / destination), repro steps, and version/commit.

We aim to acknowledge within a few days and will keep you posted through to a fix and coordinated disclosure.

## Notes
- Grand Log runs on **your own** infrastructure with **your own** keys and cookies — keep your `.env` private (it's gitignored). See [PRIVACY.md](PRIVACY.md).
- The downloaders (yt-dlp / gallery-dl) fetch from third-party sites; treat all downloaded content as untrusted input.
- Hardening in place: CodeQL scanning, OpenSSF Scorecard, Dependabot, secret scanning + push protection, least-privilege CI, pinned third-party actions.
