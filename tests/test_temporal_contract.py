import numpy as np
import pandas as pd
import pytest
from tidal_gate.data import make_windows, clean_observations, hydraulic_factor


def frame(n=30):
    return pd.DataFrame(
        {
            "gate": ["doulong"] * n,
            "timestamp": pd.date_range("2003-06-01", periods=n, freq="h"),
            "upstream_m": np.arange(n) / 100 + 2,
            "downstream_m": np.arange(n) / 100 + 1,
            "discharge_m3s": np.arange(n) * 10.0 + 100,
        }
    )


def test_twelve_observations_predict_thirteenth():
    f = frame()
    x, m = make_windows(f)
    assert m.iloc[0].origin == f.iloc[11].timestamp
    assert m.iloc[0].target_time == f.iloc[12].timestamp
    assert m.iloc[0].target == f.iloc[12].discharge_m3s
    assert x.iloc[0]["discharge_m3s_lag1"] == f.iloc[11].discharge_m3s
    assert x.shape[1] == 12 * 3 + 11


def test_future_values_cannot_change_first_prediction_features():
    f = frame()
    x, m = make_windows(f)
    f.loc[12:, ["upstream_m", "downstream_m", "discharge_m3s"]] = 999999
    xx, mm = make_windows(f)
    np.testing.assert_array_equal(x.iloc[0], xx.iloc[0])
    assert m.iloc[0].target != mm.iloc[0].target


def test_future_sampling_interval_is_not_a_feature():
    f = frame()
    x, _ = make_windows(f)
    f.loc[12, "timestamp"] += pd.Timedelta(minutes=20)
    xx, _ = make_windows(f)
    np.testing.assert_array_equal(x.iloc[0], xx.iloc[0])


def test_windows_do_not_cross_long_gaps_or_years():
    f = frame()
    f.loc[15:, "timestamp"] += pd.Timedelta(days=4)
    _, m = make_windows(f)
    assert not (
        (m.history_start < f.iloc[15].timestamp)
        & (m.target_time >= f.iloc[15].timestamp)
    ).any()
    f = frame()
    f["timestamp"] = pd.date_range("2003-12-31 12:00", periods=len(f), freq="h")
    _, m = make_windows(f)
    assert (m.history_start.dt.year == m.target_time.dt.year).all()


def test_conflicting_duplicates_excluded_and_exact_duplicates_deduplicated():
    f = frame(4)
    conflict = f.iloc[[0]].copy()
    conflict["discharge_m3s"] = 999
    x = pd.concat([f, conflict, f.iloc[[1]]], ignore_index=True)
    kept, removed = clean_observations(x)
    assert len(kept) == 3
    assert removed.exclusion_reason.value_counts().to_dict() == {
        "conflicting_duplicate_timestamp": 2,
        "duplicate_measurement": 1,
    }


def test_zero_flow_not_automatically_missing():
    f = frame(4)
    f.loc[0, "discharge_m3s"] = 0
    f.loc[1, ["upstream_m", "discharge_m3s"]] = 0
    kept, removed = clean_observations(f)
    assert 0 in kept.discharge_m3s.values
    assert len(removed) == 1


def test_hydraulic_factor_handles_invalid_heads():
    actual = hydraulic_factor(np.array([1.0, 0.5]), np.array([0.5, 1.0]), 80, -3)
    assert actual[0] == pytest.approx(80 * 3.5 * np.sqrt(19.6 * 0.5))
    assert np.isnan(actual[1])


def test_hybrid_input_does_not_use_current_flow():
    from tidal_gate.hybrid import samples, FEATURES

    f = frame()
    geo = pd.DataFrame([{"gate": "doulong", "width_m": 80, "sill_m": -3}])
    before = samples(f, geo)
    f.loc[2, "discharge_m3s"] = 99999
    after = samples(f, geo)
    np.testing.assert_array_equal(
        before.iloc[0][FEATURES].astype(float), after.iloc[0][FEATURES].astype(float)
    )
    assert before.iloc[0].log_coefficient != after.iloc[0].log_coefficient
