"""Causal regime attribution and frozen entry-policy replay, not a parameter search."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from lorentzian_classification.core import calc_atr

from .data import aggregate_timeframe, load_asset_minutes
from .run import _json_default
from .run_entry_comparison import paired_blocks
from .run_v3 import ROOT, _describe, _sha256
from .runner import build_runner_trades, simulate_account
from .signals import build_full_history_variants, feature_kernel_outputs


def daily_trend(minutes, span=200, slope_days=20):
    daily = aggregate_timeframe(minutes, "24h")
    ema = daily.close.ewm(span=span, adjust=False, min_periods=span).mean()
    slope = ema - ema.shift(slope_days)
    ready = slope.notna()
    regime = pd.Series("unavailable", index=daily.index)
    regime.loc[ready] = "mixed"
    regime.loc[ready & daily.close.gt(ema) & slope.gt(0)] = "bull"
    regime.loc[ready & daily.close.lt(ema) & slope.lt(0)] = "bear"
    return pd.DataFrame(
        {
            "available_at": daily.bar_end,
            "close": daily.close,
            "ema": ema,
            "slope": slope,
            "regime": regime,
        }
    )


def map_regime(bars, daily):
    query = pd.DataFrame({"decision": bars.bar_end, "signal_time": bars.index})
    mapped = pd.merge_asof(
        query,
        daily.reset_index(drop=True),
        left_on="decision",
        right_on="available_at",
        direction="backward",
    )
    mapped["regime"] = mapped.regime.fillna("unavailable")
    return mapped.set_index("signal_time")


def policy_mask(signals, regime, policy):
    if policy == "baseline":
        return pd.Series(True, index=signals.index)
    if policy == "long_only":
        return signals.start_long.copy()
    if policy == "short_only":
        return signals.start_short.copy()
    if policy != "trend_aligned":
        raise ValueError(policy)
    return (signals.start_long & regime.eq("bull")) | (signals.start_short & regime.eq("bear"))


def matching_candidates(bars, signals, mapped, minutes, start, end):
    atr = np.asarray(calc_atr(bars.high.tolist(), bars.low.tolist(), bars.close.tolist(), 14))
    frame = pd.DataFrame(index=bars.index)
    frame["entry_time"] = pd.Series(bars.index, index=bars.index).shift(-1)
    frame["relative_atr"] = atr / bars.close.to_numpy()
    frame["regime"] = mapped.regime
    frame["month"] = frame.entry_time.dt.strftime("%Y-%m")
    frame["ny_hour"] = frame.entry_time.dt.tz_convert("America/New_York").dt.hour
    eligible = (
        frame.entry_time.ge(start)
        & frame.entry_time.lt(end)
        & frame.entry_time.isin(minutes.index)
        & np.isfinite(frame.relative_atr)
        & frame.relative_atr.gt(0)
        & ~signals.start_long
        & ~signals.start_short
    )
    return frame, frame.loc[eligible].copy()


def candidate_indices(pool, anchor):
    return pool.index[
        (pool.month == anchor.month)
        & (pool.ny_hour == anchor.ny_hour)
        & (pool.regime == anchor.regime)
        & (pool.relative_atr / anchor.relative_atr).between(0.75, 1.25)
    ]


def main():
    config_path = ROOT / "config/contract_trend_diagnosis.json"
    config = json.loads(config_path.read_text())
    parent = ROOT / "config/contract_v3_atr_runner_sizing.json"
    assert _sha256(parent) == config["parent_v3_sha256"]
    v3 = json.loads(parent.read_text())
    v2 = json.loads((ROOT / "config/contract_v2_lower_timeframes.json").read_text())
    old_sources = json.loads(
        (ROOT / "evidence/v3_atr_runner_sizing/source_manifest.json").read_text()
    )
    dates = ["signal_time", "entry_time", "exit_time"]
    old = pd.read_csv(ROOT / "evidence/v3_atr_runner_sizing/trades.csv.gz", parse_dates=dates)
    start, end = (
        pd.Timestamp(v3["data"][k]) for k in ("evaluation_start", "evaluation_end_exclusive")
    )
    weeks = (end - start).total_seconds() / 604800
    months = pd.period_range(start.tz_localize(None), end.tz_localize(None), freq="M")[:-1]
    out = ROOT / "evidence/trend_diagnosis"
    out.mkdir(parents=True, exist_ok=True)
    all_trades, account_ledgers, metrics, accounts, monthly, annual, cells = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    coverage, draws, controls, control_trades, sources = [], [], [], [], {}
    parity = {}
    for asset in ("xauusd", "sp500"):
        print(f"Loading/features {asset}", flush=True)
        spec = v3["data"]["assets"][asset]
        minutes, sources[asset] = load_asset_minutes(ROOT, asset, spec, v3["data"])
        assert {f["name"]: f["sha256"] for f in sources[asset]["files"]} == {
            f["name"]: f["sha256"] for f in old_sources[asset]["files"]
        }
        bars = aggregate_timeframe(minutes, "30min")
        features = feature_kernel_outputs(bars, spec["price_scale"])
        variants, diag = build_full_history_variants(bars, features)
        assert diag["causal_lorentzian"]["maximum_selected_label_maturity_minus_decision"] <= 0
        signals = variants["causal_lorentzian"]
        daily = daily_trend(minutes)
        mapped = map_regime(bars, daily)
        assert (
            mapped.available_at.dropna() <= mapped.loc[mapped.available_at.notna(), "decision"]
        ).all()
        daily.to_csv(out / f"{asset}_daily_trend.csv", index=False)
        mapped.to_csv(out / f"{asset}_signal_regime.csv.gz")
        active = mapped.loc[mapped.decision.ge(start) & mapped.decision.lt(end)]
        for (year, regime), group in active.groupby([active.decision.dt.year, "regime"]):
            coverage.append(
                {
                    "asset": asset,
                    "year": int(year),
                    "regime": regime,
                    "m30_decisions": len(group),
                }
            )

        def replay(
            signal_frame, mask, cost="base", asset=asset, bars=bars, minutes=minutes, spec=spec
        ):
            return build_runner_trades(
                asset=asset,
                timeframe="30min",
                bars=bars,
                minutes=minutes,
                signals=signal_frame,
                asset_config=spec,
                profile=v2["costs"][asset][cost],
                exit_config=v3["exit"],
                evaluation_start=start,
                evaluation_end=end,
                entry_mask=mask,
            )

        base_long = None
        for cost in ("base", "stress"):
            for policy in config["policies"]:
                print(f"Replay {asset} {cost} {policy}", flush=True)
                trades = replay(signals, policy_mask(signals, mapped.regime, policy), cost)
                if trades.empty:
                    raise ValueError(
                        f"Empty policy must be reported explicitly: {asset} {policy}"
                    )
                if policy == "baseline" and cost == "base":
                    prior = old.loc[
                        old.asset.eq(asset) & old.timeframe.eq("30min")
                    ].reset_index(drop=True)
                    pd.testing.assert_frame_equal(
                        trades[prior.columns],
                        prior,
                        check_dtype=False,
                        check_exact=False,
                        rtol=1e-10,
                        atol=1e-10,
                    )
                    parity[asset] = True
                trades["regime"] = mapped.regime.reindex(
                    pd.DatetimeIndex(trades.signal_time)
                ).to_numpy()
                tags = {"asset": asset, "policy": policy, "cost": cost}
                all_trades.append(trades.assign(policy=policy, cost=cost))
                values = trades.net_r.to_numpy(float)
                metrics.append(
                    tags
                    | _describe(values, weeks)
                    | {"holding_hours": float(trades.holding_hours.sum())}
                )
                for (year, direction, regime), group in trades.groupby(
                    [trades.entry_time.dt.year, "direction", "regime"]
                ):
                    cells.append(
                        tags
                        | {"year": int(year), "direction": int(direction), "regime": regime}
                        | _describe(group.net_r.to_numpy(float), weeks)
                    )
                for year, group in trades.groupby(trades.entry_time.dt.year):
                    annual.append(
                        tags
                        | {
                            "year": int(year),
                            "trades": len(group),
                            "total_r": float(group.net_r.sum()),
                        }
                    )
                by_month = (
                    trades.groupby(trades.exit_time.dt.tz_localize(None).dt.to_period("M"))
                    .net_r.sum()
                    .reindex(months, fill_value=0)
                )
                assert np.isclose(by_month.sum(), values.sum())
                monthly.extend(
                    tags | {"month": str(m), "net_r": float(r)} for m, r in by_month.items()
                )
                ledger, account = simulate_account(trades, spec, 3000, 1, start, end)
                accounts.append(tags | account)
                account_ledgers.append(ledger.assign(**tags))
                if policy == "long_only" and cost == "base":
                    base_long = trades
        # Classifier short events remain the COMMON exit policy in matched schedules.
        if asset == "xauusd":
            frame, pool = matching_candidates(bars, signals, mapped, minutes, start, end)
            anchor_data = frame.reindex(pd.DatetimeIndex(base_long.signal_time)).copy()
            # Use actual baseline entry clock, including gaps, when matching anchors.
            anchor_data["entry_time"] = base_long.entry_time.to_numpy()
            anchor_data["month"] = pd.to_datetime(anchor_data.entry_time).dt.strftime("%Y-%m")
            anchor_data["ny_hour"] = (
                pd.to_datetime(anchor_data.entry_time).dt.tz_convert("America/New_York").dt.hour
            )
            candidates = [candidate_indices(pool, row) for row in anchor_data.itertuples()]
            rng = np.random.default_rng(config["matched_controls"]["seed"])
            for schedule in range(config["matched_controls"]["schedules"]):
                control = signals.copy()
                control["start_long"] = False
                used = set()
                for j, eligible in enumerate(candidates):
                    available = [stamp for stamp in eligible if stamp not in used]
                    chosen = (
                        available[int(rng.integers(len(available)))] if available else pd.NaT
                    )
                    draws.append(
                        {
                            "schedule": schedule,
                            "anchor_trade_id": int(base_long.trade_id.iloc[j]),
                            "anchor_signal_time": base_long.signal_time.iloc[j],
                            "control_signal_time": chosen,
                            "eligible_count": len(available),
                        }
                    )
                    if available:
                        used.add(chosen)
                        control.loc[chosen, "start_long"] = True
                print(f"Matched gold-long schedule {schedule + 1}/20", flush=True)
                result = replay(control, control.start_long)
                assert result.direction.eq(1).all()
                controls.append(
                    {
                        "schedule": schedule,
                        "matched_entry_events": len(used),
                        "anchor_trades": len(base_long),
                    }
                    | _describe(result.net_r.to_numpy(float), weeks)
                    | {"holding_hours": float(result.holding_hours.sum())}
                )
                control_trades.append(result.assign(schedule=schedule))
            frame.to_csv(out / "xauusd_matching_features.csv.gz")
            pool.to_csv(out / "xauusd_matching_pool.csv.gz")
    month_df = pd.DataFrame(monthly)
    comparisons = []
    for asset in ("xauusd", "sp500"):
        wide = (
            month_df.loc[month_df.asset.eq(asset) & month_df.cost.eq("base")]
            .pivot(index="month", columns="policy", values="net_r")
            .sort_index()
        )
        for policy in config["policies"][1:]:
            comparisons.append(
                {"asset": asset, "policy": policy}
                | paired_blocks(wide[policy], wide.baseline, seed=config["statistics"]["seed"])
            )
    files = {
        "trades.csv.gz": pd.concat(all_trades),
        "accounts.csv.gz": pd.concat(account_ledgers),
        "metrics.csv": pd.DataFrame(metrics),
        "account_summary.csv": pd.DataFrame(accounts),
        "monthly.csv": month_df,
        "annual.csv": pd.DataFrame(annual),
        "regime_cells.csv": pd.DataFrame(cells),
        "regime_coverage.csv": pd.DataFrame(coverage),
        "control_draws.csv.gz": pd.DataFrame(draws),
        "control_metrics.csv": pd.DataFrame(controls),
        "control_trades.csv.gz": pd.concat(control_trades),
    }
    for name, frame in files.items():
        frame.to_csv(out / name, index=False)
    summary = {
        "contract_sha256": _sha256(config_path),
        "metrics": metrics,
        "accounts": accounts,
        "paired_monthly_differences": comparisons,
        "controls": controls,
        "baseline_parity": parity,
        "verdict": "RETROSPECTIVE_TREND_DIAGNOSIS_NO_PROMOTION",
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=_json_default) + "\n"
    )
    (out / "source_manifest.json").write_text(json.dumps(sources, indent=2) + "\n")
    print("All replays finished; validate artifacts before interpretation.", flush=True)


if __name__ == "__main__":
    main()
