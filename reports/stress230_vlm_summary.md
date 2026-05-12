# Stress230 VLM Summary

| Judge | n | Reject | Accept | Chart-family match | Label match | Readable |
|---|---:|---:|---:|---:|---:|---:|
| qwen3-vl:4b | 230 | 37.8% | 62.2% | 62.2% | 99.6% | 99.6% |
| qwen2.5vl:3b | 230 | 3.0% | 97.0% | 97.0% | 100.0% | 100.0% |
| minicpm-v | 230 | 3.9% | 96.1% | 98.7% | 43.9% | 96.1% |
| llava:7b | 230 | 67.8% | 32.2% | 80.4% | 21.3% | 97.4% |
| moondream | 230 | 2.6% | 97.4% | 43.9% | 89.1% | 97.4% |

## By Evidence Family

| Judge | Case family | n | Reject | Accept | Issues |
|---|---|---:|---:|---:|---|
| llava:7b | cross_or_weak_judge_disagreement | 22 | 95.5% | 4.5% | `{"none": 1, "wrong_fields": 19, "wrong_fields|unreadable": 2}` |
| llava:7b | major_visual_sanity_failure | 70 | 74.3% | 25.7% | `{"none": 18, "wrong_chart_type": 44, "wrong_fields": 8}` |
| llava:7b | primary_vlm_flagged | 60 | 76.7% | 23.3% | `{"none": 14, "unreadable": 1, "wrong_fields": 45}` |
| llava:7b | repair_confirmed_known_bad | 8 | 75.0% | 25.0% | `{"none": 2, "wrong_fields": 6}` |
| llava:7b | strict_transform_failure | 70 | 44.3% | 55.7% | `{"none": 39, "wrong_fields": 31}` |
| minicpm-v | cross_or_weak_judge_disagreement | 22 | 0.0% | 100.0% | `{"none": 22}` |
| minicpm-v | major_visual_sanity_failure | 70 | 8.6% | 91.4% | `{"empty_or_broken": 2, "missing_labels": 2, "none": 64, "wrong_chart_type": 2}` |
| minicpm-v | primary_vlm_flagged | 60 | 5.0% | 95.0% | `{"none": 57, "wrong_chart_type": 1, "wrong_fields": 2}` |
| minicpm-v | repair_confirmed_known_bad | 8 | 0.0% | 100.0% | `{"none": 8}` |
| minicpm-v | strict_transform_failure | 70 | 0.0% | 100.0% | `{"none": 70}` |
| moondream | cross_or_weak_judge_disagreement | 22 | 4.5% | 95.5% | `{"missing": 1, "none": 21}` |
| moondream | major_visual_sanity_failure | 70 | 1.4% | 98.6% | `{"missing": 1, "none": 69}` |
| moondream | primary_vlm_flagged | 60 | 6.7% | 93.3% | `{"missing": 4, "none": 56}` |
| moondream | repair_confirmed_known_bad | 8 | 0.0% | 100.0% | `{"none": 8}` |
| moondream | strict_transform_failure | 70 | 0.0% | 100.0% | `{"none": 70}` |
| qwen2.5vl:3b | cross_or_weak_judge_disagreement | 22 | 0.0% | 100.0% | `{"none": 22}` |
| qwen2.5vl:3b | major_visual_sanity_failure | 70 | 10.0% | 90.0% | `{"none": 63, "wrong_chart_type": 7}` |
| qwen2.5vl:3b | primary_vlm_flagged | 60 | 0.0% | 100.0% | `{"none": 60}` |
| qwen2.5vl:3b | repair_confirmed_known_bad | 8 | 0.0% | 100.0% | `{"none": 8}` |
| qwen2.5vl:3b | strict_transform_failure | 70 | 0.0% | 100.0% | `{"none": 70}` |
| qwen3-vl:4b | cross_or_weak_judge_disagreement | 22 | 0.0% | 100.0% | `{"none": 22}` |
| qwen3-vl:4b | major_visual_sanity_failure | 70 | 28.6% | 71.4% | `{"none": 50, "wrong_chart_type": 20}` |
| qwen3-vl:4b | primary_vlm_flagged | 60 | 98.3% | 1.7% | `{"none": 1, "wrong_chart_type": 57, "wrong_fields": 2}` |
| qwen3-vl:4b | repair_confirmed_known_bad | 8 | 100.0% | 0.0% | `{"wrong_chart_type": 8}` |
| qwen3-vl:4b | strict_transform_failure | 70 | 0.0% | 100.0% | `{"none": 70}` |
