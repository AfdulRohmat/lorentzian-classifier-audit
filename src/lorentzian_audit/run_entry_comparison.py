"""Frozen, retrospective signal-policy ablation with the unchanged v3 runner."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .data import aggregate_timeframe, load_asset_minutes
from .run import _json_default
from .run_v3 import ROOT, _describe, _sha256
from .runner import build_runner_trades, simulate_account
from .signals import build_full_history_variants, feature_kernel_outputs


def paired_blocks(left, right, *, block=3, replicates=10000, seed=20260926, family=3):
    """Bootstrap paired calendar differences, preserving contiguous circular blocks."""
    left, right = np.asarray(left, float), np.asarray(right, float)
    if left.shape != right.shape or left.ndim != 1 or not len(left):
        raise ValueError("Expected equal, nonempty one-dimensional monthly arrays")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("Nonfinite monthly observations")
    if block < 1 or replicates < 1 or family < 1:
        raise ValueError("Positive bootstrap settings required")
    n = len(left)
    starts = np.random.default_rng(seed).integers(0, n, (replicates, (n + block - 1) // block))
    indices = ((starts[:, :, None] + np.arange(block)) % n).reshape(replicates, -1)[:, :n]
    samples = (left - right)[indices].mean(axis=1)
    alpha = 0.05 / family
    return {
        "mean_monthly_difference_r": float((left - right).mean()),
        "ci95": np.quantile(samples, [0.025, 0.975]).tolist(),
        "family_adjusted_ci": np.quantile(samples, [alpha / 2, 1 - alpha / 2]).tolist(),
        "months": n,
    }


def main():
    contract_path = ROOT / "config/contract_runner_entry_comparison.json"
    contract = json.loads(contract_path.read_text())
    v3_path = ROOT / "config/contract_v3_atr_runner_sizing.json"
    v2_path = ROOT / "config/contract_v2_lower_timeframes.json"
    assert _sha256(v3_path) == contract["parent_v3_sha256"]
    assert _sha256(v2_path) == contract["parent_v2_sha256"]
    v3, v2 = json.loads(v3_path.read_text()), json.loads(v2_path.read_text())
    out = ROOT / "evidence/runner_entry_comparison"
    out.mkdir(exist_ok=True, parents=True)
    previous_manifest = json.loads(
        (ROOT / "evidence/v3_atr_runner_sizing/source_manifest.json").read_text()
    )
    previous = pd.read_csv(
        ROOT / "evidence/v3_atr_runner_sizing/trades.csv.gz",
        parse_dates=["signal_time", "entry_time", "exit_time"],
    )
    start = pd.Timestamp(v3["data"]["evaluation_start"])
    end = pd.Timestamp(v3["data"]["evaluation_end_exclusive"])
    weeks = (end - start).total_seconds() / (7 * 86400)
    months = pd.period_range(start.tz_localize(None), end.tz_localize(None), freq="M")[:-1]
    trade_frames, monthly_rows, annual_rows, account_frames = [], [], [], []
    cells, accounts, manifest, checks, signal_diagnostics = [], [], {}, {}, {}
    for asset, spec in v3["data"]["assets"].items():
        print(f"Loading {asset}", flush=True)
        minutes, diag = load_asset_minutes(ROOT, asset, spec, v3["data"])
        manifest[asset] = diag
        hashes = lambda d: {f["name"]: f["sha256"] for f in d["files"]}  # noqa: E731
        assert hashes(diag) == hashes(previous_manifest[asset]), "Source data changed"
        checks[f"{asset}_source_parity"] = True
        bars = aggregate_timeframe(minutes, contract["timeframe"], 1)
        features = feature_kernel_outputs(bars, spec["price_scale"])
        variants, diagnostics = build_full_history_variants(bars, features)
        signal_diagnostics[asset] = diagnostics
        for variant in contract["variants"][:2]:
            assert diagnostics[variant]["maximum_selected_label_maturity_minus_decision"] <= 0
        for cost in contract["cost_profiles"]:
            for variant in contract["variants"]:
                print(f"Replay {asset} {cost} {variant}", flush=True)
                trades = build_runner_trades(
                    asset=asset,
                    timeframe=contract["timeframe"],
                    bars=bars,
                    minutes=minutes,
                    signals=variants[variant],
                    asset_config=spec,
                    profile=v2["costs"][asset][cost],
                    exit_config=v3["exit"],
                    evaluation_start=start,
                    evaluation_end=end,
                )
                assert len(trades) and np.isfinite(trades.net_r).all()
                assert (trades.entry_time > trades.signal_time).all()
                assert (trades.exit_time >= trades.entry_time).all()
                assert (
                    trades.entry_time.iloc[1:].reset_index(drop=True)
                    >= trades.exit_time.iloc[:-1].reset_index(drop=True)
                ).all()
                np.testing.assert_allclose(
                    trades.net_r, trades.net_price / trades.planned_risk_price
                )
                np.testing.assert_allclose(
                    trades.net_per_lot_usd, trades.net_price * spec["contract_size"]
                )
                if cost == "base" and variant == "causal_lorentzian":
                    old = previous.loc[
                        previous.asset.eq(asset) & previous.timeframe.eq("30min")
                    ].reset_index(drop=True)
                    pd.testing.assert_frame_equal(
                        trades[old.columns].reset_index(drop=True),
                        old,
                        check_dtype=False,
                        check_exact=False,
                        rtol=1e-10,
                        atol=1e-10,
                    )
                    checks[f"{asset}_v3_ledger_parity"] = True
                tags = {"asset": asset, "cost": cost, "variant": variant}
                values = trades.net_r.to_numpy(float)
                stats = _describe(values, weeks)
                stats.update(
                    {
                        "total_holding_hours": float(trades.holding_hours.sum()),
                        "mean_holding_hours": float(trades.holding_hours.mean()),
                        "tail_above_3r_count": int((values > 3).sum()),
                        "tail_above_3r_sum": float(values[values > 3].sum()),
                        "long_r": float(trades.loc[trades.direction.eq(1), "net_r"].sum()),
                        "short_r": float(trades.loc[trades.direction.eq(-1), "net_r"].sum()),
                    }
                )
                cells.append(tags | stats)
                periods = trades.exit_time.dt.tz_localize(None).dt.to_period("M")
                grouped = trades.assign(month=periods).groupby("month").net_r.sum()
                monthly = grouped.reindex(months, fill_value=0.0)
                assert np.isclose(monthly.sum(), values.sum()), "Exit outside calendar"
                monthly_rows.extend(
                    tags | {"month": str(m), "net_r": float(r)} for m, r in monthly.items()
                )
                for year, rows in trades.groupby(trades.exit_time.dt.year):
                    annual_rows.append(
                        tags
                        | {
                            "year": int(year),
                            "trades": len(rows),
                            "net_r": float(rows.net_r.sum()),
                        }
                    )
                ledger, account = simulate_account(
                    trades,
                    spec,
                    contract["account"]["initial_balance_usd"],
                    contract["account"]["risk_percent"],
                    start,
                    end,
                )
                assert np.isclose(ledger.pnl_usd.sum(), account["final_balance_usd"] - 3000)
                accounts.append(tags | account)
                trade_frames.append(trades.assign(cost=cost, variant=variant))
                account_frames.append(ledger.assign(**tags))
    monthly_frame = pd.DataFrame(monthly_rows)
    comparisons = []
    settings = contract["bootstrap"]
    for asset in v3["data"]["assets"]:
        wide = (
            monthly_frame.loc[monthly_frame.asset.eq(asset) & monthly_frame.cost.eq("base")]
            .pivot(index="month", columns="variant", values="net_r")
            .sort_index()
        )
        for control in contract["variants"][1:]:
            result = paired_blocks(
                wide.causal_lorentzian,
                wide[control],
                block=settings["circular_block_months"],
                replicates=settings["replicates"],
                seed=settings["seed"],
                family=settings["primary_comparisons"],
            )
            comparisons.append({"asset": asset, "control": control, **result})
    primary = {r["variant"]: r for r in cells if r["asset"] == "sp500" and r["cost"] == "base"}
    lor = primary["causal_lorentzian"]
    beats_controls = all(
        lor["total_r"] > primary[c]["total_r"]
        and lor["profit_factor"] > primary[c]["profit_factor"]
        for c in contract["variants"][1:]
    )
    significant = all(
        r["family_adjusted_ci"][0] > 0 for r in comparisons if r["asset"] == "sp500"
    )
    result = {
        "contract_sha256": _sha256(contract_path),
        "cells": cells,
        "accounts": accounts,
        "paired_monthly_comparisons": comparisons,
        "historical_point_estimates_beat_all_controls": beats_controls,
        "all_primary_adjusted_intervals_positive": significant,
        "verdict": (
            "HISTORICAL_INCREMENTAL_SUPPORT_NOT_UNSEEN"
            if beats_controls and significant
            else "LORENTZIAN_INCREMENTAL_VALUE_UNCONFIRMED"
        ),
        "limitations": contract["limitations"],
    }
    pd.concat(trade_frames, ignore_index=True).to_csv(out / "trades.csv.gz", index=False)
    pd.concat(account_frames, ignore_index=True).to_csv(out / "accounts.csv.gz", index=False)
    monthly_frame.to_csv(out / "monthly.csv", index=False)
    pd.DataFrame(annual_rows).to_csv(out / "annual.csv", index=False)
    pd.DataFrame(cells).to_csv(out / "metrics.csv", index=False)
    pd.DataFrame(accounts).to_csv(out / "account_summary.csv", index=False)
    checks.update(
        {
            "cell_count_16": len(cells) == 16,
            "all_calendars_32_months": len(monthly_frame) == 16 * 32,
            "trade_invariants_and_account_reconciliation": True,
            "causal_label_maturity": True,
        }
    )
    assert all(checks.values())
    for name, content in [
        ("summary", result),
        ("source_manifest", manifest),
        ("signal_diagnostics", signal_diagnostics),
        ("validation", checks),
    ]:
        (out / f"{name}.json").write_text(
            json.dumps(content, indent=2, default=_json_default) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2, default=_json_default), flush=True)


if __name__ == "__main__":
    main()
