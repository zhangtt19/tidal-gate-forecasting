# Method and evaluation contract

## Data and source authority

Two original observation workbooks (2003 and 2006), each with four gate sheets, control observations. Columns are identified by header rather than position: Xinyang's 2003 column order differs. Every exported row retains source year, sheet and Excel row. Source workbook hashes are in `data/provenance.json`.

Timestamps are local field-record times, timezone unspecified; no timezone conversion is applied. Sampling is irregular. Source values are preserved, including water-level differences <=0; these rows remain eligible for forecasting but not for the square-root weir equation. No interpolated observations are invented.

Rows with zero upstream level **and** zero flow are excluded as operation markers. Other measured zero flows are retained. Missing/nonfinite measurements and negative flow would be excluded. Conflicting same-time records are all excluded; exact duplicates retain their first instance. Exclusion reasons are exported.

## Experiment A: physics-guided estimation

```
Q = phi * B * (Zd - Z0) * sqrt(2 * 9.8 * (Zu - Zd))
```

A five-hidden-neuron tanh MLP predicts log(phi); exponentiation ensures a positive coefficient. Its six features are current Zu and Zd, their backward rates in metres/hour, the previous log coefficient, and the previous flow-change rate calculated between the two *previous* observations. Current Q is used only to construct the training target and score predictions. Rows require positive head, downstream depth and current/previous observed flow; each of the two adjacent observation gaps must be <=24 h.

Widths/sill elevations are fixed study parameters from archived coefficient sheets: Doulong and Huangsha 80 m / −3 m, Sheyang 350 m / −3.5 m, Xinyang 170 m / −3.5 m. Remarks indicate varying gate operation; these constants are an approximation, not a reconstruction of every opening.

Baselines: median coefficient fitted on training observations, previous observed coefficient, previous measured discharge. The first baseline is **not claimed to reproduce the paper's traditional-method calibration**.

## Experiment B: next-observation forecast

12 preceding observations of Zu, Zd and Q plus 11 historical sampling intervals create 47 predictors. Target is the next recorded Q. No target-time measurement or target sampling interval is an input. Gaps >24 h break windows; windows cannot cross calendar years or gates. A shorter eligible history does not silently fall back to another model.

This is a retrospective next-observation task with variable horizon, not a scheduled one-hour operational forecast. Eligibility is assessed using archived timestamps; the time of the next observation is not forecast. After each observation, the history updates with measured values; models stay frozen. It is not recursive multi-step forecasting.

Models: persistence, standardized ridge regression, standardized five-neuron tanh MLP. MLP uses L-BFGS, maximum 5,000 iterations, maximum 100,000 function evaluations, seed 42. It differs from the proprietary training method. Forecast outputs are clipped at zero uniformly for learned models.

## Validation

All parameters are selected inside 2003. Last 20% of eligible windows form temporal validation. Fit windows whose target overlaps the first validation history are purged. Feature and target scalers are fit only inside the training estimator. Ridge alpha candidates: 1, 10, 100. MLP regularization candidates: .01, .1, 1. Choose lowest validation discharge RMSE; refit all eligible 2003 records; score 2006 once per specified experiment. No post-test tuning is performed.

MAE and RMSE use m³/s; R² uses the test-mean denominator and can be negative. Forecast RMSE skill is 1 − model_RMSE / persistence_RMSE. Pooled metrics concatenate rows, so high-flow gates dominate; station tables must accompany them. No uncertainty interval or significance claim is made from these correlated, limited observations.

Separate model tasks have separate eligibility rules; their metrics are not interchangeable. The archived paper's fitting metrics and cross-validation metrics are not substituted for this project's held-out scores. Environment versions are saved in `results/run_config.json`. Convergence warnings, if any, are retained as artifacts.
