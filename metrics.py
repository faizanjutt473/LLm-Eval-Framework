"""Helpers to load run files and summarise them."""
import json
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path("results")


def load_run(name: str) -> dict:
    path = RESULTS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} nahi mila. Pehle runner.py chalayein.")
    return json.loads(path.read_text(encoding="utf-8"))


def run_to_df(run: dict) -> pd.DataFrame:
    rows = []
    for r in run["records"]:
        rows.append({
            "id": r["id"],
            "format_type": r["format_spec"]["type"],
            "factual": r["factual"]["score"],
            "factual_pass": float(r["factual"]["passed"]),
            "format": r["format"]["score"],
            "judge": r["judge"]["overall"],
        })
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> dict:
    return {
        "n": len(df),
        "factual_mean": round(df["factual"].mean(), 3),
        "factual_pass_rate": round(df["factual_pass"].mean(), 3),
        "format_pass_rate": round(df["format"].mean(), 3),
        "judge_mean": round(df["judge"].mean(), 3),
        "judge_failures": int(df["judge"].isna().sum()),
    }
