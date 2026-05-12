#!/usr/bin/env python3
"""Summarize two model-assisted annotation files."""

from __future__ import annotations

import csv
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "conferences" / "04_vlm_as_judge_nl2vis" / "calibration" / "model_labels"
TABLES = ROOT / "conferences" / "04_vlm_as_judge_nl2vis" / "tables"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_case: dict[str, dict[str, str]] = {}
    for row in rows:
        by_case[row["case_id"]] = row
    return [by_case[key] for key in sorted(by_case)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def cohen_kappa(a: list[str], b: list[str]) -> float:
    labels = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return 0.0
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca = Counter(a)
    cb = Counter(b)
    expected = sum((ca[label] / n) * (cb[label] / n) for label in labels)
    if expected == 1:
        return 1.0
    return round((observed - expected) / (1 - expected), 4)


def main() -> None:
    name_map = {
        "qwen3_vl_4b": "qwen3-vl:4b",
        "qwen2_5vl_3b": "qwen2.5vl:3b",
        "minicpm_v": "minicpm-v",
        "llava_7b": "llava:7b",
        "moondream": "moondream",
    }
    files = {
        name_map.get(path.stem, path.stem): path
        for path in sorted(LABELS.glob("*.csv"))
        if path.stem not in {"model_annotation_summary", "model_model_agreement"}
    }
    data = {
        model: rows
        for model, path in files.items()
        if (rows := dedupe(read_csv(path)))
    }
    files = {model: path for model, path in files.items() if model in data}
    by_model = {model: {row["case_id"]: row for row in rows} for model, rows in data.items()}

    summary_rows = []
    for model, rows in data.items():
        overall = Counter(row["human_overall_acceptable"] for row in rows)
        errors = Counter(row["human_primary_error"] for row in rows)
        confidence = Counter(row["human_confidence"] for row in rows)
        summary_rows.append(
            {
                "model": model,
                "n": len(rows),
                "overall_yes": overall.get("yes", 0),
                "overall_no": overall.get("no", 0),
                "overall_unclear": overall.get("unclear", 0),
                "yes_pct": round(100 * overall.get("yes", 0) / len(rows), 3),
                "no_pct": round(100 * overall.get("no", 0) / len(rows), 3),
                "unclear_pct": round(100 * overall.get("unclear", 0) / len(rows), 3),
                "top_errors": "; ".join(f"{k}:{v}" for k, v in errors.most_common(6)),
                "confidence": "; ".join(f"{k}:{v}" for k, v in confidence.most_common()),
            }
        )
    write_csv(
        LABELS / "model_annotation_summary.csv",
        summary_rows,
        ["model", "n", "overall_yes", "overall_no", "overall_unclear", "yes_pct", "no_pct", "unclear_pct", "top_errors", "confidence"],
    )

    agreement_rows = []
    for a_model, b_model in combinations(files, 2):
        shared = sorted(set(by_model[a_model]) & set(by_model[b_model]))
        a_overall = [by_model[a_model][case_id]["human_overall_acceptable"] for case_id in shared]
        b_overall = [by_model[b_model][case_id]["human_overall_acceptable"] for case_id in shared]
        a_error = [by_model[a_model][case_id]["human_primary_error"] for case_id in shared]
        b_error = [by_model[b_model][case_id]["human_primary_error"] for case_id in shared]
        agreement_rows.append(
            {
                "model_a": a_model,
                "model_b": b_model,
                "n": len(shared),
                "overall_exact_agreement_pct": round(100 * sum(x == y for x, y in zip(a_overall, b_overall)) / len(shared), 3),
                "overall_kappa": cohen_kappa(a_overall, b_overall),
                "primary_error_exact_agreement_pct": round(100 * sum(x == y for x, y in zip(a_error, b_error)) / len(shared), 3),
                "primary_error_kappa": cohen_kappa(a_error, b_error),
            }
        )
    write_csv(
        LABELS / "model_model_agreement.csv",
        agreement_rows,
        ["model_a", "model_b", "n", "overall_exact_agreement_pct", "overall_kappa", "primary_error_exact_agreement_pct", "primary_error_kappa"],
    )

    md = ["# Model-Assisted Annotation Summary", ""]
    md.append("| Model | n | Overall yes | Overall no | Unclear | Top errors |")
    md.append("|---|---:|---:|---:|---:|---|")
    for row in summary_rows:
        md.append(
            f"| {row['model']} | {row['n']} | {row['yes_pct']:.1f}% | {row['no_pct']:.1f}% | "
            f"{row['unclear_pct']:.1f}% | `{row['top_errors']}` |"
        )
    md.append("")
    md.append("| Pair | n | Overall agreement | Overall kappa | Error agreement | Error kappa |")
    md.append("|---|---:|---:|---:|---:|---:|")
    for agreement in agreement_rows:
        md.append(
            f"| {agreement['model_a']} vs {agreement['model_b']} | {agreement['n']} | {agreement['overall_exact_agreement_pct']:.1f}% | "
            f"{agreement['overall_kappa']:.3f} | {agreement['primary_error_exact_agreement_pct']:.1f}% | {agreement['primary_error_kappa']:.3f} |"
        )
    md.append("")
    md.append("These labels are model-assisted pre-annotations, not human calibration labels.")
    (TABLES / "model_annotation_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print({"models": list(files), "pairs": len(agreement_rows)})


if __name__ == "__main__":
    main()
