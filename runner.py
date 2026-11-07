"""Run one (model, prompt version) over the test set and score it with all 3 checks.

Example:
    python runner.py --name v1_modelA --model $MODEL_A --prompt v1
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

import llm_client
from evaluators import factual, format_check, judge
from metrics import run_to_df, summarize
from prompts import build_messages

load_dotenv()


def main():
    p = argparse.ArgumentParser(description="LLM Output Evaluation runner")
    p.add_argument("--name", required=True, help="run ka naam, e.g. v1_modelA")
    p.add_argument("--model", default=os.getenv("MODEL_A"), help="generation model")
    p.add_argument("--prompt", choices=["v1", "v2"], required=True, help="prompt version")
    p.add_argument("--judge-model", default=os.getenv("JUDGE_MODEL"), help="judge model")
    p.add_argument("--test-set", default="data/test_set.json")
    p.add_argument("--limit", type=int, default=None, help="sirf pehle N prompts (testing ke liye)")
    args = p.parse_args()

    if not args.model or not args.judge_model:
        p.error("--model aur --judge-model do, ya .env me MODEL_A / JUDGE_MODEL set karein")

    items = json.loads(Path(args.test_set).read_text(encoding="utf-8"))
    if args.limit:
        items = items[: args.limit]

    records = []
    for item in tqdm(items, desc=args.name):
        messages = build_messages(args.prompt, item)
        response = llm_client.chat(args.model, messages, temperature=0.0, max_tokens=300)
        records.append({
            "id": item["id"],
            "question": item["question"],
            "reference": item["reference"],
            "format_spec": item["format"],
            "prompt_messages": messages,
            "response": response,
            "factual": factual.evaluate(item, response),
            "format": format_check.evaluate(item, response),
            "judge": judge.evaluate(item, response, args.judge_model),
        })

    run = {
        "meta": {
            "name": args.name,
            "model": args.model,
            "prompt_version": args.prompt,
            "judge_model": args.judge_model,
            "n_prompts": len(records),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        },
        "records": records,
    }
    Path("results").mkdir(exist_ok=True)
    out = Path("results") / f"{args.name}.json"
    out.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved -> {out}")
    for k, v in summarize(run_to_df(run)).items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
