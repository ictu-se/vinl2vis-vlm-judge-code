# VLM-as-Judge Evidence Summary

Generated from existing ViNL2Vis-FaithBench VLM audit artifacts.

## Primary qwen3-vl Full Audits

| Setting | Judge | n | Acceptable | Chart family | Labels | Readable | Issues |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Vietnamese balanced | `qwen3-vl:4b` | 800 | 96.5 | 96.625 | 99.875 | 100 | `{"none": 772, "wrong_chart_type": 26, "wrong_fields": 2}` |
| English explicit | `qwen3-vl:4b` | 1000 | 95.2 | 95.3 | 99.9 | 99.8 | `{"none": 952, "wrong_chart_type": 47, "wrong_fields": 1}` |
| Matched bilingual | `qwen3-vl:4b` | 1000 | 98.2 | 98.2 | 100 | 100 | `{"none": 982, "wrong_chart_type": 18}` |
| Held-out Vietnamese | `qwen3-vl:4b` | 660 | 99.848 | 99.848 | 100 | 100 | `{"none": 659, "wrong_chart_type": 1}` |

## Cross-Judge Held-Out Audit

| Judge | Tier | n | Acceptable | Chart family | Labels | Readable | Issues |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `qwen2.5vl:3b` | primary | 660 | 100.0 | 100.0 | 100.0 | 100.0 | `{"none": 660}` |
| `qwen3-vl:4b` | primary | 660 | 99.848 | 99.848 | 100.0 | 100.0 | `{"none": 659, "wrong_chart_type": 1}` |
| `minicpm-v` | secondary | 660 | 99.091 | 100.0 | 83.182 | 99.091 | `{"empty_or_broken": 2, "explanation": 1, "none": 654, "wrong_chart_type": 2, "wrong_fields": 1}` |
| `llava:7b` | weak | 660 | 47.8 | 100.0 | 0.455 | 98.483 | `{"none": 315, "unreadable": 4, "wrong_fields": 334, "wrong_fields|unreadable": 6}` |
| `moondream` | weak | 660 | 99.848 | 22.424 | 81.97 | 99.848 | `{"missing": 113, "unreadable": 545, "wrong_fields": 2}` |

## Failure-Case Classifications

| Classification | Count |
| --- | ---: |
| inspected_vlm_false_positive | 1 |
| secondary_only_no_primary_support | 6 |
| targeted_repair_check | 3 |
| true_repair_gap_resolved | 8 |
| weak_judge_excluded | 340 |

## Immediate Interpretation

- `qwen3-vl:4b` is useful as a primary local visual auditor for chart-family, labels, and readability.
- `qwen2.5vl:3b` agrees strongly on the final held-out audit, but its all-accept behavior needs stress tests on known-bad cases.
- `llava:7b` and `moondream` should be analyzed as weak judges because their label or chart-family behavior is unstable.
- Existing evidence supports a triage claim: VLM judges discover visual repair gaps, but deterministic evaluators remain necessary for semantic faithfulness.
