"""Create data/manual_labels.csv with 20 samples for YOUR manual labelling.

Judge scores are NOT included, so your labels stay independent.
Samples me pehle woh jawab aate hain jin par factual check fail hua (max 8),
baaqi random hote hain.

    python sample_for_labeling.py --runs v1_modelA v2_modelA
"""
import argparse
import random
from pathlib import Path

import pandas as pd

from metrics import load_run


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs", nargs="+", required=True, help="run names to sample from")
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--max-hard", type=int, default=8, help="factual-fail samples ki max tadad")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default="data/manual_labels.csv")
    p.add_argument("--force", action="store_true", help="existing labels overwrite karo")
    args = p.parse_args()

    out = Path(args.out)
    if out.exists() and not args.force:
        raise SystemExit(f"{out} pehle se maujood hai (aapke labels hon sakte hain). Overwrite ke liye --force.")

    runs = {name: {r["id"]: r for r in load_run(name)["records"]} for name in args.runs}
    ids = sorted(set.intersection(*[set(r) for r in runs.values()]))
    rng = random.Random(args.seed)

    # 1) woh (run, id) jahan factual check fail hua
    hard = [(name, i) for name in args.runs for i in ids if not runs[name][i]["factual"]["passed"]]
    rng.shuffle(hard)
    chosen, used = [], set()
    for name, i in hard:
        if i not in used and len(chosen) < args.max_hard:
            chosen.append((name, i))
            used.add(i)

    # 2) baaqi random, runs ko alternate karte hue
    rest = [i for i in ids if i not in used]
    rng.shuffle(rest)
    for k, i in enumerate(rest[: args.n - len(chosen)]):
        chosen.append((args.runs[k % len(args.runs)], i))

    rng.shuffle(chosen)  # order mix kar do
    rows = []
    for run_name, item_id in chosen:
        rec = runs[run_name][item_id]
        rows.append({
            "run": run_name, "id": item_id, "question": rec["question"],
            "reference": rec["reference"], "response": rec["response"],
            "manual_score": "", "notes": "",
        })
    out.parent.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"{len(rows)} samples ({min(len(hard), args.max_hard)} factual-fail wale) -> {out}")
    print("Ab 'manual_score' (1-5) khud bharein.")


if __name__ == "__main__":
    main()