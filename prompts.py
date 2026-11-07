"""Two prompt versions to compare.

v1 = casual prompt with only a vague format hint.
v2 = strict prompt with an explicit system message and exact format rules.
"""

SHORT_HINT = {
    "json": "Answer in JSON.",
    "bullets": "Use bullet points.",
    "one_sentence": "Keep it short.",
    "max_words": "Keep it brief.",
    "number_only": "Just give the number.",
}


def strict_instruction(spec: dict) -> str:
    t = spec["type"]
    if t == "json":
        keys = " and ".join(f'"{k}"' for k in spec["keys"])
        return (f"Respond ONLY with a valid JSON object with exactly the keys {keys}. "
                "No markdown, no code fences, no text outside the JSON.")
    if t == "bullets":
        return (f"Respond with exactly {spec['count']} bullet points, each starting with '- '. "
                "No introduction and no conclusion.")
    if t == "one_sentence":
        return "Respond in exactly one sentence."
    if t == "max_words":
        return f"Respond in at most {spec['limit']} words."
    if t == "number_only":
        return "Respond with only the number: no words, no units, no punctuation."
    raise ValueError(f"unknown format type: {t}")


def build_messages(version: str, item: dict) -> list:
    if version == "v1":
        text = f"{item['question']} {SHORT_HINT[item['format']['type']]}"
        return [{"role": "user", "content": text}]
    if version == "v2":
        system = ("You are a precise assistant. Answer factually and follow the "
                  "requested output format exactly. Never add extra text.")
        user = f"{item['question']}\n\n{strict_instruction(item['format'])}"
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]
    raise ValueError("prompt version 'v1' ya 'v2' hona chahiye")
