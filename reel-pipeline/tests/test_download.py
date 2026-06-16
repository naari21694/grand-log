"""Unit tests for the download host-guard (SSRF defense in depth): fetch and fetch_meta both
reject a disallowed host before any network work, so yt-dlp is never reached. No network."""
import pytest
from pipeline import download


def test_fetch_rejects_disallowed_host():
    with pytest.raises(RuntimeError, match="refusing to download"):
        download.fetch("https://evil.example.com/x")


def test_fetch_meta_rejects_disallowed_host():
    with pytest.raises(RuntimeError, match="refusing to fetch"):
        download.fetch_meta("https://evil.example.com/x")


def test_fetch_guard_runs_before_yt_dlp(monkeypatch):
    """The host check must short-circuit ahead of any download work."""
    monkeypatch.setattr(download.security, "is_allowed_host", lambda url: False)

    def boom(*a, **k):
        raise AssertionError("download work ran before the host guard")

    monkeypatch.setattr(download, "_ydl_opts", boom)
    with pytest.raises(RuntimeError, match="refusing to download"):
        download.fetch("https://instagram.com/reel/abc/")


def test_fetch_meta_guard_runs_before_yt_dlp(monkeypatch):
    monkeypatch.setattr(download.security, "is_allowed_host", lambda url: False)

    def boom(*a, **k):
        raise AssertionError("metadata work ran before the host guard")

    monkeypatch.setattr(download, "_ydl_opts", boom)
    with pytest.raises(RuntimeError, match="refusing to fetch"):
        download.fetch_meta("https://instagram.com/reel/abc/")
