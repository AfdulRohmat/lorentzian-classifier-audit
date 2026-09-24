from __future__ import annotations

import numpy as np
import pandas as pd

from lorentzian_audit.backtest import event_windows, price_trade
from lorentzian_audit.signals import causal_knn_predictions


def test_causal_knn_never_uses_unmatured_label() -> None:
    features = np.arange(150, dtype=float).reshape(30, 5) / 100.0
    close = np.arange(30, dtype=float)
    _, diagnostic = causal_knn_predictions(
        features, close, "lorentzian", neighbors=2, max_bars_back=20
    )
    assert diagnostic["prediction_rows"] > 0
    assert diagnostic["maximum_selected_label_maturity_minus_decision"] <= 0


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
