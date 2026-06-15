# Ideas

What we have considered for Grand Log, kept separate from the README so the README stays a map of what is real. This is a thinking list, not a set of promises. Shipped work is in the [CHANGELOG](CHANGELOG.md).

## Make it easier to spin up (onboarding)
In build order, biggest and most-real first:

1. **Bundle Mealie in compose.** The local recipe cookbook is done (see the [CHANGELOG](CHANGELOG.md)): on the no-Mealie path recipes append to `work/recipes.json` and `work/recipes.csv`, so nothing is lost. Still open: bundle Mealie in `compose.yaml` so the rich destination also works end to end with no extra manual service.
2. **Split dependencies** into a small core plus optional extras (`whisper`, `bot`, `anthropic`), so the caption-first plus Gemini path installs light and fast instead of pulling the whole tree.
3. **A prebuilt multi-arch image on GHCR,** published on release, so setup becomes `docker run` or `docker compose up` with no Python, pip, ffmpeg, or build step.
4. **The non-developer path:** one-click deploy buttons (the templates already exist, see [docs/DEPLOY.md](docs/DEPLOY.md)) and a Codespaces badge for a zero-install trial. (The `python -m pipeline.setup` wizard and the mode-aware doctor are now shipped, see the [CHANGELOG](CHANGELOG.md).)

## Robustness and performance
- Small worker concurrency with rate-limiting for backfill; prompt-cache the schema and use a batch API at half price for the one-time backlog.
- A quality and per-reel latency and cost benchmark across providers, so "good" is a number, not a claim.

(Shipped, see the [CHANGELOG](CHANGELOG.md): worker retry-with-backoff plus a dead-letter; transcribe off the box, now done via GPU auto-detect and the Groq Whisper backend; and deleting the downloaded media after processing via `KEEP_MEDIA`.)

## Product
- **Auto-router:** the brain picks the bucket so a share needs zero taps, with the crew buttons as an override.
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
