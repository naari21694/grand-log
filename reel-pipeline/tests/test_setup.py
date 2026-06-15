"""Setup wizard: the pure .env rendering. The interactive prompts are not unit-tested."""
from pipeline import setup


def test_render_env_keeps_set_values():
    body = setup.render_env({"BRAIN_PROVIDER": "gemini", "GEMINI_API_KEY": "k"})
    assert "BRAIN_PROVIDER=gemini\n" in body
    assert "GEMINI_API_KEY=k\n" in body


def test_render_env_skips_empty_values():
    body = setup.render_env({"BRAIN_PROVIDER": "gemini", "TELEGRAM_BOT_TOKEN": ""})
    assert "TELEGRAM_BOT_TOKEN" not in body


def test_provider_key_map_covers_the_three_providers():
    assert set(setup._PROVIDER_KEY) == {"gemini", "openai", "anthropic"}
