"""The brain: one schema-locked extraction call, against any provider you have a key for.

text + vision provider, chosen by BRAIN_PROVIDER / BRAIN_VISION:
- gemini     free tier, text + vision in one key (default)
- openai     any OpenAI-compatible endpoint: OpenAI, OpenRouter, Groq, Together, local Ollama
- anthropic  the official SDK; cheapest reliable extraction is Haiku

Every provider returns JSON; `_ensure_valid` checks it against the schema and runs one repair
pass if it is wrong, so even a small free model lands a complete, schema-valid record.
"""
from __future__ import annotations

import base64
import json

import requests

from . import config, schema


# ---------------- public API ----------------
def extract_text(caption: str, transcript: str, url: str, handle: str) -> dict:
    prompt = schema.TEXT_PROMPT.format(
        url=url, handle=handle, caption=caption[:8000], transcript=transcript[:12000])
    return _extract(prompt, schema.RECIPE_SCHEMA, schema.SCHEMA_HINT)


def extract_place(caption: str, transcript: str, url: str, handle: str) -> dict:
    prompt = schema.PLACE_PROMPT.format(
        url=url, handle=handle, caption=caption[:8000], transcript=transcript[:12000])
    return _extract(prompt, schema.PLACE_SCHEMA, schema.PLACE_SCHEMA_HINT)


def extract_home(caption: str, transcript: str, url: str, handle: str) -> dict:
    prompt = schema.HOME_PROMPT.format(
        url=url, handle=handle, caption=caption[:8000], transcript=transcript[:12000])
    return _extract(prompt, schema.HOME_SCHEMA, schema.HOME_SCHEMA_HINT)


# ---------------- auto-router (classify a saved item) ----------------
_BUCKET_SCHEMA = {
    "type": "object",
    "properties": {"bucket": {"type": "string", "enum": ["recipe", "place", "home", "other"]}},
    "required": ["bucket"],
}
_CLASSIFY_PROMPT = """Classify this saved Instagram post into ONE bucket.
- recipe: food, a dish or drink to cook or make
- place: a restaurant, cafe, bar, shop, viewpoint, or travel spot to visit
- home: furniture, decor, materials, or home build and renovation ideas
- other: anything else (art, memes, fashion, fitness, books, quotes, news)

Saved in collection: {name}

Caption:
{caption}

Return JSON for this schema: {schema}"""


def classify(caption: str, name: str = "") -> str:
    """Auto-route a saved item to recipe, place, home, or 'saved' (generic) from its caption."""
    prompt = _CLASSIFY_PROMPT.format(
        name=name or "(none)", caption=caption[:2000], schema=json.dumps(_BUCKET_SCHEMA))
    out = _extract(prompt, _BUCKET_SCHEMA, json.dumps(_BUCKET_SCHEMA))
    bucket = out.get("bucket") if isinstance(out, dict) else None
    return bucket if bucket in ("recipe", "place", "home") else "saved"


# ---------------- text dispatch + repair ----------------
def _extract(prompt: str, json_schema: dict, schema_hint: str) -> dict:
    record = _call_text(prompt, json_schema, schema_hint)
    return _ensure_valid(record, prompt, json_schema, schema_hint)


def _call_text(prompt: str, json_schema: dict, schema_hint: str) -> dict:
    provider = config.BRAIN_PROVIDER
    if provider == "openai":
        return _openai_json(prompt, schema_hint)
    if provider == "anthropic":
        return _anthropic_json(prompt, json_schema)
    if provider == "gemini":
        return _gemini([{"text": f"{prompt}\n\nReturn ONLY JSON for this schema:\n{schema_hint}"}])
    raise RuntimeError(f"unknown BRAIN_PROVIDER {provider!r}; use gemini, openai, or anthropic")


def _validate(record: dict, json_schema: dict) -> list[str]:
    """Cheap schema check: required fields present and non-empty, enum values legal."""
    if not isinstance(record, dict):
        return ["response was not a JSON object"]
    errors: list[str] = []
    for key in json_schema.get("required", []):
        if record.get(key) in (None, "", [], {}):
            errors.append(f"missing required field '{key}'")
    for key, spec in json_schema.get("properties", {}).items():
        value = record.get(key)
        if value not in (None, "") and "enum" in spec and value not in spec["enum"]:
            errors.append(f"field '{key}'={value!r} is not one of {spec['enum']}")
    return errors


def _ensure_valid(record: dict, prompt: str, json_schema: dict, schema_hint: str) -> dict:
    errors = _validate(record, json_schema)
    if not errors:
        return record
    repair = (f"{prompt}\n\nYour previous JSON had these problems:\n- " + "\n- ".join(errors)
              + f"\n\nReturn corrected JSON for this schema, keeping every good field:\n{schema_hint}")
    try:
        fixed = _call_text(repair, json_schema, schema_hint)
    except Exception as exc:  # repair is best-effort; never lose the first extraction
        print(f"   ⚠ repair pass failed ({exc}); keeping best-effort extraction")
        return record
    return fixed if not _validate(fixed, json_schema) else {**record, **fixed}


# ---------------- providers (text) ----------------
def _gemini(parts: list) -> dict:
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Get a free key at aistudio.google.com and put it in .env.")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}")
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"response_mime_type": "application/json"}}
    resp = requests.post(url, json=body, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    try:
        txt = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Gemini returned no usable candidate (blocked or empty): "
                           f"{json.dumps(data)[:400]}")
    return json.loads(txt)


def _openai_json(prompt: str, schema_hint: str) -> dict:
    """Any OpenAI-compatible /chat/completions endpoint. A key is required only for OpenAI itself;
    local Ollama / LM Studio need none."""
    if not config.OPENAI_API_KEY and "api.openai.com" in config.OPENAI_BASE_URL:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it, or point OPENAI_BASE_URL at a "
                           "local or alternative OpenAI-compatible server.")
    headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"} if config.OPENAI_API_KEY else {}
    body = {
        "model": config.OPENAI_MODEL,
        "messages": [{"role": "user",
                      "content": f"{prompt}\n\nReturn ONLY JSON for this schema:\n{schema_hint}"}],
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(f"{config.OPENAI_BASE_URL}/chat/completions",
                         json=body, headers=headers, timeout=300)
    resp.raise_for_status()
    return json.loads(resp.json()["choices"][0]["message"]["content"])


def _anthropic_json(prompt: str, json_schema: dict) -> dict:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Get one at console.anthropic.com.")
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("The anthropic SDK is not installed. Run: pip install anthropic")
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    kwargs = dict(model=config.ANTHROPIC_MODEL, max_tokens=4096,
                  messages=[{"role": "user", "content": f"{prompt}\n\nReturn only JSON."}])
    try:  # strict structured output where the model supports it; fall back to prompt-only JSON
        msg = client.messages.create(
            **kwargs, output_config={"format": {"type": "json_schema", "schema": _strict(json_schema)}})
    except anthropic.BadRequestError:
        msg = client.messages.create(**kwargs)
    txt = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    return json.loads(txt)


def _strict(node):
    """Anthropic strict schemas require additionalProperties:false on every object."""
    if isinstance(node, dict):
        out = {k: _strict(v) for k, v in node.items()}
        if out.get("type") == "object":
            out.setdefault("additionalProperties", False)
        return out
    if isinstance(node, list):
        return [_strict(x) for x in node]
    return node


# ---------------- vision pass (on-screen quantities) ----------------
def _vision_provider() -> str:
    choice = config.BRAIN_VISION
    keyed = {"gemini": config.GEMINI_API_KEY, "openai": config.OPENAI_API_KEY,
             "anthropic": config.ANTHROPIC_API_KEY}
    if choice == "none":
        return "none"
    if choice == "auto":
        return next((p for p in ("gemini", "openai", "anthropic") if keyed[p]), "none")
    return choice if keyed.get(choice) else "none"


def vision_available() -> bool:
    return _vision_provider() != "none"


def extract_vision(frames: list[str], recipe: dict, missing: list[str]) -> dict:
    provider = _vision_provider()
    if provider == "none" or not frames:
        return recipe
    instruction = schema.VISION_PROMPT.format(
        recipe_json=json.dumps(recipe, ensure_ascii=False),
        missing=", ".join(missing), schema_hint=schema.SCHEMA_HINT)
    try:
        if provider == "gemini":
            return {**recipe, **_gemini_vision(instruction, frames)}
        if provider == "openai":
            return {**recipe, **_openai_vision(instruction, frames)}
        return {**recipe, **_anthropic_vision(instruction, frames)}
    except Exception as exc:
        print(f"   ⚠ vision pass failed ({exc}); keeping text-only recipe")
        return recipe


_VISION_HINT = {"recipe": schema.SCHEMA_HINT, "place": schema.PLACE_SCHEMA_HINT,
                "home": schema.HOME_SCHEMA_HINT}


def extract_vision_full(frames: list[str], record: dict, bucket: str) -> dict:
    """Read ALL on-screen text/detail from the frames and merge it into the record, any crew bucket.

    Broader than extract_vision (which only fills missing recipe quantities): captures on-screen
    steps, names, addresses, prices, dimensions, anything the caption missed. Best-effort: a failed
    or keyless vision pass returns the text-only record unchanged.
    """
    provider = _vision_provider()
    if provider == "none" or not frames:
        return record
    instruction = schema.VISION_FULL_PROMPT.format(
        bucket=bucket, record_json=json.dumps(record, ensure_ascii=False),
        schema_hint=_VISION_HINT.get(bucket, schema.SCHEMA_HINT))
    try:
        if provider == "gemini":
            return {**record, **_gemini_vision(instruction, frames)}
        if provider == "openai":
            return {**record, **_openai_vision(instruction, frames)}
        return {**record, **_anthropic_vision(instruction, frames)}
    except Exception as exc:
        print(f"   ⚠ full vision pass failed ({exc}); keeping text-only record")
        return record


def _read(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def _gemini_vision(instruction: str, frames: list[str]) -> dict:
    parts: list = [{"text": instruction}]
    for fp in frames:
        parts.append({"inline_data": {"mime_type": "image/jpeg",
                                      "data": base64.b64encode(_read(fp)).decode()}})
    return _gemini(parts)


def _openai_vision(instruction: str, frames: list[str]) -> dict:
    content: list = [{"type": "text", "text": instruction}]
    for fp in frames:
        b64 = base64.b64encode(_read(fp)).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"} if config.OPENAI_API_KEY else {}
    body = {"model": config.OPENAI_MODEL, "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"}}
    resp = requests.post(f"{config.OPENAI_BASE_URL}/chat/completions",
                         json=body, headers=headers, timeout=300)
    resp.raise_for_status()
    return json.loads(resp.json()["choices"][0]["message"]["content"])


def _anthropic_vision(instruction: str, frames: list[str]) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    content: list = [{"type": "text", "text": instruction}]
    for fp in frames:
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                     "data": base64.b64encode(_read(fp)).decode()}})
    msg = client.messages.create(model=config.ANTHROPIC_MODEL, max_tokens=4096,
                                 messages=[{"role": "user", "content": content}])
    txt = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    return json.loads(txt)
