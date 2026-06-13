"""Sample frames for the vision pass via ffmpeg scene-change detection.

Recipes swap overlay cards on cuts, so scene detection grabs each distinct text card
while skipping redundant frames; falls back to time-sampling for continuous shots.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import config


def _ff() -> str:
    return shutil.which(config.FFMPEG) or config.FFMPEG


def sample(video: str, threshold: float = 0.3, max_frames: int = 8) -> list[str]:
    d = Path(config.WORKDIR) / (Path(video).stem + "_frames")
    d.mkdir(exist_ok=True)
    for f in d.glob("*.jpg"):
        f.unlink()
    patt = str(d / "f_%03d.jpg")

    subprocess.run([_ff(), "-y", "-i", video, "-vf",
                    f"select='gt(scene,{threshold})',scale=1280:-1",
                    "-vsync", "vfr", "-frames:v", str(max_frames), patt], capture_output=True)
    out = sorted(d.glob("*.jpg"))

    if len(out) < 2:  # no hard cuts to time-sample one frame / 2s
        for f in out:
            f.unlink()
        subprocess.run([_ff(), "-y", "-i", video, "-vf", "fps=1/2,scale=1280:-1",
                        "-vsync", "vfr", "-frames:v", str(max_frames), patt], capture_output=True)
        out = sorted(d.glob("*.jpg"))

    return [str(p) for p in out[:max_frames]]


def grab_one(video: str, ts: str = "00:00:01") -> str | None:
    p = str(Path(config.WORKDIR) / (Path(video).stem + "_thumb.jpg"))
    subprocess.run([_ff(), "-y", "-ss", ts, "-i", video, "-frames:v", "1",
                    "-vf", "scale=1080:-1", p], capture_output=True)
    return p if Path(p).exists() else None
