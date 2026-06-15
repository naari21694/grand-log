"""Doctor preflight: ffmpeg is mandatory only in full mode, advisory in auto/caption."""
from pipeline import config, doctor


def _set(monkeypatch, **kw):
    for key, value in kw.items():
        monkeypatch.setattr(config, key, value)


def test_full_mode_requires_ffmpeg(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _: None)  # ffmpeg missing
    _set(monkeypatch, CAPTURE_MODE="full", BRAIN_PROVIDER="gemini", GEMINI_API_KEY="k")
    assert doctor.check() is False


def test_caption_mode_ffmpeg_is_optional(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _: None)  # ffmpeg missing
    _set(monkeypatch, CAPTURE_MODE="caption", BRAIN_PROVIDER="gemini", GEMINI_API_KEY="k")
    assert doctor.check() is True


def test_brain_key_still_gates_in_caption_mode(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _: None)
    _set(monkeypatch, CAPTURE_MODE="caption", BRAIN_PROVIDER="gemini", GEMINI_API_KEY="")
    assert doctor.check() is False
