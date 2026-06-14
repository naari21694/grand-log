"""Unit tests for the provider-agnostic brain: provider dispatch, the validate/repair loop,
and each provider's JSON parsing and key guards. No network calls."""
import pytest
from pipeline import brain, config

RECIPE = {"title": "Miso Soup", "base_servings": 2, "ingredients": [{}], "instructions": ["x"]}


def test_dispatch_gemini(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_PROVIDER", "gemini")
    seen = {}

    def fake(parts):
        seen["p"] = parts
        return dict(RECIPE)

    monkeypatch.setattr(brain, "_gemini", fake)
    out = brain.extract_text("cap", "trans", "url", "chef")
    assert out["title"] == "Miso Soup"
    assert "Return ONLY JSON" in seen["p"][0]["text"]


def test_dispatch_openai(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_PROVIDER", "openai")
    monkeypatch.setattr(brain, "_openai_json", lambda prompt, hint: dict(RECIPE))
    assert brain.extract_text("c", "t", "u", "h")["title"] == "Miso Soup"


def test_dispatch_anthropic(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_PROVIDER", "anthropic")
    monkeypatch.setattr(brain, "_anthropic_json", lambda prompt, sch: dict(RECIPE))
    assert brain.extract_text("c", "t", "u", "h")["base_servings"] == 2


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_PROVIDER", "bogus")
    with pytest.raises(RuntimeError, match="unknown BRAIN_PROVIDER"):
        brain.extract_text("c", "t", "u", "h")


def test_validate_flags_missing_and_enum():
    errs = brain._validate(
        {"category": "nope"},
        {"required": ["name"], "properties": {"category": {"enum": ["food", "see"]}}})
    assert any("name" in e for e in errs)
    assert any("category" in e for e in errs)


def test_repair_runs_once_on_invalid(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_PROVIDER", "gemini")
    calls = {"n": 0}

    def fake(parts):
        calls["n"] += 1
        return {"title": "X"} if calls["n"] == 1 else dict(RECIPE)  # invalid, then valid

    monkeypatch.setattr(brain, "_gemini", fake)
    out = brain.extract_text("c", "t", "u", "h")
    assert calls["n"] == 2 and out["base_servings"] == 2


def test_gemini_requires_key(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        brain._gemini([{"text": "hi"}])


def test_gemini_parses(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "k")

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": '{"a": 1}'}]}}]}

    monkeypatch.setattr(brain.requests, "post", lambda *a, **k: _Resp())
    assert brain._gemini([{"text": "x"}]) == {"a": 1}


def test_gemini_blocked(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "k")

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"promptFeedback": {"blockReason": "SAFETY"}}

    monkeypatch.setattr(brain.requests, "post", lambda *a, **k: _Resp())
    with pytest.raises(RuntimeError, match="no usable candidate"):
        brain._gemini([{"text": "x"}])


def test_openai_requires_key_for_openai_host(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(config, "OPENAI_BASE_URL", "https://api.openai.com/v1")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        brain._openai_json("p", "hint")


def test_openai_allows_local_without_key(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(config, "OPENAI_BASE_URL", "http://localhost:11434/v1")

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": '{"a": 1}'}}]}

    monkeypatch.setattr(brain.requests, "post", lambda *a, **k: _Resp())
    assert brain._openai_json("p", "hint") == {"a": 1}


def test_vision_auto_prefers_gemini(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_VISION", "auto")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    assert brain._vision_provider() == "gemini"
    assert brain.vision_available()


def test_vision_none_when_no_keys(monkeypatch):
    monkeypatch.setattr(config, "BRAIN_VISION", "auto")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    assert brain._vision_provider() == "none"
    assert not brain.vision_available()
