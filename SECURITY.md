# Security Policy

## Reporting a vulnerability
Please **do not open a public issue** for security problems. Email the maintainer at **vnarendrakumar21694@gmail.com** (subject: `Grand Log security`) with details and steps to reproduce. We'll acknowledge within a few days and keep you posted on a fix.

## Notes
- Grand Log runs on **your own** infrastructure with **your own** API keys and cookies — keep your `.env` private (it's gitignored).
- The downloaders (yt-dlp / gallery-dl) fetch from third-party sites; treat all downloaded content as untrusted input.

## Supported versions
The latest `main` is supported. This is an early-stage project — pin a commit if you need stability.
