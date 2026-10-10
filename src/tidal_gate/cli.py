import argparse, json
from pathlib import Path
import joblib, numpy as np
from .data import read_observations, clean_observations, NUMERIC


def forecast(bundle_path, history_path):
    bundle = joblib.load(bundle_path)  # load only trusted locally generated artifacts
    history, _ = clean_observations(read_observations(history_path))
    h = (
        history[history.gate == bundle["gate"]]
        .sort_values("timestamp")
        .tail(bundle["window"])
    )
    if len(h) != bundle["window"]:
        raise ValueError("Insufficient history for this gate")
    dt = h.timestamp.diff().dt.total_seconds().iloc[1:] / 3600
    if (dt <= 0).any() or (dt > bundle["max_gap_hours"]).any():
        raise ValueError("History crosses a gap larger than the model permits")
    import pandas as pd

    x = pd.DataFrame(
        [h[NUMERIC].to_numpy().ravel().tolist() + dt.tolist()],
        columns=bundle["features"],
    )
    return {
        "gate": bundle["gate"],
        "origin": h.timestamp.max().isoformat(),
        "prediction_m3s": max(0.0, float(bundle["estimator"].predict(x)[0])),
        "target": "next observation, time not specified",
        "history_observations": bundle["window"],
        "training_year": bundle["train_year"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Four tidal gates: research-to-code forecasting benchmark"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("benchmark")
    run.add_argument("--data", type=Path, default=Path("data"))
    run.add_argument("--output", type=Path, default=Path("results"))
    run.add_argument("--window", type=int, default=12)
    run.add_argument("--max-gap-hours", type=float, default=24)
    predict = sub.add_parser("predict")
    predict.add_argument("--model", type=Path, required=True)
    predict.add_argument("--history", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "benchmark":
        from .experiment import run as experiment

        print(
            experiment(
                args.data, args.output, args.window, args.max_gap_hours
            ).to_string(index=False)
        )
    else:
        print(json.dumps(forecast(args.model, args.history), indent=2))


if __name__ == "__main__":
    main()
