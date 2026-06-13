# OSS Android Apps: Save Videos → Extract Value → Route It Home

> A field guide to open-source Android apps for grabbing videos (Instagram, YouTube, ~1,700 sites),
> extracting the valuable content out of them (transcripts, recipes, articles, locations), and
> filing it where it belongs (cookbook, maps, bookmark vault).
>
> Researched & verified June 2026. Status of fast-moving projects noted inline.

---

## The big-picture reality

There is **no single OSS app** that watches an Instagram reel, pulls out "everything of value," and
auto-files the recipe into a cookbook and the location into maps. That's a **pipeline, not an app**.

On Android, the **Share sheet + `geo:`/intent system** is the glue. Think in three layers:

1. **Grab** the media (video/audio)
2. **Extract** the value (transcript, article text, recipe, coordinates)
3. **Route** it to its home (cookbook, maps, bookmark vault)

**Install channels for everything below:** [F-Droid](https://f-droid.org), [IzzyOnDroid](https://apt.izzysoft.de/fdroid/),
or [Obtainium](https://github.com/ImranR98/Obtainium) (auto-updates straight from GitHub releases).
[Accrescent](https://accrescent.app) for a few (e.g. Transcribro).

---

## Layer 1 — Grab the video

The whole modern FOSS download scene runs on the **yt-dlp** engine. Pick a GUI:

| App | Engine | Best for | Sites | Notes |
|---|---|---|---|---|
| **Seal** | yt-dlp | Cleanest one-tap UX | 1,700+ | Material You, embeds metadata/thumbnails/subs, custom yt-dlp commands, aria2c. The "just works" pick. |
| **YTDLnis** | yt-dlp | Power users / batch | 1,000+ | Batch queue, scheduling, format presets, cookie support. More buttons than Seal. |
| **NewPipe** | own extractor | YouTube as a *client* | YT, SoundCloud, Bandcamp, PeerTube | Watch + background + download in one app, no Google. **No Instagram.** |
| **Tubular** | NewPipe fork | NewPipe + SponsorBlock | same | Adds SponsorBlock + ReturnYouTubeDislike. |
| **PipePipe** | NewPipe fork | Most sites of the forks | + Bilibili etc. | SponsorBlock, filters, music mode. |
| **LibreTube** | Piped backend | Max privacy | YT | Proxies through Piped servers; downloads supported. |

**Flow:** open the reel/video → **Share → Seal** (or YTDLnis). They register as share targets, so no
manual URL copying.

### The Instagram caveat (important)
The dedicated OSS Instagram clients — **Barinsta** (formerly InstaGrabber) — are effectively
abandoned / "needs maintainers" and break whenever Meta changes its API. **Don't build a workflow on
them.** The durable path for Instagram reels/posts is **Seal or YTDLnis via yt-dlp**, which handle
public Instagram content. Private/age-gated content requires supplying cookies. Same story for
TikTok, Twitter/X, Facebook.

---

## Layer 2 — Extract the *value*

"Save the video" is easy. "Extract everything of value" means turning media into **text/structured data**.

### A. Get the words out (transcript / captions)
- **yt-dlp itself** pulls existing subtitles (Seal/YTDLnis expose this as a toggle).
- For media with no captions (most reels), use on-device speech-to-text:
  - **Transcribro** — whisper.cpp on-device, fully offline/private. Currently **English-only**.
  - **Easy Transcription** — whisper.cpp, handles **audio *and* video** files, transcribes locally.
- That transcript is the raw "value": recipe steps, the mentioned address, a booklist, etc.

### B. Save article / page content (read-it-later, full-text)
- **Wallabag** — mature self-hosted read-it-later; strips article to clean text; F-Droid Android app; share-to-save.
- **Readeck** — newer, slicker; stores **video transcripts**, does e-book export.
- **Linkwarden** — bookmark + full **page archival** (whole page preserved), annotations; APK via builds repo.

### C. "Save *everything* and let AI sort it" (closest to the one-box dream)
- **Karakeep** (formerly **Hoarder**) — self-hostable "bookmark-everything" for links, notes, images:
  - **AI auto-tagging**, full-text search + OCR
  - **archives videos via yt-dlp**, full-page archival via monolith, RSS auto-hoard
  - **native Android app**
  - runs against a **local Ollama model** → AI extraction stays on your hardware
  - **Best "extract value with AI, privately" hub in OSS right now.**

> **Reality check — recipes from video:** no FOSS app yet *watches a cooking reel and emits a structured
> recipe card*. Working pipeline: **Seal** (download) → **Transcribro/Easy Transcription** (transcript) →
> paste into an LLM or **Karakeep + local Ollama** to structure → into the cookbook. That's 2–3 taps, not one.

---

## Layer 3 — Route it home

### Recipes → a real cookbook
(Killer feature: paste a recipe-blog URL → it *scrapes* title/ingredients/steps/photo automatically.)
- **Mealie** — self-hosted, best URL-import recipe scraper, meal planner. Android clients: **Mealient** (+ others).
- **Tandoor** — heavier/more powerful (nutrition, costing, shopping). Android client: **Kitshn** (Jetpack Compose / Material You).
- **KitchenOwl** — FOSS, self-hosted, leaner; recipes + groceries.
- **Flow:** find a recipe (blog or transcript) → **Share → Mealie/Tandoor → "import from URL"** or paste.

### Locations → your maps
- **Organic Maps** — clean offline OSM maps; bookmark places; import/export **KML/KMZ/GPX/GeoJSON**.
  - Note: community fork **CoMaps** spun off in 2025 after a governance split — same DNA, worth knowing.
- **OsmAnd** — the Swiss-army-knife; listens to `geo:` intents so other apps drop pins straight in.
- **Geo Share** (the glue you'll love) — takes a Google/Apple Maps *share link* (`maps.app.goo.gl/…`
  that won't open in OSM apps), resolves it to coordinates, and lets you **open in
  OsmAnd/Organic Maps/CoMaps, copy as `geo:`, or save as GPX** — even auto-run an action.
  Exactly the "someone posted a place → add it to *my* maps" path.

---

## The glue layer (and an honest gap)

- **Android Share sheet + intents** do ~90% of the wiring for free — every app above registers as a share target.
- **FOSS automation is the weak spot.** There is **no great open-source Tasker**. **Easer** is the main
  FOSS option and it's limited. MacroDroid / Tasker / Automate are more capable but **not** open source.
  So fully-automatic "detect reel → extract → file it" macros aren't achievable in pure FOSS today —
  expect to tap Share manually.

---

## Two concrete end-to-end recipes

**🍳 "This reel has a recipe I want to keep"**
Reel → Share → **Seal** (download) → if you need the spoken steps, **Easy Transcription** →
paste recipe URL/text into **Mealie** (or **Tandoor/Kitshn**) → structured card, offline forever.

**📍 "This post/video mentions a place I want on my map"**
Grab the Maps link or address → **Geo Share** (resolve to coords) → open in **OsmAnd / Organic Maps** →
save as bookmark or GPX favorite.

**🗃️ "Just save the whole thing and let AI tag it"**
Anything → Share → **Karakeep** (self-hosted, local Ollama) → auto-tagged, full-text searchable, video archived.

---

## Caveats

- **Self-hosted** (need an always-on box — Raspberry Pi / old laptop / $5 VPS / Docker):
  Mealie, Tandoor, KitchenOwl, Karakeep, Wallabag, Linkwarden, Readeck.
- **100% on-device** (nothing to host): Seal, YTDLnis, NewPipe & forks, LibreTube, Transcribro,
  Easy Transcription, Organic Maps, OsmAnd, CoMaps, Geo Share.
- Downloading for **personal/offline** use is the norm, but cuts against YouTube/Instagram ToS — know the line.

---

## Decision fork (to wire up next)

1. **Self-hosted route** — willing to run a small box → unlocks Mealie/Tandoor/Karakeep (the real "extract & file" magic).
2. **Strictly on-device, zero-server kit** — Seal + Transcribro + Organic Maps + Geo Share.

Pick one + priority (recipe / location / Instagram angle) → get exact install list and step-by-step share-sheet flow.

---

## Sources

- Seal: [F-Droid](https://f-droid.org/packages/com.junkfood.seal/) · [GitHub](https://github.com/JunkFood02/Seal) · [MakeUseOf](https://www.makeuseof.com/seal-open-source-android-app-is-cleanest-way-to-download-youtube-videos/)
- YTDLnis: [F-Droid](https://f-droid.org/en/packages/com.deniscerri.ytdl/) · [GitHub](https://github.com/deniscerri/ytdlnis)
- NewPipe: [GitHub](https://github.com/TeamNewPipe/NewPipe) · PipePipe: [F-Droid](https://f-droid.org/packages/InfinityLoop1309.NewPipeEnhanced/) · [Grayjay/NewPipe alternatives](https://alternativeto.net/software/grayjay/)
- Barinsta status: [GitHub](https://github.com/The-EDev/barinsta)
- Mealie: [GitHub](https://github.com/mealie-recipes/mealie) · Tandoor: [site](https://tandoor.dev/) · [XDA: Tandoor vs Mealie + Kitshn/Mealient](https://www.xda-developers.com/reasons-tandoor-replaced-mealie-for-managing-my-recipes/) · [Cooklang: OSS recipe managers 2026](https://cooklang.org/blog/18-open-source-recipe-managers-2026/)
- Karakeep: [GitHub](https://github.com/karakeep-app/karakeep) · [site](https://karakeep.app/) · [docs](https://docs.karakeep.app/)
- Wallabag Android: [GitHub](https://github.com/wallabag/android-app) · Linkwarden: [GitHub](https://github.com/linkwarden/linkwarden) · Readeck: [overview](https://openalternative.co/alternatives/readeck)
- Transcribro: [GitHub](https://github.com/soupslurpr/Transcribro) · Easy Transcription: [whisper.cpp discussion](https://github.com/ggml-org/whisper.cpp/discussions/1266)
- Organic Maps: [Wikipedia](https://en.wikipedia.org/wiki/Organic_Maps) · OsmAnd intents: [geo:](https://osmand.net/docs/technical/algorithms/osmand-intents/) · Geo Share: [F-Droid](https://f-droid.org/packages/page.ooooo.geoshare/) · [GitHub](https://github.com/jakubvalenta/geoshare)
- FOSS Tasker alternatives (Easer): [Lemmy discussion](https://lemmy.world/post/2616306)
