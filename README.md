# ViNL2Vis VLM Judge

This repository is the code-and-evidence package for the paper `Calibrating Vision-Language Models as Chart-Faithfulness Judges for Natural-Language-to-Visualization`.

The package studies vision-language models (VLMs) as bounded chart-faithfulness judges for natural-language-to-visualization (NL2Vis). It contains scripts, generated evidence files, calibration slices, model-label files, middle-band screening outputs, stress-case summaries, and reports used to reproduce the paper-facing tables and figures. The manuscript source is intentionally not included in this public code-and-data package.

## Repository Layout

- `scripts/`: scripts for VLM model annotation, stress-case screening, calibration package construction, and paper-asset generation.
- `calibration/`: 160-case difficulty-normalized slice, 240-case annotation package metadata, five expert annotation files, expert majority-vote labels, model--expert agreement summaries, 24/72-case middle-band slices, and model-label CSV files.
- `stress230/`: 230-case stress-screening summaries and judgment details.
- `reports/`: paper-facing evidence summaries exported from the experiments.
- `docs/`: experiment protocol and planning notes.

## Data Boundary

This repository is intentionally a compact code-and-evidence package. The full ViNL2Vis-FaithBench dataset, source tables, rendered chart images, and large benchmark artifacts should be distributed through the Hugging Face dataset package:

```text
https://huggingface.co/datasets/vinhnt/vinl2vis-faithbench
```

Keeping GitHub for code/evidence and Hugging Face for full data mirrors the release pattern used by the main ViNL2Vis-FaithBench repository.

## Quick Reproduction

Install the Python dependencies used by the ViNL2Vis-FaithBench pipeline, then run the paper-asset scripts from the project root:

```bash
python scripts/summarize_vlm_model_annotation.py
python scripts/summarize_vlm_judge_stress230.py
python scripts/build_vlm_judge_paper3_assets.py
```

Some scripts expect the full benchmark artifacts to be available under the original project layout. The compact CSV files included here are sufficient to inspect the reported tables and to verify the model-screening evidence used in the manuscript.

## License

The code in this repository is released under the MIT License. Dataset artifacts should follow the license specified in the Hugging Face dataset package and the source-data compatibility notes.
