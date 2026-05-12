#!/usr/bin/env python3
"""Use API VLMs to annotate the 240-case calibration package.

The script intentionally reads API keys only from environment variables:
- OPENAI_API_KEY for OpenAI models, e.g. openai:gpt-4o
- GEMINI_API_KEY or GOOGLE_API_KEY for Gemini models, e.g. gemini:gemini-2.5-pro
- HF_TOKEN or HUGGINGFACEHUB_API_TOKEN for Hugging Face Inference Providers,
  e.g. hf:Qwen/Qwen2.5-VL-7B-Instruct or
  hf@fireworks-ai:Qwen/Qwen3-VL-30B-A3B-Instruct
- OPENROUTER_API_KEY for OpenRouter models, e.g.
  openrouter:qwen/qwen2.5-vl-7b-instruct:free
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from huggingface_hub import InferenceClient
    from huggingface_hub.errors import HfHubHTTPError
except ImportError:  # pragma: no cover - optional dependency for API runs only
    InferenceClient = None  # type: ignore[assignment]
    HfHubHTTPError = RuntimeError  # type: ignore[assignment]


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
    return model.replace(":", "_").replace("@", "_").replace(".", "_").replace("-", "_").replace("/", "_")


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
- Be conservative: if the query asks for a specific chart family and the image uses another family, mark overall no.
- Do not mark a chart acceptable when axis labels or legends are unreadable enough to prevent verification.

User query: {row.get("query", "")}
Expected chart family: {row.get("expected_chart_family", "")}
Query type: {row.get("query_type", "")}
Language: {row.get("language", "")}
"""


def data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_openai(model: str, text: str, image_path: Path, timeout: int) -> dict[str, Any]:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": data_url(image_path)}},
                ],
            }
        ],
    }
    data = post_json(
        "https://api.openai.com/v1/chat/completions",
        payload,
        {"Authorization": f"Bearer {key}"},
        timeout,
    )
    raw = data["choices"][0]["message"]["content"]
    return json.loads(raw)


def call_openrouter(model: str, text: str, image_path: Path, timeout: int) -> dict[str, Any]:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": data_url(image_path)}},
                ],
            }
        ],
    }
    data = post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        payload,
        {
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://github.com/vinhnt/ViNL2Vis-FaithBench",
            "X-Title": "ViNL2Vis FaithBench VLM Judge Audit",
        },
        timeout,
    )
    raw = data["choices"][0]["message"]["content"]
    return parse_json_response(raw)


def call_gemini(model: str, text: str, image_path: Path, timeout: int) -> dict[str, Any]:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not set")
    mime = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    payload = {
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": text},
                    {
                        "inlineData": {
                            "mimeType": mime,
                            "data": base64.b64encode(image_path.read_bytes()).decode("ascii"),
                        }
                    },
                ],
            }
        ],
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    data = post_json(url, payload, {}, timeout)
    raw = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw)


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
    return json.loads(text)


def call_huggingface(model: str, provider: str | None, text: str, image_path: Path, timeout: int) -> dict[str, Any]:
    if InferenceClient is None:
        raise RuntimeError("huggingface_hub is not installed")
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN or HUGGINGFACEHUB_API_TOKEN is not set")
    client = InferenceClient(
        model=model,
        provider=provider or os.environ.get("HF_PROVIDER") or "auto",
        token=token,
        timeout=timeout,
    )
    completion = client.chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=512,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": data_url(image_path)}},
                ],
            }
        ],
    )
    raw = completion.choices[0].message.content
    return parse_json_response(raw)


def call_model(model_spec: str, text: str, image_path: Path, timeout: int) -> dict[str, Any]:
    if model_spec.startswith("hf@"):
        provider_spec, _, model = model_spec.partition(":")
        if not model:
            raise ValueError("Hugging Face provider model must be formatted as hf@<provider>:<model_id>")
        return call_huggingface(model, provider_spec[3:], text, image_path, timeout)
    provider, _, model = model_spec.partition(":")
    if provider == "openai" and model:
        return call_openai(model, text, image_path, timeout)
    if provider == "openrouter" and model:
        return call_openrouter(model, text, image_path, timeout)
    if provider == "gemini" and model:
        return call_gemini(model, text, image_path, timeout)
    if provider == "hf" and model:
        return call_huggingface(model, None, text, image_path, timeout)
    raise ValueError("Model must be prefixed as openai:<model>, openrouter:<model>, gemini:<model>, hf:<model_id>, or hf@<provider>:<model_id>")


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
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    sheet = read_csv(PACKAGE / "annotation_sheet.csv")
    if args.limit:
        sheet = sheet[: args.limit]

    for model_spec in args.models:
        out_path = OUT / f"{safe_model(model_spec)}.csv"
        progress_path = OUT / f"{safe_model(model_spec)}.progress.json"
        rows = read_csv(out_path) if out_path.exists() and not args.force else []
        done = {row["case_id"] for row in rows if row.get("human_overall_acceptable")}
        for row in sheet:
            if row["case_id"] in done:
                continue
            image_path = PACKAGE / "images" / row["image_file"]
            try:
                parsed: dict[str, Any] | None = None
                last_exc: Exception | None = None
                for attempt in range(args.retries + 1):
                    try:
                        parsed = call_model(model_spec, prompt(row), image_path, args.timeout)
                        break
                    except urllib.error.HTTPError as exc:
                        last_exc = exc
                        if exc.code not in {429, 500, 502, 503, 504} or attempt == args.retries:
                            raise
                        time.sleep(max(args.sleep, 1.0) * (attempt + 2))
                    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                        last_exc = exc
                        if attempt == args.retries:
                            raise
                        time.sleep(max(args.sleep, 1.0) * (attempt + 2))
                if parsed is None:
                    raise RuntimeError(str(last_exc) if last_exc else "empty API response")
                ann = normalize_annotation(parsed if isinstance(parsed, dict) else {})
            except (urllib.error.HTTPError, urllib.error.URLError, HfHubHTTPError, TimeoutError, socket.timeout, json.JSONDecodeError, KeyError, RuntimeError, ValueError) as exc:
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
                        "model": model_spec,
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
            if args.sleep:
                time.sleep(args.sleep)
        print(json.dumps({"model": model_spec, "rows": len(rows), "output": str(out_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
