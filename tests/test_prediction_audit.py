import numpy as np
import pandas as pd

from lorentzian_audit.audit_predictions import block_ratio_interval, past_majority, targets


def test_exact_four_observed_bars_and_missing_labels():
    ends = pd.to_datetime(
        [
            "2024-01-05T20:00Z",
            "2024-01-05T20:30Z",
            "2024-01-05T21:00Z",
            "2024-01-08T00:00Z",
            "2024-01-08T00:30Z",
            "2024-01-08T01:00Z",
        ]
    )
    bars = pd.DataFrame(
        {"bar_end": ends, "close": [100, 101, 102, 100, 99, 101], "spread_close_points": 1},
        index=ends - pd.Timedelta(minutes=30),
    )
    result = targets(bars)
    assert result.truth.iloc[0] == -1
    assert result.truth.iloc[1] == 0  # Real unchanged price, not missing future data.
    assert result.truth.iloc[-4:].isna().all()
    assert result.elapsed_minutes.iloc[0] > 120


def test_prior_cannot_use_future_or_unmatured_labels():
    truth = pd.Series([-1.0] * 10 + [1.0] * 10)
    before = past_majority(truth, window=5, minimum=2)
    changed = truth.copy()
    changed.iloc[9:] = 1
    after = past_majority(changed, window=5, minimum=2)
    pd.testing.assert_series_equal(before.iloc[:13], after.iloc[:13])
    assert before.iloc[:5].isna().all()


def test_paired_bootstrap_preserves_constant_difference_and_zero_counts():
    monthly = np.array([[5.0, 10.0], [0.0, 0.0], [10.0, 20.0], [2.0, 4.0]])
    result = block_ratio_interval(monthly, replicates=200, family=3)
    assert result["estimate"] == 0.5
    assert result["ci95"] == [0.5, 0.5]
    assert result["adjusted_ci"] == [0.5, 0.5]
    assert block_ratio_interval(np.zeros((4, 2)))["estimate"] is None
