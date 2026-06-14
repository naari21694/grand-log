"""Unit tests for the security gate: the download host allow-list (SSRF defense) and the
bot chat allow-list. Pure functions, no Telegram, no network."""
from pipeline import config, security


def test_is_allowed_host_accepts_known_sites():
    assert security.is_allowed_host("https://www.instagram.com/reel/abc/")
    assert security.is_allowed_host("https://instagram.com/reel/abc/")
    assert security.is_allowed_host("https://vt.tiktok.com/xyz/")  # subdomain
    assert security.is_allowed_host("https://youtu.be/xyz")


def test_is_allowed_host_rejects_others():
    assert not security.is_allowed_host("https://evil.example.com/x")
    assert not security.is_allowed_host("http://localhost:8080/admin")
    assert not security.is_allowed_host("file:///etc/passwd")
    assert not security.is_allowed_host("not a url")
    assert not security.is_allowed_host("https://instagram.com.evil.com/x")  # suffix trick


def test_first_allowed_url_picks_supported_and_trims():
    text = "look at this (https://www.instagram.com/reel/abc/)."
    assert security.first_allowed_url(text) == "https://www.instagram.com/reel/abc/"


def test_first_allowed_url_skips_unsupported():
    assert security.first_allowed_url("see https://evil.example.com/x") is None
    assert security.first_allowed_url("no link here") is None


def test_allowed_hosts_override_replaces_defaults(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_HOSTS", ("example.com",))
    assert security.is_allowed_host("https://example.com/x")
    assert not security.is_allowed_host("https://instagram.com/x")


def test_chat_allowlist(monkeypatch):
    monkeypatch.setattr(config, "ALLOW_ALL_CHATS", False)
    monkeypatch.setattr(config, "ALLOWED_CHAT_IDS", {42})
    assert security.is_allowed_chat(42)
    assert not security.is_allowed_chat(7)


def test_allow_all_chats(monkeypatch):
    monkeypatch.setattr(config, "ALLOW_ALL_CHATS", True)
    monkeypatch.setattr(config, "ALLOWED_CHAT_IDS", set())
    assert security.is_allowed_chat(999)
