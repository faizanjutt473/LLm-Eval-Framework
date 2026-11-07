"""Check 3: LLM-as-judge with a clear 1-5 rubric."""
import json
import re

import llm_client

NAME = "judge"

RUBRIC = """\
correctness (most important)
  5 = fully correct, matches the reference
  4 = correct, minor imprecision or extra unneeded detail
  3 = partially correct or incomplete
  2 = mostly wrong
  1 = wrong or contradicts the reference
relevance
  5 = directly answers the question, 3 = partly off-topic, 1 = unrelated
clarity
  5 = clear and concise, 3 = understandable but wordy or awkward, 1 = confusing
overall (1-5)
  your overall quality score; correctness should drive it (about 60%),
  relevance 20%, clarity 20%."""

SYSTEM_PROMPT = f"""You are a strict and impartial evaluator of LLM answers.
Score the ANSWER on this rubric using integers 1-5:
{RUBRIC}

Do NOT penalise the answer for output format (a separate check handles that).
Respond with ONLY a JSON object and nothing else:
{{"correctness": int, "relevance": int, "clarity": int, "overall": int, "reason": "one short sentence"}}"""

_KEYS = ("correctness", "relevance", "clarity", "overall")


def _parse(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        scores = {k: int(data[k]) for k in _KEYS}
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None
    if any(not 1 <= v <= 5 for v in scores.values()):
        return None
    scores["reason"] = str(data.get("reason", ""))
    return scores


def evaluate(item: dict, response: str, judge_model: str, attempts: int = 3) -> dict:
    user_prompt = (
        f"QUESTION:\n{item['question']}\n\n"
        f"REFERENCE ANSWER:\n{item['reference'].replace('|', ' / ')}\n\n"
        f"ANSWER TO EVALUATE:\n{response}"
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    for attempt in range(attempts):
        # slightly higher temperature on retry so a bad cached reply is not reused
        raw = llm_client.chat(judge_model, messages, temperature=0.3 * attempt, max_tokens=200)
        scores = _parse(raw)
        if scores:
            return scores
    return {"correctness": None, "relevance": None, "clarity": None, "overall": None, "reason": "judge output parse nahi hua"}
