"""Preflight check: python -m pipeline.doctor

Tells you exactly what is in place and what is missing before you run anything. Required
checks gate the exit code; optional checks (bot, Mealie) are advisory.
"""
from __future__ import annotations

import shutil
import sys

from . import config


def _line(label: str, ok: bool, detail: str = "") -> bool:
    mark = "OK " if ok else "XX"
    print(f"  [{mark}] {label}" + (f"  ->  {detail}" if detail else ""))
    return ok


def _brain_ok() -> bool:
    provider = config.BRAIN_PROVIDER
    if provider == "gemini":
        return _line("brain: gemini key", bool(config.GEMINI_API_KEY),
                     "set GEMINI_API_KEY (free at aistudio.google.com)")
    if provider == "openai":
        local = "api.openai.com" not in config.OPENAI_BASE_URL
        return _line("brain: openai-compatible", bool(config.OPENAI_API_KEY) or local,
                     f"{config.OPENAI_BASE_URL} model={config.OPENAI_MODEL}")
    if provider == "anthropic":
        try:
            import anthropic  # noqa: F401
            sdk = True
        except ImportError:
            sdk = False
        key = _line("brain: anthropic key", bool(config.ANTHROPIC_API_KEY), "set ANTHROPIC_API_KEY")
        sdk_ok = _line("brain: anthropic SDK", sdk, "pip install anthropic")
        return key and sdk_ok
    return _line("brain: known provider", False,
                 f"BRAIN_PROVIDER={provider!r}; use gemini, openai, or anthropic")


def _workdir_ok() -> bool:
    try:
        probe = config.WORKDIR / ".doctor"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except Exception:
        return False


def check() -> bool:
    print("Grand Log doctor\n")
    # ffmpeg is mandatory only in full mode. auto/caption read the caption first and pull
    # the video (needing ffmpeg) only when a caption is thin, so there it is advisory.
    full_mode = config.CAPTURE_MODE == "full"
    ffmpeg_label = "ffmpeg on PATH" if full_mode else f"ffmpeg on PATH (optional in {config.CAPTURE_MODE} mode)"
    ffmpeg_detail = config.FFMPEG if full_mode else "needed only if a reel falls back to video; required for CAPTURE_MODE=full"
    ffmpeg_line = _line(ffmpeg_label, bool(shutil.which(config.FFMPEG)), ffmpeg_detail)
    required = [_brain_ok(), _line("work/ writable", _workdir_ok(), str(config.WORKDIR))]
    if full_mode:
        required.append(ffmpeg_line)

    # Advisory: needed only for the bot and the cookbook destination.

    # Advisory: needed only for the bot and the cookbook destination.
    locked = bool(config.ALLOWED_CHAT_IDS) or config.ALLOW_ALL_CHATS
    _line("bot access control", locked, "set ALLOWED_CHAT_IDS to lock the bot to you")
    _line("telegram token (optional)", bool(config.TELEGRAM_BOT_TOKEN),
          "set TELEGRAM_BOT_TOKEN to run the bot (from @BotFather)")
    if config.MEALIE_URL:
        reachable = False
        try:
            import requests
            reachable = requests.get(config.MEALIE_URL + "/api/app/about", timeout=10).ok
        except Exception:
            reachable = False
        _line("mealie reachable (optional)", reachable, config.MEALIE_URL)

    ok = all(required)
    print("\nAll required checks passed." if ok else "\nSome required checks failed (see above).")
    return ok


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
