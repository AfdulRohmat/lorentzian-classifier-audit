"""Independently reconcile conditional contract-sizing ledgers."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .run_x100 import CONTRACT, OUTPUT, ROOT, file_hash


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    accounts = pd.read_csv(OUTPUT / "accounts.csv.gz")
    summaries = pd.read_csv(OUTPUT / "account_summary.csv")
    monthly = pd.read_csv(OUTPUT / "monthly.csv")
    annual = pd.read_csv(OUTPUT / "annual.csv")
    trades = pd.read_csv(ROOT / contract["input"])
    trades = trades.loc[trades.asset.eq("sp500") & trades.timeframe.eq("30min")]
    old = pd.read_csv(ROOT / "evidence" / "v3_atr_runner_sizing" / "accounts.csv.gz")
    old = old.loc[old.asset.eq("sp500") & old.timeframe.eq("30min")]
    keys = ["symbol", "mode", "initial_balance_usd", "risk_percent"]
    checks = {
        "contract_and_source_hashes": (
            file_hash(CONTRACT) == manifest["contract_sha256"]
            and file_hash(ROOT / contract["input"])
            == contract["input_sha256"]
            == manifest["source_ledger_sha256"]
        ),
        "full_scenario_grid": len(summaries) == 75 and len(accounts) == 75 * 688,
        "unique_scenarios_and_trades": (
            not summaries.duplicated(keys).any()
            and not accounts.duplicated([*keys, "trade_id"]).any()
        ),
        "next_bar_chronological_source": bool(
            (pd.to_datetime(trades.entry_time) > pd.to_datetime(trades.signal_time)).all()
            and (pd.to_datetime(trades.exit_time) >= pd.to_datetime(trades.entry_time)).all()
            and (
                pd.to_datetime(trades.entry_time).iloc[1:].to_numpy()
                >= pd.to_datetime(trades.exit_time).iloc[:-1].to_numpy()
            ).all()
        ),
    }
    flags = dict.fromkeys(
        [
            "risk_sizing_and_skip_rules",
            "cashflow_and_compounding",
            "planned_risk_cap",
            "unchanged_price_returns",
            "summary_totals_and_drawdowns",
            "monthly_and_annual",
            "v3_reference_account_parity",
            "tail_capture_accounting",
        ],
        True,
    )
    for identity, ledger in accounts.groupby(keys, sort=False):
        symbol, mode, balance, risk = identity
        spec = contract["symbols"][symbol]
        rate = contract["scenarios"][symbol][mode]
        source = trades.set_index("trade_id").loc[ledger.trade_id]
        loss_per_lot = source.planned_risk_price.to_numpy() * spec["contract_size"]
        pnl_per_lot = source.net_price.to_numpy() * spec["contract_size"]
        budget = np.maximum(0, ledger.equity_before.to_numpy() * risk / 100)
        raw_lots = np.minimum(budget / loss_per_lot, spec["volume_max"])
        lots = np.round(
            np.floor(raw_lots / spec["volume_step"] + 1e-12) * spec["volume_step"], 8
        )
        lots[lots + 1e-12 < spec["volume_min"]] = 0
        margin = source.entry_fill.to_numpy() * spec["contract_size"] * lots * (rate or 0)
        fee = lots * spec["contract_size"] * contract["commission_round_trip_index_price"]
        expected_status = np.full(len(ledger), "EXECUTED", dtype=object)
        if rate is not None:
            expected_status[margin + fee > ledger.equity_before.to_numpy() + 1e-9] = (
                "SKIP_MARGIN"
            )
        expected_status[lots == 0] = "SKIP_MIN_LOT"
        expected_status[ledger.equity_before.to_numpy() <= 0] = "SKIP_INSOLVENT"
        expected_volume = np.where(expected_status == "EXECUTED", lots, 0)
        pnl = expected_volume * pnl_per_lot
        flags["risk_sizing_and_skip_rules"] &= bool(
            np.array_equal(ledger.status, expected_status)
            and np.allclose(ledger.volume, expected_volume)
            and np.allclose(ledger.risk_sized_volume, lots)
            and np.allclose(ledger.entry_margin_required_usd, margin)
            and np.allclose(ledger.commission_reserve_usd, fee)
        )
        flags["cashflow_and_compounding"] &= bool(
            np.allclose(ledger.pnl_usd, pnl)
            and np.allclose(ledger.equity_before, np.r_[balance, ledger.equity_after.iloc[:-1]])
            and np.allclose(ledger.equity_after, ledger.equity_before + pnl)
        )
        flags["planned_risk_cap"] &= bool(
            (ledger.planned_risk_usd <= budget + 1e-8).all()
            and np.allclose(ledger.planned_risk_usd, expected_volume * loss_per_lot)
        )
        flags["unchanged_price_returns"] &= bool(
            np.allclose(ledger.source_net_r, source.net_r)
            and np.array_equal(ledger.entry_time.to_numpy(), source.entry_time.to_numpy())
            and np.array_equal(ledger.exit_time.to_numpy(), source.exit_time.to_numpy())
        )
        select = lambda frame, identity=identity: frame.loc[  # noqa: E731
            np.logical_and.reduce([frame[k].eq(v) for k, v in zip(keys, identity, strict=True)])
        ]
        row = select(summaries).iloc[0]
        curve = np.r_[balance, ledger.equity_after]
        peaks = np.maximum.accumulate(curve)
        flags["summary_totals_and_drawdowns"] &= bool(
            row.executed_trades == ledger.status.eq("EXECUTED").sum()
            and row.skipped_min_lot == ledger.status.eq("SKIP_MIN_LOT").sum()
            and row.skipped_margin == ledger.status.eq("SKIP_MARGIN").sum()
            and np.isclose(row.final_balance_usd, curve[-1])
            and np.isclose(row.return_percent, (curve[-1] / balance - 1) * 100)
            and np.isclose(
                row.max_balance_drawdown_percent, ((peaks - curve) / peaks).max() * 100
            )
        )
        months = select(monthly)
        years = select(annual)
        actual_month = pd.to_datetime(ledger.exit_time, utc=True).dt.strftime("%Y-%m")
        actual_pnl = ledger.assign(month=actual_month).groupby("month").pnl_usd.sum()
        flags["monthly_and_annual"] &= bool(
            len(months) == 32
            and len(years) == 3
            and np.allclose(months.pnl_usd, actual_pnl.reindex(months.month, fill_value=0))
            and np.isclose(months.pnl_usd.sum(), ledger.pnl_usd.sum())
            and np.isclose(years.pnl_usd.sum(), ledger.pnl_usd.sum())
            and np.isclose(row.mean_monthly_return_percent, months.return_percent.mean())
            and np.isclose(np.prod(1 + months.return_percent / 100), curve[-1] / balance)
            and np.isclose(np.prod(1 + years.return_percent / 100), curve[-1] / balance)
        )
        flags["tail_capture_accounting"] &= bool(
            row.tail_candidates == 53
            and row.tail_executed
            == (ledger.source_net_r.gt(3) & ledger.status.eq("EXECUTED")).sum()
            and row.tail_executed + row.tail_skipped == 53
        )
        if symbol == "US500" and balance in (500, 1000):
            original = old.loc[old.initial_balance_usd.eq(balance) & old.risk_percent.eq(risk)]
            numeric = ["volume", "pnl_usd", "equity_before", "equity_after", "risk_budget_usd"]
            flags["v3_reference_account_parity"] &= bool(
                np.allclose(ledger[numeric], original[numeric], atol=1e-9)
                and np.array_equal(ledger.status.to_numpy(), original.status.to_numpy())
            )
    checks.update({name: bool(value) for name, value in flags.items()})
    payload = {
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "all_pass": all(checks.values()),
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    (OUTPUT / "validation.json").write_text(text, encoding="utf-8")
    print(text)
    if not payload["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
