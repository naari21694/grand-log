# Ideas

What we have considered for Grand Log, kept separate from the README so the README stays a map of what is real. This is a thinking list, not a set of promises. Shipped work is in the [CHANGELOG](CHANGELOG.md).

## Make it easier to spin up (onboarding)
Shipped so far (see the [CHANGELOG](CHANGELOG.md)): the local recipe cookbook, the `python -m pipeline.setup` wizard, the mode-aware doctor, and the release automation that builds and pushes a multi-arch GHCR image on every version tag. Still considered, biggest first:

1. **Bundle Mealie in `compose.yaml`** so the rich recipe destination also comes up with no extra manual service. The no-Mealie path already keeps recipes in `work/recipes.json` and `recipes.csv`, so nothing is lost without it.
2. **Split dependencies** into a small core plus optional extras (`whisper`, `bot`, `anthropic`), so the caption-first plus Gemini path installs light instead of pulling the whole tree.
3. **A GHCR-pull `compose.yaml` and one-click deploy buttons.** The image publishes on release and the deploy templates already exist (see [docs/DEPLOY.md](docs/DEPLOY.md)); the remaining win is a compose that pulls the prebuilt image with no local build, plus a Codespaces badge for a zero-install trial.

## Public launch and community
- **A demo in the README:** a short GIF of a share becoming a card, plus a dashboard screenshot. This is the single biggest driver of trust and stars. Captured once the capture path is exercised end to end on real shares.
- **Make it findable:** enable GitHub Discussions and label a handful of `good first issue`s drawn from this file.
- **A contributor seam for new buckets:** the generic `saved` bucket and centralized routing already make a new category cheap; a short "add a bucket" guide turns that into community pull requests.

## Robustness and performance
- Small worker concurrency with rate-limiting for backfill; prompt-cache the schema and use a batch API at half price for the one-time backlog.
- A quality and per-reel latency and cost benchmark across providers, so "good" is a number, not a claim.

(Shipped, see the [CHANGELOG](CHANGELOG.md): worker retry-with-backoff plus a dead-letter; transcribe off the box, now done via GPU auto-detect and the Groq Whisper backend; and deleting the downloaded media after processing via `KEEP_MEDIA`.)

## Product
- **Live auto-router:** the backfill already classifies each item with the brain (one call per collection). Bring the same auto-routing to a single live share so it needs zero taps, with the crew buttons as an override.
- **Resurfacing reminders:** a scheduled digest, on-this-day, and proximity nudges for places. The user research found resurfacing is the single most-wanted fix.
- **Live destination connectors:** Google Sheets, My Maps, and Notion APIs, replacing the manual file import.
- **Durable image-post (`/p/`) support in the pipeline itself:** download the carousel images via gallery-dl and run the vision pass on them. About half a typical saved backlog is image posts, not video reels; the offline runner already handles them, but the pipeline's `process_one` is still video-centric.
- **More sources:** TikTok, YouTube Shorts, and Pinterest. The downloader already supports them; this needs routing and end-to-end testing.

## New buckets
Fitness and workouts (structured routines), wishlist and products (links and prices), books and watchlist, outfits and lookbook, music to a playlist, trips and itineraries (Log Pose assembles day-plans), and knowledge and how-tos (a second-brain wiki).

## Bigger bets
- A shared, co-owned vault for a household or a crew.
- Natural-language queries to the bot, for example "what curries have I saved".
- Price-drop alerts on saved products.
- A custom unified skin across the three systems, once the stock destinations are proven.

## How an idea graduates
An idea moves to the [CHANGELOG](CHANGELOG.md) when it is built, tested, and documented. Each carries a trigger for when it is worth doing.
