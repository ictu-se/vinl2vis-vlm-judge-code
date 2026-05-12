# VLM-as-Judge Audit Protocol

## Audit Object

Each audit item contains:

- rendered chart image;
- user query;
- dataset schema summary;
- expected or accepted chart family;
- relevant fields and transformations;
- deterministic evaluator scores and failure tags.

The VLM judge is not asked to infer the whole benchmark from the image alone. It receives a compact audit packet so that the judgment is about faithfulness to the request and expected analytical commitments.

## Judge Output

The judge returns structured fields:

- `acceptable`: whether the rendered chart is visually acceptable for the query;
- `chart_family_match`: whether the visible chart family matches an expected or accepted family;
- `labels_match`: whether field labels and legends correspond to the intended variables;
- `readable`: whether the chart is legible enough to inspect;
- `major_issue`: one of `none`, `wrong_chart_type`, `wrong_fields`, `unreadable`, `empty_or_broken`, `missing`, or `explanation`;
- `rationale`: a short explanation for disagreement cases.

## Judge Tiers

- **Primary**: stable on smoke tests, full audits, targeted disagreement reruns, and known-bad stress tests. Current candidate: `qwen3-vl:4b`.
- **Candidate primary / aggregate-stable**: stable on final-artifact agreement but not yet promoted because known-bad stress tests reveal over-acceptance. Current candidate: `qwen2.5vl:3b`.
- **Secondary**: useful as a stress signal but not enough for main evidence without inspection. Current candidate: `minicpm-v`.
- **Weak or excluded**: unstable labels, chart-family failures, or broad false positives. Current examples: `llava:7b`, `moondream`.

## Known-Bad Stress Test

Judges that agree on final artifacts must also be tested on pre-repair artifacts that are known to contain visual failures. The current stress set contains eight chart-family failures isolated during earlier repair analysis:

- five `heldout4b_before_auditfix_full` cases;
- three `heldout8b_intermediate_bad_targeted` cases.

Detection is counted as `acceptable=false`, because the judge must reject a known-bad chart even if it assigns a noisy taxonomy. Current stress results:

- `qwen3-vl:4b`: detects 8/8 and assigns `wrong_chart_type`;
- `qwen2.5vl:3b`: detects 0/8, over-accepting all known-bad charts;
- `minicpm-v`: detects 0/8, over-accepting all known-bad charts;
- `llava:7b`: detects 6/8, but mostly as `wrong_fields`;
- `moondream`: detects 0/8 under the conservative acceptability rule.

## Disagreement Taxonomy

- **True repair gap**: the VLM flags a real chart issue, and deterministic repair plus rerun resolves it.
- **Deterministic blind spot**: the structural evaluator passed the output, but image-level inspection reveals a missing visual commitment.
- **Label ambiguity**: the chart is defensible, but the benchmark label or accepted alternatives are too narrow.
- **VLM false positive**: the VLM flags an issue that is not present under inspection or another stronger judge.
- **Weak judge failure**: a judge shows systematic instability and is excluded from main evidence.

## Reporting Rules

- Report VLM audit as model-based visual audit, not human validation.
- Do not replace deterministic faithfulness scores with VLM acceptability.
- Separate full audits from targeted disagreement reruns.
- Report weak judges because their failures are scientific evidence about judge reliability.
- Promote a judge only after both final-artifact agreement and known-bad stress sensitivity are reported.
- Use human calibration for any final claim that a VLM judgment matches human chart assessment.
