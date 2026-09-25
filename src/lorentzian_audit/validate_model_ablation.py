"""Reconcile committed model-ablation evidence without market archives or MT5."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .finalize_model_ablation import annual_statistics
from .model_ablation import MODELS, comparisons_from_saved
from .run_v3 import ROOT, _describe, _sha256
from .runner import simulate_account


def check_values(actual, expected):
    for key, value in expected.items():
        if isinstance(value, dict):
            check_values(actual[key], value)
        elif isinstance(value, (list, int, float)) and not isinstance(value, bool):
            np.testing.assert_allclose(actual[key], value, rtol=1e-9, atol=1e-9)
        else:
            assert actual[key] == value, key


def main():
    out = ROOT / "evidence/model_ablation"
    config = json.loads((ROOT / "config/contract_model_ablation.json").read_text())
    parent = json.loads((ROOT / "config/contract_v3_atr_runner_sizing.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    for path, expected in manifest["inputs"].items():
        assert _sha256(ROOT / path) == expected, path
    for path, expected in manifest["outputs"].items():
        assert _sha256(out / path) == expected, path
    observations = pd.read_csv(
        out / "observations.csv.gz", parse_dates=["signal_time", "decision_time", "label_time"]
    )
    trades = pd.read_csv(
        out / "trades.csv.gz",
        parse_dates=["signal_time", "entry_time", "exit_time", "label_time"],
    )
    original = pd.read_csv(
        ROOT / "evidence/v3_atr_runner_sizing/trades.csv.gz",
        parse_dates=["signal_time", "entry_time", "exit_time"],
    )
    monthly = pd.read_csv(out / "monthly.csv")
    annual = pd.read_csv(out / "annual.csv")
    metrics = pd.read_csv(out / "metrics.csv")
    classes = pd.read_csv(out / "classification.csv")
    confusion = pd.read_csv(out / "confusion.csv")
    quadrants = pd.read_csv(out / "pnl_quadrants.csv")
    account_summary = pd.read_csv(out / "account_summary.csv")
    account_ledger = pd.read_csv(
        out / "accounts.csv.gz", parse_dates=["entry_time", "exit_time"]
    )
    start, end = (
        pd.Timestamp(parent["data"][key])
        for key in ("evaluation_start", "evaluation_end_exclusive")
    )
    weeks = (end - start).total_seconds() / (7 * 86400)
    pd.testing.assert_frame_equal(
        annual,
        annual_statistics(trades, start, end),
        check_dtype=False,
        check_exact=False,
        rtol=1e-9,
        atol=1e-9,
    )
    assert len(metrics) == 12 and len(monthly) == 12 * 32
    assert not observations.duplicated(["asset", "signal_time"]).any()
    scored = observations.loc[observations.scoreable]
    assert scored.truth.isin([-1, 0, 1]).all()
    np.testing.assert_array_equal(
        scored.truth, np.sign(scored.target_close - scored.signal_close)
    )
    assert scored.label_time.le(end).all() and scored.label_time.gt(scored.decision_time).all()
    assert scored.training_count.ge(200).all() and scored.maturity_lag.le(0).all()
    for asset in config["assets"]:
        observed = scored.loc[scored.asset.eq(asset)]
        for name in MODELS:
            p = observed[[f"{name}_p_{label}" for label in ("down", "flat", "up")]].to_numpy()
            np.testing.assert_allclose(p.sum(axis=1), 1, atol=1e-12)
            assert np.isfinite(p).all() and (p >= 0).all() and (p <= 1).all()
            np.testing.assert_array_equal(
                np.sign(p[:, 2] - p[:, 0]), observed[f"{name}_forecast"]
            )
            expected_loss = (
                (p - (observed.truth.to_numpy()[:, None] == np.array([-1, 0, 1]))) ** 2
            ).sum(axis=1)
            np.testing.assert_allclose(expected_loss, observed[f"{name}_brier"])
            for year in ("all", "2024", "2025", "2026"):
                rows = (
                    observed
                    if year == "all"
                    else observed.loc[observed.decision_time.dt.year.eq(int(year))]
                )
                cell = classes.loc[
                    classes.asset.eq(asset) & classes.model.eq(name) & classes.year.eq(year)
                ].iloc[0]
                pred = rows[f"{name}_forecast"]
                assert int(cell.rows) == len(rows)
                np.testing.assert_allclose(cell.brier, rows[f"{name}_brier"].mean())
                recalls = []
                for side, label in ((-1, "short"), (1, "long")):
                    correct = int((pred.eq(side) & rows.truth.eq(side)).sum())
                    forecast_count = int(pred.eq(side).sum())
                    assert int(cell[f"{label}_forecasts"]) == forecast_count
                    if forecast_count:
                        np.testing.assert_allclose(
                            cell[f"{label}_precision"], correct / forecast_count
                        )
                    recalls.append(correct / rows.truth.eq(side).sum())
                np.testing.assert_allclose(
                    cell.balanced_accuracy_abstention_miss, np.mean(recalls)
                )
            counts = confusion.loc[confusion.asset.eq(asset) & confusion.model.eq(name)]
            assert counts.rows.sum() == len(observed)
            for row in counts.itertuples():
                assert (
                    row.rows
                    == (
                        observed[f"{name}_forecast"].eq(row.forecast)
                        & observed.truth.eq(row.truth)
                    ).sum()
                )
            for cost in config["cost_profiles"]:

                def selector(f, asset=asset, name=name, cost=cost):
                    return f.asset.eq(asset) & f.model.eq(name) & f.cost.eq(cost)

                ledger = trades.loc[selector(trades)].reset_index(drop=True)
                lookup = observations.loc[observations.asset.eq(asset)].set_index("signal_time")
                joined_signal = lookup.reindex(ledger.signal_time)
                np.testing.assert_array_equal(
                    ledger.direction, joined_signal[f"{name}_forecast"]
                )
                for side, label in ((-1, "short"), (1, "long")):
                    assert joined_signal.loc[
                        ledger.direction.eq(side).to_numpy(), f"{name}_start_{label}"
                    ].all()
                assert ledger.entry_time.ge(start).all() and ledger.exit_time.lt(end).all()
                assert (ledger.entry_time > ledger.signal_time).all()
                assert (ledger.exit_time >= ledger.entry_time).all()
                assert (
                    ledger.entry_time.iloc[1:].reset_index(drop=True)
                    >= ledger.exit_time.iloc[:-1].reset_index(drop=True)
                ).all()
                np.testing.assert_allclose(
                    ledger.net_r, ledger.net_price / ledger.planned_risk_price
                )
                np.testing.assert_allclose(
                    ledger.net_per_lot_usd,
                    ledger.net_price * parent["data"]["assets"][asset]["contract_size"],
                )
                if name == "lorentzian" and cost == "base":
                    frozen = original.loc[
                        original.asset.eq(asset) & original.timeframe.eq("30min")
                    ].reset_index(drop=True)
                    pd.testing.assert_frame_equal(
                        ledger[frozen.columns],
                        frozen,
                        check_dtype=False,
                        check_exact=False,
                        rtol=1e-9,
                        atol=1e-9,
                    )
                cell = metrics.loc[selector(metrics)].iloc[0].to_dict()
                check_values(cell, _describe(ledger.net_r.to_numpy(), weeks))
                calendar = monthly.loc[selector(monthly)].set_index("month").net_r
                expected = (
                    ledger.groupby(ledger.exit_time.dt.strftime("%Y-%m"))
                    .net_r.sum()
                    .reindex(calendar.index, fill_value=0)
                )
                np.testing.assert_allclose(calendar, expected)
                groups = quadrants.loc[selector(quadrants)]
                assert groups.trades.sum() == len(ledger)
                np.testing.assert_allclose(groups.net_r.sum(), ledger.net_r.sum())
                known = ledger.scoreable & ledger.truth.ne(0)
                np.testing.assert_array_equal(
                    ledger.loc[known, "label_result"].eq("correct"),
                    ledger.loc[known, "truth"].eq(ledger.loc[known, "direction"]),
                )
                rebuilt, account = simulate_account(
                    ledger, parent["data"]["assets"][asset], 3000, 1, start, end
                )
                recorded = account_summary.loc[selector(account_summary)].iloc[0].to_dict()
                check_values(recorded, account)
                saved = account_ledger.loc[selector(account_ledger)].reset_index(drop=True)
                pd.testing.assert_frame_equal(
                    rebuilt.reset_index(drop=True),
                    saved[rebuilt.columns],
                    check_dtype=False,
                    check_exact=False,
                    rtol=1e-9,
                    atol=1e-9,
                )
    comparisons = comparisons_from_saved(observations, monthly, config)
    for actual, expected in zip(summary["primary_comparisons"], comparisons, strict=True):
        check_values(actual, expected)
    checks = {
        "manifest_hashes": True,
        "matured_labels": True,
        "probability_and_loss_recomputation": True,
        "class_counts_and_recall": True,
        "all_12_trade_ledgers_and_calendars": True,
        "original_1433_trades_preserved": True,
        "account_replay": True,
        "paired_block_comparisons_recomputed": True,
        "untouched_holdout": False,
    }
    (out / "validation.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
