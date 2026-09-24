"""Conditional contract translation of frozen trades; no MT5 calls or orders."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .runner import floor_volume

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "config" / "contract_us500_x100_sizing.json"
OUTPUT = ROOT / "evidence" / "us500_x100_sizing"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def translate_contract(trades: pd.DataFrame, contract_size: float) -> pd.DataFrame:
    result = trades.copy()
    result["planned_loss_per_lot"] = result.planned_risk_price * contract_size
    result["net_per_lot_usd"] = result.net_price * contract_size
    return result


def simulate(
    trades: pd.DataFrame,
    spec: dict,
    balance: float,
    risk_percent: float,
    margin_rate: float | None,
    commission_price: float = 0.25,
) -> pd.DataFrame:
    equity = float(balance)
    rows = []
    for trade in trades.itertuples(index=False):
        budget = max(0.0, equity * risk_percent / 100.0)
        volume = floor_volume(budget, float(trade.planned_loss_per_lot), spec)
        desired_volume = volume
        margin = (
            volume * spec["contract_size"] * float(trade.entry_fill) * margin_rate
            if margin_rate is not None
            else 0.0
        )
        fee_reserve = volume * spec["contract_size"] * commission_price
        status = "EXECUTED"
        if equity <= 0:
            status = "SKIP_INSOLVENT"
        elif volume == 0:
            status = "SKIP_MIN_LOT"
        elif margin_rate is not None and margin + fee_reserve > equity + 1e-9:
            status = "SKIP_MARGIN"
        if status != "EXECUTED":
            volume = 0.0
        pnl = volume * float(trade.net_per_lot_usd)
        rows.append(
            {
                "trade_id": trade.trade_id,
                "entry_time": trade.entry_time,
                "exit_time": trade.exit_time,
                "equity_before": equity,
                "risk_budget_usd": budget,
                "risk_sized_volume": desired_volume,
                "volume": volume,
                "planned_risk_usd": volume * float(trade.planned_loss_per_lot),
                "entry_margin_required_usd": margin,
                "commission_reserve_usd": fee_reserve,
                "pnl_usd": pnl,
                "equity_after": equity + pnl,
                "source_net_r": trade.net_r,
                "status": status,
            }
        )
        equity += pnl
    return pd.DataFrame(rows)


def account_calendar(
    ledger: pd.DataFrame, balance: float, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    months = pd.period_range(
        start.tz_localize(None), (end - pd.Timedelta(days=1)).tz_localize(None), freq="M"
    )
    exits = pd.to_datetime(ledger.exit_time, utc=True).dt.tz_localize(None).dt.to_period("M")
    grouped = ledger.assign(month=exits, executed=ledger.status.eq("EXECUTED"))
    monthly = (
        grouped.groupby("month")
        .agg(
            pnl_usd=("pnl_usd", "sum"),
            executed_trades=("executed", "sum"),
            candidate_trades=("trade_id", "size"),
        )
        .reindex(months, fill_value=0.0)
    )
    monthly["equity_end"] = balance + monthly.pnl_usd.cumsum()
    monthly["equity_start"] = monthly.equity_end.shift(fill_value=balance)
    monthly["return_percent"] = monthly.pnl_usd / monthly.equity_start * 100.0
    annual = monthly.groupby(monthly.index.year).agg(
        equity_start=("equity_start", "first"),
        equity_end=("equity_end", "last"),
        pnl_usd=("pnl_usd", "sum"),
        executed_trades=("executed_trades", "sum"),
        candidate_trades=("candidate_trades", "sum"),
    )
    annual["return_percent"] = (annual.equity_end / annual.equity_start - 1.0) * 100.0
    monthly.index = monthly.index.astype(str)
    return monthly.reset_index(names="month"), annual.reset_index(names="year")


def describe(ledger: pd.DataFrame, monthly: pd.DataFrame, balance: float, weeks: float) -> dict:
    executed = ledger.loc[ledger.status.eq("EXECUTED")]
    curve = np.r_[balance, ledger.equity_after.to_numpy()]
    peaks = np.maximum.accumulate(curve)
    tail = ledger.source_net_r.gt(3.0)
    months = len(monthly)
    return {
        "candidate_trades": len(ledger),
        "executed_trades": len(executed),
        "skipped_min_lot": int(ledger.status.eq("SKIP_MIN_LOT").sum()),
        "skipped_margin": int(ledger.status.eq("SKIP_MARGIN").sum()),
        "skipped_insolvent": int(ledger.status.eq("SKIP_INSOLVENT").sum()),
        "final_balance_usd": float(curve[-1]),
        "return_percent": float((curve[-1] / balance - 1.0) * 100.0),
        "max_balance_drawdown_percent": float(((peaks - curve) / peaks).max() * 100.0),
        "trades_per_week": len(executed) / weeks,
        "trades_per_month": len(executed) / months,
        "mean_monthly_return_percent": float(monthly.return_percent.mean()),
        "geometric_monthly_return_percent": (
            float(((curve[-1] / balance) ** (1 / months) - 1) * 100) if curve[-1] > 0 else None
        ),
        "median_monthly_return_percent": float(monthly.return_percent.median()),
        "positive_months": int(monthly.return_percent.gt(0).sum()),
        "negative_months": int(monthly.return_percent.lt(0).sum()),
        "flat_months": int(monthly.return_percent.eq(0).sum()),
        "risk_budget_breaches": int(
            (executed.pnl_usd < -executed.risk_budget_usd - 1e-9).sum()
        ),
        "mean_executed_risk_budget_utilization_percent": (
            float((executed.planned_risk_usd / executed.risk_budget_usd).mean() * 100)
            if len(executed)
            else None
        ),
        "tail_candidates": int(tail.sum()),
        "tail_executed": int((tail & ledger.status.eq("EXECUTED")).sum()),
        "tail_skipped": int((tail & ~ledger.status.eq("EXECUTED")).sum()),
        "ruined": bool(np.min(curve) <= 0),
    }


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = ROOT / contract["input"]
    if file_hash(source) != contract["input_sha256"]:
        raise ValueError("Frozen input ledger hash mismatch")
    all_trades = pd.read_csv(source, parse_dates=["entry_time", "exit_time"])
    trades = (
        all_trades.loc[
            all_trades.asset.eq(contract["asset"])
            & all_trades.timeframe.eq(contract["timeframe"])
        ]
        .sort_values("entry_time")
        .reset_index(drop=True)
    )
    start = pd.Timestamp(contract["evaluation_start"])
    end = pd.Timestamp(contract["evaluation_end_exclusive"])
    weeks = (end - start).total_seconds() / (7 * 86400)
    accounts, summaries, monthly_rows, annual_rows = [], [], [], []
    for symbol, scenarios in contract["scenarios"].items():
        spec = contract["symbols"][symbol]
        converted = translate_contract(trades, float(spec["contract_size"]))
        for mode, margin_rate in scenarios.items():
            for balance in contract["balances_usd"]:
                for risk in contract["risk_percents"]:
                    identity = {
                        "symbol": symbol,
                        "mode": mode,
                        "initial_balance_usd": balance,
                        "risk_percent": risk,
                    }
                    ledger = simulate(
                        converted,
                        spec,
                        balance,
                        risk,
                        margin_rate,
                        float(contract["commission_round_trip_index_price"]),
                    )
                    monthly, annual = account_calendar(ledger, balance, start, end)
                    summaries.append({**identity, **describe(ledger, monthly, balance, weeks)})
                    accounts.append(ledger.assign(**identity))
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
        "status": "CONDITIONAL_SIZING_ONLY_LIVE_SPEC_UNVERIFIED",
        "contract_sha256": file_hash(CONTRACT),
        "source_ledger_sha256": file_hash(source),
        "scenarios": len(summaries),
        "source_trades": len(trades),
        "specification_source": contract["specification_source"],
        "limitations": contract["limitations"],
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    columns = [
        "symbol",
        "mode",
        "initial_balance_usd",
        "risk_percent",
        "executed_trades",
        "skipped_min_lot",
        "skipped_margin",
        "final_balance_usd",
        "return_percent",
        "mean_monthly_return_percent",
        "max_balance_drawdown_percent",
        "tail_executed",
    ]
    print(
        summary_frame.loc[summary_frame["mode"].eq("risk_only"), columns].to_string(index=False)
    )


if __name__ == "__main__":
    main()
