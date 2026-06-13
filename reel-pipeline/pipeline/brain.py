"""The swappable brain.

text  : claude_p (your Claude Code CLI + Max credit, strict --json-schema) | gemini
vision: gemini free tier (multimodal) | none

Why split: `claude -p`'s image input is unreliable, so overlay frames go through a
real multimodal API (Gemini free). Swap either side with one env var.
"""
from __future__ import annotations
import base64
import json
import shutil
import subprocess

import requests

from . import config, schema


# ---------------- text pass ----------------
def extract_text(caption: str, transcript: str, url: str, handle: str) -> dict:
    prompt = schema.TEXT_PROMPT.format(
        url=url, handle=handle, caption=caption[:8000], transcript=transcript[:12000])
    if config.BRAIN_TEXT == "gemini":
        return _gemini([{"text": prompt + "\n\nReturn ONLY JSON for this schema:\n" + schema.SCHEMA_HINT}])
    return _claude(prompt, schema.RECIPE_SCHEMA)


def _claude(prompt: str, json_schema: dict) -> dict:
    exe = shutil.which(config.CLAUDE_BIN) or config.CLAUDE_BIN
    cmd = [exe, "-p", prompt, "--output-format", "json", "--json-schema", json.dumps(json_schema)]
    if config.CLAUDE_MODEL:
        cmd += ["--model", config.CLAUDE_MODEL]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"claude -p failed: {(r.stderr or r.stdout)[:400]}")
    env = json.loads(r.stdout)
    if isinstance(env.get("structured_output"), dict):
        return env["structured_output"]
    res = env.get("result", env)
    return json.loads(res) if isinstance(res, str) else res


# ---------------- vision pass ----------------
def vision_available() -> bool:
    return config.BRAIN_VISION == "gemini" and bool(config.GEMINI_API_KEY)


def extract_vision(frames: list[str], recipe: dict, missing: list[str]) -> dict:
    if not vision_available() or not frames:
        return recipe
    parts = [{"text": schema.VISION_PROMPT.format(
        recipe_json=json.dumps(recipe, ensure_ascii=False),
        missing=", ".join(missing), schema_hint=schema.SCHEMA_HINT)}]
    for fp in frames:
        with open(fp, "rb") as fh:
            parts.append({"inline_data": {"mime_type": "image/jpeg",
                                          "data": base64.b64encode(fh.read()).decode()}})
    try:
        return {**recipe, **_gemini(parts)}
    except Exception as e:
        print(f"   ⚠ vision pass failed ({e}); keeping text-only recipe")
        return recipe


def _gemini(parts: list) -> dict:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}")
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"response_mime_type": "application/json"}}
    r = requests.post(url, json=body, timeout=300)
    r.raise_for_status()
    txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(txt)
