#!/usr/bin/env python3
"""Use local VLMs to pre-annotate the human calibration package."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "conferences" / "04_vlm_as_judge_nl2vis" / "calibration" / "annotation_package"
OUT = ROOT / "conferences" / "04_vlm_as_judge_nl2vis" / "calibration" / "model_labels"

FIELDS = [
    "case_id",
    "sample_id",
    "image_file",
    "source_bucket",
    "query_type",
    "language",
    "expected_chart_family",
    "query",
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

ALLOWED = {
    "human_visible_chart_family": {
        "area", "bar", "boxplot", "bubble_chart", "heatmap", "histogram",
        "line", "point", "scatter", "tick_plot", "table_or_text",
        "empty_or_broken", "unknown",
    },
    "human_chart_family_acceptable": {"yes", "no", "unclear"},
    "human_labels_readable": {"yes", "no", "unclear"},
    "human_relevant_fields_visible": {"yes", "no", "unclear"},
    "human_transform_preserved": {"yes", "no", "not_applicable", "unclear"},
    "human_overall_acceptable": {"yes", "no", "unclear"},
    "human_primary_error": {
        "none", "wrong_chart_type", "wrong_fields", "missing_transform",
        "missing_labels", "unreadable", "empty_or_broken", "overplotting",
        "other", "unclear",
    },
    "human_confidence": {"high", "medium", "low"},
}


def safe_model(model: str) -> str:
    return model.replace(":", "_").replace(".", "_").replace("-", "_")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def prompt(row: dict[str, str]) -> str:
    return f"""
You are annotating one rendered chart for a natural-language-to-visualization study.

Judge only the provided chart image and the user query. Do not reward visual beauty.
Decide whether the chart is usable and faithful enough for the query.

Return only strict JSON with exactly these keys:
{{
  "human_visible_chart_family": "area|bar|boxplot|bubble_chart|heatmap|histogram|line|point|scatter|tick_plot|table_or_text|empty_or_broken|unknown",
  "human_chart_family_acceptable": "yes|no|unclear",
  "human_labels_readable": "yes|no|unclear",
  "human_relevant_fields_visible": "yes|no|unclear",
  "human_transform_preserved": "yes|no|not_applicable|unclear",
  "human_overall_acceptable": "yes|no|unclear",
  "human_primary_error": "none|wrong_chart_type|wrong_fields|missing_transform|missing_labels|unreadable|empty_or_broken|overplotting|other|unclear",
  "human_confidence": "high|medium|low",
  "human_notes": "one short sentence"
}}

Rules:
- Use "yes" for overall acceptable only if chart type, fields, labels/readability, and visible transformations are adequate.
- If the image says no rendered chart is available, use empty_or_broken and overall no unless the query explicitly asks not to plot.
- If the expected chart family is none and the query is unanswerable, a non-chart refusal/table/text may be acceptable.
- Do not require exact underscore field names if the natural-language label is equivalent.
- Use not_applicable for transform preservation when the query does not request filtering, ranking, grouping, aggregation, or latest-year selection.

User query: {row.get("query", "")}
Expected chart family: {row.get("expected_chart_family", "")}
Query type: {row.get("query_type", "")}
Language: {row.get("language", "")}
"""


def ollama(model: str, text: str, image_path: Path, host: str, timeout: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": text,
        "images": [base64.b64encode(image_path.read_bytes()).decode("ascii")],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        host.rstrip("/") + "/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    raw = data.get("response", "") or data.get("thinking", "")
    return parse_json_response(raw)


def parse_json_response(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    text = str(raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    elif text.startswith("{") and "human_notes" in text:
        text = text + "}"
    try:
        return json.loads(text)
    except Exception:
        return {"parse_error": text[:500]}


def normalize_label(key: str, value: Any) -> str:
    text = str(value or "").strip().lower().replace(" ", "_")
    if key == "human_visible_chart_family" and text == "bubble":
        text = "bubble_chart"
    if key in ALLOWED and text not in ALLOWED[key]:
        return "unclear" if "unclear" in ALLOWED[key] else "unknown"
    return text


def normalize_annotation(parsed: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key in ALLOWED:
        out[key] = normalize_label(key, parsed.get(key, ""))
    out["human_notes"] = str(parsed.get("human_notes", parsed.get("parse_error", "")))[:300]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["qwen3-vl:4b", "qwen2.5vl:3b"])
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--case-file", default="")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    sheet = read_csv(PACKAGE / "annotation_sheet.csv")
    if args.case_file:
        case_rows = read_csv(Path(args.case_file))
        case_ids = {row["case_id"] for row in case_rows}
        sheet = [row for row in sheet if row["case_id"] in case_ids]
    if args.limit:
        sheet = sheet[: args.limit]

    for model in args.models:
        out_path = OUT / f"{safe_model(model)}.csv"
        progress_path = OUT / f"{safe_model(model)}.progress.json"
        rows = read_csv(out_path) if out_path.exists() and not args.force else []
        done = {row["case_id"] for row in rows if row.get("human_overall_acceptable")}
        for idx, row in enumerate(sheet, 1):
            if row["case_id"] in done:
                continue
            image_path = PACKAGE / "images" / row["image_file"]
            try:
                parsed = ollama(model, prompt(row), image_path, args.host, args.timeout)
                ann = normalize_annotation(parsed if isinstance(parsed, dict) else {})
            except Exception as exc:
                ann = {
                    "human_visible_chart_family": "unknown",
                    "human_chart_family_acceptable": "unclear",
                    "human_labels_readable": "unclear",
                    "human_relevant_fields_visible": "unclear",
                    "human_transform_preserved": "unclear",
                    "human_overall_acceptable": "unclear",
                    "human_primary_error": "unclear",
                    "human_confidence": "low",
                    "human_notes": str(exc)[:300],
                }
            rows.append({**row, **ann})
            write_csv(out_path, rows)
            progress_path.write_text(
                json.dumps(
                    {
                        "model": model,
                        "completed": len(rows),
                        "total": len(sheet),
                        "completed_pct": round(100 * len(rows) / len(sheet), 2),
                        "last_case_id": row["case_id"],
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        print(json.dumps({"model": model, "rows": len(rows), "output": str(out_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
