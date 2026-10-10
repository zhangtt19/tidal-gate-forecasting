from pathlib import Path
import numpy as np
import pandas as pd

COLUMNS = ["gate", "timestamp", "upstream_m", "downstream_m", "discharge_m3s"]
NUMERIC = COLUMNS[2:]


def read_observations(path):
    frame = pd.read_csv(path, keep_default_na=False)
    missing = set(COLUMNS) - set(frame)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    for c in NUMERIC:
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    return frame


def clean_observations(frame):
    """Exclude known operation-marker placeholders and ambiguous duplicates, not hard cases."""
    f = frame.copy()
    reasons = pd.Series("", index=f.index)
    invalid = (
        f["timestamp"].isna()
        | ~np.isfinite(f[NUMERIC]).all(axis=1)
        | (f.discharge_m3s < 0)
    )
    reasons.loc[invalid] = "invalid_or_missing_measurement"
    # In this archive opening/closing rows use zero to mark unknown upstream level and flow.
    placeholder = (f.upstream_m == 0) & (f.discharge_m3s == 0)
    reasons.loc[placeholder] = "operation_placeholder"
    candidates = f.loc[reasons.eq("")]
    keys = ["gate", "timestamp"]
    conflicting = candidates.groupby(keys)[NUMERIC].nunique().gt(1).any(axis=1)
    conflict_keys = set(conflicting[conflicting].index)
    conflict = f.apply(lambda r: (r["gate"], r["timestamp"]) in conflict_keys, axis=1)
    reasons.loc[conflict & reasons.eq("")] = "conflicting_duplicate_timestamp"
    eligible = f.loc[reasons.eq("")]
    duplicate = eligible.duplicated(keys, keep="first")
    reasons.loc[eligible.index[duplicate]] = "duplicate_measurement"
    excluded = f.loc[reasons.ne("")].copy()
    excluded["exclusion_reason"] = reasons[reasons.ne("")]
    kept = f.loc[reasons.eq("")].sort_values(keys).reset_index(drop=True)
    if len(kept) == 0:
        raise ValueError("No usable observations")
    return kept, excluded


def hydraulic_factor(upstream, downstream, width, sill):
    head = np.asarray(upstream) - np.asarray(downstream)
    depth = np.asarray(downstream) - sill
    valid = (head > 0) & (depth > 0)
    return np.where(
        valid, width * depth * np.sqrt(2 * 9.8 * np.maximum(head, 0)), np.nan
    )


def make_windows(frame, window=12, max_gap_hours=24):
    """History ends strictly before target. Window means observations, not hours.

    No future levels, target discharge or realized next sampling interval enters X.
    Runs are reset on gaps > max_gap_hours. The target is the next recorded sample.
    """
    if window < 2:
        raise ValueError("window must be at least 2")
    X, meta = [], []
    for (gate, year), g in frame.groupby(["gate", frame.timestamp.dt.year], sort=True):
        g = g.sort_values("timestamp").reset_index(drop=True)
        for target in range(window, len(g)):
            block = g.iloc[target - window : target + 1]
            dt = block.timestamp.diff().dt.total_seconds().iloc[1:] / 3600
            if (dt <= 0).any() or (dt > max_gap_hours).any():
                continue
            history = block.iloc[:-1]
            row = block.iloc[-1]
            gaps = history.timestamp.diff().dt.total_seconds().iloc[1:] / 3600
            vals = history[NUMERIC].to_numpy().ravel().tolist() + gaps.tolist()
            last = history.iloc[-1]
            X.append(vals)
            meta.append(
                {
                    "gate": gate,
                    "year": year,
                    "history_start": history.iloc[0].timestamp,
                    "origin": last.timestamp,
                    "target_time": row.timestamp,
                    "target": row.discharge_m3s,
                    "persistence": last.discharge_m3s,
                    "horizon_hours": dt.iloc[-1],
                }
            )
    if not X:
        raise ValueError("No windows satisfy the history and gap rules")
    names = [f"{c}_lag{lag}" for lag in range(window, 0, -1) for c in NUMERIC] + [
        f"history_gap_hours_{i}" for i in range(window - 1)
    ]
    return pd.DataFrame(X, columns=names), pd.DataFrame(meta)
