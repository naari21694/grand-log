# Contributing to Grand Log 🏴‍☠️

Thanks for wanting to join the crew. Grand Log stays free and community-driven — contributions are genuinely welcome.

## Ways to contribute
- 🐛 Report bugs · 💡 propose features → open an issue
- 🍳 Improve extraction (prompts/`schema.py`), add a destination, harden the downloaders
- 📖 Docs, examples, translations, good-first-issue triage

## Dev setup
See [`reel-pipeline/README.md`](reel-pipeline/README.md). TL;DR:
```bash
cd reel-pipeline && pip install -r requirements.txt   # + install ffmpeg
cp .env.example .env
python -m pipeline.process "<reel-url>" --dry-run
```

## The golden rule of this codebase
**If 10 lines do the job as well as 200 — write 10.** Match the surrounding style. Every stage (download / transcribe / brain / destination) is a *swappable adapter* — keep new vendors behind the same small interface.

## Workflow
1. Fork → branch (`feat/…` or `fix/…`).
2. Keep the change focused. Run `python -m py_compile pipeline/*.py`.
3. Open a PR against `main` with a clear description (link issues, e.g. `Closes #12`) and example output where useful.
4. A maintainer reviews; CI + the CLA check must pass. We squash-merge.

## CLA
Grand Log is dual-licensed (AGPL-3.0 + commercial — see [LICENSING.md](LICENSING.md)). On your first PR the CLA bot will ask you to agree to the [CLA](CLA.md). This keeps a single clean copyright line so the project can stay free *and* sustainable.

## Climbing the crew
Trusted contributors climb a transparent, rules-based ladder — **Contributor → Triager → Reviewer → Maintainer** — with measurable promotion criteria (merged-PR counts, time-in-grade, named sponsors, a no-objection window). It's all in [GOVERNANCE.md](GOVERNANCE.md), and every promotion is itself a reviewable PR. New here? Look for [`good first issue`](https://github.com/naari21694/grand-log/labels/good%20first%20issue).

## Be kind
See the [Code of Conduct](CODE_OF_CONDUCT.md). We're here to build something joyful.
