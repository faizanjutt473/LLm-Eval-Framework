"""Generates data/test_set.json (50 prompts). Run once: python build_test_set.py"""
import json
from pathlib import Path

JSON_FMT = {"type": "json", "keys": ["answer", "reason"]}
BULLETS = {"type": "bullets", "count": 3}
ONE = {"type": "one_sentence"}
WORDS = {"type": "max_words", "limit": 20}
NUM = {"type": "number_only"}

# (question, reference (alternatives split by '|'), format)
RAW = [
    # --- JSON (10)
    ("What is the capital of Australia?", "Canberra", JSON_FMT),
    ("What is the chemical symbol for gold?", "Au", JSON_FMT),
    ("Who wrote the novel 1984?", "George Orwell|Orwell", JSON_FMT),
    ("What is the largest planet in the solar system?", "Jupiter", JSON_FMT),
    ("Which programming language was created by Guido van Rossum?", "Python", JSON_FMT),
    ("What does HTTP stand for?", "HyperText Transfer Protocol", JSON_FMT),
    ("Which gas do plants absorb for photosynthesis?", "carbon dioxide|CO2", JSON_FMT),
    ("In which year did World War II end?", "1945", JSON_FMT),
    ("Which organ pumps blood through the human body?", "heart", JSON_FMT),
    ("What is the currency of Japan?", "yen", JSON_FMT),
    # --- 3 bullet points (10)
    ("Explain why the sky appears blue.", "Rayleigh|scattering", BULLETS),
    ("Describe the water cycle.", "evaporation", BULLETS),
    ("Explain what machine learning is.", "learn|data", BULLETS),
    ("Explain the benefits of version control such as Git.", "Git", BULLETS),
    ("Explain what an API is.", "interface", BULLETS),
    ("Describe how vaccines work.", "immune", BULLETS),
    ("Explain why regular exercise is healthy.", "heart|cardiovascular", BULLETS),
    ("Explain what caused the French Revolution.", "tax|taxes", BULLETS),
    ("Explain what photosynthesis produces.", "oxygen|glucose", BULLETS),
    ("Explain how binary search works.", "half|middle|divide", BULLETS),
    # --- exactly one sentence (10)
    ("What causes ocean tides?", "moon|gravity", ONE),
    ("What is DNS used for?", "domain|IP address|IP", ONE),
    ("What is inflation?", "prices|price", ONE),
    ("Why is the ocean salty?", "rivers|rocks|minerals", ONE),
    ("What is a black hole?", "gravity", ONE),
    ("What does a CPU do?", "instructions|processing|execute", ONE),
    ("What is the Pythagorean theorem about?", "right triangle|right angled|hypotenuse", ONE),
    ("What is overfitting in machine learning?", "training data|noise", ONE),
    ("Who developed the theory of general relativity?", "Einstein", ONE),
    ("What is the boiling point of water at sea level in Celsius?", "100", ONE),
    # --- max 20 words (10)
    ("Who painted the Mona Lisa?", "Leonardo|da Vinci", WORDS),
    ("What is the capital of Canada?", "Ottawa", WORDS),
    ("What is the largest ocean on Earth?", "Pacific", WORDS),
    ("Who discovered penicillin?", "Fleming", WORDS),
    ("What is the square root of 144?", "12", WORDS),
    ("Which planet is known as the Red Planet?", "Mars", WORDS),
    ("What is the chemical formula of table salt?", "NaCl", WORDS),
    ("Who was the first person to walk on the Moon?", "Armstrong", WORDS),
    ("What is the longest river in Africa?", "Nile", WORDS),
    ("What is the freezing point of water in Fahrenheit?", "32", WORDS),
    # --- number only (10)
    ("What is 15 multiplied by 12?", "180", NUM),
    ("How many continents are there?", "7", NUM),
    ("How many days are there in a leap year?", "366", NUM),
    ("What is 144 divided by 12?", "12", NUM),
    ("How many sides does a hexagon have?", "6", NUM),
    ("How many bits are in a byte?", "8", NUM),
    ("What is 2 to the power of 10?", "1024", NUM),
    ("How many minutes are there in 3 hours?", "180", NUM),
    ("What is the atomic number of carbon?", "6", NUM),
    ("How many players does one soccer team have on the field?", "11", NUM),
]

items = [
    {"id": i + 1, "question": q, "reference": ref, "format": fmt}
    for i, (q, ref, fmt) in enumerate(RAW)
]
assert len(items) == 50
Path("data").mkdir(exist_ok=True)
Path("data/test_set.json").write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(items)} prompts -> data/test_set.json")
