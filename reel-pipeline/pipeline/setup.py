"""Setup wizard: python -m pipeline.setup

Asks a few questions, writes reel-pipeline/.env, then runs the doctor. No hand-editing.
Never echoes secret values back, and will not overwrite an existing .env without consent.
"""
from __future__ import annotations

from pathlib import Path

from . import doctor

_ENV = Path(__file__).resolve().parent.parent / ".env"  # reel-pipeline/.env

_PROVIDER_KEY = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def render_env(values: dict) -> str:
    """Render a .env body from name->value, skipping empty values. Pure and testable."""
    return "".join(f"{k}={v}\n" for k, v in values.items() if v)


def _ask(prompt: str, default: str = "") -> str:
    answer = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return answer or default


def main() -> None:
    print("Grand Log setup\n")
    if _ENV.exists() and _ask("A .env already exists. Overwrite? (y/N)", "N").lower() != "y":
        print("Keeping the existing .env. Running the doctor.\n")
        raise SystemExit(0 if doctor.check() else 1)

    provider = _ask("Brain provider (gemini/openai/anthropic)", "gemini").lower()
    if provider not in _PROVIDER_KEY:
        provider = "gemini"
    values = {
        "BRAIN_PROVIDER": provider,
        _PROVIDER_KEY[provider]: _ask(f"{provider} API key"),
        "TELEGRAM_BOT_TOKEN": _ask("Telegram bot token (optional, from @BotFather)"),
    }
    _ENV.write_text(render_env(values), encoding="utf-8")
    print(f"\nWrote {_ENV.name}. Running the doctor.\n")
    raise SystemExit(0 if doctor.check() else 1)


if __name__ == "__main__":
    main()
