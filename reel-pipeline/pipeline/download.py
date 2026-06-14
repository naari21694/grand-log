"""Grab the reel: yt-dlp primary to gallery-dl fallback. Returns video + caption + handle.

Instagram is the #1 fragility (login-walled): set YTDLP_COOKIES_BROWSER to a logged-in
browser profile of a THROWAWAY account, and keep yt-dlp updated.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import config, security


@dataclass
class Media:
    video: str
    caption: str
    handle: str


def _ydl_opts() -> dict:
    opts = {
        "outtmpl": str(config.WORKDIR / "%(id)s.%(ext)s"),
        "format": "mp4/bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True, "no_warnings": True, "noprogress": True,
    }
    if config.YTDLP_COOKIES_BROWSER:
        opts["cookiesfrombrowser"] = (config.YTDLP_COOKIES_BROWSER,)
    return opts


def _resolve(path: str) -> str:
    p = Path(path)
    if p.exists():
        return str(p)
    cand = sorted(Path(config.WORKDIR).glob(p.stem + ".*"))
    return str(cand[-1]) if cand else path


def fetch_meta(url: str) -> Media:
    """Caption and handle only, no media download (yt-dlp metadata). The caption-first path."""
    if not security.is_allowed_host(url):
        raise RuntimeError(f"refusing to fetch a disallowed host: {url}")
    import yt_dlp
    with yt_dlp.YoutubeDL({**_ydl_opts(), "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    return Media(
        video="",
        caption=info.get("description") or "",
        handle=info.get("uploader_id") or info.get("uploader") or "",
    )


def fetch(url: str) -> Media:
    if not security.is_allowed_host(url):
        raise RuntimeError(f"refusing to download a disallowed host: {url}")
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=True)
            video = _resolve(ydl.prepare_filename(info))
        return Media(
            video=video,
            caption=info.get("description") or "",
            handle=info.get("uploader_id") or info.get("uploader") or "",
        )
    except Exception as e:
        return _gallery_dl(url, e)


def _gallery_dl(url: str, prev_err: Exception) -> Media:
    cmd = ["gallery-dl", "-D", str(config.WORKDIR), "--write-metadata"]
    if config.YTDLP_COOKIES_BROWSER:
        cmd += ["--cookies-from-browser", config.YTDLP_COOKIES_BROWSER]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp failed ({prev_err}); gallery-dl also failed:\n{r.stderr[:500]}")
    vids = sorted(Path(config.WORKDIR).glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not vids:
        raise RuntimeError("gallery-dl downloaded no mp4")
    caption, handle = "", ""
    metas = sorted(Path(config.WORKDIR).glob("*.json"), key=lambda p: p.stat().st_mtime)
    if metas:
        m = json.loads(metas[-1].read_text(encoding="utf-8"))
        caption = m.get("description") or m.get("caption") or ""
        handle = m.get("username") or m.get("uploader_id") or ""
    return Media(video=str(vids[-1]), caption=caption, handle=handle)
