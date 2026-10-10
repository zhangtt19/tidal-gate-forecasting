# Physics-guided discharge estimation

This supplementary experiment estimates **current** discharge with current measured water levels and two past flow observations. It does not require current measured flow as an input. It is not an advance forecast.

The model learns log(phi); Q = exp(predicted log(phi)) × B × (Zd − Z0) × sqrt(2g(Zu − Zd)). Fixed geometry comes from the archived worksheets. Rows with nonpositive head/depth or nonpositive observed flow are excluded for this experiment only. Changes in actual gate opening are not reconstructed.

The six predictors are current upstream/downstream levels, their backward rates per hour, previous log(coefficient), and previous flow-change rate. This is a documented **new causal feature design**, not a claim of an exact reimplementation of the proprietary 2025 training pipeline.

Parameters selected using purged temporal validation in 2003; final model refit on 2003; 2006 used only for final scoring. Same five-neuron tanh MLP and seed as forecasting. No headline paper metric is reused.

| Gate | Model | N | MAE (m³/s) | RMSE (m³/s) | R² |
|---|---|---:|---:|---:|---:|
| doulong | fixed_coefficient | 90 | 47.84 | 62.20 | 0.550 |
| doulong | previous_coefficient | 90 | 47.17 | 64.14 | 0.521 |
| doulong | persistence | 90 | 60.63 | 77.78 | 0.296 |
| doulong | hybrid_mlp | 90 | 30.29 | 39.21 | 0.821 |
| huangsha | fixed_coefficient | 100 | 100.58 | 124.67 | -7.528 |
| huangsha | previous_coefficient | 100 | 70.38 | 94.79 | -3.930 |
| huangsha | persistence | 100 | 18.70 | 25.51 | 0.643 |
| huangsha | hybrid_mlp | 100 | 29.74 | 39.33 | 0.151 |
| sheyang | fixed_coefficient | 54 | 271.65 | 346.44 | -0.689 |
| sheyang | previous_coefficient | 54 | 226.35 | 296.33 | -0.235 |
| sheyang | persistence | 54 | 173.41 | 224.82 | 0.289 |
| sheyang | hybrid_mlp | 54 | 192.41 | 233.25 | 0.235 |
| xinyang | fixed_coefficient | 95 | 130.51 | 200.96 | -0.934 |
| xinyang | previous_coefficient | 95 | 87.72 | 124.82 | 0.254 |
| xinyang | persistence | 95 | 60.97 | 78.14 | 0.708 |
| xinyang | hybrid_mlp | 95 | 80.47 | 104.49 | 0.477 |
| pooled | fixed_coefficient | 339 | 122.22 | 189.86 | 0.346 |
| pooled | previous_coefficient | 339 | 93.92 | 148.65 | 0.599 |
| pooled | persistence | 339 | 66.32 | 107.52 | 0.790 |
| pooled | hybrid_mlp | 339 | 70.01 | 112.21 | 0.771 |

Baselines are a train-only median coefficient, the most recently observed coefficient, and the most recently measured discharge. Performance is reported even when the neural network loses. Different eligibility rules mean these metrics must not be directly compared with the 12-step forecast metrics.
