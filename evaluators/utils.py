"""Shared helper functions for the evaluators."""
import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def strip_fences(text: str) -> str:
    """Remove a surrounding ```json ... ``` markdown fence if present."""
    text = text.strip()
    match = _FENCE_RE.match(text)
    return match.group(1).strip() if match else text


def try_parse_json(text: str):
    """Return parsed JSON or None if the text is not valid JSON."""
    try:
        return json.loads(strip_fences(text))
    except (json.JSONDecodeError, TypeError):
        return None
