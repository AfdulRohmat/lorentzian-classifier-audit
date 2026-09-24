import numpy as np
import pandas as pd
import pytest

from lorentzian_audit.run_entry_comparison import paired_blocks
from lorentzian_audit.signals import build_full_history_variants, feature_kernel_outputs


def test_calendar_pairing_cancels_shared_shocks():
    shocks = np.array([40, -30, 25, -18, 4, 10, -9, -22.0])
    result = paired_blocks(shocks + 2, shocks)
    assert result["ci95"] == [2.0, 2.0]
    assert result["family_adjusted_ci"] == [2.0, 2.0]


def test_direction_reversal_and_multiplicity_interval():
    left = np.arange(32.0) ** 1.5
    right = np.sin(left)
    forward = paired_blocks(left, right)
    backward = paired_blocks(right, left)
    np.testing.assert_allclose(forward["ci95"], -np.array(backward["ci95"])[::-1])
    assert forward["family_adjusted_ci"][0] <= forward["ci95"][0]
    assert forward["family_adjusted_ci"][1] >= forward["ci95"][1]
    assert forward == paired_blocks(left, right)


@pytest.mark.parametrize("left,right", [([], []), ([1], [1, 2]), ([np.nan], [1])])
def test_invalid_calendar_rejected(left, right):
    with pytest.raises(ValueError):
        paired_blocks(left, right)


def test_all_signal_policies_invariant_to_unseen_suffix():
    rng = np.random.default_rng(37)
    close = 100 + rng.normal(size=320).cumsum()
    opening = np.r_[close[0], close[:-1]]
    bars = pd.DataFrame(
        {
            "open": opening,
            "high": np.maximum(opening, close) + 0.5,
            "low": np.minimum(opening, close) - 0.5,
            "close": close,
        },
        index=pd.date_range("2024-01-01", periods=len(close), freq="30min", tz="UTC"),
    )
    prefix = bars.iloc[:240]
    short_features = feature_kernel_outputs(prefix, 100)
    full_features = feature_kernel_outputs(bars, 100)
    pd.testing.assert_frame_equal(short_features, full_features.iloc[:240])
    short_signals, _ = build_full_history_variants(prefix, short_features)
    full_signals, _ = build_full_history_variants(bars, full_features)
    for name in short_signals:
        pd.testing.assert_frame_equal(short_signals[name], full_signals[name].iloc[:240])
