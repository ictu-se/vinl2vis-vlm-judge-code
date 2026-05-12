#!/usr/bin/env python3
"""Build calibration and stress-test artifacts for the VLM-as-judge paper."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmark" / "faithbench" / "results"
OUT = ROOT / "conferences" / "04_vlm_as_judge_nl2vis"
CALIB = OUT / "calibration"
STRESS = OUT / "stress"


PRIMARY_QWEN3_DIRS = [
    RESULTS / "vlm_audit_vietnamese_balanced_auditfix_v2_n1000_qwen3vl4b_promptv4",
    RESULTS / "vlm_audit_english_explicit_auditfix_v2_n1000_qwen3vl4b_promptv4",
    RESULTS / "vlm_audit_matched_bilingual_auditfix_v2_n1000_qwen3vl4b_promptv4",
    RESULTS / "vlm_audit_heldout860_qwen3_8b_auditfix_v4_n860_qwen3vl4b_promptv4",
]

HELDOUT_FINAL_DIRS = {
    "qwen3-vl:4b": RESULTS / "vlm_audit_heldout860_qwen3_8b_auditfix_v4_n860_qwen3vl4b_promptv4",
    "qwen2.5vl:3b": RESULTS / "vlm_audit_heldout860_qwen3_8b_auditfix_v4_n860_qwen25vl3b_promptv4",
    "minicpm-v": RESULTS / "vlm_audit_heldout860_qwen3_8b_auditfix_v4_n860_minicpmv_promptv4",
    "llava:7b": RESULTS / "vlm_audit_heldout860_qwen3_8b_auditfix_v4_n860_llava7b_promptv4",
    "moondream": RESULTS / "vlm_audit_heldout860_qwen3_8b_auditfix_v4_n860_moondream_promptv4",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def rel_image_path(audit_dir: Path, row: dict[str, Any]) -> str:
    image = str(row.get("image_path", "")).replace("\\", "/")
    return str((audit_dir / image).resolve()) if image else ""


def compact_judgment(row: dict[str, Any]) -> str:
    judgment = row.get("judgment", {})
    if not isinstance(judgment, dict):
        return ""
    return json.dumps(
        {
            "acceptable": judgment.get("acceptable", ""),
            "visible_chart_family": judgment.get("visible_chart_family", ""),
            "major_issue": judgment.get("major_issue", ""),
            "conservative_issue": row.get("conservative_issue", ""),
        },
        ensure_ascii=False,
    )


def base_case(row: dict[str, Any], bucket: str, source: str, image_path: str = "") -> dict[str, Any]:
    return {
        "sample_id": row.get("sample_id", ""),
        "source_bucket": bucket,
        "source_artifact": source,
        "dataset_id": row.get("dataset_id", ""),
        "query_type": row.get("query_type", ""),
        "language": row.get("language", ""),
        "expected_chart_family": row.get("chart_family") or row.get("expected_chart_family", ""),
        "query": row.get("query", ""),
        "image_path": image_path,
        "existing_vlm_issue": row.get("conservative_issue") or row.get("issues", ""),
        "existing_vlm_judgment": compact_judgment(row),
        "deterministic_evidence": row.get("issues") or row.get("visual_sanity_tags", "") or row.get("failure_tags", ""),
        "human_visible_chart_family": "",
        "human_chart_family_acceptable": "",
        "human_labels_readable": "",
        "human_relevant_fields_visible": "",
        "human_transform_preserved": "",
        "human_overall_acceptable": "",
        "human_primary_error": "",
        "human_confidence": "",
        "human_notes": "",
    }


def sample_unique(rows: list[dict[str, Any]], n: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    shuffled = rows[:]
    rng.shuffle(shuffled)
    seen: set[tuple[str, str]] = set()
    selected: list[dict[str, Any]] = []
    for row in shuffled:
        key = (row.get("sample_id", ""), row.get("source_bucket", ""))
        if key in seen:
            continue
        selected.append(row)
        seen.add(key)
        if len(selected) >= n:
            break
    return selected


def selected_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("sample_id", "")) for row in rows if row.get("sample_id")}


def build_consensus_accepted() -> list[dict[str, Any]]:
    per_model: dict[str, dict[str, dict[str, Any]]] = {}
    for model, audit_dir in HELDOUT_FINAL_DIRS.items():
        rows = read_jsonl(audit_dir / "vlm_judgments.jsonl")
        per_model[model] = {str(row.get("sample_id")): row for row in rows}
    primary_a = per_model.get("qwen3-vl:4b", {})
    primary_b = per_model.get("qwen2.5vl:3b", {})
    shared = sorted(set(primary_a) & set(primary_b))
    cases: list[dict[str, Any]] = []
    audit_dir = HELDOUT_FINAL_DIRS["qwen3-vl:4b"]
    for sample_id in shared:
        a = primary_a[sample_id]
        b = primary_b[sample_id]
        if a.get("conservative_issue") == "none" and b.get("conservative_issue") == "none":
            cases.append(base_case(a, "vlm_consensus_accepted", audit_dir.name, rel_image_path(audit_dir, a)))
    return cases


def build_primary_flagged() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for audit_dir in PRIMARY_QWEN3_DIRS:
        for row in read_jsonl(audit_dir / "vlm_judgments.jsonl"):
            if row.get("conservative_issue") and row.get("conservative_issue") != "none":
                cases.append(base_case(row, "primary_vlm_flagged", audit_dir.name, rel_image_path(audit_dir, row)))
    return cases


def build_failure_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = read_csv(RESULTS / "vlm_consensus_failure_cases.csv")
    disagreements: list[dict[str, Any]] = []
    weak_only: list[dict[str, Any]] = []
    for row in rows:
        if row.get("classification") == "weak_judge_excluded":
            weak_only.append(base_case(row, "weak_judge_only_flag", "vlm_consensus_failure_cases.csv"))
        elif row.get("classification") in {
            "secondary_only_no_primary_support",
            "inspected_vlm_false_positive",
            "targeted_repair_check",
            "true_repair_gap_resolved",
        }:
            disagreements.append(base_case(row, "cross_judge_disagreement", "vlm_consensus_failure_cases.csv"))
    return disagreements, weak_only


def build_deterministic_failures() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row in read_csv(RESULTS / "strict_transformation_audit.csv"):
        if row.get("issues"):
            cases.append(base_case(row, "deterministic_failure", "strict_transformation_audit.csv"))
    for path in RESULTS.glob("**/visual_sanity_per_output.csv"):
        for row in read_csv(path):
            if row.get("severity", "none") not in {"", "none"}:
                cases.append(base_case(row, "deterministic_failure", str(path.relative_to(RESULTS))))
    return cases


def write_stress_sets(failure_rows: list[dict[str, str]]) -> None:
    STRESS.mkdir(parents=True, exist_ok=True)
    heldout4b = [
        row["sample_id"]
        for row in failure_rows
        if row.get("classification") == "true_repair_gap_resolved"
        and row.get("audit_group") == "heldout4b_before_auditfix_full"
    ]
    heldout8b = [
        row["sample_id"]
        for row in failure_rows
        if row.get("audit_group") == "heldout8b_intermediate_bad_targeted"
    ]
    (STRESS / "heldout4b_before_auditfix_known_bad_ids.txt").write_text(
        "\n".join(sorted(set(heldout4b))) + "\n",
        encoding="utf-8",
    )
    (STRESS / "heldout8b_intermediate_bad_ids.txt").write_text(
        "\n".join(sorted(set(heldout8b))) + "\n",
        encoding="utf-8",
    )
    rows = [
        {"setting": "heldout4b_before_auditfix_full", "sample_id": sample_id}
        for sample_id in sorted(set(heldout4b))
    ] + [
        {"setting": "heldout8b_intermediate_bad_targeted", "sample_id": sample_id}
        for sample_id in sorted(set(heldout8b))
    ]
    write_csv(STRESS / "known_bad_stress_items.csv", rows, ["setting", "sample_id"])


def main() -> None:
    rng_seed = 20260511
    consensus = sample_unique(build_consensus_accepted(), 80, rng_seed)
    primary = sample_unique(build_primary_flagged(), 40, rng_seed + 1)
    disagreements, weak_only = build_failure_cases()
    disagreements = sample_unique(disagreements, 40, rng_seed + 2)
    deterministic = sample_unique(build_deterministic_failures(), 40, rng_seed + 3)
    weak = sample_unique(weak_only, 40, rng_seed + 4)
    calibration_rows = consensus + primary + disagreements + deterministic + weak
    if len(calibration_rows) < 240:
        used = selected_ids(calibration_rows)
        extras = [
            row | {"source_bucket": "supplemental_vlm_consensus_accepted"}
            for row in build_consensus_accepted()
            if row.get("sample_id") not in used
        ]
        calibration_rows.extend(sample_unique(extras, 240 - len(calibration_rows), rng_seed + 5))

    fields = [
        "sample_id",
        "source_bucket",
        "source_artifact",
        "dataset_id",
        "query_type",
        "language",
        "expected_chart_family",
        "query",
        "image_path",
        "existing_vlm_issue",
        "existing_vlm_judgment",
        "deterministic_evidence",
        "human_visible_chart_family",
        "human_chart_family_acceptable",
        "human_labels_readable",
        "human_relevant_fields_visible",
        "human_transform_preserved",
        "human_overall_acceptable",
        "human_primary_error",
        "human_confidence",
        "human_notes",
    ]
    write_csv(CALIB / "human_calibration_240.csv", calibration_rows, fields)

    bucket_counts = Counter(row["source_bucket"] for row in calibration_rows)
    write_csv(
        CALIB / "human_calibration_bucket_counts.csv",
        [{"source_bucket": key, "n": value} for key, value in sorted(bucket_counts.items())],
        ["source_bucket", "n"],
    )
    failure_rows = read_csv(RESULTS / "vlm_consensus_failure_cases.csv")
    write_stress_sets(failure_rows)

    readme = f"""# Paper 3 Calibration Assets

Generated by `scripts/build_vlm_judge_paper3_assets.py`.

## Human calibration subset

`human_calibration_240.csv` contains {len(calibration_rows)} candidate items:

{chr(10).join(f'- {key}: {value}' for key, value in sorted(bucket_counts.items()))}

The sheet intentionally mixes consensus-accepted charts, primary-judge flags,
cross-judge disagreements, deterministic failures, and weak-judge-only flags.
Blank `human_*` columns are reserved for independent human annotation.

## Known-bad stress items

`../stress/known_bad_stress_items.csv` lists the pre-repair visual failures that
are used to test whether a judge can reject charts known to have needed repair.
"""
    (CALIB / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({"calibration_rows": len(calibration_rows), "bucket_counts": dict(bucket_counts)}, indent=2))


if __name__ == "__main__":
    main()
