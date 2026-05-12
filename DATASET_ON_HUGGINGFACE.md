# Dataset Package Boundary

The VLM-as-judge paper reuses ViNL2Vis-FaithBench rendered artifacts, calibration cases, and model outputs. GitHub should contain the compact code-and-evidence package. Hugging Face should contain the full dataset package, including large rendered images and source-table artifacts.

Recommended Hugging Face dataset URL:

```text
https://huggingface.co/datasets/vinhnt/vinl2vis-faithbench
```

GitHub package:

- scripts needed to rebuild paper-facing summaries,
- model-label CSV files,
- difficulty-normalized and middle-band slices,
- stress-screening summaries,
- checksum manifest.

Hugging Face package:

- full benchmark data,
- rendered chart images,
- source tables and metadata,
- full annotation package with images,
- large model-output artifacts.
