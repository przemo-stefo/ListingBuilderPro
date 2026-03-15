# backend/utils/json_extract.py
# Purpose: Extract JSON from LLM responses (handles markdown fences, preamble, truncation)
# NOT for: LLM calling logic (that's llm_providers.py)

import json
import re


def extract_json(text: str) -> dict:
    """Extract JSON object/array from LLM response text.

    WHY: LLMs wrap JSON in markdown fences, add preamble text, or truncate output.
    This handles all common patterns before falling back to substring extraction.
    """
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting outermost { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    # Try extracting outermost [ ... ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON found in LLM response", text, 0)
