#!/usr/bin/env python3
"""Build a 230-case stress/audit set for the VLM-as-judge paper."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark" / "faithbench"
RESULTS = BENCH / "results"
OUT = ROOT / "conferences" / "04_vlm_as_judge_nl2vis" / "stress230"


RUNS = {
    "balanced_residualfix": {
        "outputs": "benchmark/faithbench/outputs/balanced1000_qwen3_4b_qwen_chart_family_strict_repair_residualfix_v1/qwen3_4b__qwen_chart_family_strict_repair_residualfix_v1__n1000.jsonl",
        "split": "benchmark/faithbench/splits/balanced_eval_1000.jsonl",
        "metrics": "benchmark/faithbench/results/balanced1000_qwen3_4b_qwen_chart_family_strict_repair_residualfix_v1/per_output_metrics.csv",
    },
    "english_residualfix": {
        "outputs": "benchmark/faithbench/outputs/english1000_qwen3_4b_residualfix_v1/qwen3_4b__residualfix_v1__n1000.jsonl",
        "split": "benchmark/faithbench/splits/english_explicit_1000_label_audit_v3.jsonl",
        "metrics": "benchmark/faithbench/results/english1000_qwen3_4b_residualfix_v1/per_output_metrics.csv",
    },
    "matched_residualfix": {
        "outputs": "benchmark/faithbench/outputs/matched_bilingual1000_qwen3_4b_residualfix_v1/qwen3_4b__residualfix_v1__n1000.jsonl",
        "split": "benchmark/faithbench/splits/matched_bilingual_explicit_1000.jsonl",
        "metrics": "benchmark/faithbench/results/matched_bilingual1000_qwen3_4b_residualfix_v1/per_output_metrics.csv",
    },
    "balanced_final": {
        "outputs": "benchmark/faithbench/outputs/balanced1000_qwen3_4b_visualfix_v1_auditfix_v2/qwen3_4b__visualfix_v1_auditfix_v2__n1000.jsonl",
        "split": "benchmark/faithbench/splits/balanced_eval_1000.jsonl",
        "metrics": "benchmark/faithbench/results/balanced1000_qwen3_4b_visualfix_v1_auditfix_v2/per_output_metrics.csv",
    },
    "english_final": {
        "outputs": "benchmark/faithbench/outputs/english1000_qwen3_4b_visualfix_v1_auditfix_v2/qwen3_4b__visualfix_v1_auditfix_v2__n1000.jsonl",
        "split": "benchmark/faithbench/splits/english_explicit_1000_label_audit_v3.jsonl",
        "metrics": "benchmark/faithbench/results/english1000_qwen3_4b_visualfix_v1_auditfix_v2/per_output_metrics.csv",
    },
    "matched_final": {
        "outputs": "benchmark/faithbench/outputs/matched_bilingual1000_qwen3_4b_visualfix_v5_auditfix_v2/qwen3_4b__visualfix_v5_auditfix_v2__n1000.jsonl",
        "split": "benchmark/faithbench/splits/matched_bilingual_explicit_1000.jsonl",
        "metrics": "benchmark/faithbench/results/matched_bilingual1000_qwen3_4b_visualfix_v5_auditfix_v2/per_output_metrics.csv",
    },
    "heldout4b_visualfix": {
        "outputs": "benchmark/faithbench/outputs/heldout860_qwen3_4b_visualfix_v1/qwen3_4b__heldout_visualfix_v1__n860.jsonl",
        "split": "benchmark/faithbench/splits/heldout_860_v1.jsonl",
        "metrics": "benchmark/faithbench/results/heldout860_qwen3_4b_visualfix_v1/per_output_metrics.csv",
    },
    "heldout4b_final": {
        "outputs": "benchmark/faithbench/outputs/heldout860_qwen3_4b_auditfix_v2/qwen3_4b__heldout_auditfix_v2__n860.jsonl",
        "split": "benchmark/faithbench/splits/heldout_860_v1.jsonl",
        "metrics": "benchmark/faithbench/results/heldout860_qwen3_4b_auditfix_v2/per_output_metrics.csv",
    },
    "heldout8b_visualfix": {
        "outputs": "benchmark/faithbench/outputs/heldout860_qwen3_8b_visualfix_v3/qwen3_8b__heldout_visualfix_v3__n860.jsonl",
        "split": "benchmark/faithbench/splits/heldout_860_v1.jsonl",
        "metrics": "benchmark/faithbench/results/heldout860_qwen3_8b_visualfix_v3/per_output_metrics.csv",
    },
    "heldout8b_intermediate": {
        "outputs": "benchmark/faithbench/outputs/heldout860_qwen3_8b_auditfix_v2/qwen3_8b__heldout_auditfix_v2__n860.jsonl",
        "split": "benchmark/faithbench/splits/heldout_860_v1.jsonl",
        "metrics": "benchmark/faithbench/results/heldout860_qwen3_8b_auditfix_v2/per_output_metrics.csv",
    },
    "heldout8b_final": {
        "outputs": "benchmark/faithbench/outputs/heldout860_qwen3_8b_auditfix_v4/qwen3_8b__heldout_auditfix_v4__n860.jsonl",
        "split": "benchmark/faithbench/splits/heldout_860_v1.jsonl",
        "metrics": "benchmark/faithbench/results/heldout860_qwen3_8b_auditfix_v4/per_output_metrics.csv",
    },
}

STRICT_RUN_TO_RUN_KEY = {
    "balanced_qwen_final": "balanced_final",
    "english_qwen_final": "english_final",
    "matched_qwen_final": "matched_final",
    "heldout_4b_final": "heldout4b_final",
    "heldout_8b_final": "heldout8b_final",
}

QWEN3_AUDITS = {
    "vlm_audit_vietnamese_balanced_auditfix_v2_n1000_qwen3vl4b_promptv4": "balanced_final",
    "vlm_audit_english_explicit_auditfix_v2_n1000_qwen3vl4b_promptv4": "english_final",
    "vlm_audit_matched_bilingual_auditfix_v2_n1000_qwen3vl4b_promptv4": "matched_final",
    "vlm_audit_heldout860_qwen3_8b_auditfix_v4_n860_qwen3vl4b_promptv4": "heldout8b_final",
    "vlm_audit_heldout860_qwen3_4b_visualfix_v1_n860_qwen3vl4b_promptv4": "heldout4b_visualfix",
    "vlm_audit_heldout860_qwen3_8b_visualfix_v3_n500_qwen3vl4b_promptv4": "heldout8b_visualfix",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def load_sample_meta() -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    for path in (BENCH / "splits").glob("*.jsonl"):
        for row in read_jsonl(path):
            meta.setdefault(row["sample_id"], row)
    return meta


def available_ids(run_key: str) -> set[str]:
    run = RUNS[run_key]
    return {row["sample_id"] for row in read_jsonl(ROOT / run["outputs"])}


def make_case(
    row: dict[str, Any],
    sample_meta: dict[str, dict[str, Any]],
    case_family: str,
    evidence_strength: str,
    source_artifact: str,
    run_key: str,
    issue: str,
) -> dict[str, Any]:
    meta = sample_meta.get(str(row.get("sample_id")), {})
    return {
        "case_id": "",
        "sample_id": row.get("sample_id", ""),
        "case_family": case_family,
        "evidence_strength": evidence_strength,
        "source_artifact": source_artifact,
        "run_key": run_key,
        "issue": issue,
        "dataset_id": row.get("dataset_id") or meta.get("dataset_id", ""),
        "query_type": row.get("query_type") or meta.get("query_type", ""),
        "language": row.get("language") or meta.get("language", ""),
        "expected_chart_family": row.get("chart_family") or row.get("expected_chart_family") or meta.get("chart_family", ""),
        "query": row.get("query") or meta.get("query", ""),
        "notes": row.get("notes") or row.get("action") or "",
    }


def sample_rows(rows: list[dict[str, Any]], n: int, seed: int, used: set[tuple[str, str, str]]) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    shuffled = rows[:]
    rng.shuffle(shuffled)
    selected: list[dict[str, Any]] = []
    for row in shuffled:
        key = (row["run_key"], row["sample_id"], row["case_family"])
        if key in used:
            continue
        selected.append(row)
        used.add(key)
        if len(selected) == n:
            break
    return selected


def main() -> None:
    sample_meta = load_sample_meta()
    used: set[tuple[str, str, str]] = set()
    cases: list[dict[str, Any]] = []

    failures = read_csv(RESULTS / "vlm_consensus_failure_cases.csv")
    repair_rows: list[dict[str, Any]] = []
    for row in failures:
        if row.get("audit_group") == "heldout4b_before_auditfix_full" and row.get("classification") == "true_repair_gap_resolved":
            repair_rows.append(make_case(row, sample_meta, "repair_confirmed_known_bad", "repair_confirmed", "vlm_consensus_failure_cases.csv", "heldout4b_visualfix", row.get("issues", "")))
        if row.get("audit_group") == "heldout8b_intermediate_bad_targeted":
            repair_rows.append(make_case(row, sample_meta, "repair_confirmed_known_bad", "repair_confirmed", "vlm_consensus_failure_cases.csv", "heldout8b_intermediate", row.get("issues", "")))
    cases.extend(sample_rows(repair_rows, 8, 11, used))

    visual_sources = [
        ("english_residualfix", RESULTS / "english1000_qwen3_4b_residualfix_v1" / "visual_sanity_per_output.csv"),
        ("balanced_residualfix", RESULTS / "balanced1000_qwen3_4b_qwen_chart_family_strict_repair_residualfix_v1" / "visual_sanity_per_output.csv"),
        ("matched_residualfix", RESULTS / "matched_bilingual1000_qwen3_4b_residualfix_v1" / "visual_sanity_per_output.csv"),
    ]
    visual_rows: list[dict[str, Any]] = []
    for run_key, path in visual_sources:
        ids = available_ids(run_key)
        for row in read_csv(path):
            if row.get("severity") == "major" and row.get("sample_id") in ids:
                visual_rows.append(make_case(row, sample_meta, "major_visual_sanity_failure", "programmatic_visual_failure", str(path.relative_to(ROOT)), run_key, row.get("visual_sanity_tags", "")))
    cases.extend(sample_rows(visual_rows, 70, 12, used))

    strict_rows: list[dict[str, Any]] = []
    for row in read_csv(RESULTS / "strict_transformation_audit.csv"):
        run_key = STRICT_RUN_TO_RUN_KEY.get(row.get("run", ""))
        if not run_key or not row.get("issues"):
            continue
        if row.get("sample_id") not in available_ids(run_key):
            continue
        strict_rows.append(make_case(row, sample_meta, "strict_transform_failure", "deterministic_semantic_failure", "strict_transformation_audit.csv", run_key, row.get("issues", "")))
    cases.extend(sample_rows(strict_rows, 70, 13, used))

    primary_rows: list[dict[str, Any]] = []
    for audit_dir, run_key in QWEN3_AUDITS.items():
        ids = available_ids(run_key)
        for row in read_jsonl(RESULTS / audit_dir / "vlm_judgments.jsonl"):
            issue = row.get("conservative_issue", "")
            if issue and issue != "none" and row.get("sample_id") in ids:
                primary_rows.append(make_case(row, sample_meta, "primary_vlm_flagged", "primary_vlm_visual_flag", audit_dir, run_key, issue))
    cases.extend(sample_rows(primary_rows, 60, 14, used))

    disagreement_rows: list[dict[str, Any]] = []
    for row in failures:
        if row.get("classification") in {"secondary_only_no_primary_support", "inspected_vlm_false_positive", "weak_judge_excluded"}:
            run_key = "heldout8b_final"
            if row.get("sample_id") in available_ids(run_key):
                disagreement_rows.append(make_case(row, sample_meta, "cross_or_weak_judge_disagreement", "judge_disagreement", "vlm_consensus_failure_cases.csv", run_key, row.get("issues", "")))
    cases.extend(sample_rows(disagreement_rows, 22, 15, used))

    if len(cases) != 230:
        raise SystemExit(f"expected 230 cases, got {len(cases)}")

    fields = [
        "case_id",
        "sample_id",
        "case_family",
        "evidence_strength",
        "source_artifact",
        "run_key",
        "issue",
        "dataset_id",
        "query_type",
        "language",
        "expected_chart_family",
        "query",
        "notes",
    ]
    for idx, row in enumerate(cases, 1):
        row["case_id"] = f"stress230_{idx:03d}"
    write_csv(OUT / "stress230_cases.csv", cases, fields)

    run_rows = []
    for run_key in sorted({row["run_key"] for row in cases}):
        rows = [row for row in cases if row["run_key"] == run_key]
        id_file = OUT / "ids_by_run" / f"{run_key}.txt"
        id_file.parent.mkdir(parents=True, exist_ok=True)
        id_file.write_text("\n".join(row["sample_id"] for row in rows) + "\n", encoding="utf-8")
        run_rows.append({"run_key": run_key, "n": len(rows), "sample_ids": str(id_file.relative_to(OUT)), **RUNS[run_key]})
    write_csv(OUT / "stress230_run_config.csv", run_rows, ["run_key", "n", "sample_ids", "outputs", "split", "metrics"])

    counts = Counter(row["case_family"] for row in cases)
    strengths = Counter(row["evidence_strength"] for row in cases)
    write_csv(OUT / "stress230_counts.csv", [{"case_family": k, "n": v} for k, v in sorted(counts.items())], ["case_family", "n"])
    readme = f"""# Stress230 Audit Set

This directory contains a 230-case audit/stress set for the VLM-as-judge paper.

The set is intentionally stratified by evidence provenance:

{chr(10).join(f'- {key}: {value}' for key, value in sorted(counts.items()))}

Evidence strength:

{chr(10).join(f'- {key}: {value}' for key, value in sorted(strengths.items()))}

Use `stress230_run_config.csv` to run VLM audits per source artifact. The set
contains true repair-confirmed cases, deterministic/programmatic suspected
failures, primary VLM flags, and judge-disagreement cases. It should therefore
be reported as a stratified audit set, not as 230 human-verified failures.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({"n": len(cases), "case_family": dict(counts), "run_groups": {r["run_key"]: r["n"] for r in run_rows}}, indent=2))


if __name__ == "__main__":
    main()
