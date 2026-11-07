import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("API_KEY"), base_url=os.getenv("BASE_URL"))

SKIP = ("tts", "live", "audio", "embedding", "image", "imagen", "veo", "lyria",
        "robotics", "computer-use", "research", "antigravity", "aqa", "transcribe", "translate")

names = [m.id.replace("models/", "") for m in client.models.list()]
candidates = [n for n in names if "gemini" in n and not any(s in n for s in SKIP)]
print(f"{len(candidates)} text models try ho rahe hain...\n")

for name in candidates:
    try:
        r = client.chat.completions.create(
            model=name, max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}],
        )
        print(f"WORKS   {name}  -> {r.choices[0].message.content!r}")
    except Exception as e:
        print(f"FAILED  {name}  -> {type(e).__name__}")
    time.sleep(6)