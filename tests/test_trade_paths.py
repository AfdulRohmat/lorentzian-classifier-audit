from types import SimpleNamespace

import numpy as np
import pandas as pd

from lorentzian_audit.audit_trade_paths import (
    first_barrier,
    marks,
    position_path,
    shadow_window,
)


def fixture():
    index = pd.date_range("2024-01-01", periods=5, freq="min", tz="UTC")
    m = pd.DataFrame(
        {
            "open": 100.0,
            "high": [100.5, 102, 900, 101, 101],
            "low": 99.0,
            "close": 100.0,
            "spread": 1.0,
        },
        index=index,
    )
    t = SimpleNamespace(
        entry_time=index[0],
        exit_time=index[2],
        entry_fill=100.0,
        direction=1,
        planned_risk_price=1.0,
        net_r=-1.0,
        exit_reason="STOP_INTRAMINUTE",
        trail_activated=False,
    )
    return (
        m,
        t,
        {"point": 0.1},
        {
            "spread_multiplier": 1.0,
            "spread_floor": 0.0,
            "slippage_side": 0.0,
            "commission_round_trip_price": 0.0,
        },
    )


def test_exit_minute_is_not_claimed_as_available_profit():
    m, t, spec, profile = fixture()
    path = position_path(m, t, spec, profile)
    assert path["mfe_lower_r"] == 2
    assert path["mfe_upper_r"] == 800
    assert path["giveback_lower_r"] == 3
    assert path["peak_minutes"] == 1
    t.exit_reason = "STOP_GAP"
    assert position_path(m, t, spec, profile)["mfe_upper_r"] == 2


def test_short_liquidation_uses_ask_and_low_is_favorable():
    m, t, spec, profile = fixture()
    t.direction = -1
    r = marks(m, t, spec, profile)
    np.testing.assert_allclose(r["favorable"], 0.9)
    np.testing.assert_allclose(r["open"], -0.1)


def test_same_minute_barriers_are_ambiguous():
    assert first_barrier([0.5, 2], [-0.5, -2]) == "SAME_MINUTE_AMBIGUOUS"
    assert first_barrier([2, 0.5], [-0.5, -2]) == "POSITIVE_FIRST"
    assert first_barrier([0.5, 0.5], [-0.5, -0.5]) == "NEITHER"


def test_shadow_requires_exact_horizon_and_coverage():
    m, t, spec, profile = fixture()
    assert shadow_window(m, t, spec, profile, 4)["valid"]
    assert not shadow_window(m.drop(m.index[4]), t, spec, profile, 4)["valid"]
    assert not shadow_window(m.drop(m.index[1]), t, spec, profile, 4)["valid"]
    assert not shadow_window(m.drop(m.index[0]), t, spec, profile, 4)["valid"]
