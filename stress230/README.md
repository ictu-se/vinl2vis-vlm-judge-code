# Stress230 Audit Set

This directory contains a 230-case audit/stress set for the VLM-as-judge paper.

The set is intentionally stratified by evidence provenance:

- cross_or_weak_judge_disagreement: 22
- major_visual_sanity_failure: 70
- primary_vlm_flagged: 60
- repair_confirmed_known_bad: 8
- strict_transform_failure: 70

Evidence strength:

- deterministic_semantic_failure: 70
- judge_disagreement: 22
- primary_vlm_visual_flag: 60
- programmatic_visual_failure: 70
- repair_confirmed: 8

Use `stress230_run_config.csv` to run VLM audits per source artifact. The set
contains true repair-confirmed cases, deterministic/programmatic suspected
failures, primary VLM flags, and judge-disagreement cases. It should therefore
be reported as a stratified audit set, not as 230 human-verified failures.
