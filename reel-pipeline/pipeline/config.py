"""Central config, everything is read from environment / .env (12-factor).

Nothing here is secret-in-code; copy .env.example to .env and fill it in.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # dotenv optional; real env still works
    pass


def _s(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _bool(name: str, default: bool = False) -> bool:
    val = _s(name).lower()
    return val in ("1", "true", "yes", "on") if val else default


def _id_set(name: str) -> set[int]:
    """Parse a comma or space separated list of integer ids (e.g. Telegram chat ids)."""
    out: set[int] = set()
    for tok in _s(name).replace(",", " ").split():
        try:
            out.add(int(tok))
        except ValueError:
            pass
    return out


# --- paths / tools ---
WORKDIR = Path(_s("WORKDIR", "./work")).resolve()
FFMPEG = _s("FFMPEG", "ffmpeg")
YTDLP_COOKIES_BROWSER = _s("YTDLP_COOKIES_BROWSER")  # e.g. "chrome"; empty = no cookies
# A Netscape cookies.txt from a throwaway account; sidesteps the Windows DPAPI browser-cookie
# limitation. Defaults to work/cookies.txt if present, so dropping the file in just works.
YTDLP_COOKIES_FILE = _s("YTDLP_COOKIES_FILE") or (
    str(WORKDIR / "cookies.txt") if (WORKDIR / "cookies.txt").exists() else "")

# --- transcription ---
TRANSCRIBE_BACKEND = _s("TRANSCRIBE_BACKEND", "faster_whisper")  # faster_whisper | whisper_cpp | groq
WHISPER_MODEL = _s("WHISPER_MODEL", "large-v3-turbo")
WHISPER_CPP_BIN = _s("WHISPER_CPP_BIN")
WHISPER_CPP_MODEL = _s("WHISPER_CPP_MODEL")
# Groq: free, fast cloud Whisper (OpenAI-compatible). Set TRANSCRIBE_BACKEND=groq + GROQ_API_KEY
# (free at console.groq.com) to move transcription off the local CPU.
GROQ_API_KEY = _s("GROQ_API_KEY")
GROQ_WHISPER_MODEL = _s("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")

# --- capture mode ---
# auto: read the caption first, download the video and transcribe only if the caption is thin
# caption: never download the video; full: always download and transcribe
CAPTURE_MODE = _s("CAPTURE_MODE", "auto")  # auto | caption | full

# --- media archive ---
# Keep the downloaded video, sampled frames, and thumbnail after extraction (your local archive).
# Set false to delete them once extraction is done and save disk.
KEEP_MEDIA = _bool("KEEP_MEDIA", True)

# --- backfill ---
BACKFILL_SLEEP = float(_s("BACKFILL_SLEEP", "0") or "0")  # seconds to pause after each AI call

# --- brain (provider-agnostic; pick one provider, bring your own key) ---
BRAIN_PROVIDER = _s("BRAIN_PROVIDER", "gemini")  # gemini | openai | anthropic
BRAIN_VISION = _s("BRAIN_VISION", "auto")        # auto | gemini | openai | anthropic | none

# Gemini (free tier): text + vision from one key
GEMINI_API_KEY = _s("GEMINI_API_KEY")
GEMINI_MODEL = _s("GEMINI_MODEL", "gemini-2.5-flash")

# OpenAI-compatible: OpenAI, OpenRouter, Groq, Together, DeepSeek, local Ollama / LM Studio
OPENAI_API_KEY = _s("OPENAI_API_KEY")
OPENAI_BASE_URL = _s("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = _s("OPENAI_MODEL", "gpt-4o-mini")

# Anthropic (official SDK): cheapest reliable extraction = Haiku; set Sonnet/Opus for hard reels
ANTHROPIC_API_KEY = _s("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = _s("ANTHROPIC_MODEL", "claude-haiku-4-5")

# --- destination ---
MEALIE_URL = _s("MEALIE_URL").rstrip("/")
MEALIE_TOKEN = _s("MEALIE_TOKEN")

# --- Den Den Mushi (Telegram bot) ---
TELEGRAM_BOT_TOKEN = _s("TELEGRAM_BOT_TOKEN")

# --- security ---
# Lock the bot to its owner. With no ids set and ALLOW_ALL_CHATS off, the bot replies with
# your chat id and refuses to process until you add it. Never run a public bot unlocked.
ALLOWED_CHAT_IDS = _id_set("ALLOWED_CHAT_IDS")
ALLOW_ALL_CHATS = _bool("ALLOW_ALL_CHATS", False)
# Only these hosts may be downloaded; defends against SSRF via a crafted shared link.
# Empty falls back to the safe default list in security.py.
ALLOWED_HOSTS = tuple(h.lower() for h in _s("ALLOWED_HOSTS").replace(",", " ").split())

# --- dashboard (the tile Mini App) ---
WEBAPP_URL = _s("WEBAPP_URL")  # https URL of the dashboard; enables the /dashboard Mini App button
DASHBOARD_HOST = _s("DASHBOARD_HOST", "127.0.0.1")  # bind localhost by default; expose via a tunnel
DASHBOARD_PORT = int(_s("DASHBOARD_PORT", "8080"))
DASHBOARD_TOKEN = _s("DASHBOARD_TOKEN")  # optional ?token= gate when exposed over a tunnel

WORKDIR.mkdir(parents=True, exist_ok=True)
