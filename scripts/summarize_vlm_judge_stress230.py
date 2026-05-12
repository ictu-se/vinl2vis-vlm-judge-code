#!/usr/bin/env python3
"""Summarize VLM audits over the 230-case stress set."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "conferences" / "04_vlm_as_judge_nl2vis"
STRESS = PAPER / "stress230"
TABLES = PAPER / "tables"

MODELS = [
    "qwen3-vl:4b",
    "qwen2.5vl:3b",
    "minicpm-v",
    "llava:7b",
    "moondream",
]


def safe_model_name(model: str) -> str:
    return model.replace(":", "_").replace(".", "_").replace("-", "_")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def bool_value(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def main() -> None:
    cases = read_csv(STRESS / "stress230_cases.csv")
    case_by_sample = defaultdict(list)
    for case in cases:
        case_by_sample[case["sample_id"]].append(case)

    run_config = read_csv(STRESS / "stress230_run_config.csv")
    run_keys = [row["run_key"] for row in run_config]
    raw_rows: list[dict[str, Any]] = []
    for model in MODELS:
        safe = safe_model_name(model)
        for run_key in run_keys:
            path = STRESS / "audits" / f"{run_key}__{safe}__promptv4" / "vlm_judgments.jsonl"
            judgment_by_sample: dict[str, dict[str, Any]] = {}
            for judgment_row in read_jsonl(path):
                judgment_by_sample.setdefault(str(judgment_row.get("sample_id", "")), judgment_row)
            for sample_id, judgment_row in judgment_by_sample.items():
                for case in case_by_sample.get(judgment_row.get("sample_id", ""), []):
                    if case["run_key"] != run_key:
                        continue
                    judgment = judgment_row.get("judgment", {})
                    if not isinstance(judgment, dict):
                        judgment = {}
                    raw_rows.append(
                        {
                            "case_id": case["case_id"],
                            "sample_id": case["sample_id"],
                            "case_family": case["case_family"],
                            "evidence_strength": case["evidence_strength"],
                            "run_key": run_key,
                            "model": model,
                            "acceptable": bool_value(judgment.get("acceptable")),
                            "chart_family_matches": bool_value(judgment.get("chart_family_matches")),
                            "labels_match_query": bool_value(judgment.get("labels_match_query")),
                            "readable": bool_value(judgment.get("readable")),
                            "visible_chart_family": judgment.get("visible_chart_family", ""),
                            "major_issue": judgment.get("major_issue", ""),
                            "conservative_issue": judgment_row.get("conservative_issue", ""),
                        }
                    )

    detail_fields = [
        "case_id",
        "sample_id",
        "case_family",
        "evidence_strength",
        "run_key",
        "model",
        "acceptable",
        "chart_family_matches",
        "labels_match_query",
        "readable",
        "visible_chart_family",
        "major_issue",
        "conservative_issue",
    ]
    write_csv(STRESS / "stress230_vlm_judgment_details.csv", raw_rows, detail_fields)

    summary_rows: list[dict[str, Any]] = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        groups[(row["model"], row["case_family"])].append(row)
    for (model, case_family), rows in sorted(groups.items()):
        n = len(rows)
        rejected = sum(1 for row in rows if not row["acceptable"])
        chart = sum(1 for row in rows if row["chart_family_matches"])
        labels = sum(1 for row in rows if row["labels_match_query"])
        readable = sum(1 for row in rows if row["readable"])
        issues = Counter(row["conservative_issue"] or "missing" for row in rows)
        summary_rows.append(
            {
                "model": model,
                "case_family": case_family,
                "n": n,
                "reject_pct": round(100 * rejected / n, 3) if n else 0,
                "accept_pct": round(100 * (n - rejected) / n, 3) if n else 0,
                "chart_family_match_pct": round(100 * chart / n, 3) if n else 0,
                "labels_match_pct": round(100 * labels / n, 3) if n else 0,
                "readable_pct": round(100 * readable / n, 3) if n else 0,
                "conservative_issue_counts": json.dumps(dict(sorted(issues.items())), ensure_ascii=False),
            }
        )
    fields = [
        "model",
        "case_family",
        "n",
        "reject_pct",
        "accept_pct",
        "chart_family_match_pct",
        "labels_match_pct",
        "readable_pct",
        "conservative_issue_counts",
    ]
    write_csv(STRESS / "stress230_vlm_summary_by_family.csv", summary_rows, fields)

    overall_rows = []
    for model in MODELS:
        rows = [row for row in raw_rows if row["model"] == model]
        n = len(rows)
        if not rows:
            continue
        rejected = sum(1 for row in rows if not row["acceptable"])
        overall_rows.append(
            {
                "model": model,
                "n": n,
                "reject_pct": round(100 * rejected / n, 3),
                "accept_pct": round(100 * (n - rejected) / n, 3),
                "chart_family_match_pct": round(100 * sum(1 for row in rows if row["chart_family_matches"]) / n, 3),
                "labels_match_pct": round(100 * sum(1 for row in rows if row["labels_match_query"]) / n, 3),
                "readable_pct": round(100 * sum(1 for row in rows if row["readable"]) / n, 3),
            }
        )
    write_csv(STRESS / "stress230_vlm_summary_overall.csv", overall_rows, ["model", "n", "reject_pct", "accept_pct", "chart_family_match_pct", "labels_match_pct", "readable_pct"])

    md = ["# Stress230 VLM Summary", ""]
    md.append("| Judge | n | Reject | Accept | Chart-family match | Label match | Readable |")
    md.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in overall_rows:
        md.append(
            f"| {row['model']} | {row['n']} | {row['reject_pct']:.1f}% | {row['accept_pct']:.1f}% | "
            f"{row['chart_family_match_pct']:.1f}% | {row['labels_match_pct']:.1f}% | {row['readable_pct']:.1f}% |"
        )
    md.append("")
    md.append("## By Evidence Family")
    md.append("")
    md.append("| Judge | Case family | n | Reject | Accept | Issues |")
    md.append("|---|---|---:|---:|---:|---|")
    for row in summary_rows:
        md.append(
            f"| {row['model']} | {row['case_family']} | {row['n']} | {row['reject_pct']:.1f}% | "
            f"{row['accept_pct']:.1f}% | `{row['conservative_issue_counts']}` |"
        )
    (TABLES / "stress230_vlm_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"detail_rows": len(raw_rows), "overall_rows": len(overall_rows), "family_rows": len(summary_rows)}, indent=2))


if __name__ == "__main__":
    main()
