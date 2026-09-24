import numpy as np
import pandas as pd
import pytest

from lorentzian_audit.data import aggregate_timeframe
from lorentzian_audit.runner import build_runner_trades
from lorentzian_audit.trend_diagnosis import (
    candidate_indices,
    daily_trend,
    map_regime,
    policy_mask,
)


def minutes_fixture(index, close):
    return pd.DataFrame(
        {
            "open": close,
            "high": np.asarray(close) + 2,
            "low": np.asarray(close) - 2,
            "close": close,
            "spread": 0.0,
            "tick_volume": 1,
        },
        index=index,
    )


def test_daily_regime_is_available_only_after_day_end_and_prefix_stable():
    index = pd.date_range("2023-01-01", periods=250, freq="D", tz="UTC")
    m = minutes_fixture(index, np.arange(250.0) + 100)
    full = daily_trend(m)
    prefix = daily_trend(m.iloc[:230])
    pd.testing.assert_frame_equal(prefix, full.iloc[:230])
    times = pd.DatetimeIndex([index[230] - pd.Timedelta(minutes=30), index[230]])
    bars = pd.DataFrame({"bar_end": times}, index=times - pd.Timedelta(minutes=30))
    mapped = map_regime(bars, full)
    assert mapped.available_at.iloc[0] == index[229]
    assert mapped.available_at.iloc[1] == index[230]
    assert mapped.regime.eq("bull").all()


def test_policy_rejects_mixed_and_does_not_change_signals():
    s = pd.DataFrame(
        {"start_long": [True, True, False, False], "start_short": [False, False, True, True]}
    )
    regime = pd.Series(["bull", "mixed", "bear", "bull"])
    assert policy_mask(s, regime, "trend_aligned").tolist() == [True, False, True, False]
    assert s.start_short.tolist() == [False, False, True, True]


def test_bear_mixed_and_unavailable_are_distinct():
    prices = np.linspace(500.0, 250.0, 250)
    m = minutes_fixture(pd.date_range("2023-01-01", periods=250, freq="D", tz="UTC"), prices)
    trend = daily_trend(m)
    assert trend.regime.iloc[:219].eq("unavailable").all()
    assert trend.regime.iloc[-1] == "bear"
    m.loc[m.index[-1], ["open", "high", "low", "close"]] = [999.0, 1001.0, 997.0, 999.0]
    changed = daily_trend(m)
    assert changed.regime.iloc[-1] == "mixed"


def test_rejected_short_entry_still_closes_long():
    m = minutes_fixture(
        pd.date_range("2024-01-01", periods=2400, freq="min", tz="UTC"), np.full(2400, 100.0)
    )
    bars = aggregate_timeframe(m, "30min")
    s = pd.DataFrame({"start_long": False, "start_short": False}, index=bars.index)
    s.iloc[15, 0] = True
    s.iloc[17, 1] = True
    args = dict(
        asset="test",
        timeframe="30min",
        bars=bars,
        minutes=m,
        signals=s,
        asset_config={"point": 0.01, "contract_size": 1},
        profile={
            "spread_multiplier": 1,
            "spread_floor": 0,
            "slippage_side": 0,
            "commission_round_trip_price": 0,
        },
        exit_config={
            "atr_period": 14,
            "initial_stop_atr": 1,
            "trail_activation_net_r": 1,
            "trail_distance_net_r": 1,
            "maximum_holding_hours": 24,
        },
        evaluation_start=m.index[0],
        evaluation_end=m.index[-1],
    )
    unrestricted = build_runner_trades(**args)
    explicit = build_runner_trades(**args, entry_mask=pd.Series(True, index=bars.index))
    pd.testing.assert_frame_equal(unrestricted, explicit)
    gated = build_runner_trades(**args, entry_mask=s.start_long)
    assert len(gated) == 1 and gated.exit_reason.iloc[0] == "OPPOSITE"
    assert gated.exit_time.iloc[0] == bars.index[18]
    assert unrestricted.direction.tolist() == [1, -1]
    with pytest.raises(ValueError):
        build_runner_trades(**args, entry_mask=s.start_long.iloc[:-1])


def test_matches_do_not_cross_clock_regime_or_volatility_caliper():
    pool = pd.DataFrame(
        {
            "month": ["2024-01"] * 4,
            "ny_hour": [9, 9, 9, 10],
            "regime": ["bull", "bear", "bull", "bull"],
            "relative_atr": [0.01, 0.01, 0.02, 0.01],
        }
    )
    anchor = pd.Series(
        {"month": "2024-01", "ny_hour": 9, "regime": "bull", "relative_atr": 0.01}
    )
    assert candidate_indices(pool, anchor).tolist() == [0]
