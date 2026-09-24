"""Portable independent reconciliation of saved entry-comparison artifacts."""

import json

import numpy as np
import pandas as pd

from .run_entry_comparison import paired_blocks
from .run_v3 import ROOT, _sha256
from .statistics import max_drawdown, profit_factor


def main():
    folder = ROOT / "evidence/runner_entry_comparison"
    contract_path = ROOT / "config/contract_runner_entry_comparison.json"
    contract = json.loads(contract_path.read_text())
    v3 = json.loads((ROOT / "config/contract_v3_atr_runner_sizing.json").read_text())
    v2 = json.loads((ROOT / "config/contract_v2_lower_timeframes.json").read_text())
    summary = json.loads((folder / "summary.json").read_text())
    trades = pd.read_csv(
        folder / "trades.csv.gz", parse_dates=["signal_time", "entry_time", "exit_time"]
    )
    accounts = pd.read_csv(folder / "accounts.csv.gz")
    monthly = pd.read_csv(folder / "monthly.csv")
    annual = pd.read_csv(folder / "annual.csv")
    assert summary["contract_sha256"] == _sha256(contract_path)
    assert (trades.entry_time >= trades.signal_time + pd.Timedelta(minutes=30)).all()
    for cell in summary["cells"]:
        asset, cost, variant = (cell[k] for k in ("asset", "cost", "variant"))

        def select(frame, asset=asset, cost=cost, variant=variant):
            return frame.loc[
                frame.asset.eq(asset) & frame.cost.eq(cost) & frame.variant.eq(variant)
            ].reset_index(drop=True)

        rows, ledger, calendar = select(trades), select(accounts), select(monthly)
        profile, spec = v2["costs"][asset][cost], v3["data"]["assets"][asset]
        expected = rows.direction * (rows.exit_fill - rows.entry_fill)
        expected -= profile["commission_round_trip_price"]
        np.testing.assert_allclose(rows.net_price, expected, atol=1e-9)
        risk = rows.atr + profile["slippage_side"] + profile["commission_round_trip_price"]
        np.testing.assert_allclose(rows.planned_risk_price, risk)
        np.testing.assert_allclose(rows.net_r, expected / risk, atol=1e-9)
        assert (rows.direction * (rows.final_stop - rows.initial_stop) >= -1e-9).all()
        assert len(rows) == cell["trades"]
        assert np.isclose(rows.net_r.sum(), cell["total_r"])
        assert np.isclose(profit_factor(rows.net_r.to_numpy()), cell["profit_factor"])
        assert np.isclose(max_drawdown(rows.net_r.to_numpy()), cell["max_drawdown_r"])
        months = rows.exit_time.dt.strftime("%Y-%m")
        expected_monthly = (
            rows.groupby(months).net_r.sum().reindex(calendar.month, fill_value=0)
        )
        np.testing.assert_allclose(expected_monthly, calendar.net_r, atol=1e-9)
        assert len(calendar) == 32 and np.isclose(select(annual).net_r.sum(), rows.net_r.sum())
        assert len(ledger) == len(rows)
        np.testing.assert_allclose(ledger.pnl_usd, ledger.volume * rows.net_per_lot_usd)
        np.testing.assert_allclose(ledger.equity_after, 3000 + ledger.pnl_usd.cumsum())
        np.testing.assert_allclose(ledger.risk_budget_usd, ledger.equity_before * 0.01)
        assert (
            ledger.volume * rows.planned_loss_per_lot <= ledger.risk_budget_usd + 1e-8
        ).all()
        positive = ledger.volume > 0
        assert (ledger.loc[positive, "volume"] >= spec["volume_min"] - 1e-9).all()
        units = ledger.volume / spec["volume_step"]
        np.testing.assert_allclose(units, np.round(units), atol=1e-7)
        account = next(
            r
            for r in summary["accounts"]
            if r["asset"] == asset and r["cost"] == cost and r["variant"] == variant
        )
        assert np.isclose(account["final_balance_usd"], ledger.equity_after.iloc[-1])
        assert account["executed_trades"] == int(positive.sum())
        assert account["skipped_min_lot"] == int((~positive).sum())
    settings = contract["bootstrap"]
    for comparison in summary["paired_monthly_comparisons"]:
        wide = monthly.loc[monthly.asset.eq(comparison["asset"]) & monthly.cost.eq("base")]
        wide = wide.pivot(index="month", columns="variant", values="net_r").sort_index()
        replay = paired_blocks(
            wide.causal_lorentzian,
            wide[comparison["control"]],
            block=settings["circular_block_months"],
            replicates=settings["replicates"],
            seed=settings["seed"],
            family=settings["primary_comparisons"],
        )
        for key in replay:
            np.testing.assert_allclose(replay[key], comparison[key], atol=1e-9)
    result = {
        "passed": True,
        "cells_reconciled": len(summary["cells"]),
        "comparisons_replayed": len(summary["paired_monthly_comparisons"]),
        "scope": (
            "Saved-artifact accounting, calendar, sizing and bootstrap reconciliation; "
            "source hashes and original ledger parity checked during full replay"
        ),
    }
    (folder / "independent_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
