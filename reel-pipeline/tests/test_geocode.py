from unittest.mock import patch

from pipeline import geocode


class _Resp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_lookup_returns_coords():
    with patch("pipeline.geocode.requests.get", return_value=_Resp([{"lat": "35.0", "lon": "139.0"}])):
        assert geocode.lookup("Tokyo Tower") == (35.0, 139.0)


def test_lookup_empty_query_returns_none():
    assert geocode.lookup("") is None


def test_lookup_no_hits_returns_none():
    with patch("pipeline.geocode.requests.get", return_value=_Resp([])):
        assert geocode.lookup("nowhere at all") is None


def test_lookup_handles_request_error():
    with patch("pipeline.geocode.requests.get", side_effect=RuntimeError("boom")):
        assert geocode.lookup("x") is None


def _no_sleep(monkeypatch):
    monkeypatch.setattr(geocode.time, "sleep", lambda *_: None)


def test_locate_empty_name_returns_none():
    assert geocode.locate("") is None


def test_locate_returns_nominatim_poi(monkeypatch):
    _no_sleep(monkeypatch)
    monkeypatch.setattr(geocode.requests, "get",
                        lambda *a, **k: _Resp([{"lat": "35.0", "lon": "139.0", "addresstype": "restaurant"}]))
    hit = geocode.locate("Ichiran", "Tokyo", "Japan", "restaurant")
    assert (hit["lat"], hit["lng"]) == (35.0, 139.0)
    assert hit["source"] == "nominatim" and hit["confidence"] == "poi"


def test_locate_constrains_lookup_to_country(monkeypatch):
    _no_sleep(monkeypatch)
    seen = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        seen.update(params or {})
        return _Resp([{"lat": "1", "lon": "2", "addresstype": "cafe"}])

    monkeypatch.setattr(geocode.requests, "get", fake_get)
    geocode.locate("Blue Tokai", "Mumbai", "India", "cafe")
    assert seen.get("countrycodes") == "in"


def test_locate_rejects_country_centroid_and_falls_to_photon(monkeypatch):
    _no_sleep(monkeypatch)

    def fake_get(url, params=None, headers=None, timeout=None):
        if "nominatim" in url:
            return _Resp([{"lat": "22", "lon": "78", "addresstype": "country"}])  # too coarse
        return _Resp({"features": [{"properties": {"countrycode": "IN", "type": "house",
                                                   "city": "Karjat"},
                                    "geometry": {"coordinates": [73.4, 18.9]}}]})

    monkeypatch.setattr(geocode.requests, "get", fake_get)
    hit = geocode.locate("Kondhane Caves", "", "India", "attraction")
    assert hit["source"] == "photon" and (hit["lat"], hit["lng"]) == (18.9, 73.4)


def test_locate_area_category_accepts_centroid(monkeypatch):
    _no_sleep(monkeypatch)
    monkeypatch.setattr(geocode.requests, "get",
                        lambda *a, **k: _Resp([{"lat": "64.9", "lon": "-18.1", "addresstype": "country"}]))
    hit = geocode.locate("Iceland", "", "Iceland", "country")
    assert hit and hit["confidence"] == "area"


def test_locate_photon_prefers_the_claimed_city(monkeypatch):
    _no_sleep(monkeypatch)

    def fake_get(url, params=None, headers=None, timeout=None):
        if "nominatim" in url:
            return _Resp([])  # miss, so Photon is tried
        return _Resp({"features": [
            {"properties": {"countrycode": "IN", "type": "house", "city": "Delhi"},
             "geometry": {"coordinates": [77.2, 28.6]}},
            {"properties": {"countrycode": "IN", "type": "house", "city": "Mumbai"},
             "geometry": {"coordinates": [72.9, 19.1]}},
        ]})

    monkeypatch.setattr(geocode.requests, "get", fake_get)
    hit = geocode.locate("Perch", "Mumbai", "India", "cafe")
    assert (hit["lat"], hit["lng"]) == (19.1, 72.9)  # the Mumbai candidate wins


def test_locate_all_sources_miss_returns_none(monkeypatch):
    _no_sleep(monkeypatch)
    monkeypatch.setattr(geocode.requests, "get",
                        lambda url, **k: _Resp([]) if "nominatim" in url else _Resp({"features": []}))
    assert geocode.locate("Nowhere Cafe", "X", "India", "cafe") is None
