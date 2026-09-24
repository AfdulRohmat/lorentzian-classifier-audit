from __future__ import annotations

import numpy as np
import pandas as pd

from lorentzian_audit.backtest import event_windows, price_trade
from lorentzian_audit.data import aggregate_timeframe
from lorentzian_audit.runner import (
    floor_volume,
    proposed_trailing_stop,
    stop_exit,
    tighten_stop,
)
from lorentzian_audit.signals import (
    causal_knn_prediction_pair_batched,
    causal_knn_predictions,
    feature_kernel_outputs,
    official_outputs,
)


def test_causal_knn_never_uses_unmatured_label() -> None:
    features = np.arange(150, dtype=float).reshape(30, 5) / 100.0
    close = np.arange(30, dtype=float)
    _, diagnostic = causal_knn_predictions(
        features, close, "lorentzian", neighbors=2, max_bars_back=20
    )
    assert diagnostic["prediction_rows"] > 0
    assert diagnostic["maximum_selected_label_maturity_minus_decision"] <= 0


def test_batched_causal_knn_matches_transparent_reference() -> None:
    rng = np.random.default_rng(20260925)
    features = rng.normal(size=(240, 5))
    close = 100.0 + rng.normal(size=240).cumsum()
    pair, diagnostics = causal_knn_prediction_pair_batched(
        features, close, neighbors=8, max_bars_back=80, batch_size=31
    )
    for metric in ("lorentzian", "euclidean"):
        expected, expected_diagnostic = causal_knn_predictions(
            features, close, metric, neighbors=8, max_bars_back=80
        )
        np.testing.assert_array_equal(pair[metric], expected)
        assert diagnostics[metric] == expected_diagnostic


def test_generic_aggregation_aligns_and_counts_minutes() -> None:
    index = pd.date_range("2026-01-01T00:00:00Z", periods=75, freq="min")
    minutes = pd.DataFrame(
        {
            "open": np.arange(75, dtype=float) + 100,
            "high": np.arange(75, dtype=float) + 101,
            "low": np.arange(75, dtype=float) + 99,
            "close": np.arange(75, dtype=float) + 100.5,
            "spread": 2.0,
            "tick_volume": 1,
        },
        index=index,
    )
    bars = aggregate_timeframe(minutes, "30min")
    assert bars.index.tolist() == list(index[[0, 30, 60]])
    assert bars["m1_rows"].tolist() == [30, 30, 15]
    assert (bars["bar_end"] - bars.index == pd.Timedelta(minutes=30)).all()


def test_fast_feature_kernel_path_matches_pinned_upstream() -> None:
    rng = np.random.default_rng(4824172)
    close = 100.0 + rng.normal(scale=0.2, size=260).cumsum()
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + rng.uniform(0.01, 0.25, size=len(close))
    low = np.minimum(open_, close) - rng.uniform(0.01, 0.25, size=len(close))
    bars = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close},
        index=pd.date_range("2026-01-01T00:00:00Z", periods=len(close), freq="30min"),
    )
    official = official_outputs(bars, 100.0)
    fast = feature_kernel_outputs(bars, 100.0)
    for column in ("kernel", "f1", "f2", "f3", "f4", "f5"):
        np.testing.assert_allclose(fast[column], official[column], equal_nan=True)


def test_position_size_floors_and_never_clamps_to_minimum() -> None:
    spec = {"volume_min": 0.14, "volume_step": 0.01, "volume_max": 1000.0}
    assert floor_volume(13.99, 100.0, spec) == 0.0
    assert floor_volume(14.99, 100.0, spec) == 0.14
    assert floor_volume(19.99, 100.0, spec) == 0.19


def test_long_and_short_stop_execution_use_correct_quote_side() -> None:
    profile = {
        "spread_floor": 0.0,
        "spread_multiplier": 1.0,
        "slippage_side": 0.02,
        "commission_round_trip_price": 0.07,
    }
    long_row = pd.Series({"open": 101.0, "high": 102.0, "low": 99.5, "spread": 20})
    short_row = pd.Series({"open": 100.0, "high": 101.0, "low": 99.0, "spread": 20})
    assert stop_exit(long_row, 1, 100.0, 0.01, profile) == (
        99.98,
        "STOP_INTRAMINUTE",
    )
    short_exit = stop_exit(short_row, -1, 100.1, 0.01, profile)
    assert short_exit is not None
    assert np.isclose(short_exit[0], 100.22)
    assert short_exit[1] == "STOP_GAP"


def test_trailing_stop_locks_requested_net_r_and_never_loosens() -> None:
    profile = {"slippage_side": 0.02, "commission_round_trip_price": 0.08}
    proposed = proposed_trailing_stop(
        entry_fill=100.0,
        side=1,
        locked_net_r=1.5,
        planned_risk_price=2.1,
        profile=profile,
    )
    assert np.isclose(proposed, 103.25)
    assert tighten_stop(99.0, proposed, 1) == proposed
    assert tighten_stop(proposed, 102.0, 1) == proposed
    short = proposed_trailing_stop(
        entry_fill=100.0,
        side=-1,
        locked_net_r=1.5,
        planned_risk_price=2.1,
        profile=profile,
    )
    assert np.isclose(short, 96.75)
    assert tighten_stop(101.0, short, -1) == short
    assert tighten_stop(short, 98.0, -1) == short


def test_event_window_enters_next_bar_and_holds_four_bars() -> None:
    signals = pd.DataFrame(
        {"start_long": [False, True] + [False] * 8, "start_short": [False] * 10}
    )
    assert event_windows(signals, 10) == [(1, 2, 6, 1)]


def test_early_opposite_event_flips_at_same_next_open() -> None:
    signals = pd.DataFrame(
        {
            "start_long": [False, True, False, False, False, False, False, False],
            "start_short": [False, False, False, True, False, False, False, False],
        }
    )
    assert event_windows(signals, 8) == [(1, 2, 4, 1)]


def test_long_and_short_pay_correct_spread_side() -> None:
    row = pd.Series(
        {
            "entry_bid": 100.0,
            "exit_bid": 102.0,
            "entry_spread_points": 10,
            "exit_spread_points": 20,
        }
    )
    profile = {
        "spread_floor": 0.0,
        "spread_multiplier": 1.0,
        "slippage_side": 0.1,
        "commission_round_trip_price": 0.3,
    }
    long = price_trade(row, 1, 0.01, profile)
    short = price_trade(row, -1, 0.01, profile)
    assert long["paid_spread_points"] == 0.1
    assert np.isclose(long["net_points"], 1.4)
    assert short["paid_spread_points"] == 0.2
    assert np.isclose(short["net_points"], -2.7)
