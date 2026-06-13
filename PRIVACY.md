# Privacy

**No telemetry. No analytics. No tracking. Grand Log never phones home.**

Grand Log is self-hosted software you run on your own machine. It is built so that *nothing sensitive ever leaves your control*.

- **All your data stays local.** Downloaded reels, audio, transcripts, sampled frames, and the structured results are processed and stored only on the box you run Grand Log on. They are never sent to us — there is no "us" to send them to.
- **Secrets stay local.** Every credential (LLM keys, Instagram cookies, Telegram bot token, Mealie token) is read from environment variables / a git-ignored `.env`. None are committed to this repository or transmitted anywhere except the service you explicitly point them at.
- **No hidden outbound calls.** The only network calls Grand Log makes are to the services *you* configure: the source platform (to download the reel you shared), your chosen LLM/transcription, and your chosen destination (e.g. your Mealie). Every integration is opt-in and configured by you.
- **No accounts, no profiles, no collection.** Grand Log does not create an account, build a profile, or collect usage data from anyone who runs it.
- **You own retention.** Media and logs live on your disk until *you* delete them. Logs default to local output only. No automatic cloud backup.

If you self-host the destinations (Mealie, etc.), their privacy is governed by their own projects — Grand Log only writes to the ones you point it at.

> The whole point of Grand Log is to put *your* treasure back in *your* hands. Collecting your data would defeat it.
