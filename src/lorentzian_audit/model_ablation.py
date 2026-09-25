"""Precontracted rolling learner comparison; no strategy or feature tuning."""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from .audit_predictions import block_ratio_interval, calendar_counts, targets
from .data import aggregate_timeframe, load_asset_minutes
from .run import _json_default
from .run_entry_comparison import paired_blocks
from .run_v3 import ROOT, _describe, _sha256
from .runner import build_runner_trades, simulate_account
from .signals import (
    FEATURE_COLUMNS,
    build_full_history_variants,
    default_filter_mask,
    feature_kernel_outputs,
    start_events_from_predictions,
)

CLASSES = np.array([-1, 0, 1])
MODELS = ("lorentzian", "logistic", "prior")


def eligible(features, i, window=2000):
    indices = np.arange(max(0, i - window), max(0, i - 3))
    return indices[(indices % 4 != 0) & np.isfinite(features[indices]).all(axis=1)]


def neighbor_probabilities(features, close, window=2000, neighbors=8, batch=128):
    """Same candidate order/argpartition as the immutable batched baseline."""
    count = len(close)
    result = np.full((count, 3), np.nan)
    truth = np.zeros(count, dtype=int)
    truth[:-4] = np.sign(close[4:] - close[:-4]).astype(int)
    finite = np.isfinite(features).all(axis=1)
    for begin in range(0, count, batch):
        current = np.arange(begin, min(begin + batch, count), dtype=np.int32)
        candidate = current[:, None] - np.arange(4, window + 1, dtype=np.int32)
        safe = np.clip(candidate, 0, count - 1)
        valid = (candidate >= 0) & (safe % 4 != 0) & finite[safe] & finite[current, None]
        distances = np.log1p(np.abs(features[safe] - features[current, None])).sum(axis=2)
        distances[~valid] = np.inf
        positions = np.argpartition(distances, kth=neighbors - 1, axis=1)[:, :neighbors]
        selected = np.take_along_axis(safe, positions, axis=1)
        enough = valid.sum(axis=1) >= neighbors
        for column, value in enumerate(CLASSES):
            result[current[enough], column] = (truth[selected[enough]] == value).mean(axis=1)
    return result


def rolling_learners(features, close, settings, *, progress=False):
    count = len(close)
    labels = np.full(count, np.nan)
    labels[:-4] = np.sign(close[4:] - close[:-4])
    probability = {name: np.full((count, 3), np.nan) for name in ("logistic", "prior")}
    diagnostics = np.full((count, 4), -1, dtype=int)
    coefficients = np.full((count, features.shape[1] + 1), np.nan)
    with threadpool_limits(limits=1), warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        for i in range(count):
            if not np.isfinite(features[i]).all():
                continue
            indices = eligible(features, i, settings["window"])
            if len(indices) < settings["minimum"]:
                continue
            assert indices.max() + 4 <= i
            y = labels[indices].astype(int)
            prior = np.array([(y == side).mean() for side in CLASSES])
            probability["prior"][i] = prior
            classes = np.unique(y)
            iterations = 0
            if len(classes) == 1:
                probability["logistic"][i] = prior
            else:
                model = LogisticRegression(**settings["logistic"])
                model.fit(features[indices], y)
                p = np.zeros(3)
                p[np.searchsorted(CLASSES, model.classes_)] = model.predict_proba(
                    features[i : i + 1]
                )[0]
                probability["logistic"][i] = p
                iterations = int(model.n_iter_.max())
                # Diagnostic up-class coefficients; binary coefficient is for class +1.
                position = 0 if len(classes) == 2 else int(np.flatnonzero(classes == 1)[0])
                coefficients[i] = np.r_[model.intercept_[position], model.coef_[position]]
            diagnostics[i] = [
                len(indices),
                int(indices.max() + 4 - i),
                len(classes),
                iterations,
            ]
            if progress and i % 5000 == 0:
                print(f"  rolling fits {i}/{count}", flush=True)
    return probability, diagnostics, coefficients


def forecast(p):
    return np.nan_to_num(np.sign(p[:, 2] - p[:, 0])).astype(int)


def brier(p, truth):
    return np.square(p - (np.asarray(truth)[:, None] == CLASSES)).sum(axis=1)


def classification_metrics(rows, name):
    truth = rows.truth.to_numpy()
    pred = rows[f"{name}_forecast"].to_numpy()
    covered = pred != 0
    result = {
        "rows": len(rows),
        "coverage": float(covered.mean()),
        "accuracy_abstention_incorrect": float(((pred == truth) & covered).mean()),
        "covered_accuracy": float((pred[covered] == truth[covered]).mean())
        if covered.any()
        else None,
        "brier": float(rows[f"{name}_brier"].mean()),
        "flat_targets": int((truth == 0).sum()),
    }
    recalls = []
    for side, label in ((-1, "short"), (1, "long")):
        selection = pred == side
        actual = truth == side
        correct = selection & actual
        recall = float(correct.sum() / actual.sum()) if actual.any() else None
        result.update(
            {
                f"{label}_forecasts": int(selection.sum()),
                f"{label}_precision": float(correct.sum() / selection.sum())
                if selection.any()
                else None,
                f"{label}_recall": recall,
            }
        )
        if recall is not None:
            recalls.append(recall)
    result["balanced_accuracy_abstention_miss"] = float(np.mean(recalls)) if recalls else None
    return result


def comparisons_from_saved(observations, monthly, config):
    rows = []
    months = pd.period_range("2024-01", "2026-08", freq="M").astype(str)
    settings = config["bootstrap"]
    for asset in config["assets"]:
        frame = observations.loc[observations.asset.eq(asset) & observations.scoreable].copy()
        wide = (
            monthly.loc[monthly.asset.eq(asset) & monthly.cost.eq("base")]
            .pivot(index="month", columns="model", values="net_r")
            .reindex(months)
        )
        for control in ("prior", "lorentzian"):
            monthly_counts = calendar_counts(
                frame, frame[f"{control}_brier"] - frame.logistic_brier, months
            )
            prediction = block_ratio_interval(
                monthly_counts.to_numpy(),
                replicates=settings["replicates"],
                seed=settings["seed"],
                family=settings["family"],
            )
            pnl = paired_blocks(
                wide.logistic,
                wide[control],
                block=settings["circular_block_months"],
                replicates=settings["replicates"],
                seed=settings["seed"],
                family=settings["family"],
            )
            rows.append(
                {
                    "asset": asset,
                    "control": control,
                    "brier_improvement": prediction,
                    "monthly_r_improvement": pnl,
                }
            )
    return rows


def main():
    path = ROOT / "config/contract_model_ablation.json"
    config = json.loads(path.read_text())
    parent_path = ROOT / "config/contract_v3_atr_runner_sizing.json"
    assert _sha256(parent_path) == config["parent_v3_sha256"]
    parent = json.loads(parent_path.read_text())
    v2 = json.loads((ROOT / "config/contract_v2_lower_timeframes.json").read_text())
    out = ROOT / "evidence/model_ablation"
    out.mkdir(parents=True, exist_ok=True)
    original_path = ROOT / "evidence/v3_atr_runner_sizing/trades.csv.gz"
    old = pd.read_csv(original_path, parse_dates=["signal_time", "entry_time", "exit_time"])
    source_old = json.loads(
        (ROOT / "evidence/v3_atr_runner_sizing/source_manifest.json").read_text()
    )
    start, end = (
        pd.Timestamp(parent["data"][k])
        for k in ("evaluation_start", "evaluation_end_exclusive")
    )
    months = pd.period_range("2024-01", "2026-08", freq="M").astype(str)
    weeks = (end - start).total_seconds() / (7 * 86400)
    observations, trades_all, metrics, annual, monthly, accounts, account_ledgers = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    classifications, confusion, reliability, coefficients_all, matched, quadrants = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    sources, checks = {}, {}
    for asset in config["assets"]:
        print(f"Loading and reconstructing {asset}", flush=True)
        spec = parent["data"]["assets"][asset]
        minutes, sources[asset] = load_asset_minutes(ROOT, asset, spec, parent["data"])
        assert {f["name"]: f["sha256"] for f in sources[asset]["files"]} == {
            f["name"]: f["sha256"] for f in source_old[asset]["files"]
        }
        bars = aggregate_timeframe(minutes, "30min")
        features = feature_kernel_outputs(bars, spec["price_scale"])
        original_signals, _ = build_full_history_variants(bars, features)
        x, close = features[FEATURE_COLUMNS].to_numpy(float), bars.close.to_numpy(float)
        probabilities, diagnostics, coefficients = rolling_learners(
            x, close, config["training"], progress=True
        )
        probabilities["lorentzian"] = neighbor_probabilities(x, close)
        np.testing.assert_array_equal(
            forecast(probabilities["lorentzian"]),
            np.sign(original_signals["causal_lorentzian"].prediction).astype(int),
        )
        frame = targets(bars)
        frame["asset"] = asset
        frame["training_count"] = diagnostics[:, 0]
        frame["maturity_lag"] = diagnostics[:, 1]
        frame["fit_iterations"] = diagnostics[:, 3]
        frame["scoreable"] = (
            frame.truth.notna() & frame.label_time.le(end) & (diagnostics[:, 0] >= 200)
        )
        signals = {}
        for name in MODELS:
            p = probabilities[name]
            signals[name] = start_events_from_predictions(
                forecast(p), default_filter_mask(bars), features.kernel.to_numpy()
            )
            signals[name].index = bars.index
            frame[f"{name}_forecast"] = forecast(p)
            frame[f"{name}_start_short"] = signals[name].start_short
            frame[f"{name}_start_long"] = signals[name].start_long
            for column, label in enumerate(("down", "flat", "up")):
                frame[f"{name}_p_{label}"] = p[:, column]
            frame[f"{name}_brier"] = brier(p, frame.truth)
            frame.loc[~frame.scoreable, f"{name}_brier"] = np.nan
        frame.index.name = "signal_time"
        evaluation = frame.loc[
            frame.decision_time.ge(start) & frame.decision_time.lt(end)
        ].copy()
        observations.append(evaluation.reset_index())
        scored = evaluation.loc[evaluation.scoreable]
        assert scored.maturity_lag.le(0).all()
        for name in MODELS:
            p = scored[[f"{name}_p_{label}" for label in ("down", "flat", "up")]].to_numpy()
            np.testing.assert_allclose(p.sum(axis=1), 1, atol=1e-12)
            assert np.isfinite(p).all() and (p >= 0).all() and (p <= 1).all()
            for year in ("all", 2024, 2025, 2026):
                subset = (
                    scored
                    if year == "all"
                    else scored.loc[scored.decision_time.dt.year.eq(year)]
                )
                classifications.append(
                    {
                        "asset": asset,
                        "model": name,
                        "year": str(year),
                        **classification_metrics(subset, name),
                    }
                )
            for (pred, truth), group in scored.groupby([f"{name}_forecast", "truth"]):
                confusion.append(
                    {
                        "asset": asset,
                        "model": name,
                        "forecast": int(pred),
                        "truth": int(truth),
                        "rows": len(group),
                    }
                )
            for side, label in ((-1, "down"), (1, "up")):
                pp = scored[f"{name}_p_{label}"]
                bins = np.minimum((pp * 10).astype(int), 9)
                for bin_id in range(10):
                    subset = scored.loc[bins.eq(bin_id)]
                    if len(subset):
                        reliability.append(
                            {
                                "asset": asset,
                                "model": name,
                                "side": label,
                                "bin": bin_id,
                                "rows": len(subset),
                                "mean_probability": subset[f"{name}_p_{label}"].mean(),
                                "observed_frequency": subset.truth.eq(side).mean(),
                            }
                        )
            fixed_short = old.loc[
                old.asset.eq(asset) & old.timeframe.eq("30min") & old.direction.eq(-1),
                "signal_time",
            ]
            for cohort, subset in (
                ("original_negative_vote", scored.loc[scored.lorentzian_forecast.eq(-1)]),
                ("original_executed_short", scored.loc[scored.index.isin(fixed_short)]),
            ):
                matched.append(
                    {
                        "asset": asset,
                        "model": name,
                        "cohort": cohort,
                        **classification_metrics(subset, name),
                    }
                )
        coeff = pd.DataFrame(
            coefficients, index=bars.index, columns=["intercept", *FEATURE_COLUMNS]
        )
        coeff = (
            coeff.loc[evaluation.index]
            .groupby(evaluation.decision_time.dt.strftime("%Y-%m"))
            .head(1)
        )
        coefficients_all.append(coeff.reset_index().assign(asset=asset))
        for cost in config["cost_profiles"]:
            for name in MODELS:
                print(f"Replay {asset} {cost} {name}", flush=True)
                trades = build_runner_trades(
                    asset=asset,
                    timeframe="30min",
                    bars=bars,
                    minutes=minutes,
                    signals=signals[name],
                    asset_config=spec,
                    profile=v2["costs"][asset][cost],
                    exit_config=parent["exit"],
                    evaluation_start=start,
                    evaluation_end=end,
                )
                assert len(trades) and np.isfinite(trades.net_r).all()
                assert (trades.entry_time > trades.signal_time).all()
                assert (
                    trades.entry_time.iloc[1:].reset_index(drop=True)
                    >= trades.exit_time.iloc[:-1].reset_index(drop=True)
                ).all()
                if name == "lorentzian" and cost == "base":
                    frozen = old.loc[
                        old.asset.eq(asset) & old.timeframe.eq("30min")
                    ].reset_index(drop=True)
                    pd.testing.assert_frame_equal(
                        trades[frozen.columns].reset_index(drop=True),
                        frozen,
                        check_dtype=False,
                        check_exact=False,
                        rtol=1e-10,
                        atol=1e-10,
                    )
                tags = {"asset": asset, "cost": cost, "model": name}
                stats = _describe(trades.net_r.to_numpy(), weeks)
                stats.update(
                    {
                        "long_r": trades.loc[trades.direction.eq(1), "net_r"].sum(),
                        "short_r": trades.loc[trades.direction.eq(-1), "net_r"].sum(),
                        "trades_per_month": len(trades) / 32,
                        "mean_monthly_r": trades.net_r.sum() / 32,
                        "mean_holding_hours": trades.holding_hours.mean(),
                    }
                )
                metrics.append(tags | stats)
                for year, group in trades.groupby(trades.exit_time.dt.year):
                    annual.append(
                        tags | {"year": int(year), **_describe(group.net_r.to_numpy(), weeks)}
                    )
                month_group = (
                    trades.groupby(trades.exit_time.dt.strftime("%Y-%m"))
                    .net_r.sum()
                    .reindex(months, fill_value=0)
                )
                monthly.extend(
                    tags | {"month": month, "net_r": float(value)}
                    for month, value in month_group.items()
                )
                ledger, account = simulate_account(trades, spec, 3000, 1, start, end)
                assert np.isclose(ledger.pnl_usd.sum(), account["final_balance_usd"] - 3000)
                accounts.append(tags | account)
                account_ledgers.append(ledger.assign(**tags))
                joined = trades.merge(
                    frame[["truth", "scoreable", "label_time"]].reset_index(),
                    on="signal_time",
                    validate="one_to_one",
                )
                joined["label_result"] = np.where(
                    ~joined.scoreable,
                    "unknown",
                    np.where(
                        joined.truth.eq(0),
                        "flat",
                        np.where(joined.truth.eq(joined.direction), "correct", "wrong"),
                    ),
                )
                joined["pnl_win"] = joined.net_r.gt(0)
                for (side, label, win), group in joined.groupby(
                    ["direction", "label_result", "pnl_win"]
                ):
                    quadrants.append(
                        tags
                        | {
                            "direction": side,
                            "label_result": label,
                            "pnl_win": win,
                            "trades": len(group),
                            "net_r": group.net_r.sum(),
                        }
                    )
                trades_all.append(joined.assign(cost=cost, model=name))
        checks[asset] = {
            "source_hash_parity": True,
            "original_vote_parity": True,
            "original_trade_ledger_parity": True,
            "causal_training": True,
            "probabilities_valid": True,
            "nonconvergence": 0,
            "maximum_iterations": int(diagnostics[:, 3].max()),
            "scored": len(scored),
            "censored": int((~evaluation.scoreable).sum()),
        }
    obs, monthly_df = pd.concat(observations, ignore_index=True), pd.DataFrame(monthly)
    comparisons = comparisons_from_saved(obs, monthly_df, config)
    support = all(
        c["brier_improvement"]["adjusted_ci"][0] > 0
        and c["monthly_r_improvement"]["family_adjusted_ci"][0] > 0
        for c in comparisons
        if c["asset"] == "xauusd"
    )
    outputs = {
        "observations.csv.gz": obs,
        "trades.csv.gz": pd.concat(trades_all, ignore_index=True),
        "metrics.csv": pd.DataFrame(metrics),
        "annual.csv": pd.DataFrame(annual),
        "monthly.csv": monthly_df,
        "account_summary.csv": pd.DataFrame(accounts),
        "accounts.csv.gz": pd.concat(account_ledgers, ignore_index=True),
        "classification.csv": pd.DataFrame(classifications),
        "confusion.csv": pd.DataFrame(confusion),
        "reliability.csv": pd.DataFrame(reliability),
        "matched_cohorts.csv": pd.DataFrame(matched),
        "coefficients_monthly.csv": pd.concat(coefficients_all, ignore_index=True),
        "pnl_quadrants.csv": pd.DataFrame(quadrants),
    }
    for filename, data in outputs.items():
        data.to_csv(out / filename, index=False)
    summary = {
        "contract_sha256": _sha256(path),
        "sklearn_version": sklearn.__version__,
        "primary_comparisons": comparisons,
        "checks": checks,
        "verdict": "RETROSPECTIVE_INCREMENTAL_SUPPORT_ONLY"
        if support
        else "MODEL_REPLACEMENT_NOT_SUPPORTED",
        "untouched_holdout": False,
        "promotion": False,
    }
    for filename, data in (("summary.json", summary), ("source_manifest.json", sources)):
        (out / filename).write_text(
            json.dumps(data, indent=2, default=_json_default) + "\n", encoding="utf-8"
        )
    manifest = {
        "inputs": {
            str(p.relative_to(ROOT)): _sha256(p)
            for p in (
                path,
                parent_path,
                ROOT / "config/contract_v2_lower_timeframes.json",
                original_path,
                ROOT / "src/lorentzian_audit/model_ablation.py",
                ROOT / "src/lorentzian_audit/signals.py",
                ROOT / "src/lorentzian_audit/runner.py",
            )
        },
        "outputs": {
            p.name: _sha256(p)
            for p in out.iterdir()
            if p.name not in {"manifest.json", "validation.json"}
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
