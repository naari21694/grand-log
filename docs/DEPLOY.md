# Deploying Grand Log

Grand Log is alpha software. The commands below work, but expect rough edges and pin a commit or tag if you need stability.

The front door is a Telegram bot (Den Den Mushi) that talks to Telegram over long-polling. It dials out to Telegram and waits for replies, so a deployment needs no public port and nothing is exposed to the internet. That is the secure default. There is no web server to firewall and no inbound URL for a stranger to find.

Every option in this guide needs two things:

- A persistent volume mounted at `/app/work`. This holds the SQLite queue and the saved-items index. If the volume is not persistent, your queue and index reset on every restart.
- The environment variables from `reel-pipeline/.env.example` set in the platform. On cloud hosts you set these in the dashboard or CLI as secrets. On a self-hosted box you keep them in a `.env` file.

The Python app lives in `reel-pipeline/`. Several config files (`railway.json`, `fly.toml`, `compose.yaml`, `Dockerfile`) live inside that directory, while `render.yaml` lives at the repo root and points into it. The sections below call out the right working directory for each platform.

## Prerequisites (do this once, before any deploy)

You need three things ready before you pick a platform.

1. A Telegram bot token. Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow the prompts, and copy the token it gives you. This becomes `TELEGRAM_BOT_TOKEN`.

2. A brain key. The brain is the model that reads the reel. Start with Gemini, which has a free tier and gives you text plus on-screen vision from one key. Get a key at [aistudio.google.com](https://aistudio.google.com). This becomes `GEMINI_API_KEY`, with `BRAIN_PROVIDER=gemini`. (OpenAI-compatible and Anthropic providers are also supported, see `.env.example` for those rows.)

3. Your Telegram chat id for `ALLOWED_CHAT_IDS`. You do not have this yet, and that is expected. You get it from the bot itself after the first deploy. The bot is locked down by default: with no id set and `ALLOW_ALL_CHATS` off, it refuses to process any message and replies with your chat id instead. So the real flow is:

   - Deploy first with `ALLOWED_CHAT_IDS` empty.
   - Message your bot once. It replies with your chat id and refuses to do anything else.
   - Copy that id into `ALLOWED_CHAT_IDS` and redeploy.

   This two-step is a one-time manual step, not a bug. It is how the bot keeps a stranger who finds it from spending your API budget. Do not set `ALLOW_ALL_CHATS=true` unless you knowingly want the bot open to anyone.

The full "after deploy" checklist is at the bottom of this page.

## Choose your host

Grand Log runs the same everywhere: one image (or one Python install) plus a `.env`. The bot
long-polls Telegram, so no host needs an open inbound port, on a home machine or in the cloud.
Pick what fits you.

| Host | Best for | Always on | Cost | Where |
|------|----------|-----------|------|-------|
| Your own computer | personal use, trying it out | only while the machine is on | $0 | next section |
| Home server, mini PC, or NAS | always-on at home, any user | yes | one-time hardware | Docker Compose, below |
| Raspberry Pi | low-power always-on at home | yes | about $70 once | Docker Compose, below |
| Oracle Cloud Always-Free ARM | a free cloud box, no hardware | yes | $0 | Docker Compose, below |
| Railway / Render / Fly | fastest cloud, click to deploy | yes | free tier or a few dollars | their sections |

If you just want to see it work, start on your own computer. For a setup that answers around the
clock, use an always-on machine at home or a cloud host. Every option uses the same two keys and the
same claim flow.

## Your own computer (a personal always-on host)

Running Grand Log on your own machine is a first-class option, not only a test. Because the bot
reaches Telegram outbound only, it works from behind your home router with no port forwarding, and
you can still share reels to it from your phone anywhere. The one thing to know: it answers only
while the machine is on. For round-the-clock use, keep the machine awake (below) or move to an
always-on box later. Nothing else changes, the same `.env` and the same bot.

### 1. Install and configure
Follow [INSTALL.md](INSTALL.md) to get the code and dependencies, then set up your `.env`. The fast
way is the wizard, which asks for your keys and writes `.env` for you:

```bash
cd reel-pipeline
python -m pipeline.setup
```

It prompts for your brain provider and key (Gemini is the free default) and an optional Telegram bot
token, then runs the doctor. You can also copy `.env.example` to `.env` and edit it by hand.

### 2. Run the bot
```bash
python -m pipeline.bot
```

Or, for an isolated, self-restarting setup that matches the cloud hosts, use Docker Desktop:

```bash
cd reel-pipeline
docker compose up -d
```

Docker also sidesteps a Windows quirk where yt-dlp cannot read Chrome cookies, since the container is
Linux. For most reels this does not matter, because caption-first mode reads the caption without
downloading the video.

### 3. Keep it running (always-on)
The bot restarts itself after a crash (the Docker `restart` policy) and resumes its queue after a
reboot. To have it answer around the clock, stop the machine from sleeping, and start it on login:

- **Windows:** Settings, then System, then Power, set sleep to Never on power. To start on boot, either
  enable Docker Desktop's "Start when you log in" (Docker path), or add `python -m pipeline.bot` as a
  Task Scheduler task at logon (native path).
- **macOS:** run under `caffeinate -s`, or add a `launchd` agent. Docker Desktop has a start-on-login
  option too.
- **Linux:** use the Docker Compose path with `restart: unless-stopped` (already set) and enable Docker
  on boot (`systemctl enable docker`). For the native path, a small `systemd` service works.

Caveats to accept: a home machine is offline during power or internet outages, and full-mode Whisper
transcription is slow on a laptop. Both are eased by caption-first mode and by the queue resuming when
the machine comes back. When you want always-on without relying on your own hardware, use the home
server Docker Compose path below or a cloud host.

## Railway

`railway.json` lives inside `reel-pipeline/`, not at the repo root. So the first thing to set in the Railway dashboard is the service Root Directory.

1. Create a new project from your repo.
2. In the service settings, set **Root Directory** to `reel-pipeline`. Railway then finds `railway.json` and the `Dockerfile` there.
3. Railway builds from the Dockerfile and runs the start command from `railway.json`.
4. Add a volume mounted at `/app/work`.
5. Set the environment variables (`TELEGRAM_BOT_TOKEN`, `BRAIN_PROVIDER`, `GEMINI_API_KEY`, and `ALLOWED_CHAT_IDS` once you have it) in the service Variables tab.

The key fields from `railway.json`:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python -m pipeline.bot",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

So: builder is `DOCKERFILE`, the Dockerfile path is `Dockerfile` (resolved relative to the `reel-pipeline` root directory you set), the start command is `python -m pipeline.bot`, and Railway restarts the service on failure up to 10 times.

## Fly.io

Deploy from inside the `reel-pipeline` directory. Run the exact sequence below (it is the same one recorded in the comment at the top of `fly.toml`):

```bash
cd reel-pipeline
fly launch --no-deploy
fly volumes create grandlog_work --size 3
fly secrets set TELEGRAM_BOT_TOKEN=... BRAIN_PROVIDER=gemini GEMINI_API_KEY=... ALLOWED_CHAT_IDS=...
fly deploy
```

Notes:

- `fly launch --no-deploy` creates the app without deploying yet, so you can set up the volume and secrets first.
- The volume is named `grandlog_work` at 3 GB. `fly.toml` mounts that volume at `/app/work`:

  ```toml
  [[mounts]]
    source = "grandlog_work"
    destination = "/app/work"
  ```

- On your first deploy you will not have `ALLOWED_CHAT_IDS` yet. Set the other secrets, deploy, message the bot to get your id, then run `fly secrets set ALLOWED_CHAT_IDS=...` and `fly deploy` again.
- No http service is needed. The bot runs as a process (`bot = "python -m pipeline.bot"` in `fly.toml`) and uses long-polling, so there is no public port to configure.

## Render

Render reads `render.yaml` from the repo root, and that file already sets `rootDir: reel-pipeline` so the build runs against the Python app.

1. In the Render dashboard, choose **New > Blueprint** and point it at this repo.
2. Render reads `render.yaml` and creates one service: a worker named `grand-log-bot`. A worker has no inbound port, which fits the long-polling bot.
3. The blueprint declares a disk named `work` mounted at `/app/work` at 3 GB, and runs `python -m pipeline.bot` from the Docker image.
4. Set the secret env vars in the dashboard (see below), then deploy.

Which env vars are which:

- `BRAIN_PROVIDER` is set in the blueprint to `gemini`. No action needed.
- `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, and `ALLOWED_CHAT_IDS` are marked `sync: false`, which means Render does not read their values from the file. You set each one by hand in the dashboard. Set the first two before the first deploy, and fill in `ALLOWED_CHAT_IDS` after the bot gives you your chat id, then redeploy.

## Docker Compose (self-host)

This is the path for your own box, for example an Oracle Cloud Always-Free ARM instance. The image is multi-arch (amd64 and arm64), so it runs on ARM hardware without changes.

From the `reel-pipeline` directory:

```bash
cd reel-pipeline
cp .env.example .env
# edit .env: set TELEGRAM_BOT_TOKEN, your brain key (GEMINI_API_KEY), and later ALLOWED_CHAT_IDS
docker compose up -d
```

What `compose.yaml` sets up:

- A single service `den-den-mushi` that builds the local image, runs `python -m pipeline.bot`, reads your `.env`, and restarts unless you stop it.
- A work volume: `./work` on the host is mounted to `/app/work` in the container. This holds the SQLite queue and the saved-items index.
- A whisper cache volume: the named volume `whisper-cache` is mounted at `/cache/huggingface` so the transcription model downloads once and is reused across restarts instead of being re-downloaded every time.

As with the cloud hosts, start with `ALLOWED_CHAT_IDS` empty, message the bot to get your chat id, paste it into `.env`, then run `docker compose up -d` again to pick up the change.

To upgrade:

```bash
docker compose pull && docker compose up -d
```

Or run [Watchtower](https://containrrr.dev/watchtower/) to pull and restart on new images automatically.

## Optional: exposing the Mealie PWA or the dashboard

You do not need this to use Grand Log. The bot returns cards in Telegram on its own. Expose a web surface only if you want the Mealie cookbook PWA or the tile dashboard reachable from a browser or phone.

If you do, do not open a raw port to the internet. Use a [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to publish the service, and put [Cloudflare Access](https://developers.cloudflare.com/cloudflare-one/policies/access/) in front of it with an email one-time-passcode policy so only your email can reach it.

For the dashboard specifically (`python -m pipeline.web`, the tile view):

- It binds `127.0.0.1` by default (`DASHBOARD_HOST=127.0.0.1`), so it is not reachable from outside the host until you deliberately tunnel it.
- When you expose it, set `DASHBOARD_TOKEN` so the URL requires `?token=...`, and set `WEBAPP_URL` to the https URL of the dashboard so the bot can offer the `/dashboard` Mini App button.

This is defense in depth: the tunnel and Access gate who can connect, and the token gates the URL itself.

## After deploy (checklist)

1. Message your bot on Telegram. On the first deploy it replies with your chat id and refuses to process anything else (this is the lockdown working).
2. Copy that chat id into `ALLOWED_CHAT_IDS` on your platform (Railway Variables, `fly secrets set`, Render dashboard, or `.env` for Compose).
3. Redeploy so the new value takes effect.
4. Share an Instagram reel with the bot.
5. Confirm the card comes back. If it does, the pipeline is live.

If something is off, the app ships a self-check: run `python -m pipeline.doctor` to confirm the access-control and brain settings are in place.
