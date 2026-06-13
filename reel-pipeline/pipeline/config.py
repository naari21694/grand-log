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


# --- paths / tools ---
WORKDIR = Path(_s("WORKDIR", "./work")).resolve()
FFMPEG = _s("FFMPEG", "ffmpeg")
YTDLP_COOKIES_BROWSER = _s("YTDLP_COOKIES_BROWSER")  # e.g. "chrome"; empty = no cookies

# --- transcription ---
TRANSCRIBE_BACKEND = _s("TRANSCRIBE_BACKEND", "faster_whisper")  # faster_whisper | whisper_cpp
WHISPER_MODEL = _s("WHISPER_MODEL", "large-v3-turbo")
WHISPER_CPP_BIN = _s("WHISPER_CPP_BIN")
WHISPER_CPP_MODEL = _s("WHISPER_CPP_MODEL")

# --- brain (swappable adapters) ---
BRAIN_TEXT = _s("BRAIN_TEXT", "claude_p")   # claude_p | gemini
CLAUDE_BIN = _s("CLAUDE_BIN", "claude")
CLAUDE_MODEL = _s("CLAUDE_MODEL")           # optional override
BRAIN_VISION = _s("BRAIN_VISION", "gemini")  # gemini | none
GEMINI_API_KEY = _s("GEMINI_API_KEY")
GEMINI_MODEL = _s("GEMINI_MODEL", "gemini-2.5-flash")

# --- destination ---
MEALIE_URL = _s("MEALIE_URL").rstrip("/")
MEALIE_TOKEN = _s("MEALIE_TOKEN")

# --- Den Den Mushi (Telegram bot) ---
TELEGRAM_BOT_TOKEN = _s("TELEGRAM_BOT_TOKEN")

# --- dashboard (the tile Mini App) ---
WEBAPP_URL = _s("WEBAPP_URL")  # https URL of the dashboard; enables the /dashboard Mini App button

WORKDIR.mkdir(parents=True, exist_ok=True)
