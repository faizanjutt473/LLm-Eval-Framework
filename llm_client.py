"""Thin wrapper around any OpenAI-compatible API, with retry + disk cache."""
import hashlib
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
_client = None
_last_call = 0.0
MIN_INTERVAL = float(os.getenv("MIN_INTERVAL", "5"))  # har API call ke beech kam az kam itne seconds


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise RuntimeError("API_KEY .env file me set nahi hai (.env.example dekhein).")
        _client = OpenAI(api_key=api_key, base_url=os.getenv("BASE_URL") or None)
    return _client


def chat(model: str, messages: list, temperature: float = 0.0, max_tokens: int = 400, retries: int = 8) -> str:
    """Return the model's text reply. Identical calls are served from .cache/."""
    global _last_call
    key = hashlib.sha256(
        json.dumps([model, messages, temperature, max_tokens], sort_keys=True).encode()
    ).hexdigest()
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))["text"]

    delay = 10
    for attempt in range(retries):
        # rate limit se bachne ke liye calls ke beech gap
        wait = MIN_INTERVAL - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        try:
            _last_call = time.time()
            resp = _get_client().chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )
            text = (resp.choices[0].message.content or "").strip()
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            cache_file.write_text(json.dumps({"text": text}), encoding="utf-8")
            return text
        except Exception as exc:  # rate limit, network, server busy, etc.
            if attempt == retries - 1:
                raise
            print(f"  [retry {attempt + 1}] {type(exc).__name__}: {exc} (wait {delay}s)")
            time.sleep(delay)
            delay = min(delay * 2, 60)