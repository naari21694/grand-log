"""The recipe schema and extraction prompts.

RECIPE_SCHEMA is sent to whichever brain provider is configured (Gemini, an OpenAI-compatible
API, or Anthropic) and the returned JSON is validated against it. Quantities are captured for `base_servings`;
Mealie's native serving-scaler then renders 1/2/4/6/10 (or any N). `scaling_notes` carries the
non-linear guidance Mealie can't compute (salt, spice, leavening, time, pan).
"""
import json

RECIPE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string", "description": "1-2 sentence summary."},
        "cuisine": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"},
                 "description": "diet, meal type, method, e.g. vegetarian, dessert, no-bake"},
        "total_time_min": {"type": "integer"},
        "prep_time_min": {"type": "integer"},
        "cook_time_min": {"type": "integer"},
        "base_servings": {"type": "integer", "description": "Yield the reel states; if none, use 2."},
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "number", "description": "Amount for base_servings. 0 if unknown."},
                    "unit": {"type": "string", "description": "g, ml, cup, tbsp, tsp, piece, '' for count."},
                    "food": {"type": "string"},
                    "grams": {"type": "number", "description": "Canonical mass at base_servings if sensibly weighable, else 0."},
                    "note": {"type": "string", "description": "prep note / original-language name / 'to taste'."},
                    "optional": {"type": "boolean"},
                },
                "required": ["quantity", "unit", "food"],
            },
        },
        "instructions": {"type": "array", "items": {"type": "string"}},
        "equipment": {"type": "array", "items": {"type": "string"}},
        "nutrition_per_serving": {
            "type": "object",
            "properties": {
                "calories": {"type": "number"}, "protein_g": {"type": "number"},
                "fat_g": {"type": "number"}, "carbs_g": {"type": "number"},
                "fiber_g": {"type": "number"}, "sodium_mg": {"type": "number"},
                "sugar_g": {"type": "number"},
            },
        },
        "scaling_notes": {"type": "string",
                          "description": "Concrete non-linear scaling guidance: which lines don't scale linearly "
                                         "(salt/spices/seasoning, leavening/yeast) and how cook time, pan/tray size and "
                                         "evaporation change for bigger batches."},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "confidence_notes": {"type": "string"},
        "missing_quantities": {"type": "array", "items": {"type": "string"},
                               "description": "Food names whose quantity was never stated, triggers the vision pass."},
    },
    "required": ["title", "base_servings", "ingredients", "instructions"],
}

SCHEMA_HINT = json.dumps(RECIPE_SCHEMA)

TEXT_PROMPT = """You are a meticulous recipe extractor. From the Instagram reel's CAPTION and AUDIO TRANSCRIPT below, produce ONE recipe as JSON matching the schema.

Rules:
- Extract EXACT quantities and units as stated. NEVER invent or guess a quantity. If a quantity is never stated, still list the ingredient with quantity 0 and add its food name to "missing_quantities" (a later pass will read it from on-screen text).
- base_servings = the yield the reel states. If none is stated, use 2 and say so in confidence_notes.
- All ingredient quantities are for base_servings.
- Set "grams" to that ingredient's weight at base_servings when reasonably known (flour, sugar, butter, liquids, etc.); use 0 for things like "1 egg" or "to taste". Keep the human-friendly unit/quantity too.
- Translate non-English content to English; keep a notable original name in "note".
- "scaling_notes" is the MOST important field. Be specific about what breaks when scaling up or down: salt, spices, seasoning, and leavening (baking powder, soda, yeast) are non-linear. Note how cook time, pan or tray size, and liquid for evaporation change for larger batches.
- "nutrition_per_serving" = best estimate PER SINGLE SERVING.
- "confidence" + "confidence_notes": flag ambiguities (e.g. "amounts only shown on screen, not spoken").

SOURCE_URL: {url}
CREATOR: {handle}

CAPTION:
{caption}

TRANSCRIPT:
{transcript}
"""

VISION_PROMPT = """You are reading ON-SCREEN TEXT from frames of a cooking reel to FILL MISSING ingredient quantities.

Recipe extracted so far from caption+audio (some quantities are 0 / missing):
{recipe_json}

Quantities still missing are for: {missing}

Read the quantities/units shown as on-screen text in the attached frames and return the COMPLETE corrected recipe as JSON (same schema). Only change quantities you can actually read; leave truly-unknown ones at 0 and keep them in missing_quantities. Keep every other field intact.

Schema:
{schema_hint}
"""

# ----- Log Pose (places) -----
PLACE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "category": {"type": "string", "enum": ["food", "see", "do", "buy", "try", "stay", "other"]},
        "region": {"type": "string", "description": "Broad area, e.g. Tokyo, Kansai, Hokkaido."},
        "city": {"type": "string"},
        "country": {"type": "string"},
        "address": {"type": "string"},
        "price": {"type": "string", "description": "rough price level or amount if stated"},
        "why": {"type": "string", "description": "one line on what the reel says is worth it"},
        "lat": {"type": "number"},
        "lng": {"type": "number"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["name", "category"],
}

PLACE_SCHEMA_HINT = json.dumps(PLACE_SCHEMA)

PLACE_PROMPT = """You are extracting ONE place to remember from an Instagram reel's caption and transcript.

Return JSON matching the schema.
- name: the specific place (restaurant, shop, viewpoint, neighbourhood). If the reel covers several, pick the main one.
- category: food, see, do, buy, try, stay, or other.
- region, city, country, address: as stated. Leave blank if unknown. Do NOT invent an address.
- lat, lng: only if explicitly stated, else 0. A geocoder fills them later.
- why: one line on what the reel says is worth it.
- confidence: high, medium, low.

SOURCE_URL: {url}
CREATOR: {handle}

CAPTION:
{caption}

TRANSCRIPT:
{transcript}
"""

# ----- Going Merry (home and build-together ideas) -----
HOME_SCHEMA = {
    "type": "object",
    "properties": {
        "item": {"type": "string"},
        "category": {"type": "string",
                     "enum": ["furniture", "decor", "material", "appliance", "lighting", "idea", "other"]},
        "room": {"type": "string", "description": "living, bedroom, kitchen, bath, outdoor, whole-home, other"},
        "price": {"type": "string"},
        "store": {"type": "string", "description": "where to buy, if stated"},
        "link": {"type": "string", "description": "product or source link, if any"},
        "dimensions": {"type": "string"},
        "color": {"type": "string"},
        "why": {"type": "string", "description": "one line on what makes it worth keeping"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["item", "category"],
}

HOME_SCHEMA_HINT = json.dumps(HOME_SCHEMA)

HOME_PROMPT = """You are extracting ONE thing to remember for a home from an Instagram reel's caption and transcript.

Return JSON matching the schema.
- item: the specific thing (a sofa, a paint colour, a shelf, a layout idea).
- category: furniture, decor, material, appliance, lighting, idea, or other.
- room: living, bedroom, kitchen, bath, outdoor, whole-home, or other.
- price, store, link, dimensions, color: as stated. Leave blank if unknown. Do NOT invent a link or price.
- why: one line on what makes it worth keeping.
- confidence: high, medium, low.

SOURCE_URL: {url}
CREATOR: {handle}

CAPTION:
{caption}

TRANSCRIPT:
{transcript}
"""
