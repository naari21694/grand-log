"""Audio to text. Default backend faster-whisper (pip, cross-platform, great for dev/Windows).
whisper.cpp backend is the ARM-prod optimization (set WHISPER_CPP_BIN/MODEL).

Multilingual: language is auto-detected per clip. Failure is non-fatal, we fall back to
caption-only extraction.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import config

_model = None  # lazy-loaded faster-whisper model, reused across reels


def _ff() -> str:
    return shutil.which(config.FFMPEG) or config.FFMPEG


def _to_wav(video: str) -> str:
    wav = str(Path(video).with_suffix(".wav"))
    subprocess.run([_ff(), "-y", "-i", video, "-ar", "16000", "-ac", "1",
                    "-c:a", "pcm_s16le", wav], capture_output=True)
    return wav


def run(video: str) -> str:
    try:
        wav = _to_wav(video)
        if config.TRANSCRIBE_BACKEND == "whisper_cpp":
            return _whisper_cpp(wav)
        return _faster_whisper(wav)
    except Exception as e:
        print(f"   ⚠ transcription skipped ({e}); using caption only")
        return ""


def _faster_whisper(wav: str) -> str:
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _ = _model.transcribe(wav, language=None, vad_filter=True)
    return " ".join(s.text.strip() for s in segments).strip()


def _whisper_cpp(wav: str) -> str:
    if not config.WHISPER_CPP_BIN:
        raise RuntimeError("WHISPER_CPP_BIN not set")
    out = str(Path(wav).with_suffix(""))
    subprocess.run([config.WHISPER_CPP_BIN, "-m", config.WHISPER_CPP_MODEL, "-f", wav,
                    "-l", "auto", "-t", "4", "-oj", "-of", out], capture_output=True, check=True)
    data = json.loads(Path(out + ".json").read_text(encoding="utf-8"))
    return " ".join(seg["text"].strip() for seg in data.get("transcription", [])).strip()
