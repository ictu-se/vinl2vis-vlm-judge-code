# Known-Bad VLM Judge Stress Summary

| Setting | Judge | n | Detected known-bad | Accepted known-bad | Conservative issues |
|---|---:|---:|---:|---:|---|
| 4B pre-repair | qwen3-vl:4b | 5 | 5 (100.0%) | 0.0% | `{"wrong_chart_type": 5}` |
| 4B pre-repair | qwen2.5vl:3b | 5 | 0 (0.0%) | 100.0% | `{"none": 5}` |
| 4B pre-repair | minicpm-v | 5 | 0 (0.0%) | 100.0% | `{"none": 5}` |
| 4B pre-repair | llava:7b | 5 | 4 (80.0%) | 20.0% | `{"none": 1, "wrong_fields": 4}` |
| 4B pre-repair | moondream | 5 | 0 (0.0%) | 100.0% | `{"none": 5}` |
| 8B intermediate bad | qwen3-vl:4b | 3 | 3 (100.0%) | 0.0% | `{"wrong_chart_type": 3}` |
| 8B intermediate bad | qwen2.5vl:3b | 3 | 0 (0.0%) | 100.0% | `{"none": 3}` |
| 8B intermediate bad | minicpm-v | 3 | 0 (0.0%) | 100.0% | `{"none": 3}` |
| 8B intermediate bad | llava:7b | 3 | 2 (66.7%) | 33.3% | `{"none": 1, "wrong_fields": 2}` |
| 8B intermediate bad | moondream | 3 | 0 (0.0%) | 100.0% | `{"none": 3}` |

Known-bad detection is counted as `acceptable=false` under the prompt-v4 structured judgment. These items are pre-repair artifacts that the earlier audit identified as chart-family failures.