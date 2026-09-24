"""Replay the frozen XAUUSD M30 account model with an additional capital level."""

from __future__ import annotations

import json
from itertools import product

import numpy as np
import pandas as pd

from .run_x100 import ROOT, account_calendar, file_hash
from .runner import simulate_account

CONTRACT = ROOT / "config" / "contract_xauusd_capital_sizing.json"
OUTPUT = ROOT / "evidence" / "xauusd_capital_sizing"


def validate(contract: dict, baseline: dict, trades: pd.DataFrame) -> dict:
    accounts = pd.read_csv(OUTPUT / "accounts.csv.gz")
    summaries = pd.read_csv(OUTPUT / "account_summary.csv")
    monthly = pd.read_csv(OUTPUT / "monthly.csv")
    annual = pd.read_csv(OUTPUT / "annual.csv")
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    old = pd.read_csv(ROOT / "evidence" / "v3_atr_runner_sizing" / "accounts.csv.gz")
    old = old.loc[old.asset.eq("xauusd") & old.timeframe.eq("30min")]
    spec = baseline["data"]["assets"]["xauusd"]
    keys = ["initial_balance_usd", "risk_percent"]
    checks = {
        "input_and_contract_hashes": (
            file_hash(CONTRACT) == manifest["contract_sha256"]
            and file_hash(ROOT / contract["input"]) == contract["input_sha256"]
            and file_hash(ROOT / contract["baseline_contract"])
            == contract["baseline_contract_sha256"]
        ),
        "full_grid": (
            set(map(tuple, summaries[keys].to_numpy()))
            == set(product(contract["balances_usd"], contract["risk_percents"]))
            and len(summaries) == 15
            and len(accounts) == 15 * contract["expected_candidate_trades"]
        ),
        "unique_rows": not accounts.duplicated([*keys, "trade_id"]).any(),
        "risk_and_volume": True,
        "cashflow_and_compounding": True,
        "same_fills_and_returns": True,
        "summaries_and_drawdowns": True,
        "calendar_returns": True,
        "ten_original_accounts_match": True,
    }
    for (balance, risk), ledger in accounts.groupby(keys):
        source = trades.set_index("trade_id").loc[ledger.trade_id]
        budget = ledger.equity_before.to_numpy() * risk / 100
        raw = np.minimum(budget / source.planned_loss_per_lot.to_numpy(), spec["volume_max"])
        lots = np.floor(raw / spec["volume_step"] + 1e-12) * spec["volume_step"]
        lots[lots + 1e-12 < spec["volume_min"]] = 0
        lots = np.round(lots, 8)
        checks["risk_and_volume"] &= bool(
            np.allclose(ledger.risk_budget_usd, budget)
            and np.allclose(ledger.volume, lots)
            and np.array_equal(ledger.status.eq("EXECUTED"), lots > 0)
            and (lots * source.planned_loss_per_lot.to_numpy() <= budget + 1e-8).all()
        )
        pnl = lots * source.net_per_lot_usd.to_numpy()
        checks["cashflow_and_compounding"] &= bool(
            np.allclose(ledger.pnl_usd, pnl)
            and np.allclose(ledger.equity_after, ledger.equity_before + pnl)
            and np.allclose(ledger.equity_before, np.r_[balance, ledger.equity_after.iloc[:-1]])
        )
        checks["same_fills_and_returns"] &= bool(
            np.array_equal(pd.to_datetime(ledger.entry_time), source.entry_time)
            and np.array_equal(pd.to_datetime(ledger.exit_time), source.exit_time)
        )
        row = summaries.loc[
            summaries.initial_balance_usd.eq(balance) & summaries.risk_percent.eq(risk)
        ].iloc[0]
        curve = np.r_[balance, ledger.equity_after]
        peak = np.maximum.accumulate(curve)
        checks["summaries_and_drawdowns"] &= bool(
            row.executed_trades == ledger.status.eq("EXECUTED").sum()
            and row.skipped_min_lot == ledger.status.eq("SKIP_MIN_LOT").sum()
            and np.isclose(row.final_balance_usd, curve[-1])
            and np.isclose(row.return_percent, (curve[-1] / balance - 1) * 100)
            and np.isclose(
                row.maximum_balance_drawdown_percent, ((peak - curve) / peak).max() * 100
            )
        )
        months = monthly.loc[
            monthly.initial_balance_usd.eq(balance) & monthly.risk_percent.eq(risk)
        ]
        years = annual.loc[
            annual.initial_balance_usd.eq(balance) & annual.risk_percent.eq(risk)
        ]
        actual = ledger.assign(month=pd.to_datetime(ledger.exit_time).dt.strftime("%Y-%m"))
        month_pnl = actual.groupby("month").pnl_usd.sum().reindex(months.month, fill_value=0)
        checks["calendar_returns"] &= bool(
            len(months) == 32
            and len(years) == 3
            and np.allclose(months.pnl_usd, month_pnl)
            and np.isclose(years.pnl_usd.sum(), pnl.sum())
            and np.isclose(row.mean_monthly_return_percent, months.return_percent.mean())
            and np.isclose(np.prod(1 + months.return_percent / 100), curve[-1] / balance)
            and np.isclose(np.prod(1 + years.return_percent / 100), curve[-1] / balance)
        )
        if balance in (500, 1000):
            original = old.loc[old.initial_balance_usd.eq(balance) & old.risk_percent.eq(risk)]
            cols = ["volume", "pnl_usd", "equity_before", "equity_after", "risk_budget_usd"]
            checks["ten_original_accounts_match"] &= bool(
                np.allclose(ledger[cols], original[cols], atol=1e-9)
                and np.array_equal(ledger.status.to_numpy(), original.status.to_numpy())
            )
    checks = {key: bool(value) for key, value in checks.items()}
    result = {
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "all_pass": all(checks.values()),
    }
    (OUTPUT / "validation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    if not result["all_pass"]:
        raise ValueError(f"Account validation failed: {result}")
    return result


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = ROOT / contract["input"]
    baseline_path = ROOT / contract["baseline_contract"]
    if file_hash(source) != contract["input_sha256"]:
        raise ValueError("Frozen trade ledger mismatch")
    if file_hash(baseline_path) != contract["baseline_contract_sha256"]:
        raise ValueError("Frozen v3 contract mismatch")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    all_trades = pd.read_csv(source, parse_dates=["entry_time", "exit_time"])
    trades = all_trades.loc[
        all_trades.asset.eq(contract["asset"]) & all_trades.timeframe.eq(contract["timeframe"])
    ].sort_values("entry_time")
    spec = baseline["data"]["assets"]["xauusd"]
    start = pd.Timestamp(baseline["data"]["evaluation_start"])
    end = pd.Timestamp(baseline["data"]["evaluation_end_exclusive"])
    weeks = (end - start).total_seconds() / (7 * 86400)
    accounts, summaries, monthly_rows, annual_rows = [], [], [], []
    for balance, risk in product(contract["balances_usd"], contract["risk_percents"]):
        ledger, summary = simulate_account(trades, spec, balance, risk, start, end)
        monthly, annual = account_calendar(ledger, balance, start, end)
        selected = trades.set_index("trade_id").loc[ledger.trade_id]
        tail = selected.net_r.to_numpy() > 3
        summary.update(
            {
                "trades_per_week": summary["executed_trades"] / weeks,
                "trades_per_month": summary["executed_trades"] / len(monthly),
                "geometric_monthly_return_percent": (
                    ((summary["final_balance_usd"] / balance) ** (1 / len(monthly)) - 1) * 100
                    if summary["final_balance_usd"] > 0
                    else None
                ),
                "median_monthly_return_percent": float(monthly.return_percent.median()),
                "positive_months": int(monthly.return_percent.gt(0).sum()),
                "negative_months": int(monthly.return_percent.lt(0).sum()),
                "tail_candidates": int(tail.sum()),
                "tail_executed": int((tail & ledger.status.eq("EXECUTED").to_numpy()).sum()),
            }
        )
        identity = {
            "asset": "xauusd",
            "timeframe": "30min",
            "initial_balance_usd": balance,
            "risk_percent": risk,
        }
        accounts.append(ledger.assign(**identity))
        summaries.append({**identity, **summary})
        monthly_rows.append(monthly.assign(**identity))
        annual_rows.append(annual.assign(**identity))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pd.concat(accounts, ignore_index=True).to_csv(
        OUTPUT / "accounts.csv.gz", index=False, compression={"method": "gzip", "mtime": 0}
    )
    summary_frame = pd.DataFrame(summaries)
    summary_frame.to_csv(OUTPUT / "account_summary.csv", index=False)
    pd.concat(monthly_rows, ignore_index=True).to_csv(OUTPUT / "monthly.csv", index=False)
    pd.concat(annual_rows, ignore_index=True).to_csv(OUTPUT / "annual.csv", index=False)
    manifest = {
        "study": contract["study"],
        "contract_sha256": file_hash(CONTRACT),
        "source_ledger_sha256": file_hash(source),
        "baseline_contract_sha256": file_hash(baseline_path),
        "spec": spec,
        "costs": baseline["costs"]["xauusd"],
        "evaluation_start": start.isoformat(),
        "evaluation_end_exclusive": end.isoformat(),
        "scenarios": len(summaries),
        "source_trades": len(trades),
        "limitations": contract["limitations"],
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(validate(contract, baseline, trades), indent=2))
    print(summary_frame.to_string(index=False))


if __name__ == "__main__":
    main()
