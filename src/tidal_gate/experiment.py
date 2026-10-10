"""Chronological holdout benchmark. Hyperparameters never see the 2006 holdout."""

import json
import warnings
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .data import clean_observations, read_observations, make_windows, hydraulic_factor

SEED = 42


def model(kind, alpha):
    reg = (
        Ridge(alpha=alpha)
        if kind == "ridge"
        else MLPRegressor(
            hidden_layer_sizes=(5,),
            activation="tanh",
            solver="lbfgs",
            alpha=alpha,
            max_iter=5000,
            max_fun=100000,
            random_state=SEED,
        )
    )
    return TransformedTargetRegressor(
        regressor=make_pipeline(StandardScaler(), reg), transformer=StandardScaler()
    )


def scores(y, p):
    return {
        "mae_m3s": float(mean_absolute_error(y, p)),
        "rmse_m3s": float(np.sqrt(mean_squared_error(y, p))),
        "r2": float(r2_score(y, p)),
    }


def run(data_dir, output, window=12, max_gap_hours=24):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "models").mkdir(exist_ok=True)
    raw = read_observations(Path(data_dir) / "observations.csv")
    clean, excluded = clean_observations(raw)
    excluded.to_csv(output / "excluded_observations.csv", index=False)
    profile = []
    for (gate, year), g in clean.groupby(["gate", clean.timestamp.dt.year]):
        dt = g.timestamp.diff().dt.total_seconds() / 3600
        profile.append(
            {
                "gate": gate,
                "year": int(year),
                "records": len(g),
                "start": str(g.timestamp.min()),
                "end": str(g.timestamp.max()),
                "median_interval_hours": float(dt.median()),
                "max_interval_hours": float(dt.max()),
                "nonpositive_head_records": int((g.upstream_m <= g.downstream_m).sum()),
            }
        )
    audit = {
        "raw_records": len(raw),
        "clean_records": len(clean),
        "excluded_records": len(excluded),
        "exclusion_counts": excluded.exclusion_reason.value_counts().to_dict(),
        "profiles": profile,
    }
    (output / "data_quality.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    X, meta = make_windows(clean, window, max_gap_hours)
    predictions = []
    metrics = []
    selection = []
    warnings_log = []
    coverage = []
    for gate in sorted(clean.gate.unique()):
        train = np.flatnonzero((meta.gate == gate) & (meta.year == 2003))
        test = np.flatnonzero((meta.gate == gate) & (meta.year == 2006))
        coverage.append(
            {"gate": gate, "train_windows": len(train), "test_windows": len(test)}
        )
        if len(train) < 20 or len(test) < 2:
            continue
        # Purge windows whose labels overlap the first validation history.
        val = train[int(len(train) * 0.8) :]
        cutoff = meta.iloc[val[0]].history_start
        fit = train[meta.iloc[train].target_time.to_numpy() < cutoff]
        if len(fit) < 10:
            raise ValueError(f"{gate}: insufficient purged training history")
        yt = meta.iloc[test].target.to_numpy()
        base = meta.iloc[test].persistence.to_numpy()
        pred = meta.iloc[test].copy()
        pred["persistence_pred"] = base
        base_rmse = scores(yt, base)["rmse_m3s"]
        metrics.append(
            {
                "gate": gate,
                "model": "persistence",
                "n_test": len(test),
                **scores(yt, base),
                "rmse_skill_vs_persistence": 0.0,
            }
        )
        for kind, alphas in [("ridge", [1.0, 10.0, 100.0]), ("mlp", [0.01, 0.1, 1.0])]:
            trials = []
            for alpha in alphas:
                candidate = model(kind, alpha)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ConvergenceWarning)
                    candidate.fit(X.iloc[fit], meta.iloc[fit].target)
                warnings_log.extend(
                    {
                        "gate": gate,
                        "model": kind,
                        "stage": "validation",
                        "alpha": alpha,
                        "warning": str(w.message),
                    }
                    for w in caught
                )
                pv = np.maximum(0, candidate.predict(X.iloc[val]))
                error = scores(meta.iloc[val].target, pv)["rmse_m3s"]
                trials.append((error, alpha))
                selection.append(
                    {
                        "gate": gate,
                        "model": kind,
                        "alpha": alpha,
                        "validation_rmse_m3s": error,
                        "n_fit": len(fit),
                        "n_validation": len(val),
                        "fit_last_target": str(meta.iloc[fit].target_time.max()),
                        "validation_first_history": str(cutoff),
                    }
                )
            _, alpha = min(trials)
            fitted = model(kind, alpha)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                fitted.fit(X.iloc[train], meta.iloc[train].target)
            warnings_log.extend(
                {
                    "gate": gate,
                    "model": kind,
                    "stage": "final",
                    "alpha": alpha,
                    "warning": str(w.message),
                }
                for w in caught
            )
            p = np.maximum(0, fitted.predict(X.iloc[test]))
            pred[kind + "_pred"] = p
            result = scores(yt, p)
            metrics.append(
                {
                    "gate": gate,
                    "model": kind,
                    "n_test": len(test),
                    **result,
                    "rmse_skill_vs_persistence": 1 - result["rmse_m3s"] / base_rmse,
                }
            )
            joblib.dump(
                {
                    "estimator": fitted,
                    "features": list(X.columns),
                    "window": window,
                    "max_gap_hours": max_gap_hours,
                    "gate": gate,
                    "train_year": 2003,
                    "selected_alpha": alpha,
                },
                output / "models" / f"{gate}_{kind}.joblib",
            )
        predictions.append(pred)
    if not predictions:
        raise ValueError("No gate has enough training and test windows")
    pd.DataFrame(coverage).to_csv(output / "coverage.csv", index=False)
    pred = pd.concat(predictions, ignore_index=True)
    pred.to_csv(output / "predictions.csv", index=False)
    for kind in ["persistence", "ridge", "mlp"]:
        result = scores(pred.target, pred[kind + "_pred"])
        base = scores(pred.target, pred.persistence_pred)["rmse_m3s"]
        metrics.append(
            {
                "gate": "pooled",
                "model": kind,
                "n_test": len(pred),
                **result,
                "rmse_skill_vs_persistence": 1 - result["rmse_m3s"] / base,
            }
        )
    metric = pd.DataFrame(metrics)
    metric.to_csv(output / "metrics.csv", index=False)
    pd.DataFrame(selection).to_csv(output / "validation.csv", index=False)
    (output / "training_warnings.json").write_text(
        json.dumps(warnings_log, indent=2), encoding="utf-8"
    )
    versions = {}
    from importlib.metadata import version

    for package in ["numpy", "pandas", "scikit-learn", "matplotlib", "joblib"]:
        versions[package] = version(package)
    (output / "run_config.json").write_text(
        json.dumps(
            {
                "window": window,
                "max_gap_hours": max_gap_hours,
                "seed": SEED,
                "train_year": 2003,
                "test_year": 2006,
                "validation": "last 20% of 2003 eligible windows; overlapping histories purged from fit",
                "target": "next observed discharge, not fixed-hour forecast",
                "refit": "all eligible 2003 windows after selection",
                "test_update": "history receives actual observations; model weights remain frozen",
                "nonnegative_clipping": True,
                "versions": versions,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plot_results(pred, metric, output, window)
    write_results(metric, pred, coverage, audit, output, window, max_gap_hours)
    return metric


def plot_results(pred, metric, out, window):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "#fbfaf7",
            "axes.facecolor": "#fbfaf7",
            "savefig.facecolor": "#fbfaf7",
        }
    )
    gates = sorted(pred.gate.unique())
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for ax, gate in zip(axes.flat, gates):
        m = metric[metric.gate == gate]
        ax.bar(m.model, m.rmse_m3s, color=["#94a3b8", "#d69544", "#127b80"])
        ax.set_title(gate.title(), loc="left", fontweight="bold")
        ax.set_ylabel("Holdout RMSE (m³/s)")
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    fig.suptitle(
        f"Forecasting across years: train 2003 → test 2006\n{window}-observation history · next recorded measurement",
        fontsize=16,
        fontweight="bold",
    )
    fig.savefig(out / "benchmark.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for ax, gate in zip(axes.flat, gates):
        g = pred[pred.gate == gate]
        ax.plot(range(len(g)), g.target, label="Observed", color="#1e293b", lw=2)
        ax.plot(
            range(len(g)), g.mlp_pred, label="Neural network", color="#127b80", lw=1.4
        )
        ax.plot(
            range(len(g)),
            g.persistence_pred,
            label="Last observation",
            color="#d69544",
            alpha=0.7,
            lw=1,
        )
        ax.set_title(gate.title(), loc="left", fontweight="bold")
        ax.set_xlabel("Eligible held-out sample, chronological order")
        ax.set_ylabel("Discharge (m³/s)")
        ax.grid(alpha=0.2)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle(
        "What the model gets right—and where it misses", fontsize=16, fontweight="bold"
    )
    fig.savefig(out / "holdout_predictions.png", dpi=160)
    plt.close(fig)


def write_results(metric, pred, coverage, audit, out, window, max_gap_hours):
    lines = [
        "# Reproducible benchmark results",
        "",
        f"Imported {audit['raw_records']} records; retained {audit['clean_records']}; excluded {audit['excluded_records']} with reasons in `excluded_observations.csv`.",
        "",
        "Training: 2003. Hyperparameter selection: purged chronological validation inside 2003. Test: 2006, never used to select parameters.",
        "",
        f"History: {window} observations, not hours. Adjacent gaps must be <={max_gap_hours:g} hours. Predictions target the next recorded observation; the next sampling time is not a model input.",
        "",
        "| Gate | Model | Test samples | MAE (m³/s) | RMSE (m³/s) | R² | RMSE improvement over persistence |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in metric.to_dict("records"):
        lines.append(
            f"| {r['gate']} | {r['model']} | {r['n_test']} | {r['mae_m3s']:.2f} | {r['rmse_m3s']:.2f} | {r['r2']:.3f} | {r['rmse_skill_vs_persistence']:.1%} |"
        )
    lines += [
        "",
        "Positive improvement is better; negative means worse than simply retaining the latest measured discharge. Pooled metrics are sample-weighted and dominated by larger-flow gates; per-gate metrics are essential.",
        "",
        "## Coverage",
        "",
        "| Gate | Train windows | Test windows |",
        "|---|---:|---:|",
    ]
    for c in coverage:
        lines.append(f"| {c['gate']} | {c['train_windows']} | {c['test_windows']} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "This is a new forecasting benchmark inspired by the author’s research, not a numerical reproduction of the published DTPM fit or a validation of the proprietary software. The five-hidden-neuron neural network is deliberately small. Its value is assessed against persistence and regularized linear regression, including cases where it loses.",
        "",
        "The next-observation horizon is irregular. Long gaps, operating changes and the small two-year archive limit generalization. Gate-operation remarks are preserved in source records but are not predictors. No performance outside these four gates or real-time deployment is claimed.",
        "",
        f"Observed test horizons: {pred.horizon_hours.min():.2f}–{pred.horizon_hours.max():.2f} hours; median {pred.horizon_hours.median():.2f} hours.",
        "",
    ]
    (out / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
