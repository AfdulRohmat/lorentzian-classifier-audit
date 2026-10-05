from datetime import UTC, datetime

import pandas as pd
import pytest

from lorentzian_audit.native_results import summarize_native


def fixture():
    stamp = int(datetime(2026, 1, 5, tzinfo=UTC).timestamp())
    stats = {
        "failed": 0,
        "ready": 1,
        "deposit": 1000,
        "net_profit": 9,
        "final_balance": 1009,
        "final_equity": 1009,
        "trades": 1,
        "winners": 1,
    }
    deals = pd.DataFrame(
        [
            {
                "position_id": 1,
                "entry": 0,
                "type": 0,
                "reason": 3,
                "volume": 0.01,
                "time": stamp,
                "profit": 0,
                "commission": -1,
                "fee": 0,
                "swap": 0,
            },
            {
                "position_id": 1,
                "entry": 1,
                "type": 1,
                "reason": 4,
                "volume": 0.01,
                "time": stamp + 3600,
                "profit": 10,
                "commission": 0,
                "fee": 0,
                "swap": 0,
            },
        ]
    )
    events = pd.DataFrame(
        [{"event": "ENTRY_BUDGET", "detail": "usd", "time": stamp, "value": 10}]
    )
    return stats, deals, events


def test_native_cash_reconciliation_and_eight_month_calendar():
    result, months = summarize_native(*fixture())
    assert result["return_percent"] == pytest.approx(0.9)
    assert result["commission"] == -1
    assert len(months) == 8
    assert months[0]["return_percent"] == pytest.approx(0.9)
    assert months[1]["return_percent"] == 0
    assert result["mean_monthly_profit_usd"] == 9 / 8


def test_native_failure_and_balance_mismatch_cannot_pass():
    stats, deals, events = fixture()
    stats["failed"] = 1
    with pytest.raises(ValueError, match="valid initialized"):
        summarize_native(stats, deals, events)
    stats["failed"] = 0
    stats["final_balance"] = 999
    with pytest.raises(ValueError, match="Final balance"):
        summarize_native(stats, deals, events)


def test_unclosed_position_cannot_be_counted_as_closed_trade():
    stats, deals, events = fixture()
    deals.loc[1, "volume"] = 0.005
    with pytest.raises(ValueError, match="Unreconciled position"):
        summarize_native(stats, deals, events)


def test_nominal_risk_is_not_assumed_hard_loss_cap():
    stats, deals, events = fixture()
    deals.loc[1, "profit"] = -11
    stats.update(net_profit=-12, final_balance=988, final_equity=988, winners=0)
    result, _ = summarize_native(stats, deals, events)
    assert result["losses_exceeding_nominal_budget"] == 1


def test_minimum_lot_risk_is_reported_above_nominal_target():
    stats, deals, events = fixture()
    stats["risk_percent"] = 1
    extra = pd.DataFrame(
        [
            {
                "event": "ENTRY_PLANNED_RISK",
                "detail": "usd",
                "time": events.iloc[0].time,
                "value": 25,
            },
            {
                "event": "ENTRY_MINIMUM_FALLBACK",
                "detail": "actual_risk_percent",
                "time": events.iloc[0].time,
                "value": 2.5,
            },
        ]
    )
    result, _ = summarize_native(stats, deals, pd.concat([events, extra], ignore_index=True))
    assert result["planned_actual_risk_percent_max"] == 2.5
    assert result["minimum_lot_fallback_entries"] == 1


def test_insolvency_is_retained_without_inventing_monthly_compounding():
    stats, deals, events = fixture()
    deals["profit"] = deals.profit.astype(float)
    deals.loc[1, "profit"] = -999.02
    deals.loc[1, "reason"] = 6
    stats.update(net_profit=-1000.02, final_balance=-0.02, final_equity=-0.02, winners=0)
    result, months = summarize_native(stats, deals, events)
    assert result["return_percent"] == pytest.approx(-100.002)
    assert result["stopout_deals"] == 1
    assert result["mean_monthly_return_percent"] is None
    assert result["geometric_monthly_return_percent"] is None
    assert months[1]["return_percent"] is None
