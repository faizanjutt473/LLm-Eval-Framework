"""Check 2: Format compliance (pure code, no LLM).

Supported format specs (item["format"]):
  {"type": "json", "keys": ["answer", "reason"]}
  {"type": "bullets", "count": 3}
  {"type": "one_sentence"}
  {"type": "max_words", "limit": 20}
  {"type": "number_only"}
"""
import re

import jsonschema

from .utils import try_parse_json

NAME = "format"
_BULLET_RE = re.compile(r"^([-*\u2022]|\d+[.)])\s+")


def _check_json(spec, response):
    parsed = try_parse_json(response)
    if parsed is None:
        return False, "valid JSON nahi hai"
    schema = {"type": "object", "required": spec["keys"]}
    try:
        jsonschema.validate(parsed, schema)
    except jsonschema.ValidationError as e:
        return False, f"schema fail: {e.message}"
    return True, "ok"


def _check_bullets(spec, response):
    lines = [l.strip() for l in response.splitlines() if l.strip()]
    bullets = [l for l in lines if _BULLET_RE.match(l)]
    extra = [l for l in lines if not _BULLET_RE.match(l)]
    if extra:
        return False, "bullets ke ilawa extra text hai"
    if len(bullets) != spec["count"]:
        return False, f"{len(bullets)} bullets mile, {spec['count']} chahiye the"
    return True, "ok"


def _check_one_sentence(spec, response):
    text = response.strip()
    if "\n" in text:
        return False, "multiple lines hain"
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s]
    if len(sentences) != 1:
        return False, f"{len(sentences)} sentences mile"
    return True, "ok"


def _check_max_words(spec, response):
    words = len(response.split())
    if words > spec["limit"]:
        return False, f"{words} words, limit {spec['limit']}"
    return True, "ok"


def _check_number_only(spec, response):
    if re.fullmatch(r"-?\d[\d,]*(\.\d+)?\.?", response.strip()):
        return True, "ok"
    return False, "sirf number nahi hai"


_CHECKERS = {
    "json": _check_json,
    "bullets": _check_bullets,
    "one_sentence": _check_one_sentence,
    "max_words": _check_max_words,
    "number_only": _check_number_only,
}


def evaluate(item: dict, response: str) -> dict:
    spec = item["format"]
    passed, reason = _CHECKERS[spec["type"]](spec, response)
    return {"score": 1.0 if passed else 0.0, "passed": passed, "reason": reason}
