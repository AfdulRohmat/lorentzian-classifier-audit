from __future__ import annotations

import numpy as np
import pandas as pd

from lorentzian_audit.run_x100 import simulate, translate_contract


def trades() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_id": [1, 2],
            "entry_time": pd.to_datetime(["2024-01-01", "2024-01-02"], utc=True),
            "exit_time": pd.to_datetime(["2024-01-01T01:00Z", "2024-01-02T01:00Z"]),
            "entry_fill": [5000.0, 5000.0],
            "planned_risk_price": [10.0, 10.0],
            "net_price": [20.0, -10.0],
            "net_r": [2.0, -1.0],
        }
    )


def test_x100_scales_dollars_not_prices_or_r() -> None:
    original = trades()
    mapped = translate_contract(original, 100)
    assert mapped.planned_loss_per_lot.tolist() == [1000.0, 1000.0]
    assert mapped.net_per_lot_usd.tolist() == [2000.0, -1000.0]
    pd.testing.assert_frame_equal(mapped[original.columns], original)


def test_equal_exposure_has_equal_return_with_scaled_lot_constraints() -> None:
    regular = {
        "contract_size": 1.0,
        "volume_min": 1.0,
        "volume_step": 1.0,
        "volume_max": 2000.0,
    }
    large = {
        "contract_size": 100.0,
        "volume_min": 0.01,
        "volume_step": 0.01,
        "volume_max": 20.0,
    }
    left = simulate(translate_contract(trades(), 1), regular, 1000, 5, None)
    right = simulate(translate_contract(trades(), 100), large, 1000, 5, None)
    assert np.allclose(left.pnl_usd, right.pnl_usd)
    assert np.allclose(left.volume, right.volume * 100)
    assert right.risk_budget_usd.tolist() == [50.0, 55.0]


def test_x100_rejects_minimum_volume_when_risk_is_too_small() -> None:
    spec = {"contract_size": 100.0, "volume_min": 0.03, "volume_step": 0.01, "volume_max": 20.0}
    ledger = simulate(translate_contract(trades(), 100), spec, 500, 1, None)
    assert ledger.status.eq("SKIP_MIN_LOT").all()
    assert ledger.volume.eq(0).all()
    assert ledger.equity_after.eq(500).all()


def test_margin_sensitivity_skips_without_clamping_or_debiting_margin() -> None:
    spec = {"contract_size": 100.0, "volume_min": 0.03, "volume_step": 0.01, "volume_max": 20.0}
    source = translate_contract(trades(), 100)
    allowed = simulate(source, spec, 1000, 5, 0.0025)
    blocked = simulate(source, spec, 1000, 5, 0.05)
    assert np.isclose(allowed.entry_margin_required_usd.iloc[0], 62.5)
    assert np.isclose(allowed.equity_after.iloc[0], 1100)
    assert blocked.status.eq("SKIP_MARGIN").all()
    assert blocked.equity_after.eq(1000).all()


def test_gap_loss_can_exceed_planned_budget() -> None:
    spec = {"contract_size": 100.0, "volume_min": 0.03, "volume_step": 0.01, "volume_max": 20.0}
    source = trades().iloc[:1].copy()
    source["net_price"] = -15.0
    source["net_r"] = -1.5
    ledger = simulate(translate_contract(source, 100), spec, 1000, 5, None)
    assert ledger.planned_risk_usd.iloc[0] == 50
    assert ledger.pnl_usd.iloc[0] == -75
