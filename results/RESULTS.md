# Reproducible benchmark results

Imported 1309 records; retained 1298; excluded 11 with reasons in `excluded_observations.csv`.

Training: 2003. Hyperparameter selection: purged chronological validation inside 2003. Test: 2006, never used to select parameters.

History: 12 observations, not hours. Adjacent gaps must be <=24 hours. Predictions target the next recorded observation; the next sampling time is not a model input.

| Gate | Model | Test samples | MAE (m³/s) | RMSE (m³/s) | R² | RMSE improvement over persistence |
|---|---|---:|---:|---:|---:|---:|
| doulong | persistence | 69 | 69.00 | 89.16 | 0.219 | 0.0% |
| doulong | ridge | 69 | 65.30 | 93.27 | 0.145 | -4.6% |
| doulong | mlp | 69 | 116.09 | 150.81 | -1.235 | -69.1% |
| huangsha | persistence | 115 | 20.37 | 29.00 | 0.653 | 0.0% |
| huangsha | ridge | 115 | 24.02 | 32.48 | 0.565 | -12.0% |
| huangsha | mlp | 115 | 39.73 | 52.45 | -0.134 | -80.8% |
| sheyang | persistence | 67 | 169.52 | 221.16 | 0.192 | 0.0% |
| sheyang | ridge | 67 | 407.44 | 462.14 | -2.529 | -109.0% |
| sheyang | mlp | 67 | 299.10 | 341.99 | -0.933 | -54.6% |
| xinyang | persistence | 94 | 71.19 | 92.73 | 0.601 | 0.0% |
| xinyang | ridge | 94 | 81.50 | 104.43 | 0.494 | -12.6% |
| xinyang | mlp | 94 | 99.12 | 135.73 | 0.145 | -46.4% |
| pooled | persistence | 345 | 72.91 | 117.10 | 0.773 | 0.0% |
| pooled | ridge | 345 | 122.40 | 215.73 | 0.230 | -84.2% |
| pooled | mlp | 345 | 121.55 | 182.20 | 0.451 | -55.6% |

Positive improvement is better; negative means worse than simply retaining the latest measured discharge. Pooled metrics are sample-weighted and dominated by larger-flow gates; per-gate metrics are essential.

## Coverage

| Gate | Train windows | Test windows |
|---|---:|---:|
| doulong | 243 | 69 |
| huangsha | 249 | 115 |
| sheyang | 69 | 67 |
| xinyang | 153 | 94 |

## Interpretation

This is a new forecasting benchmark inspired by the author’s research, not a numerical reproduction of the published DTPM fit or a validation of the proprietary software. The five-hidden-neuron neural network is deliberately small. Its value is assessed against persistence and regularized linear regression, including cases where it loses.

The next-observation horizon is irregular. Long gaps, operating changes and the small two-year archive limit generalization. Gate-operation remarks are preserved in source records but are not predictors. No performance outside these four gates or real-time deployment is claimed.

Observed test horizons: 0.33–14.50 hours; median 1.33 hours.
