"""Unit tests for frame sampling: scene-detect first, fall back to time-sampling when there
are no hard cuts, and cap the frame count. ffmpeg is stubbed, so no video and no binary."""
from pathlib import Path

from pipeline import config, frames


def _writer(n):
    """A fake subprocess.run that drops n jpgs at the ffmpeg output pattern's directory."""
    def run(cmd, **kw):
        out_dir = Path(cmd[-1]).parent
        for i in range(n):
            (out_dir / f"f_{i:03d}.jpg").write_bytes(b"x")
    return run


def test_sample_caps_returned_frames(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WORKDIR", str(tmp_path))
    monkeypatch.setattr(frames.subprocess, "run", _writer(5))
    got = frames.sample("clip.mp4", max_frames=3)
    assert len(got) == 3
    assert all(p.endswith(".jpg") for p in got)


def test_sample_falls_back_to_time_sampling(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WORKDIR", str(tmp_path))
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        out_dir = Path(cmd[-1]).parent
        n = 1 if len(calls) == 1 else 3  # one frame first -> triggers the fallback
        for i in range(n):
            (out_dir / f"f_{i:03d}.jpg").write_bytes(b"x")

    monkeypatch.setattr(frames.subprocess, "run", run)
    got = frames.sample("clip.mp4")
    assert len(calls) == 2  # scene-detect, then time-sample
    assert "fps=1/2" in " ".join(calls[1])
    assert len(got) == 3


def test_grab_one_returns_path_when_written(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WORKDIR", str(tmp_path))
    monkeypatch.setattr(frames.subprocess, "run",
                        lambda cmd, **kw: Path(cmd[-1]).write_bytes(b"x"))
    assert frames.grab_one("clip.mp4").endswith("_thumb.jpg")


def test_grab_one_returns_none_when_no_frame(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WORKDIR", str(tmp_path))
    monkeypatch.setattr(frames.subprocess, "run", lambda *a, **k: None)
    assert frames.grab_one("clip.mp4") is None
