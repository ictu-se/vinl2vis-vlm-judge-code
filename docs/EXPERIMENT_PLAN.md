# Experiment Plan

## What Can Be Reported Now

The current evidence supports a paper about calibrated VLM-as-judge auditing, not a paper claiming that VLMs replace human reviewers.

Reportable now:

- `qwen3-vl:4b` full audits:
  - Vietnamese balanced: 800 rendered charts, 96.5% acceptable.
  - English explicit: 1000 rendered charts, 95.2% acceptable.
  - matched bilingual: 1000 rendered charts, 98.2% acceptable.
  - held-out Vietnamese: 660 rendered charts, 99.848% acceptable.
- Cross-judge held-out comparison:
  - `qwen3-vl:4b` behaves as the current primary local judge.
  - `qwen2.5vl:3b` is aggregate-stable on final artifacts but fails the current known-bad stress test.
  - `minicpm-v` is useful as secondary stress evidence, but also fails the current known-bad stress test.
  - `llava:7b` and `moondream` are weak judges and should be excluded from main validation.
- Targeted before/after evidence:
  - VLM-discovered held-out chart-family failures were repaired.
  - Targeted reruns accepted the repaired cases.
- Known-bad stress evidence:
  - `qwen3-vl:4b` detects 8/8 pre-repair chart-family failures.
  - `qwen2.5vl:3b`, `minicpm-v`, and `moondream` detect 0/8 under the acceptability rule.
  - `llava:7b` detects 6/8 but reports mostly `wrong_fields`, so it is useful as a failure-mode example rather than a reliable judge.
- Stratified stress set:
  - `stress230/stress230_cases.csv` contains 230 audit cases.
  - Composition: 8 repair-confirmed known-bad cases, 70 major visual-sanity failures, 70 strict-transform failures, 60 primary VLM flags, and 22 cross/weak-judge disagreement cases.
  - `stress230/stress230_run_config.csv` maps the 230 cases back to their output, split, metrics, and per-run sample ID files.
- Human calibration artifacts:
  - `calibration/human_calibration_240.csv` contains 240 candidate items.
  - The disagreement pool has only 13 real cross-judge disagreement cases, so the remainder is filled with supplemental consensus-accepted cases rather than synthetic disagreements.

## Missing for a Strong Journal Submission

The paper needs a human calibration subset if it targets a Q1 venue. The subset does not need to be large, but it must be stratified and defensible.

Recommended calibration size: 240 cases.

Sampling design:

- 80 VLM-consensus accepted cases.
- 40 `qwen3-vl:4b` flagged cases.
- 40 cross-judge disagreement cases.
- 40 known deterministic visual-sanity failures or strict-transform pre-repair cases.
- 40 weak-judge-only flagged cases from `llava:7b` or `moondream`.

Label fields:

- chart family visible;
- expected chart family acceptable;
- labels/legend readable;
- relevant fields visible;
- requested comparison or transformation preserved;
- overall acceptable;
- primary error type;
- reviewer confidence.

## Additional Experiments to Run or Extend

1. **Known-bad stress test**

   Done for eight pre-repair chart-family failures and five local VLM judges. A stronger version should expand the stress set with deterministic visual-sanity failures and strict-transform failures from more splits.

   Next run: execute the five local VLM judges on the 230-case stratified stress set. Report results separately by evidence provenance rather than as a single human-ground-truth accuracy number.

2. **Prompt sensitivity**

   Run prompt versions `v3` and `v4` on the same 100-case subset. Report whether acceptability and chart-family labels are stable.

3. **Language/query-type stratification**

   Break VLM flags down by language and query type: Vietnamese, English, matched bilingual; explicit, ambiguous, underspecified, multi-turn, unanswerable.

4. **Human calibration**

   Use the 240-case subset above. Report agreement between human labels and each VLM judge using accuracy, balanced accuracy, Cohen's kappa, and false-positive/false-negative counts.

## Paper-Specific Metrics

- VLM acceptability rate.
- Chart-family match rate.
- Label/legend match rate.
- Readability rate.
- Disagreement rate between VLM judges.
- Known-bad detection rate.
- False positive rate against inspected/human labels.
- False negative rate against inspected/human labels.
- Repair validation rate on targeted before/after cases.

## Main Claim Boundary

Acceptable wording:

> VLMs can act as scalable visual auditors when used with deterministic checks, judge-tiering, and disagreement inspection.

Do not claim:

> VLMs replace human validation.

Do not claim:

> A VLM acceptability score is the same as NL2Vis faithfulness.

The safe framing is that VLMs are useful for visual triage and repair discovery, while deterministic evaluators and human calibration remain necessary for semantic and publication-grade validation.
