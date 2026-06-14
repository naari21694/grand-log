# Contributing to Grand Log

Welcome aboard. Grand Log stays free and crew-driven, so contributions are genuinely welcome.

## Ways to help
- Report bugs or propose features: open an issue.
- Improve extraction (prompts and `schema.py`), add a destination, harden the downloaders.
- Docs, examples, translations, triage.

## Dev setup
Start with [ARCHITECTURE.md](ARCHITECTURE.md) for the module map, then [`reel-pipeline/README.md`](reel-pipeline/README.md). Quick version:
```bash
cd reel-pipeline
python -m venv .venv && . .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt                 # plus install ffmpeg
cp .env.example .env                            # add a free brain key (Gemini at aistudio.google.com)
python -m pipeline.doctor                       # confirms ffmpeg, your key, and access control
python -m pipeline.process "<reel-url>" --dry-run
```
Bring any provider's key (Gemini, OpenAI-compatible, or Anthropic); the full matrix is in [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## The one rule of this codebase
If 10 lines do the job as well as 200, write 10. Match the surrounding style. Every stage (download, transcribe, brain, destination) is a swappable adapter, so keep new vendors behind the same small interface.

## Naming
snake_case for functions and variables, PascalCase for classes, UPPER_SNAKE for constants, a leading underscore for private helpers. Functions are verbs, variables are nouns, booleans read as questions (is_ready, has_token). Modules are lowercase and single-purpose. Tests are `test_<module>.py` with `test_<behaviour>` functions. No abbreviations for their own sake, and no hype or internal-instruction words in any public name.

## Workflow
1. Fork, then branch (`feat/name` or `fix/name`).
2. Keep the change focused, and run the same checks CI does before you push:
   ```bash
   cd reel-pipeline
   python -m ruff check pipeline tests tools
   python -m pytest -q
   ```
3. Open a pull request against `main` with a clear description (link issues, for example `Closes #12`) and example output where useful.
4. A maintainer reviews. CI and the CLA check must pass. We squash-merge.

## CLA
Grand Log is dual-licensed (AGPL-3.0 plus a commercial license, see [LICENSING.md](LICENSING.md)). On your first PR the CLA bot asks you to agree to the [CLA](CLA.md). This keeps a single clean copyright line so the project stays free and sustainable.

## Climbing the ranks
Trusted contributors climb a transparent, rules-based ladder: Contributor, Triager, Reviewer, Maintainer. The criteria are measurable (merged-PR counts, time in grade, named sponsors, a no-objection window), and every promotion is itself a reviewable PR. See [GOVERNANCE.md](GOVERNANCE.md). New here? Look for [`good first issue`](https://github.com/naari21694/grand-log/labels/good%20first%20issue).

## Be kind
See the [Code of Conduct](CODE_OF_CONDUCT.md). Every good crew runs on respect.
