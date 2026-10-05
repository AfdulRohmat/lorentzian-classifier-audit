"""Summarize actual MT5 exports. No price simulation or synthetic fills."""

from __future__ import annotations

import pandas as pd


def summarize_native(
    stats: dict, deals: pd.DataFrame, events: pd.DataFrame
) -> tuple[dict, list]:
    if int(stats["failed"]) or not int(stats["ready"]):
        raise ValueError("EA did not complete a valid initialized run")
    deposit = float(stats["deposit"])
    data = deals.copy()
    data["net"] = data[["profit", "commission", "fee", "swap"]].sum(axis=1)
    net = float(data.net.sum())
    if abs(net - float(stats["net_profit"])) > 0.011:
        raise ValueError("Native net profit does not reconcile to exported deals")
    if abs(deposit + net - float(stats["final_balance"])) > 0.011:
        raise ValueError("Final balance does not reconcile to deposit plus deals")
    if abs(float(stats["final_balance"]) - float(stats["final_equity"])) > 0.011:
        raise ValueError("Unresolved floating PnL at the end")
    closed = []
    for position_id, group in data.groupby("position_id"):
        entries = group.loc[group.entry.eq(0)]
        exits = group.loc[group.entry.isin([1, 3])]
        if (
            entries.empty
            or exits.empty
            or abs(entries.volume.sum() - exits.volume.sum()) > 1e-8
        ):
            raise ValueError(f"Unreconciled position {position_id}")
        closed.append(
            {
                "net": float(group.net.sum()),
                "side": int(entries.iloc[0]["type"]),
                "entry_time": int(entries.time.min()),
                "exit_time": int(exits.time.max()),
            }
        )
    if len(closed) != int(stats["trades"]):
        raise ValueError("Closed position count differs from native trade count")
    months = pd.period_range("2026-01", "2026-08", freq="M")
    data["month"] = pd.to_datetime(data.time, unit="s", utc=True).dt.strftime("%Y-%m")
    if not data.month.isin(months.astype(str)).all():
        raise ValueError("Deal outside frozen evaluation window")
    monthly = []
    balance = deposit
    for month in months.astype(str):
        selected = data.loc[data.month.eq(month)]
        pnl = float(selected.net.sum())
        monthly.append(
            {
                "month": month,
                "opening_balance": balance,
                "net_profit": pnl,
                "return_percent": pnl / balance * 100 if balance > 0 else None,
                "ending_balance": balance + pnl,
                "entries": int(selected.entry.eq(0).sum()),
            }
        )
        balance += pnl
    result = {key: float(value) for key, value in stats.items()}
    result.update(
        {
            "return_percent": net / deposit * 100,
            "commission": float(data.commission.sum()),
            "fee": float(data.fee.sum()),
            "swap": float(data.swap.sum()),
            "gross_price_profit": float(data.profit.sum()),
            "trades_per_week": len(closed)
            / ((pd.Timestamp("2026-09-01") - pd.Timestamp("2026-01-01")).days / 7),
            "trades_per_month": len(closed) / 8,
            "mean_monthly_profit_usd": net / 8,
            "mean_monthly_return_percent": sum(m["return_percent"] for m in monthly) / 8
            if all(m["return_percent"] is not None for m in monthly)
            else None,
            "geometric_monthly_return_percent": ((balance / deposit) ** (1 / 8) - 1) * 100
            if balance > 0
            else None,
            "win_rate_percent": float(stats["winners"]) / len(closed) * 100 if closed else None,
            "positive_months": sum(m["net_profit"] > 0 for m in monthly),
            "stopout_deals": int(data.reason.eq(6).sum()),
            "skips": events.loc[events.event.eq("SKIP"), "detail"].value_counts().to_dict(),
            "failure_events": int(events.event.eq("FAIL").sum()),
            "long_trades": sum(t["side"] == 0 for t in closed),
            "short_trades": sum(t["side"] == 1 for t in closed),
            "long_net": sum(t["net"] for t in closed if t["side"] == 0),
            "short_net": sum(t["net"] for t in closed if t["side"] == 1),
            "reconciliation": "PASS",
        }
    )
    if result["failure_events"]:
        raise ValueError("Failure event in purportedly valid run")
    budget_rows = events.loc[events.event.eq("ENTRY_BUDGET")]
    budgets = {int(row.time): float(row.value) for row in budget_rows.itertuples()}
    if len(budgets) != len(closed):
        raise ValueError("Missing or duplicate entry budgets")
    result["losses_exceeding_nominal_budget"] = sum(
        -t["net"] > budgets[t["entry_time"]] + 0.011 for t in closed
    )
    planned = events.loc[events.event.eq("ENTRY_PLANNED_RISK")]
    if len(planned):
        percents = [
            float(row.value) / budgets[int(row.time)] * float(stats["risk_percent"])
            for row in planned.itertuples()
        ]
        result["planned_actual_risk_percent_min"] = min(percents)
        result["planned_actual_risk_percent_max"] = max(percents)
        result["planned_actual_risk_percent_mean"] = sum(percents) / len(percents)
    result["minimum_lot_fallback_entries"] = int(
        events.event.eq("ENTRY_MINIMUM_FALLBACK").sum()
    )
    return result, monthly
