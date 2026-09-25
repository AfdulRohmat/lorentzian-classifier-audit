"""Reconcile exact targets, prediction cohorts, baselines and original trade PnL."""

import json

import numpy as np
import pandas as pd

from .audit_predictions import block_ratio_interval, calendar_counts, past_majority
from .run_v3 import ROOT, _sha256


def main():
    out = ROOT / "evidence/prediction_audit"
    summary = json.loads((out / "summary.json").read_text())
    config_path = ROOT / "config/contract_prediction_audit.json"
    assert _sha256(config_path) == summary["contract_sha256"]
    ledger_path = ROOT / "evidence/v3_atr_runner_sizing/trades.csv.gz"
    assert _sha256(ledger_path) == summary["parent_ledger_sha256"]
    times = ["signal_time", "entry_time", "exit_time"]
    old = pd.read_csv(ledger_path, parse_dates=times)
    old = old.loc[old.timeframe.eq("30min")]
    trades = pd.read_csv(
        out / "trade_labels.csv.gz", parse_dates=[*times, "decision_time", "label_time"]
    )
    obs = pd.read_csv(
        out / "observations.csv.gz", parse_dates=["signal_time", "decision_time", "label_time"]
    )
    keys = ["asset", "trade_id"]
    pd.testing.assert_frame_equal(
        trades[old.columns].sort_values(keys).reset_index(drop=True),
        old.sort_values(keys).reset_index(drop=True),
        check_dtype=False,
    )
    np.testing.assert_allclose(
        obs.truth, np.sign(obs.target_close - obs.signal_close), equal_nan=True
    )
    np.testing.assert_array_equal(obs.forecast, np.sign(obs.vote))
    assert obs.loc[~obs.scoreable, "truth"].isna().all()
    assert obs.loc[obs.scoreable, "label_time"].le(pd.Timestamp("2026-09-01", tz="UTC")).all()
    np.testing.assert_allclose(
        obs.elapsed_minutes,
        (obs.label_time - obs.decision_time).dt.total_seconds() / 60,
        equal_nan=True,
    )
    assert (obs.loc[obs.scoreable, "elapsed_minutes"] >= 120).all()
    months = pd.period_range("2024-01", "2026-08", freq="M").astype(str)
    for asset, rows in obs.groupby("asset"):
        prior = past_majority(rows.truth.reset_index(drop=True))
        np.testing.assert_allclose(rows.matured_rolling_prior.iloc[2004:], prior.iloc[2004:])
        eligible = rows.loc[rows.scoreable]
        confusion = pd.read_csv(out / "confusion.csv")
        assert confusion.loc[confusion.asset.eq(asset), "rows"].sum() == len(eligible)
        for cohort in [r for r in summary["cohorts"] if r["asset"] == asset]:
            side = -1 if cohort["side"] == "short" else 1
            if cohort["scope"] == "raw":
                selected = eligible.loc[eligible.forecast.eq(side)]
            elif cohort["scope"] == "qualified_start":
                selected = eligible.loc[eligible[f"start_{cohort['side']}"]]
            else:
                selected = trades.loc[
                    trades.asset.eq(asset) & trades.direction.eq(side) & trades.scoreable
                ]
            assert len(selected) == cohort["rows"]
            assert int(selected.truth.eq(side).sum()) == cohort["correct"]
            interval = block_ratio_interval(
                calendar_counts(selected, selected.truth.eq(side), months)
            )
            np.testing.assert_allclose(interval["ci95"], cohort["precision_ci95"])
        for comparison in [
            r for r in summary["paired_raw_short_accuracy"] if r["asset"] == asset
        ]:
            name = comparison["baseline"]
            selected = eligible.loc[
                eligible.forecast.eq(-1)
                & eligible.truth.ne(0)
                & eligible[name].notna()
                & eligible[name].ne(0)
            ]
            hit = selected.truth.eq(-1).astype(int)
            base_hit = selected[name].eq(selected.truth).astype(int)
            assert len(selected) == comparison["rows"]
            assert np.isclose(hit.mean(), comparison["model_accuracy"])
            assert np.isclose(base_hit.mean(), comparison["baseline_accuracy"])
            result = block_ratio_interval(
                calendar_counts(selected, hit - base_hit, months), family=3
            )
            np.testing.assert_allclose(result["adjusted_ci"], comparison["adjusted_ci"])
    assert trades.forecast.eq(trades.direction).all()
    assert trades.pnl_win.eq(trades.net_r.gt(0)).all()
    assert trades.correct_label.eq(trades.truth.eq(trades.direction) & trades.scoreable).all()
    assert trades.exit_before_label_maturity.eq(trades.exit_time.lt(trades.label_time)).all()
    expected_outcome = pd.Series(
        np.where(trades.correct_label, "correct_", "wrong_"), index=trades.index
    ) + np.where(trades.pnl_win, "win", "nonwin")
    expected_outcome.loc[trades.truth.eq(0)] = "flat_target"
    expected_outcome.loc[~trades.scoreable] = "unavailable_target"
    assert trades.outcome.eq(expected_outcome).all()
    for record in summary["pnl_quadrants"]:
        side = -1 if record["side"] == "short" else 1
        selected = trades.loc[
            trades.asset.eq(record["asset"])
            & trades.direction.eq(side)
            & trades.outcome.eq(record["outcome"])
        ]
        assert len(selected) == record["trades"]
        assert np.isclose(selected.net_r.sum(), record["total_r"])
    assert sum(r["trades"] for r in summary["pnl_quadrants"]) == len(old)
    result = {
        "passed": True,
        "original_trades_preserved": len(old),
        "prediction_rows": len(obs),
        "cohorts": len(summary["cohorts"]),
        "checks": [
            "target maturity and censoring",
            "saved price target reconstruction",
            "matured prior on full internal windows",
            "confusion/cohort accounting",
            "paired baseline bootstrap",
            "original PnL and outcome reconciliation",
        ],
    }
    (out / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
