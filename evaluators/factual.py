"""Check 1: Factual consistency against a reference answer.

The reference may contain alternatives separated by '|'
(e.g. "Canberra" or "carbon dioxide|CO2"). Any alternative that appears in the
response counts. If there is no exact match, a fuzzy match (typos, plurals)
is used for references with 5+ characters.
"""
import re

from rapidfuzz import fuzz

from .utils import try_parse_json

NAME = "factual"
PASS_THRESHOLD = 0.85


def normalize(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"(?<=\d),(?=\d)", "", text)      # 1,024 -> 1024
    text = re.sub(r"[^a-z0-9\s.]", " ", text)       # drop punctuation
    text = re.sub(r"\.(?!\d)", " ", text)           # keep dots only inside numbers
    text = re.sub(r"(?<!\d)\.", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _response_text(response: str) -> str:
    """If the response is JSON, compare against all its values."""
    parsed = try_parse_json(response)
    if isinstance(parsed, dict):
        return " ".join(str(v) for v in parsed.values())
    return response


def evaluate(item: dict, response: str) -> dict:
    answer = normalize(_response_text(response))
    padded = f" {answer} "
    best, matched = 0.0, None

    for ref in item["reference"].split("|"):
        ref_n = normalize(ref)
        if not ref_n:
            continue
        if f" {ref_n} " in padded:
            return {"score": 1.0, "passed": True, "matched": ref.strip()}
        if len(ref_n) >= 5:
            fuzzy = fuzz.partial_ratio(ref_n, answer) / 100
            if fuzzy > best:
                best, matched = fuzzy, ref.strip()

    return {
        "score": round(best, 3),
        "passed": best >= PASS_THRESHOLD,
        "matched": matched if best >= PASS_THRESHOLD else None,
    }
