# Annotation Package

This package was generated from `calibration/human_calibration_240.csv`.

- `annotation_sheet.csv`: sheet for annotators.
- `annotation_guidelines.md`: label definitions and practical rules.
- `images/`: copied PNG files named by `case_id` and `sample_id`.
- `missing_images.csv`: cases whose original rendered image was unavailable; the package uses a placeholder PNG for these cases.

Packaged images: 240
Original missing images replaced by placeholders: 1

Source buckets:

- cross_judge_disagreement: 13
- deterministic_failure: 40
- primary_vlm_flagged: 40
- supplemental_vlm_consensus_accepted: 27
- vlm_consensus_accepted: 80
- weak_judge_only_flag: 40

Recommended workflow: give each annotator a separate copy of this directory and ask them to fill only the `human_*` columns.
