"""Reconcile saved trend and matched-control evidence without raw archives."""

import json

import numpy as np
import pandas as pd

from .run_entry_comparison import paired_blocks
from .run_v3 import ROOT, _sha256
from .statistics import max_drawdown, profit_factor
from .trend_diagnosis import candidate_indices


def main():
    folder = ROOT / "evidence/trend_diagnosis"
    config_path = ROOT / "config/contract_trend_diagnosis.json"
    config = json.loads(config_path.read_text())
    v3 = json.loads((ROOT / "config/contract_v3_atr_runner_sizing.json").read_text())
    v2 = json.loads((ROOT / "config/contract_v2_lower_timeframes.json").read_text())
    summary = json.loads((folder / "summary.json").read_text())
    assert _sha256(config_path) == summary["contract_sha256"]
    trades = pd.read_csv(
        folder / "trades.csv.gz", parse_dates=["signal_time", "entry_time", "exit_time"]
    )
    accounts = pd.read_csv(folder / "accounts.csv.gz")
    monthly = pd.read_csv(folder / "monthly.csv")
    cells = pd.read_csv(folder / "regime_cells.csv")
    assert len(summary["metrics"]) == 16 and len(summary["controls"]) == 20
    assert all(summary["baseline_parity"].values())
    for row in summary["metrics"]:
        a, p, c = row["asset"], row["policy"], row["cost"]
        selected = trades.loc[
            trades.asset.eq(a) & trades.policy.eq(p) & trades.cost.eq(c)
        ].reset_index(drop=True)
        ledger = accounts.loc[
            accounts.asset.eq(a) & accounts.policy.eq(p) & accounts.cost.eq(c)
        ].reset_index(drop=True)
        cal = monthly.loc[monthly.asset.eq(a) & monthly.policy.eq(p) & monthly.cost.eq(c)]
        assert len(selected) == row["trades"] == len(ledger)
        assert (selected.entry_time >= selected.signal_time + pd.Timedelta(minutes=30)).all()
        assert (
            selected.entry_time.iloc[1:].to_numpy() >= selected.exit_time.iloc[:-1].to_numpy()
        ).all()
        profile = v2["costs"][a][c]
        expected = (
            selected.direction * (selected.exit_fill - selected.entry_fill)
            - profile["commission_round_trip_price"]
        )
        np.testing.assert_allclose(selected.net_price, expected, atol=1e-9)
        np.testing.assert_allclose(
            selected.net_r, expected / selected.planned_risk_price, atol=1e-9
        )
        assert np.isclose(selected.net_r.sum(), row["total_r"])
        assert np.isclose(profit_factor(selected.net_r.to_numpy()), row["profit_factor"])
        assert np.isclose(max_drawdown(selected.net_r.to_numpy()), row["max_drawdown_r"])
        assert len(cal) == 32 and np.isclose(cal.net_r.sum(), row["total_r"])
        grouped = selected.groupby(selected.exit_time.dt.strftime("%Y-%m")).net_r.sum()
        np.testing.assert_allclose(
            grouped.reindex(cal.month, fill_value=0), cal.net_r, atol=1e-9
        )
        slice_cells = cells.loc[cells.asset.eq(a) & cells.policy.eq(p) & cells.cost.eq(c)]
        assert slice_cells.trades.sum() == len(selected)
        assert np.isclose(slice_cells.total_r.sum(), row["total_r"])
        np.testing.assert_allclose(ledger.pnl_usd, ledger.volume * selected.net_per_lot_usd)
        np.testing.assert_allclose(ledger.equity_after, 3000 + ledger.pnl_usd.cumsum())
        np.testing.assert_allclose(ledger.risk_budget_usd, ledger.equity_before * 0.01)
        assert (
            ledger.volume * selected.planned_loss_per_lot <= ledger.risk_budget_usd + 1e-8
        ).all()
        positive = ledger.volume > 0
        assert (
            ledger.loc[positive, "volume"] >= v3["data"]["assets"][a]["volume_min"] - 1e-9
        ).all()
        if p == "long_only":
            assert selected.direction.eq(1).all()
        if p == "short_only":
            assert selected.direction.eq(-1).all()
        if p == "trend_aligned":
            assert (
                (selected.direction.eq(1) & selected.regime.eq("bull"))
                | (selected.direction.eq(-1) & selected.regime.eq("bear"))
            ).all()
    for a in ("sp500", "xauusd"):
        mapping = pd.read_csv(
            folder / f"{a}_signal_regime.csv.gz", parse_dates=["decision", "available_at"]
        )
        valid = mapping.available_at.notna()
        assert (mapping.loc[valid, "available_at"] <= mapping.loc[valid, "decision"]).all()
    draws = pd.read_csv(
        folder / "control_draws.csv.gz",
        parse_dates=["anchor_signal_time", "control_signal_time"],
    )
    pool = pd.read_csv(
        folder / "xauusd_matching_pool.csv.gz", index_col=0, parse_dates=[0, "entry_time"]
    )
    features = pd.read_csv(
        folder / "xauusd_matching_features.csv.gz", index_col=0, parse_dates=[0, "entry_time"]
    )
    anchors = trades.loc[
        trades.asset.eq("xauusd") & trades.policy.eq("long_only") & trades.cost.eq("base")
    ]
    anchors = anchors.set_index("trade_id")
    control_trades = pd.read_csv(
        folder / "control_trades.csv.gz", parse_dates=["signal_time", "entry_time", "exit_time"]
    )
    rng = np.random.default_rng(config["matched_controls"]["seed"])
    for schedule, group in draws.groupby("schedule", sort=True):
        used = set()
        for draw in group.itertuples(index=False):
            anchor = features.loc[draw.anchor_signal_time].copy()
            entry = anchors.loc[draw.anchor_trade_id, "entry_time"]
            anchor["month"] = entry.strftime("%Y-%m")
            anchor["ny_hour"] = entry.tz_convert("America/New_York").hour
            eligible = [stamp for stamp in candidate_indices(pool, anchor) if stamp not in used]
            assert len(eligible) == draw.eligible_count
            expected = eligible[int(rng.integers(len(eligible)))] if eligible else pd.NaT
            if eligible:
                assert expected == draw.control_signal_time
                used.add(expected)
            else:
                assert pd.isna(draw.control_signal_time)
        executed = control_trades.loc[control_trades.schedule.eq(schedule)]
        assert executed.signal_time.isin(used).all() and executed.direction.eq(1).all()
        assert (
            executed.entry_time.iloc[1:].to_numpy() >= executed.exit_time.iloc[:-1].to_numpy()
        ).all()
        metric = summary["controls"][int(schedule)]
        assert len(executed) == metric["trades"]
        assert np.isclose(executed.net_r.sum(), metric["total_r"])
        profile = v2["costs"]["xauusd"]["base"]
        expected = (
            executed.exit_fill - executed.entry_fill - profile["commission_round_trip_price"]
        )
        np.testing.assert_allclose(executed.net_price, expected, atol=1e-9)
        np.testing.assert_allclose(
            executed.net_r, expected / executed.planned_risk_price, atol=1e-9
        )
    for item in summary["paired_monthly_differences"]:
        wide = (
            monthly.loc[monthly.asset.eq(item["asset"]) & monthly.cost.eq("base")]
            .pivot(index="month", columns="policy", values="net_r")
            .sort_index()
        )
        replay = paired_blocks(
            wide[item["policy"]], wide.baseline, seed=config["statistics"]["seed"]
        )
        for key in replay:
            np.testing.assert_allclose(item[key], replay[key], atol=1e-9)
    result = {
        "passed": True,
        "policy_cells": 16,
        "control_schedules": 20,
        "checks": [
            "accounting",
            "calendar",
            "eligibility",
            "nonoverlap",
            "daily availability",
            "seeded outcome-blind match regeneration",
            "bootstrap reproduction",
        ],
    }
    (folder / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
