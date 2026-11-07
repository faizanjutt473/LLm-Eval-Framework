"""Compare two runs (two prompt versions OR two models) and write report.md.

    python compare.py --a v1_modelA --b v2_modelA
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import wilcoxon

from metrics import load_run, run_to_df, summarize

METRICS = [("factual", "Factual consistency (0-1)"),
           ("format", "Format compliance (0/1)"),
           ("judge", "LLM judge overall (1-5)")]


def paired_stats(a: pd.Series, b: pd.Series) -> dict:
    ok = a.notna() & b.notna()
    a, b = a[ok], b[ok]
    diff = b - a
    try:
        p = float(wilcoxon(diff).pvalue) if (diff != 0).any() else 1.0
    except ValueError:
        p = 1.0
    return {"mean_a": a.mean(), "mean_b": b.mean(), "diff": diff.mean(),
            "b_wins": int((diff > 0).sum()), "a_wins": int((diff < 0).sum()),
            "ties": int((diff == 0).sum()), "p": p}


def short(text: str, n: int = 160) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 3] + "..."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="run A (baseline)")
    ap.add_argument("--b", required=True, help="run B (candidate)")
    ap.add_argument("--out", default="report.md")
    args = ap.parse_args()

    run_a, run_b = load_run(args.a), load_run(args.b)
    df_a, df_b = run_to_df(run_a), run_to_df(run_b)
    merged = df_a.merge(df_b, on=["id", "format_type"], suffixes=("_a", "_b"))
    ma, mb = run_a["meta"], run_b["meta"]

    # ---- summary table
    rows, stats = [], {}
    for col, label in METRICS:
        s = paired_stats(merged[f"{col}_a"], merged[f"{col}_b"])
        stats[col] = s
        rows.append({"Metric": label, f"A: {args.a}": round(s["mean_a"], 3), f"B: {args.b}": round(s["mean_b"], 3),
                     "B - A": round(s["diff"], 3), "B wins": s["b_wins"], "A wins": s["a_wins"],
                     "Ties": s["ties"], "p (Wilcoxon)": round(s["p"], 4)})
    summary_md = pd.DataFrame(rows).to_markdown(index=False)

    # ---- per format type
    per_type = merged.groupby("format_type").agg(
        format_A=("format_a", "mean"), format_B=("format_b", "mean"),
        factual_A=("factual_a", "mean"), factual_B=("factual_b", "mean"),
        judge_A=("judge_a", "mean"), judge_B=("judge_b", "mean"),
    ).round(2).reset_index()
    per_type_md = per_type.to_markdown(index=False)

    # ---- chart
    labels = ["Factual", "Format", "Judge (/5)"]
    vals_a = [stats["factual"]["mean_a"], stats["format"]["mean_a"], stats["judge"]["mean_a"] / 5]
    vals_b = [stats["factual"]["mean_b"], stats["format"]["mean_b"], stats["judge"]["mean_b"] / 5]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar([i - 0.2 for i in x], vals_a, 0.4, label=f"A: {args.a}")
    ax.bar([i + 0.2 for i in x], vals_b, 0.4, label=f"B: {args.b}")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05)
    ax.set_ylabel("score (normalised 0-1)"); ax.legend(); fig.tight_layout()
    Path("results").mkdir(exist_ok=True)
    fig.savefig("results/comparison.png", dpi=150)

    # ---- biggest differences (by judge, then format)
    merged["judge_diff"] = (merged["judge_b"] - merged["judge_a"]).abs()
    top = merged.sort_values(["judge_diff", "id"], ascending=[False, True]).head(5)
    rec_a = {r["id"]: r for r in run_a["records"]}
    rec_b = {r["id"]: r for r in run_b["records"]}
    examples = []
    for i in top["id"]:
        ra, rb = rec_a[i], rec_b[i]
        examples.append(
            f"**#{i}** {ra['question']} (ref: `{ra['reference']}`)\n"
            f"- A (judge {ra['judge']['overall']}, format {'pass' if ra['format']['passed'] else 'FAIL'}): {short(ra['response'])}\n"
            f"- B (judge {rb['judge']['overall']}, format {'pass' if rb['format']['passed'] else 'FAIL'}): {short(rb['response'])}\n")

    # ---- judge agreement (if already computed)
    agree_path = Path("results/agreement.json")
    if agree_path.exists():
        ag = json.loads(agree_path.read_text())
        agree_md = ("| Measure | Value |\n|---|---|\n" +
                    "\n".join(f"| {k} | {v} |" for k, v in ag.items() if "confusion" not in k) +
                    f"\n\nConfusion matrix (rows = manual 1-5, columns = judge 1-5):\n\n```\n" +
                    "\n".join(str(r) for r in ag["confusion_matrix_rows_manual_cols_judge_1to5"]) + "\n```")
    else:
        agree_md = "_Abhi nahi nikala. `sample_for_labeling.py` aur `agreement.py` chalayein, phir compare.py dobara chalayein._"

    # ---- auto findings
    def verdict(col, label):
        d = stats[col]["diff"]
        if abs(d) < 1e-9:
            return f"- {label}: no difference."
        winner = "B" if d > 0 else "A"
        sig = "statistically significant (p<0.05)" if stats[col]["p"] < 0.05 else "not statistically significant"
        return f"- {label}: **{winner}** is better by {abs(d):.3f} ({sig})."
    findings = "\n".join(verdict(c, l) for c, l in METRICS)

    report = f"""# LLM Output Evaluation Report

## 1. Setup
| | A | B |
|---|---|---|
| Run name | {args.a} | {args.b} |
| Model | {ma['model']} | {mb['model']} |
| Prompt version | {ma['prompt_version']} | {mb['prompt_version']} |
| Judge model | {ma['judge_model']} | {mb['judge_model']} |
| Prompts evaluated | {len(merged)} | {len(merged)} |

Checks: (1) factual consistency vs reference, (2) format compliance, (3) LLM-as-judge (1-5 rubric: correctness, relevance, clarity, overall).

## 2. Overall comparison
{summary_md}

![comparison](results/comparison.png)

## 3. Key findings
{findings}

## 4. Breakdown by format type
{per_type_md}

## 5. Largest differences (examples)
{chr(10).join(examples)}

## 6. Judge vs manual labels
{agree_md}

## 7. Analysis and limitations
_(Yahan apni 4-5 lines likhein: kaun sa version/model behtar raha aur kyun, judge kitna bharosemand hai, aur limitations jaise chhota test set ya judge bias.)_
"""
    Path(args.out).write_text(report, encoding="utf-8")
    print(f"Report -> {args.out}")
    print(summary_md)


if __name__ == "__main__":
    main()
