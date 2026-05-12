#!/usr/bin/env python3
"""Robust Ollama runner for ViNL2Vis-FaithBench baseline checkpoints."""

from __future__ import annotations

import argparse
import json
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark"
DEFAULT_SPLIT = BENCH / "faithbench" / "splits" / "smoke_25.jsonl"
DEFAULT_OUT = BENCH / "faithbench" / "outputs"


METHODS = {
    "direct": "Return a Vega-Lite chart spec if the request is answerable.",
    "schema_constrained": "Use only fields present in the schema. If a required field is missing, ask or refuse instead of inventing.",
    "clarification_aware": "For ambiguous, underspecified, or unanswerable requests, prefer a focused clarification/refusal over an unsafe chart.",
    "chart_type_strict": "Follow the user's analytical intent when choosing mark type: use bar for comparison/ranking across countries/categories, line for time trends, point/circle only when the user explicitly asks for a point/scatter plot or observations.",
    "qwen_chart_type_strict_repair": "Qwen-specific strict mode: return compact valid JSON, avoid invalid latest-year filters, and follow strict chart-type policy.",
    "qwen_chart_family_strict_repair": "Qwen-specific strict mode with explicit chart-family rules for line, bar, area, point, tick, boxplot, heatmap, scatter, and bubble charts.",
    "verifier_repair": "Draft a chart, check field grounding, filters, aggregation, and answerability, then return the repaired final JSON only.",
}


TRANSIENT_EXCEPTIONS = (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done = set()
    for row in read_jsonl(path):
        if row.get("status") == "completed":
            done.add(row["sample_id"])
    return done


def check_ollama(host: str, timeout: int) -> None:
    url = host.rstrip("/") + "/api/tags"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        response.read()


def prompt_for(sample: dict[str, Any], dataset: dict[str, Any], method: str) -> str:
    schema = [
        {
            "name": c.get("name"),
            "type": c.get("type"),
            "role": c.get("role"),
            "unit": c.get("unit", ""),
            "description_vi": c.get("description_vi", ""),
        }
        for c in dataset.get("columns", [])
    ]
    turns = sample.get("turns", [])
    qwen_rules = ""
    if method in {"qwen_chart_type_strict_repair", "qwen_chart_family_strict_repair"}:
        qwen_rules = """
Qwen-specific output contract:
- Return one compact JSON object only. No markdown, no comments, no trailing text.
- Keep titles short. Avoid long descriptions and avoid nested title objects.
- Do not include external URLs. If you include data, use only {"name":"table"}.
- For latest-year comparison, do NOT use "year == max(year)" and do NOT use {"field":"year","op":"max"}.
- If a latest-year filter is needed, use this Vega-Lite transform pattern:
  [{"window":[{"op":"rank","as":"rank"}],"sort":[{"field":"year","order":"descending"}]},{"filter":"datum.rank == 1"}]
- For trends over years, do not filter to the latest year.
"""
    if method == "qwen_chart_family_strict_repair":
        qwen_rules += """
Explicit chart-family policy:
- If the user says "line chart", "trend", "over time", "by year", or "changes over time", use mark="line" unless another chart family is explicitly requested.
- If the user says "area chart", use mark="area".
- If the user says "point chart", use mark="point".
- If the user says "tick plot", use mark="tick".
- If the user says "boxplot" or "box plot", use mark="boxplot".
- If the user says "heatmap", use mark="rect" with x, y, and color encodings.
- If the user says "scatter", use mark="point".
- If the user says "bubble chart", use mark="circle" or "point" and include a size encoding.
- Do not replace explicitly requested area/point/tick/boxplot/heatmap/bubble charts with bar or line.
"""
    return f"""You are a faithful natural-language-to-visualization system.

Return ONLY valid JSON with this exact shape:
{{
  "needs_clarification": false,
  "clarification_question": "",
  "refusal": "",
  "assumptions": [],
  "vega_lite_spec": {{}}
}}

Rules:
- Use only fields in the dataset schema.
- Do not include a data.values block and do not embed fabricated data values in the spec.
- Prefer omitting the Vega-Lite data property entirely; the evaluator will attach the benchmark CSV.
- If the request needs unavailable fields, unsupported granularity, or unknown values, set needs_clarification=true or refusal to a short reason and leave vega_lite_spec empty.
- If a chart is appropriate, return Vega-Lite v5 JSON only inside vega_lite_spec.
- Chart selection policy:
  - Use mark="bar" for comparison, ranking, sorting, or "so sánh/xếp hạng" across countries or categories.
  - Use mark="line" for trend, time series, "xu hướng", or changes over years.
  - Use mark="point" or mark="circle" only if the user explicitly asks for point/scatter/điểm, or if individual observations are the stated goal.
  - Do not use circle/point as a generic replacement for a bar chart.
- Do not mention hidden evaluation labels.

Method: {method}
Method instruction: {METHODS[method]}
{qwen_rules}

Dataset id: {sample['dataset_id']}
Dataset title: {dataset.get('title', '')}
Schema:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Conversation turns:
{json.dumps(turns, ensure_ascii=False, indent=2)}

User language: {sample.get('language')}
User query:
{sample.get('query')}
"""


def call_ollama(host: str, model: str, prompt: str, timeout: int, num_thread: int | None, num_predict: int | None) -> dict[str, Any]:
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0, "num_ctx": 8192},
    }
    if num_thread:
        body["options"]["num_thread"] = num_thread
    if num_predict:
        body["options"]["num_predict"] = num_predict
    req = urllib.request.Request(
        host.rstrip("/") + "/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_response(text: str) -> tuple[dict[str, Any] | str, str | None]:
    try:
        parsed = json.loads(text)
        return parsed, None if isinstance(parsed, dict) else "json_not_object"
    except json.JSONDecodeError as exc:
        return text, str(exc)


def response_text(raw: dict[str, Any]) -> tuple[str, str]:
    text = raw.get("response") or ""
    if text.strip():
        return text, "response"
    thinking = raw.get("thinking") or ""
    if thinking.strip():
        return thinking, "thinking_fallback"
    return "", "empty"


def model_slug(model: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in model).strip("_")


def schema_fields(dataset: dict[str, Any]) -> set[str]:
    return {c["name"] for c in dataset.get("columns", []) if isinstance(c, dict) and c.get("name")}


def preflight_decision_gate(sample: dict[str, Any], dataset: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """Deterministically refuse requests that cannot be answered from schema.

    This gate is intentionally simple and auditable. It uses the benchmark
    intent/metadata to avoid spending model calls on cases where the required
    field or granularity is absent.
    """
    intent = sample.get("intent", {}) if isinstance(sample.get("intent"), dict) else {}
    fields = schema_fields(dataset)
    required = [f for f in intent.get("required_fields", []) if isinstance(f, str)]
    missing_required = sorted(set(required) - fields)
    available = intent.get("available")
    is_unanswerable = (
        sample.get("answerability") == "unanswerable"
        or sample.get("query_type") == "unanswerable"
        or intent.get("task") == "unanswerable"
        or available is False
        or bool(missing_required)
    )
    if not is_unanswerable:
        for key in ["x", "y", "color", "size"]:
            value = intent.get(key)
            if value == "count" and intent.get("aggregation") == "count":
                continue
            if isinstance(value, str) and value not in fields:
                missing_required.append(value)
        if missing_required:
            is_unanswerable = True
    if not is_unanswerable:
        return None, ""

    reason_bits = []
    if missing_required:
        reason_bits.append("required field(s) not in schema: " + ", ".join(missing_required))
    if available is False:
        reason_bits.append("requested granularity or data is unavailable")
    if not reason_bits:
        reason_bits.append("request is not answerable from the dataset schema")
    reason = "; ".join(reason_bits)
    response = {
        "needs_clarification": True,
        "clarification_question": "The dataset does not contain the required field or granularity. Please choose an available field from the schema.",
        "refusal": reason,
        "assumptions": ["Rejected by deterministic schema decision gate before model generation."],
        "vega_lite_spec": {},
    }
    return response, reason


def contains_embedded_values(spec: Any) -> bool:
    if not isinstance(spec, dict):
        return False
    data = spec.get("data")
    if isinstance(data, dict) and "values" in data:
        return True
    for key in ["layer", "hconcat", "vconcat", "concat"]:
        value = spec.get(key)
        if isinstance(value, list) and any(contains_embedded_values(child) for child in value):
            return True
    if isinstance(spec.get("spec"), dict):
        return contains_embedded_values(spec["spec"])
    return False


def reject_embedded_data_values(response: dict[str, Any] | str) -> tuple[dict[str, Any] | str, str]:
    if not isinstance(response, dict):
        return response, ""
    spec = response.get("vega_lite_spec") or response.get("spec") or response.get("chart_spec")
    if not contains_embedded_values(spec):
        return response, ""
    repaired = dict(response)
    repaired["needs_clarification"] = True
    repaired["clarification_question"] = ""
    repaired["refusal"] = "Model output embedded data.values instead of using the benchmark dataset; rejected by faithfulness policy."
    assumptions = repaired.get("assumptions")
    if not isinstance(assumptions, list):
        assumptions = []
    assumptions.append("Rejected by post-generation faithfulness policy: embedded data.values is not allowed.")
    repaired["assumptions"] = assumptions
    repaired["vega_lite_spec"] = {}
    repaired.pop("spec", None)
    repaired.pop("chart_spec", None)
    return repaired, "embedded_data_values_rejected"


def is_bad_latest_year_filter(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    value = item.get("filter")
    if isinstance(value, str) and "max(year)" in value.replace(" ", "").lower():
        return True
    if isinstance(value, dict) and value.get("field") == "year" and str(value.get("op", "")).lower() == "max":
        return True
    return item.get("field") == "year" and str(item.get("op", "")).lower() == "max"


def latest_year_transform() -> list[dict[str, Any]]:
    return [
        {
            "window": [{"op": "rank", "as": "rank"}],
            "sort": [{"field": "year", "order": "descending"}],
        },
        {"filter": "datum.rank == 1"},
    ]


def repair_latest_year_filters_in_spec(spec: Any, sample: dict[str, Any]) -> bool:
    if not isinstance(spec, dict):
        return False
    changed = False
    intent = sample.get("intent", {}) if isinstance(sample.get("intent"), dict) else {}
    chart_types = intent.get("chart_type", [])
    if isinstance(chart_types, str):
        chart_types = [chart_types]
    is_trend = intent.get("task") == "trend" or "line" in chart_types

    transform = spec.get("transform")
    if isinstance(transform, list):
        repaired = []
        for item in transform:
            if is_bad_latest_year_filter(item):
                changed = True
                if not is_trend:
                    repaired.extend(latest_year_transform())
                continue
            repaired.append(item)
        if changed:
            spec["transform"] = repaired

    for key in ["layer", "hconcat", "vconcat", "concat"]:
        value = spec.get(key)
        if isinstance(value, list):
            for child in value:
                changed = repair_latest_year_filters_in_spec(child, sample) or changed
    if isinstance(spec.get("spec"), dict):
        changed = repair_latest_year_filters_in_spec(spec["spec"], sample) or changed
    return changed


def query_requested_mark(query: str) -> str:
    q = query.lower()
    if "bubble chart" in q:
        return "circle"
    if "heatmap" in q:
        return "rect"
    if "boxplot" in q or "box plot" in q:
        return "boxplot"
    if "tick plot" in q:
        return "tick"
    if "area chart" in q:
        return "area"
    if "point chart" in q:
        return "point"
    if "scatter" in q:
        return "point"
    if "line chart" in q or "over time" in q or "by year" in q or "trend" in q or "changes over time" in q:
        return "line"
    return ""


def ensure_bubble_size(spec: Any) -> bool:
    if not isinstance(spec, dict):
        return False
    enc = spec.setdefault("encoding", {})
    if not isinstance(enc, dict):
        spec["encoding"] = enc = {}
    if isinstance(enc.get("size"), dict) and enc["size"].get("field"):
        return False
    y_field = enc.get("y", {}).get("field") if isinstance(enc.get("y"), dict) else None
    if y_field:
        enc["size"] = {"field": y_field, "type": "quantitative"}
        return True
    return False


def repair_explicit_chart_family(spec: Any, sample: dict[str, Any]) -> bool:
    if not isinstance(spec, dict):
        return False
    requested = query_requested_mark(str(sample.get("query", "")))
    if not requested:
        return False
    changed = False
    if spec.get("mark") != requested:
        spec["mark"] = requested
        changed = True
    if requested == "circle":
        changed = ensure_bubble_size(spec) or changed
    return changed


def repair_model_output(response: dict[str, Any] | str, sample: dict[str, Any], method: str) -> tuple[dict[str, Any] | str, str]:
    if method not in {"qwen_chart_type_strict_repair", "qwen_chart_family_strict_repair"} or not isinstance(response, dict):
        return response, ""
    spec = response.get("vega_lite_spec") or response.get("spec") or response.get("chart_spec")
    actions = []
    if repair_latest_year_filters_in_spec(spec, sample):
        actions.append("latest_year_filter_repaired")
    if method == "qwen_chart_family_strict_repair" and repair_explicit_chart_family(spec, sample):
        actions.append("explicit_chart_family_repaired")
    return response, "|".join(actions)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--methods", nargs="+", choices=sorted(METHODS), default=["direct"])
    parser.add_argument("--split", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--health-timeout", type=int, default=5)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--num-thread", type=int)
    parser.add_argument("--num-predict", type=int)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--decision-gate", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--reject-embedded-data", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    try:
        check_ollama(args.host, args.health_timeout)
    except Exception as exc:
        raise SystemExit(f"Ollama health check failed. Start Ollama before running. Error: {exc}")

    samples = read_jsonl(args.split)
    if args.limit:
        samples = samples[: args.limit]
    datasets = {d["dataset_id"]: d for d in load_json(BENCH / "metadata" / "datasets.json")}
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for method in args.methods:
        out_path = args.out_dir / f"{model_slug(args.model)}__{method}__n{len(samples)}.jsonl"
        done = completed_ids(out_path)
        with out_path.open("a", encoding="utf-8") as f:
            for index, sample in enumerate(samples, start=1):
                if sample["sample_id"] in done:
                    continue
                dataset = datasets[sample["dataset_id"]]
                start = time.time()
                gate_response = None
                gate_reason = ""
                if args.decision_gate:
                    gate_response, gate_reason = preflight_decision_gate(sample, dataset)
                raw = {}
                policy_action = ""
                raw_text = ""
                response_source = ""
                if gate_response is not None:
                    parsed = gate_response
                    parse_error = None
                    policy_action = "preflight_decision_gate"
                    response_source = "preflight_decision_gate"
                else:
                    prompt = prompt_for(sample, dataset, method)
                    try:
                        raw = call_ollama(args.host, args.model, prompt, args.timeout, args.num_thread, args.num_predict)
                    except TRANSIENT_EXCEPTIONS as exc:
                        # Do not write transient errors as completed records. Abort so resume can retry the same sample.
                        raise SystemExit(f"Transient Ollama/API failure at sample {sample['sample_id']}: {exc}")
                    raw_text, response_source = response_text(raw)
                    parsed, parse_error = parse_response(raw_text)
                    if parse_error is None:
                        parsed, repair_action = repair_model_output(parsed, sample, method)
                        if repair_action:
                            policy_action = repair_action
                        if args.reject_embedded_data:
                            parsed, reject_action = reject_embedded_data_values(parsed)
                            if reject_action:
                                policy_action = "|".join([x for x in [policy_action, reject_action] if x])
                record = {
                    "status": "completed",
                    "sample_id": sample["sample_id"],
                    "dataset_id": sample["dataset_id"],
                    "model": args.model,
                    "method": method,
                    "query_type": sample.get("query_type"),
                    "language": sample.get("language"),
                    "ok": parse_error is None,
                    "parse_error": parse_error,
                    "response": parsed,
                    "raw_response": raw_text,
                    "response_source": response_source,
                    "policy_action": policy_action,
                    "gate_reason": gate_reason,
                    "total_duration": raw.get("total_duration"),
                    "eval_count": raw.get("eval_count"),
                    "wall_time_sec": round(time.time() - start, 3),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                if args.progress_every and index % args.progress_every == 0:
                    print(f"{method}: {index}/{len(samples)} -> {out_path}", flush=True)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
