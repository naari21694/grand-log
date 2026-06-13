"""Geocode a place name to lat/lng via OpenStreetMap Nominatim (free, no key).

Nominatim asks for a real User-Agent and at most one request per second. Failure is
non-fatal: a place with no coordinates is still recorded, just without a pin.
"""
from __future__ import annotations

import requests

_URL = "https://nominatim.openstreetmap.org/search"
_HEADERS = {"User-Agent": "grand-log/0.1 (https://github.com/naari21694/grand-log)"}


def lookup(query: str) -> tuple[float, float] | None:
    """Return (lat, lng) for the best match, or None on miss or error."""
    query = (query or "").strip()
    if not query:
        return None
    try:
        resp = requests.get(
            _URL, params={"q": query, "format": "json", "limit": 1}, headers=_HEADERS, timeout=20
        )
        resp.raise_for_status()
        hits = resp.json()
    except Exception:
        return None
    if hits:
        return float(hits[0]["lat"]), float(hits[0]["lon"])
    return None
