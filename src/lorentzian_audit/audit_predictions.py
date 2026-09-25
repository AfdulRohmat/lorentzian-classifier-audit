"""Audit the frozen model's exact four-observed-bar target separately from PnL."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .data import aggregate_timeframe, load_asset_minutes
from .run import _json_default
from .run_v3 import ROOT, _sha256
from .signals import build_full_history_variants, feature_kernel_outputs
from .trend_diagnosis import daily_trend, map_regime


def targets(bars):
    future = bars.close.shift(-4)
    return pd.DataFrame(
        {
            "decision_time": bars.bar_end,
            "label_time": bars.bar_end.shift(-4),
            "signal_close": bars.close,
            "target_close": future,
            "target_spread_points": bars.spread_close_points.shift(-4),
            "truth": np.sign(future - bars.close),
            "elapsed_minutes": (bars.bar_end.shift(-4) - bars.bar_end).dt.total_seconds() / 60,
            "momentum4": np.sign(bars.close - bars.close.shift(4)),
        },
        index=bars.index,
    )


def past_majority(truth, window=2000, minimum=200):
    return np.sign(truth.shift(4).rolling(window, min_periods=minimum).mean())


def block_ratio_interval(monthly, *, replicates=10000, seed=20260928, family=1):
    """Paired numerator/count sufficient statistics; preserves calendar pairing."""
    values = np.asarray(monthly, float)
    if values.ndim != 2 or values.shape[1] != 2 or len(values) == 0:
        raise ValueError("Expected months by numerator/count")
    if not np.isfinite(values).all() or (values[:, 1] < 0).any():
        raise ValueError("Invalid counts")
    if values[:, 1].sum() == 0:
        return {"estimate": None, "ci95": None, "adjusted_ci": None}
    n = len(values)
    starts = np.random.default_rng(seed).integers(0, n, (replicates, (n + 2) // 3))
    indices = ((starts[:, :, None] + np.arange(3)) % n).reshape(replicates, -1)[:, :n]
    sums = values[indices].sum(axis=1)
    samples = sums[sums[:, 1] > 0, 0] / sums[sums[:, 1] > 0, 1]
    tail = 0.05 / family / 2
    return {
        "estimate": float(values[:, 0].sum() / values[:, 1].sum()),
        "ci95": np.quantile(samples, [0.025, 0.975]).tolist(),
        "adjusted_ci": np.quantile(samples, [tail, 1 - tail]).tolist(),
    }


def calendar_counts(rows, numerator, months):
    frame = pd.DataFrame(
        {
            "month": rows.decision_time.dt.strftime("%Y-%m"),
            "numerator": np.asarray(numerator, float),
            "count": 1,
        }
    )
    return frame.groupby("month")[["numerator", "count"]].sum().reindex(months, fill_value=0)


def describe(rows, side):
    return {
        "rows": len(rows),
        "correct": int(rows.truth.eq(side).sum()),
        "precision": float(rows.truth.eq(side).mean()) if len(rows) else None,
        "flat_targets": int(rows.truth.eq(0).sum()),
        "median_label_minutes": float(rows.elapsed_minutes.median()) if len(rows) else None,
        "labels_over_120_minutes": int(rows.elapsed_minutes.gt(120).sum()),
    }


def main():
    config_path = ROOT / "config/contract_prediction_audit.json"
    config = json.loads(config_path.read_text())
    parent_path = ROOT / "config/contract_v3_atr_runner_sizing.json"
    assert _sha256(parent_path) == config["parent_v3_sha256"]
    parent = json.loads(parent_path.read_text())
    out = ROOT / "evidence/prediction_audit"
    out.mkdir(parents=True, exist_ok=True)
    ledger_path = ROOT / "evidence/v3_atr_runner_sizing/trades.csv.gz"
    old = pd.read_csv(ledger_path, parse_dates=["signal_time", "entry_time", "exit_time"])
    old = old.loc[old.timeframe.eq("30min")].copy()
    source_old = json.loads(
        (ROOT / "evidence/v3_atr_runner_sizing/source_manifest.json").read_text()
    )
    start, end = (
        pd.Timestamp(parent["data"][k])
        for k in ("evaluation_start", "evaluation_end_exclusive")
    )
    months = pd.period_range("2024-01", "2026-08", freq="M").astype(str)
    observations, joined, cohorts, splits, votes, confusion, comparisons, sources = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        {},
    )
    universes, cells = [], []
    for asset in ("xauusd", "sp500"):
        print(f"Regenerating {asset} predictions", flush=True)
        spec, profile = parent["data"]["assets"][asset], parent["costs"][asset]
        minutes, sources[asset] = load_asset_minutes(ROOT, asset, spec, parent["data"])
        assert {f["name"]: f["sha256"] for f in sources[asset]["files"]} == {
            f["name"]: f["sha256"] for f in source_old[asset]["files"]
        }
        bars = aggregate_timeframe(minutes, "30min")
        variants, diagnostics = build_full_history_variants(
            bars, feature_kernel_outputs(bars, spec["price_scale"])
        )
        assert (
            diagnostics["causal_lorentzian"]["maximum_selected_label_maturity_minus_decision"]
            <= 0
        )
        signals = variants["causal_lorentzian"]
        frame = targets(bars)
        frame["matured_rolling_prior"] = past_majority(frame.truth)
        frame["always_long"] = 1
        frame["vote"] = signals.prediction
        frame["forecast"] = np.sign(frame.vote).astype(int)
        frame["start_long"] = signals.start_long
        frame["start_short"] = signals.start_short
        frame["regime"] = map_regime(bars, daily_trend(minutes)).regime
        frame["asset"] = asset
        frame["scoreable"] = frame.truth.notna() & frame.label_time.le(end)
        frame.index.name = "signal_time"
        evaluation = frame.loc[
            frame.decision_time.ge(start) & frame.decision_time.lt(end)
        ].copy()
        scored = evaluation.loc[evaluation.scoreable]
        observations.append(evaluation.reset_index())
        directional = scored.loc[scored.forecast.ne(0) & scored.truth.ne(0)]
        universes.append(
            {
                "asset": asset,
                "evaluation_rows": len(evaluation),
                "scoreable": len(scored),
                "censored": len(evaluation) - len(scored),
                "abstentions": int(scored.forecast.eq(0).sum()),
                "down_prevalence": float(scored.truth.eq(-1).mean()),
                "up_prevalence": float(scored.truth.eq(1).mean()),
                "directional_covered_accuracy": float(
                    directional.forecast.eq(directional.truth).mean()
                ),
            }
        )
        for (forecast, truth), group in scored.groupby(["forecast", "truth"]):
            confusion.append(
                {
                    "asset": asset,
                    "forecast": int(forecast),
                    "truth": int(truth),
                    "rows": len(group),
                }
            )
        trades = old.loc[old.asset.eq(asset)].copy()
        original_columns = list(trades.columns)
        trades = trades.merge(
            frame.drop(columns="asset").reset_index(),
            on="signal_time",
            how="left",
            validate="one_to_one",
        )
        assert len(trades) == len(old.loc[old.asset.eq(asset)])
        assert trades.forecast.eq(trades.direction).all()
        assert trades.loc[trades.direction.eq(1), "start_long"].all()
        assert trades.loc[trades.direction.eq(-1), "start_short"].all()
        pd.testing.assert_frame_equal(
            trades[original_columns].reset_index(drop=True),
            old.loc[old.asset.eq(asset)].reset_index(drop=True),
        )
        spread = np.maximum(
            trades.target_spread_points * spec["point"] * profile["spread_multiplier"],
            profile["spread_floor"],
        )
        liquidation = trades.target_close + np.where(trades.direction.eq(-1), spread, 0)
        trades["target_close_mark_r"] = (
            trades.direction * (liquidation - trades.entry_fill)
            - profile["slippage_side"]
            - profile["commission_round_trip_price"]
        ) / trades.planned_risk_price
        trades["correct_label"] = trades.truth.eq(trades.direction) & trades.scoreable
        trades["pnl_win"] = trades.net_r.gt(0)
        trades["exit_before_label_maturity"] = trades.exit_time.lt(trades.label_time)
        trades["outcome"] = np.where(trades.correct_label, "correct_", "wrong_")
        trades["outcome"] += np.where(trades.pnl_win, "win", "nonwin")
        trades.loc[trades.truth.eq(0), "outcome"] = "flat_target"
        trades.loc[~trades.scoreable, "outcome"] = "unavailable_target"
        trades.loc[~trades.scoreable, "target_close_mark_r"] = np.nan
        joined.append(trades)
        for side, label in ((-1, "short"), (1, "long")):
            executed_all = trades.loc[trades.direction.eq(side)]
            scopes = {
                "raw": scored.loc[scored.forecast.eq(side)],
                "qualified_start": scored.loc[scored[f"start_{label}"]],
                "executed": executed_all.loc[executed_all.scoreable],
            }
            for scope, rows in scopes.items():
                tags = {"asset": asset, "side": label, "scope": scope}
                stats = describe(rows, side)
                interval = block_ratio_interval(
                    calendar_counts(rows, rows.truth.eq(side), months)
                )
                cohorts.append(tags | stats | {"precision_ci95": interval["ci95"]})
                for year, block in rows.groupby(rows.decision_time.dt.year):
                    splits.append(
                        tags | {"split": "year", "value": str(year)} | describe(block, side)
                    )
                for regime, block in rows.groupby("regime"):
                    splits.append(
                        tags | {"split": "regime", "value": regime} | describe(block, side)
                    )
                for vote, block in rows.groupby("vote"):
                    votes.append(tags | {"vote": int(vote)} | describe(block, side))
            for outcome, group in executed_all.groupby("outcome"):
                cells.append(
                    {
                        "asset": asset,
                        "side": label,
                        "outcome": outcome,
                        "trades": len(group),
                        "total_r": float(group.net_r.sum()),
                        "mean_r": float(group.net_r.mean()),
                        "initial_stops": int(group.exit_reason.str.startswith("STOP_").sum()),
                        "initial_stops_before_label": int(
                            (
                                group.exit_reason.str.startswith("STOP_")
                                & group.exit_before_label_maturity
                            ).sum()
                        ),
                        "exits_before_label": int(group.exit_before_label_maturity.sum()),
                        "nonpositive_target_mark": int(group.target_close_mark_r.le(0).sum()),
                    }
                )
        # Pairwise comparison on identical raw-short, nonflat, non-abstaining rows.
        shorts = scored.loc[scored.forecast.eq(-1) & scored.truth.ne(0)]
        for baseline in config["baselines"]:
            rows = shorts.loc[shorts[baseline].notna() & shorts[baseline].ne(0)]
            hit = rows.truth.eq(-1).astype(int)
            base_hit = rows[baseline].eq(rows.truth).astype(int)
            interval = block_ratio_interval(
                calendar_counts(rows, hit - base_hit, months), family=3
            )
            comparisons.append(
                {
                    "asset": asset,
                    "baseline": baseline,
                    "rows": len(rows),
                    "baseline_abstentions": len(shorts) - len(rows),
                    "model_accuracy": float(hit.mean()),
                    "baseline_accuracy": float(base_hit.mean()),
                    **interval,
                }
            )
    frames = {
        "observations.csv.gz": pd.concat(observations, ignore_index=True),
        "trade_labels.csv.gz": pd.concat(joined, ignore_index=True),
        "cohort_metrics.csv": pd.DataFrame(cohorts),
        "splits.csv": pd.DataFrame(splits),
        "vote_strength.csv": pd.DataFrame(votes),
        "confusion.csv": pd.DataFrame(confusion),
        "pnl_quadrants.csv": pd.DataFrame(cells),
        "universe.csv": pd.DataFrame(universes),
    }
    for name, data in frames.items():
        data.to_csv(out / name, index=False)
    assert sum(c["trades"] for c in cells) == len(old)
    summary = {
        "contract_sha256": _sha256(config_path),
        "parent_ledger_sha256": _sha256(ledger_path),
        "universe": universes,
        "cohorts": cohorts,
        "paired_raw_short_accuracy": comparisons,
        "pnl_quadrants": cells,
        "verdict": "DIRECT_PREDICTION_DIAGNOSTIC_NO_MODEL_CHANGE",
    }
    for name, data in [("summary", summary), ("source_manifest", sources)]:
        (out / f"{name}.json").write_text(
            json.dumps(data, indent=2, default=_json_default) + "\n", encoding="utf-8"
        )
    print("Prediction audit complete; validate before interpreting.")


if __name__ == "__main__":
    main()
