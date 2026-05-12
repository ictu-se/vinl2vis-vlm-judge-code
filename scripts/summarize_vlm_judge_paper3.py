#!/usr/bin/env python3
"""Summarize existing VLM-as-judge evidence for the third NL2Vis paper."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmark" / "faithbench" / "results"
OUT = ROOT / "conferences" / "04_vlm_as_judge_nl2vis" / "tables"


PRIMARY_FULL_AUDITS = {
    "vlm_audit_vietnamese_balanced_auditfix_v2_n1000_qwen3vl4b_promptv4": "Vietnamese balanced",
    "vlm_audit_english_explicit_auditfix_v2_n1000_qwen3vl4b_promptv4": "English explicit",
    "vlm_audit_matched_bilingual_auditfix_v2_n1000_qwen3vl4b_promptv4": "Matched bilingual",
    "vlm_audit_heldout860_qwen3_8b_auditfix_v4_n860_qwen3vl4b_promptv4": "Held-out Vietnamese",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fmt(x) -> str:
    if x in ("", None):
        return ""
    if isinstance(x, str):
        return x
    return f"{float(x):.3f}".rstrip("0").rstrip(".")


def summarize_primary_audits() -> list[dict]:
    rows = []
    for audit_dir, setting in PRIMARY_FULL_AUDITS.items():
        summary_path = RESULTS / audit_dir / "vlm_audit_summary.json"
        if not summary_path.exists():
            continue
        summary = load_json(summary_path)
        judgments = summary.get("judgments") or {}
        rates = judgments.get("boolean_rates") or {}
        issues = judgments.get("conservative_issue_counts") or judgments.get("issue_counts") or {}
        rows.append(
            {
                "setting": setting,
                "audit_dir": audit_dir,
                "judge": summary.get("ollama_model", ""),
                "n": judgments.get("n", summary.get("rendered", "")),
                "acceptable": rates.get("acceptable_pct", ""),
                "chart_family": rates.get("chart_family_match_pct", ""),
                "labels": rates.get("labels_match_pct", ""),
                "readable": rates.get("readable_pct", ""),
                "issues": json.dumps(issues, ensure_ascii=False),
            }
        )
    return rows


def summarize_cross_judges() -> list[dict]:
    path = RESULTS / "vlm_consensus_audit_summary.csv"
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["audit_group"] != "heldout8b_final_full":
                continue
            rows.append(row)
    tier_order = {"primary": 0, "secondary": 1, "weak": 2}
    rows.sort(key=lambda r: (tier_order.get(r["judge_tier"], 9), r["model"]))
    return rows


def summarize_failure_cases() -> dict:
    path = RESULTS / "vlm_consensus_failure_cases.csv"
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    return counts


def write_markdown(primary: list[dict], cross: list[dict], failures: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "vlm_judge_evidence_summary.md"
    with out.open("w", encoding="utf-8") as f:
        f.write("# VLM-as-Judge Evidence Summary\n\n")
        f.write("Generated from existing ViNL2Vis-FaithBench VLM audit artifacts.\n\n")

        f.write("## Primary qwen3-vl Full Audits\n\n")
        f.write("| Setting | Judge | n | Acceptable | Chart family | Labels | Readable | Issues |\n")
        f.write("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for r in primary:
            f.write(
                f"| {r['setting']} | `{r['judge']}` | {r['n']} | {fmt(r['acceptable'])} | "
                f"{fmt(r['chart_family'])} | {fmt(r['labels'])} | {fmt(r['readable'])} | "
                f"`{r['issues']}` |\n"
            )

        f.write("\n## Cross-Judge Held-Out Audit\n\n")
        f.write("| Judge | Tier | n | Acceptable | Chart family | Labels | Readable | Issues |\n")
        f.write("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for r in cross:
            f.write(
                f"| `{r['model']}` | {r['judge_tier']} | {r['n']} | {fmt(r['acceptable_pct'])} | "
                f"{fmt(r['chart_family_match_pct'])} | {fmt(r['labels_match_pct'])} | "
                f"{fmt(r['readable_pct'])} | `{r['issue_counts']}` |\n"
            )

        f.write("\n## Failure-Case Classifications\n\n")
        f.write("| Classification | Count |\n")
        f.write("| --- | ---: |\n")
        for key, value in sorted(failures.items()):
            f.write(f"| {key} | {value} |\n")

        f.write("\n## Immediate Interpretation\n\n")
        f.write("- `qwen3-vl:4b` is useful as a primary local visual auditor for chart-family, labels, and readability.\n")
        f.write("- `qwen2.5vl:3b` agrees strongly on the final held-out audit, but its all-accept behavior needs stress tests on known-bad cases.\n")
        f.write("- `llava:7b` and `moondream` should be analyzed as weak judges because their label or chart-family behavior is unstable.\n")
        f.write("- Existing evidence supports a triage claim: VLM judges discover visual repair gaps, but deterministic evaluators remain necessary for semantic faithfulness.\n")


def main() -> None:
    primary = summarize_primary_audits()
    cross = summarize_cross_judges()
    failures = summarize_failure_cases()
    write_markdown(primary, cross, failures)
    print(OUT / "vlm_judge_evidence_summary.md")


if __name__ == "__main__":
    main()
