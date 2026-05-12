# Model-Assisted Annotation Summary

| Model | n | Overall yes | Overall no | Unclear | Top errors |
|---|---:|---:|---:|---:|---|
| bakllava_latest | 15 | 66.7% | 0.0% | 33.3% | `unclear:15` |
| gemini_gemini_2_5_flash | 26 | 80.8% | 19.2% | 0.0% | `none:21; unreadable:3; wrong_fields:1; wrong_chart_type:1` |
| granite3_2_vision_latest | 240 | 88.3% | 0.0% | 11.7% | `none:240` |
| llama3_2_vision_11b | 32 | 93.8% | 0.0% | 6.2% | `none:30; unclear:2` |
| llava:7b | 240 | 0.4% | 45.8% | 53.8% | `wrong_chart_type:110; unclear:71; wrong_fields:57; none:2` |
| llava_llama3_8b | 80 | 98.8% | 1.2% | 0.0% | `empty_or_broken:67; none:12; unclear:1` |
| minicpm-v | 240 | 95.4% | 4.2% | 0.4% | `none:228; missing_transform:5; missing_labels:5; unclear:1; empty_or_broken:1` |
| openai_gpt_4o | 240 | 70.0% | 30.0% | 0.0% | `none:168; unreadable:35; wrong_fields:33; missing_labels:2; wrong_chart_type:2` |
| qwen2.5vl:3b | 240 | 99.2% | 0.4% | 0.4% | `none:238; missing_labels:1; wrong_chart_type:1` |
| qwen3-vl:4b | 240 | 85.8% | 14.2% | 0.0% | `none:206; wrong_chart_type:15; empty_or_broken:13; wrong_fields:4; unclear:2` |

| Pair | n | Overall agreement | Overall kappa | Error agreement | Error kappa |
|---|---:|---:|---:|---:|---:|
| bakllava_latest vs gemini_gemini_2_5_flash | 15 | 66.7% | 0.210 | 0.0% | 0.000 |
| bakllava_latest vs granite3_2_vision_latest | 15 | 66.7% | 0.000 | 0.0% | 0.000 |
| bakllava_latest vs llama3_2_vision_11b | 15 | 66.7% | 0.000 | 0.0% | 0.000 |
| bakllava_latest vs llava:7b | 15 | 6.7% | 0.000 | 26.7% | 0.000 |
| bakllava_latest vs llava_llama3_8b | 15 | 66.7% | 0.000 | 0.0% | 0.000 |
| bakllava_latest vs minicpm-v | 15 | 66.7% | 0.000 | 0.0% | 0.000 |
| bakllava_latest vs openai_gpt_4o | 15 | 60.0% | 0.053 | 0.0% | 0.000 |
| bakllava_latest vs qwen2.5vl:3b | 15 | 66.7% | 0.000 | 0.0% | 0.000 |
| bakllava_latest vs qwen3-vl:4b | 15 | 66.7% | 0.000 | 0.0% | 0.000 |
| gemini_gemini_2_5_flash vs granite3_2_vision_latest | 26 | 76.9% | 0.093 | 80.8% | 0.000 |
| gemini_gemini_2_5_flash vs llama3_2_vision_11b | 26 | 76.9% | -0.033 | 76.9% | -0.033 |
| gemini_gemini_2_5_flash vs llava:7b | 26 | 11.5% | -0.012 | 0.0% | -0.030 |
| gemini_gemini_2_5_flash vs llava_llama3_8b | 26 | 80.8% | 0.000 | 23.1% | 0.054 |
| gemini_gemini_2_5_flash vs minicpm-v | 26 | 80.8% | 0.000 | 80.8% | 0.000 |
| gemini_gemini_2_5_flash vs openai_gpt_4o | 26 | 88.5% | 0.598 | 88.5% | 0.614 |
| gemini_gemini_2_5_flash vs qwen2.5vl:3b | 26 | 80.8% | 0.000 | 80.8% | 0.000 |
| gemini_gemini_2_5_flash vs qwen3-vl:4b | 26 | 80.8% | 0.000 | 80.8% | 0.000 |
| granite3_2_vision_latest vs llama3_2_vision_11b | 32 | 87.5% | -0.067 | 93.8% | 0.000 |
| granite3_2_vision_latest vs llava:7b | 240 | 7.5% | 0.009 | 0.8% | 0.000 |
| granite3_2_vision_latest vs llava_llama3_8b | 80 | 88.8% | -0.011 | 15.0% | 0.000 |
| granite3_2_vision_latest vs minicpm-v | 240 | 84.2% | -0.011 | 95.0% | 0.000 |
| granite3_2_vision_latest vs openai_gpt_4o | 240 | 64.2% | 0.061 | 70.0% | 0.000 |
| granite3_2_vision_latest vs qwen2.5vl:3b | 240 | 87.9% | 0.022 | 99.2% | 0.000 |
| granite3_2_vision_latest vs qwen3-vl:4b | 240 | 77.1% | 0.052 | 85.8% | 0.000 |
| llama3_2_vision_11b vs llava:7b | 32 | 3.1% | 0.006 | 3.1% | 0.014 |
| llama3_2_vision_11b vs llava_llama3_8b | 32 | 93.8% | 0.000 | 15.6% | -0.024 |
| llama3_2_vision_11b vs minicpm-v | 32 | 93.8% | 0.000 | 93.8% | 0.000 |
| llama3_2_vision_11b vs openai_gpt_4o | 32 | 78.1% | -0.047 | 78.1% | -0.047 |
| llama3_2_vision_11b vs qwen2.5vl:3b | 32 | 93.8% | 0.000 | 93.8% | 0.000 |
| llama3_2_vision_11b vs qwen3-vl:4b | 32 | 93.8% | 0.000 | 93.8% | 0.000 |
| llava:7b vs llava_llama3_8b | 80 | 0.0% | -0.006 | 0.0% | -0.003 |
| llava:7b vs minicpm-v | 240 | 1.7% | -0.009 | 0.8% | -0.001 |
| llava:7b vs openai_gpt_4o | 240 | 6.7% | -0.086 | 4.2% | -0.001 |
| llava:7b vs qwen2.5vl:3b | 240 | 0.8% | 0.000 | 0.4% | -0.006 |
| llava:7b vs qwen3-vl:4b | 240 | 5.8% | -0.011 | 5.8% | 0.017 |
| llava_llama3_8b vs minicpm-v | 80 | 98.8% | 0.000 | 13.8% | -0.013 |
| llava_llama3_8b vs openai_gpt_4o | 80 | 72.5% | -0.024 | 13.8% | 0.030 |
| llava_llama3_8b vs qwen2.5vl:3b | 80 | 98.8% | 0.000 | 15.0% | 0.000 |
| llava_llama3_8b vs qwen3-vl:4b | 80 | 93.8% | -0.020 | 20.0% | 0.019 |
| minicpm-v vs openai_gpt_4o | 240 | 73.3% | 0.166 | 69.6% | 0.092 |
| minicpm-v vs qwen2.5vl:3b | 240 | 95.4% | 0.145 | 94.6% | 0.063 |
| minicpm-v vs qwen3-vl:4b | 240 | 85.8% | 0.191 | 83.8% | 0.118 |
| openai_gpt_4o vs qwen2.5vl:3b | 240 | 69.6% | 0.001 | 69.6% | 0.005 |
| openai_gpt_4o vs qwen3-vl:4b | 240 | 75.0% | 0.299 | 67.1% | 0.170 |
| qwen2.5vl:3b vs qwen3-vl:4b | 240 | 85.8% | 0.044 | 85.4% | 0.018 |

These labels are model-assisted pre-annotations, not human calibration labels.
