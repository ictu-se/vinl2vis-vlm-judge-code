# Human Annotation Guidelines

Goal: judge whether a rendered chart is visually faithful enough to the user query. The task is not to reward beauty. It is to decide whether a human reader can inspect the chart and verify the requested analytical intent.

Annotate independently. Do not use the previous VLM judgment as ground truth. The `source_bucket` column is included for later analysis; it should not determine your answer.

## Allowed Labels

`human_visible_chart_family`:
Use one of `area`, `bar`, `boxplot`, `bubble_chart`, `heatmap`, `histogram`, `line`, `point`, `scatter`, `tick_plot`, `table_or_text`, `empty_or_broken`, `unknown`.

`human_chart_family_acceptable`:
Use `yes`, `no`, or `unclear`. Mark `yes` when the visible chart family is the requested family or a defensible equivalent for the query. For example, point and scatter can be equivalent when both show unconnected dots over axes.

`human_labels_readable`:
Use `yes`, `no`, or `unclear`. Mark `yes` if title, axis labels, or legend are readable enough to understand what the plotted fields are.

`human_relevant_fields_visible`:
Use `yes`, `no`, or `unclear`. Mark `yes` if the chart shows the fields needed by the query. Do not require exact underscore field names if the natural-language label is equivalent.

`human_transform_preserved`:
Use `yes`, `no`, `not_applicable`, or `unclear`. Mark `no` if a requested latest-year filter, ranking/sorting, grouping, aggregation, or comparison is visibly missing. Use `unclear` when the image alone cannot verify it.

`human_overall_acceptable`:
Use `yes`, `no`, or `unclear`. Mark `yes` only when the chart is usable for the query after considering chart family, labels, visible fields, readability, and visible transformations.

`human_primary_error`:
Use one of `none`, `wrong_chart_type`, `wrong_fields`, `missing_transform`, `missing_labels`, `unreadable`, `empty_or_broken`, `overplotting`, `other`, `unclear`.

`human_confidence`:
Use `high`, `medium`, or `low`.

`human_notes`:
Optional short explanation, especially for `no` or `unclear`.

## Practical Rules

- If the chart is ugly but still lets a reader answer the query, it can be acceptable.
- If a chart has the right type but the requested fields are not visible, mark overall unacceptable.
- If labels are crowded but still identifiable, mark labels readable.
- If the chart clearly uses a wrong visual family, mark overall unacceptable even if labels are readable.
- If the query asks for a latest year, ranking, grouping, or aggregation and the chart does not visibly reflect it, use `missing_transform`.
- If the image is missing from the package, leave the human fields blank and write `image_missing` in `human_notes`.
