# Source-to-implementation audit

The paper describes six predictors and a next-step discharge coefficient. The archive also contains historical screenshots mentioning twelve prior steps. These are not enough to establish a single identical implementation across all drafts and software versions.

Read-only checks of the eight archived six-input `.dat` exports find row counts matching their corresponding cleaned coefficient sheets. Five match same-row features and coefficients numerically at the strict tolerance used by `scripts/audit_legacy_inputs.py`; three differ and remain unresolved. This does not establish that the proprietary software did or did not internally shift targets. Therefore no exact twelve-step reproduction or original-code claim is made.

In checked calculation-sheet rows, the stored Q change rate matches a difference divided by Excel date differences (days). The column labelled as a head-difference change rate matches the **sum** of adjacent head differences divided by elapsed days. This differs from the mathematical temporal derivative of the head difference. Some manuscript unit labels also differ from the spreadsheet's per-day scale. The new implementation computes its own explicitly defined per-hour features rather than silently reusing these columns.

The archived proprietary `.fann` file is not treated as source code and is not redistributed or reverse engineered. Saved historical fit outputs, review drafts and their authorship metadata are not used as out-of-sample evidence.

Consequently this repository separates (1) documented research provenance, (2) a newly specified physics-guided conditional estimator, and (3) a twelve-observation forecast extension. Original method interpretation remains distinct from verified behaviour of the new code. These file-level observations do not alone determine the validity of every result in the published study.

Detailed local audit: `results/legacy_input_audit.json`. Re-run only with access to the author's archive:

```bash
python scripts/audit_legacy_inputs.py "PATH_TO/2 小论文-3篇"
```
