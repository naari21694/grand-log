# Ideas

What we have considered for Grand Log, kept separate from the README so the README stays a map of what is real. This is a thinking list, not a set of promises. Shipped work is in the [CHANGELOG](CHANGELOG.md).

## Make it easier to spin up (onboarding)
Shipped so far: the local recipe cookbook, a prebuilt multi-arch GHCR image on every release, and the offline saved-export backfill (no cookies needed to get value from your existing saves). Still considered, biggest first:

1. **Mode-aware doctor.** `auto` and `caption` modes need no ffmpeg, no Whisper, and no cookies for public reels. The preflight should require ffmpeg only for `full` mode and treat cookies and Whisper as progressive, so the lightest path is not blocked by a dependency it does not use.
2. **Split dependencies** into a small core plus optional extras (`whisper`, `bot`, `anthropic`), so the caption-first plus Gemini path installs light and fast instead of pulling the whole tree.

## Make it god-tier easy and community-driven (public-launch pass)
Gated on verifying the pipeline end to end on a real saved export, which is the trigger for flipping the repo public. In leverage order:

1. **A 5-minute quickstart** at the top of the README: a free Gemini key, `pip install`, point at your saved export, watch the dashboard fill. One copy-paste path with no cookies and no server.
2. **A first-run setup wizard** (`python -m pipeline.setup`) that writes `.env` interactively and runs the doctor, so nobody hand-edits config. A Codespaces badge gives a zero-install trial.
3. **A demo** in the README: a short GIF and screenshots of the dashboard filling, the biggest driver of trust and stars.
4. **Make it findable:** flip the repo public, enable Discussions, and label a handful of `good first issue`s drawn from this file.
5. **A contributor seam for new buckets:** the auto-router and the generic `saved` bucket already make new categories cheap; a short "add a bucket" guide turns that into community contributions.

## Robustness and performance
- Retry-with-backoff on the worker plus a dead-letter, so a transient Instagram or network blip never loses a reel.
- Transcribe off the box: a Groq free Whisper API option or `whisper_cpp`, so the server never has to run the 1.5 GB local model.
- Delete the downloaded video after processing; small worker concurrency with rate-limiting for backfill; prompt-cache the schema and use a batch API at half price for the one-time backlog.
- A quality and per-reel latency and cost benchmark across providers, so "good" is a number, not a claim.

## Product
- **Auto-router (live):** shipped for the backfill, where the brain classifies each item once per collection. Bring the same auto-routing to a single live share so it needs zero taps, with the crew buttons as an override.
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
