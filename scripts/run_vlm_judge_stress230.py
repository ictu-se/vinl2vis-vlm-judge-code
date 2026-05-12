#!/usr/bin/env python3
"""Run Ollama VLM audits on the 230-case stress set."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRESS = ROOT / "conferences" / "04_vlm_as_judge_nl2vis" / "stress230"

MODELS = [
    "qwen3-vl:4b",
    "qwen2.5vl:3b",
    "minicpm-v",
    "llava:7b",
    "moondream",
]


def safe_model_name(model: str) -> str:
    return model.replace(":", "_").replace(".", "_").replace("-", "_")


def read_run_config() -> list[dict[str, str]]:
    with (STRESS / "stress230_run_config.csv").open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=MODELS)
    parser.add_argument("--only-run-key", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    configs = read_run_config()
    if args.only_run_key:
        configs = [row for row in configs if row["run_key"] == args.only_run_key]
    if not configs:
        raise SystemExit("No matching run config rows")

    for model in args.models:
        safe = safe_model_name(model)
        for cfg in configs:
            out_dir = STRESS / "audits" / f"{cfg['run_key']}__{safe}__promptv4"
            summary = out_dir / "vlm_audit_summary.json"
            progress = out_dir / "vlm_audit_progress.json"
            if summary.exists() and not args.force:
                print(f"[skip] {cfg['run_key']} {model}", flush=True)
                continue
            if progress.exists() and not args.force:
                text = progress.read_text(encoding="utf-8", errors="ignore")
                if '"status": "done"' in text and summary.exists():
                    print(f"[skip] {cfg['run_key']} {model}", flush=True)
                    continue
            cmd = [
                sys.executable,
                str(ROOT / "scripts" / "faithbench_vlm_audit.py"),
                "--outputs",
                str(ROOT / cfg["outputs"]),
                "--split",
                str(ROOT / cfg["split"]),
                "--metrics",
                str(ROOT / cfg["metrics"]),
                "--out-dir",
                str(out_dir),
                "--sample-ids",
                str(STRESS / cfg["sample_ids"]),
                "--sample-n",
                str(cfg["n"]),
                "--ollama-model",
                model,
                "--prompt-version",
                "v4",
            ]
            print(f"[run] {cfg['run_key']} {model} n={cfg['n']}", flush=True)
            subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
