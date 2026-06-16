import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest
from pipeline import config, store, web


def _fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_DB", tmp_path / "items.db")
    store.init_db()


def test_items_payload_lists_saved(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    store.save(bucket="recipe", title="Miso", summary="serves 2", link="http://x", thumb="t.jpg")
    payload = web._items_payload()
    assert payload[0]["title"] == "Miso"
    assert payload[0]["crew"] == "Baratie"
    assert payload[0]["has_thumb"] is True


def test_items_payload_search(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    store.save(bucket="place", title="Ichiran", text="tonkotsu ramen")
    assert web._items_payload("tonkotsu")
    assert web._items_payload("nope") == []


def test_page_is_self_contained():
    assert "Grand Log" in web._PAGE
    assert "/api/items" in web._PAGE


@pytest.fixture
def server(tmp_path, monkeypatch):
    """A real dashboard server on an ephemeral loopback port, token-gated. No external network."""
    _fresh(tmp_path, monkeypatch)
    monkeypatch.setattr(config, "DASHBOARD_TOKEN", "s3cret")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), web._Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _status(url):
    try:
        with urlopen(url, timeout=5) as resp:
            return resp.status
    except HTTPError as exc:
        return exc.code


def test_do_get_rejects_missing_token(server):
    assert _status(server + "/") == 401


def test_do_get_rejects_wrong_token(server):
    assert _status(server + "/?token=nope") == 401


def test_do_get_accepts_right_token(server):
    assert _status(server + "/?token=s3cret") == 200


def test_do_get_unknown_path_is_404_with_right_token(server):
    assert _status(server + "/nope?token=s3cret") == 404
