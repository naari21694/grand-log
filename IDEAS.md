# Ideas

What we have considered for Grand Log, kept separate from the README so the README stays a map of what is real. This is a thinking list, not a set of promises. Shipped work is in the [CHANGELOG](CHANGELOG.md).

## Make it easier to spin up (onboarding)
In build order, biggest and most-real first:

1. **Bundle Mealie in compose.** The local recipe cookbook is done (see the [CHANGELOG](CHANGELOG.md)): on the no-Mealie path recipes append to `work/recipes.json` and `work/recipes.csv`, so nothing is lost. Still open: bundle Mealie in `compose.yaml` so the rich destination also works end to end with no extra manual service.
2. **Mode-aware doctor.** `auto` and `caption` modes need no ffmpeg, no Whisper, and no cookies for public reels. The preflight should require ffmpeg only for `full` mode and treat cookies and Whisper as progressive, so the lightest path is not blocked by a dependency it does not use.
3. **Split dependencies** into a small core plus optional extras (`whisper`, `bot`, `anthropic`), so the caption-first plus Gemini path installs light and fast instead of pulling the whole tree.
4. **A prebuilt multi-arch image on GHCR,** published on release, so setup becomes `docker run` or `docker compose up` with no Python, pip, ffmpeg, or build step.
5. **The non-developer path:** one-click deploy buttons (the templates already exist, see [docs/DEPLOY.md](docs/DEPLOY.md)), a `python -m pipeline.setup` wizard that writes `.env` and runs the doctor, and a Codespaces badge for a zero-install trial.

## Robustness and performance
- Retry-with-backoff on the worker plus a dead-letter, so a transient Instagram or network blip never loses a reel.
- Transcribe off the box: a Groq free Whisper API option or `whisper_cpp`, so the server never has to run the 1.5 GB local model.
- Delete the downloaded video after processing; small worker concurrency with rate-limiting for backfill; prompt-cache the schema and use a batch API at half price for the one-time backlog.
- A quality and per-reel latency and cost benchmark across providers, so "good" is a number, not a claim.

## Product
- **Auto-router:** the brain picks the bucket so a share needs zero taps, with the crew buttons as an override.
- **Resurfacing reminders:** a scheduled digest, on-this-day, and proximity nudges for places. The user research found resurfacing is the single most-wanted fix.
- **Live destination connectors:** Google Sheets, My Maps, and Notion APIs, replacing the manual file import.
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
