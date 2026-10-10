"""Physics + ML: estimate current discharge from current water levels and past flow.

This is conditional estimation, not a forecast of unobserved future water levels.
"""

import json, warnings
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.exceptions import ConvergenceWarning
from .data import clean_observations, read_observations, hydraulic_factor
from .experiment import model, scores

FEATURES = [
    "upstream_m",
    "downstream_m",
    "upstream_rate_mph",
    "downstream_rate_mph",
    "previous_log_coefficient",
    "previous_flow_rate_m3sph",
]


def samples(clean, geometry, max_gap_hours=24):
    records = []
    for (gate, year), g in clean.groupby(["gate", clean.timestamp.dt.year]):
        g = g.sort_values("timestamp").reset_index(drop=True)
        geo = geometry.set_index("gate").loc[gate]
        factors = hydraulic_factor(
            g.upstream_m, g.downstream_m, geo.width_m, geo.sill_m
        )
        for i in range(2, len(g)):
            prev2, prev, cur = g.iloc[i - 2], g.iloc[i - 1], g.iloc[i]
            dt = (cur.timestamp - prev.timestamp).total_seconds() / 3600
            dtp = (prev.timestamp - prev2.timestamp).total_seconds() / 3600
            if not (0 < dt <= max_gap_hours and 0 < dtp <= max_gap_hours):
                continue
            if not (
                np.isfinite(factors[i])
                and np.isfinite(factors[i - 1])
                and cur.discharge_m3s > 0
                and prev.discharge_m3s > 0
            ):
                continue
            records.append(
                {
                    "gate": gate,
                    "year": year,
                    "history_start": prev2.timestamp,
                    "timestamp": cur.timestamp,
                    "upstream_m": cur.upstream_m,
                    "downstream_m": cur.downstream_m,
                    "upstream_rate_mph": (cur.upstream_m - prev.upstream_m) / dt,
                    "downstream_rate_mph": (cur.downstream_m - prev.downstream_m) / dt,
                    "previous_log_coefficient": np.log(
                        prev.discharge_m3s / factors[i - 1]
                    ),
                    "previous_flow_rate_m3sph": (
                        prev.discharge_m3s - prev2.discharge_m3s
                    )
                    / dtp,
                    "log_coefficient": np.log(cur.discharge_m3s / factors[i]),
                    "factor": factors[i],
                    "target": cur.discharge_m3s,
                    "previous_discharge": prev.discharge_m3s,
                    "previous_coefficient": prev.discharge_m3s / factors[i - 1],
                }
            )
    return pd.DataFrame(records)


def run(data_dir, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    clean, _ = clean_observations(
        read_observations(Path(data_dir) / "observations.csv")
    )
    s = samples(clean, pd.read_csv(Path(data_dir) / "geometry.csv"))
    metrics = []
    predictions = []
    selections = []
    warn = []
    for gate, g in s.groupby("gate"):
        train = g[g.year == 2003]
        test = g[g.year == 2006]
        val = train.iloc[int(len(train) * 0.8) :]
        fit = train[train.timestamp < val.iloc[0].history_start]
        if len(fit) < 10 or len(test) < 2:
            raise ValueError(f"{gate}: insufficient data")
        const = float(np.exp(train.log_coefficient.median()))
        output_rows = test[["gate", "timestamp", "target"]].copy()
        for kind, baseline in [
            ("fixed_coefficient", const * test.factor),
            ("previous_coefficient", test.previous_coefficient * test.factor),
            ("persistence", test.previous_discharge),
        ]:
            metrics.append(
                {
                    "gate": gate,
                    "model": kind,
                    "n_test": len(test),
                    **scores(test.target, baseline),
                }
            )
            output_rows[kind] = baseline
        trials = []
        for alpha in [0.01, 0.1, 1.0]:
            m = model("mlp", alpha)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                m.fit(fit[FEATURES], fit.log_coefficient)
            warn.extend(
                {
                    "gate": gate,
                    "stage": "validation",
                    "alpha": alpha,
                    "warning": str(w.message),
                }
                for w in caught
            )
            y = np.exp(m.predict(val[FEATURES])) * val.factor
            rmse = scores(val.target, y)["rmse_m3s"]
            trials.append((rmse, alpha))
            selections.append(
                {
                    "gate": gate,
                    "alpha": alpha,
                    "validation_rmse_m3s": rmse,
                    "n_fit": len(fit),
                    "n_validation": len(val),
                    "last_fit_target": str(fit.timestamp.max()),
                    "first_validation_history": str(val.history_start.min()),
                }
            )
        _, alpha = min(trials)
        m = model("mlp", alpha)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            m.fit(train[FEATURES], train.log_coefficient)
        warn.extend(
            {"gate": gate, "stage": "final", "alpha": alpha, "warning": str(w.message)}
            for w in caught
        )
        y = np.exp(m.predict(test[FEATURES])) * test.factor
        output_rows["hybrid_mlp"] = y
        metrics.append(
            {
                "gate": gate,
                "model": "hybrid_mlp",
                "n_test": len(test),
                **scores(test.target, y),
            }
        )
        predictions.append(output_rows)
    pred = pd.concat(predictions, ignore_index=True)
    for kind in [
        "fixed_coefficient",
        "previous_coefficient",
        "persistence",
        "hybrid_mlp",
    ]:
        metrics.append(
            {
                "gate": "pooled",
                "model": kind,
                "n_test": len(pred),
                **scores(pred.target, pred[kind]),
            }
        )
    pd.DataFrame(metrics).to_csv(output / "hybrid_metrics.csv", index=False)
    pred.to_csv(output / "hybrid_predictions.csv", index=False)
    pd.DataFrame(selections).to_csv(output / "hybrid_validation.csv", index=False)
    (output / "hybrid_warnings.json").write_text(
        json.dumps(warn, indent=2), encoding="utf-8"
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(
        2, 2, figsize=(12, 8), constrained_layout=True, facecolor="#fbfaf7"
    )
    for ax, (gate, g) in zip(axs.flat, pred.groupby("gate")):
        ax.set_facecolor("#fbfaf7")
        ax.scatter(g.target, g.hybrid_mlp, s=20, color="#127b80", alpha=0.7)
        top = max(g.target.max(), g.hybrid_mlp.max()) * 1.05
        ax.plot([0, top], [0, top], color="#9b724d", ls="--")
        ax.set_title(gate.title(), loc="left", fontweight="bold")
        ax.set_xlabel("Observed discharge (m³/s)")
        ax.set_ylabel("Hybrid estimate (m³/s)")
        ax.grid(alpha=0.2)
    fig.suptitle(
        "Physics + neural network: conditional discharge estimation\n2006 holdout · current levels and past flow available",
        fontsize=16,
        fontweight="bold",
    )
    fig.savefig(output / "hybrid_estimation.png", dpi=160)
    plt.close(fig)
    lines = [
        "# Physics-guided discharge estimation",
        "",
        "This supplementary experiment estimates **current** discharge with current measured water levels and two past flow observations. It does not require current measured flow as an input. It is not an advance forecast.",
        "",
        "The model learns log(phi); Q = exp(predicted log(phi)) × B × (Zd − Z0) × sqrt(2g(Zu − Zd)). Fixed geometry comes from the archived worksheets. Rows with nonpositive head/depth or nonpositive observed flow are excluded for this experiment only. Changes in actual gate opening are not reconstructed.",
        "",
        "The six predictors are current upstream/downstream levels, their backward rates per hour, previous log(coefficient), and previous flow-change rate. This is a documented **new causal feature design**, not a claim of an exact reimplementation of the proprietary 2025 training pipeline.",
        "",
        "Parameters selected using purged temporal validation in 2003; final model refit on 2003; 2006 used only for final scoring. Same five-neuron tanh MLP and seed as forecasting. No headline paper metric is reused.",
        "",
        "| Gate | Model | N | MAE (m³/s) | RMSE (m³/s) | R² |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in metrics:
        lines.append(
            f"| {row['gate']} | {row['model']} | {row['n_test']} | {row['mae_m3s']:.2f} | {row['rmse_m3s']:.2f} | {row['r2']:.3f} |"
        )
    lines += [
        "",
        "Baselines are a train-only median coefficient, the most recently observed coefficient, and the most recently measured discharge. Performance is reported even when the neural network loses. Different eligibility rules mean these metrics must not be directly compared with the 12-step forecast metrics.",
        "",
    ]
    (output / "HYBRID_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    return pd.DataFrame(metrics)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, default=Path("data"))
    p.add_argument("--output", type=Path, default=Path("results"))
    a = p.parse_args()
    print(run(a.data, a.output).to_string(index=False))
