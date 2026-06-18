"""Geocode a place to lat/lng via free services (OpenStreetMap Nominatim, then Photon).

Two entry points:
  lookup(query)                    free-text, one Nominatim hit. Simple, unconstrained.
  locate(name, city, country, cat) accuracy-first. The lookup is constrained to the named
                                   country, country/state centroids are rejected for real
                                   POIs (so distinct places never stack on a country's
                                   middle), a second source (Photon) is tried when Nominatim
                                   misses, and same-name hits are ranked toward the claimed
                                   city. Returns {lat, lng, source, confidence} or None.

Both send a real User-Agent and pace themselves to one request per second (Nominatim policy).
Failure is non-fatal everywhere: a place with no coordinates is still recorded, just without
a pin.
"""
from __future__ import annotations

import time

import requests

_NOMINATIM = "https://nominatim.openstreetmap.org/search"
_PHOTON = "https://photon.komoot.io/api/"
_HEADERS = {"User-Agent": "grand-log/0.4 (https://github.com/naari21694/grand-log)"}
_PACE = 1.0  # seconds between live calls; respects the Nominatim usage policy

# Categories that name an area, not a point: a region/city/country centroid is the right answer.
_AREA = {"region", "city", "country"}
# Result granularities too coarse to pin a real POI on.
_COARSE_NOMINATIM = {"country", "state", "state_district", "region", "province", "county", "continent"}
_COARSE_PHOTON = {"country", "state", "county"}

# Country name (as the brain writes it) -> ISO 3166-1 alpha-2, used to constrain the lookup.
# An unlisted country simply skips the constraint (it still rides along inside the query text).
_COUNTRY_ISO = {
    "afghanistan": "AF", "albania": "AL", "argentina": "AR", "australia": "AU", "austria": "AT",
    "bangladesh": "BD", "belgium": "BE", "bhutan": "BT", "bolivia": "BO", "brazil": "BR",
    "bulgaria": "BG", "cambodia": "KH", "canada": "CA", "chile": "CL", "china": "CN",
    "colombia": "CO", "croatia": "HR", "czech republic": "CZ", "czechia": "CZ", "denmark": "DK",
    "egypt": "EG", "england": "GB", "estonia": "EE", "faroe islands": "FO", "finland": "FI",
    "france": "FR", "georgia": "GE", "germany": "DE", "greece": "GR", "guatemala": "GT",
    "hong kong": "HK", "hungary": "HU", "iceland": "IS", "india": "IN", "indonesia": "ID",
    "iran": "IR", "iraq": "IQ", "ireland": "IE", "israel": "IL", "italy": "IT", "japan": "JP",
    "jordan": "JO", "kenya": "KE", "korea": "KR", "south korea": "KR", "laos": "LA",
    "latvia": "LV", "lebanon": "LB", "lithuania": "LT", "luxembourg": "LU", "malaysia": "MY",
    "maldives": "MV", "malta": "MT", "mexico": "MX", "monaco": "MC", "morocco": "MA",
    "myanmar": "MM", "nepal": "NP", "netherlands": "NL", "new zealand": "NZ", "norway": "NO",
    "oman": "OM", "pakistan": "PK", "peru": "PE", "philippines": "PH", "poland": "PL",
    "portugal": "PT", "qatar": "QA", "romania": "RO", "russia": "RU", "saudi arabia": "SA",
    "scotland": "GB", "singapore": "SG", "slovakia": "SK", "slovenia": "SI", "south africa": "ZA",
    "spain": "ES", "sri lanka": "LK", "sweden": "SE", "switzerland": "CH", "taiwan": "TW",
    "tanzania": "TZ", "thailand": "TH", "tunisia": "TN", "turkey": "TR", "uae": "AE",
    "united arab emirates": "AE", "uk": "GB", "united kingdom": "GB", "usa": "US",
    "united states": "US", "united states of america": "US", "vatican city": "VA",
    "vietnam": "VN", "wales": "GB",
}


def lookup(query: str) -> tuple[float, float] | None:
    """Return (lat, lng) for the best free-text match, or None on miss or error."""
    query = (query or "").strip()
    if not query:
        return None
    try:
        resp = requests.get(
            _NOMINATIM, params={"q": query, "format": "json", "limit": 1}, headers=_HEADERS, timeout=20
        )
        resp.raise_for_status()
        hits = resp.json()
    except Exception:
        return None
    if hits:
        return float(hits[0]["lat"]), float(hits[0]["lon"])
    return None


def locate(name: str, city: str = "", country: str = "", category: str = "") -> dict | None:
    """Accuracy-first geocode. Returns {lat, lng, source, confidence} or None.

    confidence is "poi" (a specific feature), "town" (a settlement centroid), or "area"
    (deliberate, for region/city/country items).
    """
    name = (name or "").strip()
    if not name:
        return None
    city, country = (city or "").strip(), (country or "").strip()
    cc = _COUNTRY_ISO.get(country.lower())
    is_area = (category or "").strip().lower() in _AREA
    queries = [", ".join(p for p in (name, city, country) if p)]
    if city and country:
        queries.append(f"{name}, {country}")          # retry without the city if the first misses
    for q in queries:
        hit = _nominatim(q, cc, is_area)
        if hit:
            return hit
    for q in queries:
        hit = _photon(q, cc, city, is_area)
        if hit:
            return hit
    return None


def _nominatim(query: str, cc: str | None, is_area: bool) -> dict | None:
    params = {"q": query, "format": "jsonv2", "addressdetails": 1, "limit": 1}
    if cc:
        params["countrycodes"] = cc.lower()
    try:
        resp = requests.get(_NOMINATIM, params=params, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        hits = resp.json()
    except Exception:
        time.sleep(_PACE)
        return None
    time.sleep(_PACE)
    if not hits:
        return None
    h = hits[0]
    kind = (h.get("addresstype") or h.get("type") or "").lower()
    if not is_area and kind in _COARSE_NOMINATIM:
        return None
    return {"lat": float(h["lat"]), "lng": float(h["lon"]), "source": "nominatim",
            "confidence": _confidence(kind, is_area)}


def _photon(query: str, cc: str | None, city: str, is_area: bool) -> dict | None:
    try:
        resp = requests.get(_PHOTON, params={"q": query, "limit": 5}, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        feats = resp.json().get("features", [])
    except Exception:
        time.sleep(_PACE)
        return None
    time.sleep(_PACE)
    cands = []
    for ft in feats:
        pr = ft.get("properties", {})
        if cc and (pr.get("countrycode") or "").upper() != cc:
            continue
        kind = (pr.get("type") or "").lower()
        if not is_area and kind in _COARSE_PHOTON:
            continue
        coords = (ft.get("geometry") or {}).get("coordinates") or [None, None]
        lon, lat = coords[0], coords[1]
        if lat is None or lon is None:
            continue
        cands.append(((pr.get("city") or pr.get("name") or ""), kind, float(lat), float(lon)))
    if not cands:
        return None
    if city:                                          # prefer a candidate in the claimed city
        cl = city.lower()
        cands.sort(key=lambda c: cl in c[0].lower() or (c[0] and c[0].lower() in cl), reverse=True)
    _, kind, lat, lon = cands[0]
    return {"lat": lat, "lng": lon, "source": "photon", "confidence": _confidence(kind, is_area)}


def _confidence(kind: str, is_area: bool) -> str:
    if is_area:
        return "area"
    if kind in {"city", "town", "village", "municipality", "locality", "district"}:
        return "town"
    return "poi"
