"""Measure how well the LLM judge agrees with your manual labels.

    python agreement.py
"""
import argparse
import json
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from metrics import load_run


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--labels", default="data/manual_labels.csv")
    p.add_argument("--out", default="results/agreement.json")
    args = p.parse_args()

    df = pd.read_csv(args.labels)
    df = df[pd.to_numeric(df["manual_score"], errors="coerce").notna()].copy()
    if df.empty:
        raise SystemExit("manual_score column khali hai. Pehle 20 samples label karein.")
    df["manual_score"] = df["manual_score"].astype(int)

    cache = {name: {r["id"]: r for r in load_run(name)["records"]} for name in df["run"].unique()}
    df["judge_score"] = [cache[r.run][r.id]["judge"]["overall"] for r in df.itertuples()]
    df = df.dropna(subset=["judge_score"])
    df["judge_score"] = df["judge_score"].astype(int)

    m, j = df["manual_score"], df["judge_score"]
    labels = [1, 2, 3, 4, 5]
    rho, rho_p = spearmanr(m, j)
    result = {
        "n_samples": int(len(df)),
        "exact_agreement": round(float((m == j).mean()), 3),
        "within_1_agreement": round(float(((m - j).abs() <= 1).mean()), 3),
        "mean_abs_error": round(float((m - j).abs().mean()), 3),
        "judge_bias (judge_mean - manual_mean)": round(float(j.mean() - m.mean()), 3),
        "spearman_rho": None if pd.isna(rho) else round(float(rho), 3),
        "spearman_p": None if pd.isna(rho_p) else round(float(rho_p), 4),
        "cohen_kappa": round(float(cohen_kappa_score(m, j, labels=labels)), 3),
        "cohen_kappa_quadratic_weighted": round(float(cohen_kappa_score(m, j, labels=labels, weights="quadratic")), 3),
        "confusion_matrix_rows_manual_cols_judge_1to5": confusion_matrix(m, j, labels=labels).tolist(),
    }
    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"\nSaved -> {args.out}")


if __name__ == "__main__":
    main()
