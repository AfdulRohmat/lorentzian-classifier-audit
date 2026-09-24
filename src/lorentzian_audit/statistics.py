from __future__ import annotations

import numpy as np
import pandas as pd


def profit_factor(values: np.ndarray) -> float | None:
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    return gains / losses if losses > 0 else None


def max_drawdown(values: np.ndarray) -> float:
    equity = np.r_[0.0, np.cumsum(values)]
    peaks = np.maximum.accumulate(equity)
    return float((peaks - equity).max())


def summary(values: np.ndarray, weeks: float, top_n: int = 5) -> dict:
    if len(values) == 0:
        return {
            "trades": 0,
            "trades_per_week": 0.0,
            "net_bps": 0.0,
            "mean_bps": None,
            "win_rate": None,
            "profit_factor": None,
            "max_drawdown_bps": 0.0,
            "net_bps_ex_top5": 0.0,
        }
    remove = min(top_n, len(values))
    top_indices = np.argsort(values)[-remove:]
    keep = np.ones(len(values), dtype=bool)
    keep[top_indices] = False
    return {
        "trades": len(values),
        "trades_per_week": len(values) / weeks,
        "net_bps": float(values.sum()),
        "mean_bps": float(values.mean()),
        "median_bps": float(np.median(values)),
        "win_rate": float((values > 0).mean()),
        "profit_factor": profit_factor(values),
        "max_drawdown_bps": max_drawdown(values),
        "net_bps_ex_top5": float(values[keep].sum()),
    }


def calendar_tables(
    trades: pd.DataFrame, value_column: str, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    months = pd.period_range(
        start=start.tz_localize(None),
        end=(end - pd.Timedelta(days=1)).tz_localize(None),
        freq="M",
    )
    if trades.empty:
        monthly = pd.DataFrame({"month": months.astype(str), "net_bps": 0.0, "trades": 0})
    else:
        periods = trades["entry_time"].dt.tz_localize(None).dt.to_period("M")
        grouped = (
            trades.assign(month=periods)
            .groupby("month")
            .agg(net_bps=(value_column, "sum"), trades=(value_column, "size"))
        )
        grouped = grouped.reindex(months, fill_value=0)
        monthly = grouped.reset_index().rename(columns={"index": "month"})
        monthly["month"] = monthly["month"].astype(str)
    monthly["year"] = monthly["month"].str[:4].astype(int)
    annual = monthly.groupby("year", as_index=False).agg(
        net_bps=("net_bps", "sum"), trades=("trades", "sum")
    )
    return monthly, annual


def bootstrap_months(month_values: np.ndarray, replicates: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    if len(month_values) == 0:
        return {"mean_monthly_bps": 0.0, "ci95": [0.0, 0.0]}
    samples = rng.choice(month_values, size=(replicates, len(month_values)), replace=True).mean(
        axis=1
    )
    return {
        "mean_monthly_bps": float(month_values.mean()),
        "ci95": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
    }
