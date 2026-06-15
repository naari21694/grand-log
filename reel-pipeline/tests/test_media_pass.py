"""Layer 2 prep: the widened full-frame vision pass and the keep-media setting."""
from pipeline import brain, config


def test_vision_full_is_noop_without_a_provider(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_VISION", "none")
    record = {"title": "Karahi"}
    assert brain.extract_vision_full(["frame.jpg"], record, "recipe") == record


def test_vision_full_is_noop_without_frames(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_VISION", "gemini")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "k")
    record = {"name": "Ghibli Museum"}
    assert brain.extract_vision_full([], record, "place") == record


def test_vision_hint_covers_every_crew_bucket():
    assert set(brain._VISION_HINT) == {"recipe", "place", "home"}


def test_keep_media_defaults_to_true():
    assert config.KEEP_MEDIA is True


def test_groq_whisper_backend_is_wired():
    from pipeline import transcribe
    assert hasattr(transcribe, "_groq")
    assert config.GROQ_WHISPER_MODEL  # default model id is set
