#!/usr/bin/env python3
"""Build a human annotation package for the VLM-as-judge calibration set."""

from __future__ import annotations

import csv
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "conferences" / "04_vlm_as_judge_nl2vis"
CALIB = PAPER / "calibration"
PACKAGE = CALIB / "annotation_package"


HUMAN_FIELDS = [
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_image_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    bases = [
        ROOT / "benchmark" / "faithbench" / "results",
        PAPER / "stress",
        PAPER / "stress230" / "audits",
    ]
    for base in bases:
        if not base.exists():
            continue
        for image_dir in base.glob("*/images"):
            for path in image_dir.glob("*.png"):
                index.setdefault(path.stem, path)
    return index


def guideline_text() -> str:
    return """# Human Annotation Guidelines

Goal: judge whether a rendered chart is visually faithful enough to the user query. The task is not to reward beauty. It is to decide whether a human reader can inspect the chart and verify the requested analytical intent.

Annotate independently. Do not use the previous VLM judgment as ground truth. The `source_bucket` column is included for later analysis; it should not determine your answer.

## Allowed Labels

`human_visible_chart_family`:
Use one of `area`, `bar`, `boxplot`, `bubble_chart`, `heatmap`, `histogram`, `line`, `point`, `scatter`, `tick_plot`, `table_or_text`, `empty_or_broken`, `unknown`.

`human_chart_family_acceptable`:
Use `yes`, `no`, or `unclear`. Mark `yes` when the visible chart family is the requested family or a defensible equivalent for the query. For example, point and scatter can be equivalent when both show unconnected dots over axes.

`human_labels_readable`:
Use `yes`, `no`, or `unclear`. Mark `yes` if title, axis labels, or legend are readable enough to understand what the plotted fields are.

`human_relevant_fields_visible`:
Use `yes`, `no`, or `unclear`. Mark `yes` if the chart shows the fields needed by the query. Do not require exact underscore field names if the natural-language label is equivalent.

`human_transform_preserved`:
Use `yes`, `no`, `not_applicable`, or `unclear`. Mark `no` if a requested latest-year filter, ranking/sorting, grouping, aggregation, or comparison is visibly missing. Use `unclear` when the image alone cannot verify it.

`human_overall_acceptable`:
Use `yes`, `no`, or `unclear`. Mark `yes` only when the chart is usable for the query after considering chart family, labels, visible fields, readability, and visible transformations.

`human_primary_error`:
Use one of `none`, `wrong_chart_type`, `wrong_fields`, `missing_transform`, `missing_labels`, `unreadable`, `empty_or_broken`, `overplotting`, `other`, `unclear`.

`human_confidence`:
Use `high`, `medium`, or `low`.

`human_notes`:
Optional short explanation, especially for `no` or `unclear`.

## Practical Rules

- If the chart is ugly but still lets a reader answer the query, it can be acceptable.
- If a chart has the right type but the requested fields are not visible, mark overall unacceptable.
- If labels are crowded but still identifiable, mark labels readable.
- If the chart clearly uses a wrong visual family, mark overall unacceptable even if labels are readable.
- If the query asks for a latest year, ranking, grouping, or aggregation and the chart does not visibly reflect it, use `missing_transform`.
- If the image is missing from the package, leave the human fields blank and write `image_missing` in `human_notes`.
"""


def write_placeholder(path: Path, sample_id: str) -> None:
    image = Image.new("RGB", (1200, 720), "white")
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype("Arial.ttf", 44)
        body_font = ImageFont.truetype("Arial.ttf", 30)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    lines = [
        "No rendered chart is available",
        f"Sample: {sample_id}",
        "This case corresponds to a missing specification or non-plot response.",
        "Annotate as empty_or_broken or not_applicable according to the query.",
    ]
    y = 180
    draw.text((90, y), lines[0], fill="black", font=title_font)
    y += 90
    for line in lines[1:]:
        draw.text((90, y), line, fill="black", font=body_font)
        y += 52
    image.save(path)


def main() -> None:
    rows = read_csv(CALIB / "human_calibration_240.csv")
    image_index = build_image_index()
    images_dir = PACKAGE / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    packaged: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, 1):
        case_id = f"calib_{idx:03d}"
        sample_id = row["sample_id"]
        raw_image_path = row.get("image_path", "")
        src = Path(raw_image_path) if raw_image_path else Path()
        if not raw_image_path or not src.is_file():
            src = image_index.get(sample_id, Path())
        image_file = ""
        if str(src) and src.is_file():
            image_file = f"{case_id}__{sample_id}.png"
            shutil.copy2(src, images_dir / image_file)
        else:
            image_file = f"{case_id}__{sample_id}__placeholder.png"
            write_placeholder(images_dir / image_file, sample_id)
            missing.append({"case_id": case_id, "sample_id": sample_id, "source_bucket": row.get("source_bucket", "")})

        out = {
            "case_id": case_id,
            "sample_id": sample_id,
            "image_file": image_file,
            "source_bucket": row.get("source_bucket", ""),
            "query_type": row.get("query_type", ""),
            "language": row.get("language", ""),
            "expected_chart_family": row.get("expected_chart_family", ""),
            "query": row.get("query", ""),
        }
        for field in HUMAN_FIELDS:
            out[field] = ""
        packaged.append(out)

    fields = [
        "case_id",
        "sample_id",
        "image_file",
        "source_bucket",
        "query_type",
        "language",
        "expected_chart_family",
        "query",
        *HUMAN_FIELDS,
    ]
    write_csv(PACKAGE / "annotation_sheet.csv", packaged, fields)
    write_csv(PACKAGE / "missing_images.csv", missing, ["case_id", "sample_id", "source_bucket"])
    (PACKAGE / "annotation_guidelines.md").write_text(guideline_text(), encoding="utf-8")

    readme = f"""# Annotation Package

This package was generated from `calibration/human_calibration_240.csv`.

- `annotation_sheet.csv`: sheet for annotators.
- `annotation_guidelines.md`: label definitions and practical rules.
- `images/`: copied PNG files named by `case_id` and `sample_id`.
- `missing_images.csv`: cases whose original rendered image was unavailable; the package uses a placeholder PNG for these cases.

Packaged images: {sum(1 for row in packaged if row['image_file'])}
Original missing images replaced by placeholders: {len(missing)}

Source buckets:

{chr(10).join(f'- {key}: {value}' for key, value in sorted(Counter(row['source_bucket'] for row in packaged).items()))}

Recommended workflow: give each annotator a separate copy of this directory and ask them to fill only the `human_*` columns.
"""
    (PACKAGE / "README.md").write_text(readme, encoding="utf-8")
    print({"rows": len(packaged), "packaged_images": sum(1 for row in packaged if row["image_file"]), "missing_images": len(missing)})


if __name__ == "__main__":
    main()
