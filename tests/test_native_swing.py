from copy import deepcopy
from datetime import UTC, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd
import pytest

from lorentzian_audit.native_swing import audit_swing, validate_coverage


def fixture(side=1, k=1):
    stamp = int(datetime(2026, 1, 5, 12, tzinfo=UTC).timestamp())
    risk = 10 * k + 0.27
    stats = dict(stop_atr_multiplier=k, max_holding_hours=0, minimum_lot_fallback=1)
    events = pd.DataFrame(
        [
            (stamp, "ENTRY", str(side), 0.01),
            (stamp, "ENTRY_INITIAL_STOP", "price", 100 - side * 10 * k),
            (stamp, "ENTRY_ATR", "points", 10),
            (stamp, "ENTRY_RISK_PRICE", "points", risk),
            (stamp, "ENTRY_PLANNED_RISK", "usd", risk),
            (stamp + 1800, "MARK_R", "completed_m30_quote", 1),
            (stamp + 1800, "TRAIL", "tighten", 100 + side * 0.27),
            (stamp + 3600, "EXIT", "opposite", 110),
        ],
        columns=["time", "event", "detail", "value"],
    )
    events = pd.concat(
        [events, pd.DataFrame([(stamp, "ENTRY_BUDGET", "usd", 10)], columns=events.columns)],
        ignore_index=True,
    )
    deals = pd.DataFrame(
        [
            dict(
                position_id=1,
                entry=0,
                type=0 if side == 1 else 1,
                time=stamp,
                price=100,
                volume=0.01,
                profit=0,
                commission=-0.13,
                fee=0,
                swap=0,
                reason=3,
            ),
            dict(
                position_id=1,
                entry=1,
                type=1 if side == 1 else 0,
                time=stamp + 3600,
                price=100 + side * 10,
                volume=0.01,
                profit=10,
                commission=0,
                fee=0,
                swap=0,
                reason=3,
            ),
        ]
    )
    signals = pd.DataFrame(
        [dict(time=stamp - 1800, start=side), dict(time=stamp + 1800, start=-side)]
    )
    return stats, deals, events, signals


@pytest.mark.parametrize("side", [1, -1])
@pytest.mark.parametrize("k", range(1, 11))
def test_frozen_stop_and_scaled_trail_all_widths(side, k):
    result = audit_swing(*fixture(side, k))
    assert result["path_audit"] == "PASS"
    assert result["mean_holding_hours"] == 1
    assert result["mean_realized_r"] == pytest.approx(9.87 / (10 * k + 0.27))


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_stop",
        "early_trail",
        "wrong_trail_width",
        "time_exit",
        "same_direction_exit",
        "wrong_entry",
        "fixed_tp",
    ],
)
def test_invalid_path_cannot_pass(mutation):
    stats, deals, events, signals = deepcopy(fixture())
    if mutation == "wrong_stop":
        events.loc[1, "value"] = 95
    elif mutation == "early_trail":
        events.loc[5, "value"] = 0.99
    elif mutation == "wrong_trail_width":
        events.loc[6, "value"] = 101
    elif mutation == "time_exit":
        events.loc[7, "detail"] = "time_24h"
    elif mutation == "same_direction_exit":
        signals.loc[1, "start"] = 1
    elif mutation == "wrong_entry":
        signals.loc[0, "start"] = -1
    elif mutation == "fixed_tp":
        deals.loc[1, "reason"] = 5
    with pytest.raises(ValueError):
        audit_swing(stats, deals, events, signals)


def test_frozen_matrix_complete_and_fallback_only_on_one_percent():
    path = Path(__file__).resolve().parents[1] / "scripts/prepare_native_swing.py"
    spec = spec_from_file_location("prepare_swing", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.scenarios("test")
    assert len(rows) == len({r["tag"] for r in rows}) == 154
    swing = [r for r in rows if not r["smoke"] and not r["control"]]
    assert len(swing) == 150
    assert all(r["minimum_lot_fallback"] == (r["risk"] == 1) for r in rows)
    assert all(r["max_holding_hours"] == 0 for r in swing)


def test_early_end_only_accepted_for_verified_insolvent_stopout():
    expected = dict(first_tick=1, last_tick=100, tick_count=1000, classifier_bars=100)
    stats = dict(
        first_tick=1, last_tick=50, tick_count=500, classifier_bars=50, final_balance=-0.02
    )
    deals = pd.DataFrame([dict(entry=1, reason=6, time=50)])
    assert (
        validate_coverage(stats, deals, b"a\n", b"a\nb\n", expected)
        == "STOPPED_EARLY_INSOLVENT"
    )
    assert (
        validate_coverage(stats | dict(last_tick=49), deals, b"a\n", b"a\nb\n", expected)
        == "STOPPED_EARLY_INSOLVENT"
    )
    for patch in (dict(final_balance=20), dict(first_tick=2), dict(last_tick=51)):
        with pytest.raises(ValueError):
            validate_coverage(stats | patch, deals, b"a\n", b"a\nb\n", expected)
    with pytest.raises(ValueError):
        validate_coverage(stats, deals, b"c\n", b"a\nb\n", expected)
    deals.loc[0, "reason"] = 4
    with pytest.raises(ValueError):
        validate_coverage(stats, deals, b"a\n", b"a\nb\n", expected)


def test_strict_risk_cannot_silently_use_minimum_fallback():
    stats, deals, events, signals = fixture(k=3)
    stats["minimum_lot_fallback"] = 0
    with pytest.raises(ValueError, match="Position size"):
        audit_swing(stats, deals, events, signals)


def test_monetary_risk_must_match_volume_and_stop():
    stats, deals, events, signals = fixture()
    deals.loc[0, "volume"] = 0.02
    with pytest.raises(ValueError, match="monetary risk"):
        audit_swing(stats, deals, events, signals)
