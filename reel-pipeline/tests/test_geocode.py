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
