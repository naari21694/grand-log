"""Security helpers: who may drive the bot, and which URLs may be downloaded.

These are pure functions with no Telegram or network dependency, so they are unit-tested
directly and reused by both the bot (front door) and the downloader (defense in depth).
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from . import config

_URL = re.compile(r"https?://[^\s]+")

# Hosts a reel can legitimately come from. Override with ALLOWED_HOSTS in .env.
# This guards the SUBMITTED host. The downloaders (yt-dlp, gallery-dl) follow 3xx redirects
# themselves with no per-hop re-check, so allowed hosts are trusted not to open-redirect to an
# internal address. Owner-locked submission keeps the real-world risk low; for a hard guarantee,
# egress-restrict the downloader away from link-local and RFC1918 at the deploy layer. Entries
# must be domain names, never IP literals.
DEFAULT_HOSTS = (
    "instagram.com", "tiktok.com", "youtube.com", "youtu.be",
    "facebook.com", "fb.watch", "pinterest.com", "pin.it",
)


def allowed_hosts() -> tuple[str, ...]:
    return config.ALLOWED_HOSTS or DEFAULT_HOSTS


def is_allowed_host(url: str) -> bool:
    """True only for http(s) URLs whose host is, or is a subdomain of, an allowed host."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    return any(host == h or host.endswith("." + h) for h in allowed_hosts())


def first_allowed_url(text: str) -> str | None:
    """The first allowed-host URL in a message, with trailing punctuation trimmed."""
    for match in _URL.finditer(text or ""):
        url = match.group(0).rstrip(").,]}\"'")
        if is_allowed_host(url):
            return url
    return None


def is_allowed_chat(chat_id: int) -> bool:
    """True if this chat may use the bot: explicitly allow-listed, or the bot is opened up."""
    if config.ALLOW_ALL_CHATS:
        return True
    return chat_id in config.ALLOWED_CHAT_IDS
