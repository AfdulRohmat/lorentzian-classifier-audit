from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import sha256_file

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    evidence = ROOT / "evidence" / "v3_atr_runner_sizing"
    contract = json.loads(
        (ROOT / "config" / "contract_v3_atr_runner_sizing.json").read_text(
            encoding="utf-8"
        )
    )
    summary = json.loads((evidence / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((evidence / "source_manifest.json").read_text(encoding="utf-8"))
    trades = pd.read_csv(
        evidence / "trades.csv.gz",
        parse_dates=["signal_time", "entry_time", "exit_time"],
    )
    accounts = pd.read_csv(
        evidence / "accounts.csv.gz", parse_dates=["entry_time", "exit_time"]
    )
    checks: dict[str, bool] = {}
    checks["source_hashes_match"] = all(
        sha256_file(Path(item["path"])) == item["sha256"]
        for asset in manifest.values()
        for item in asset["files"]
    )
    checks["causal_labels_mature"] = all(
        timeframe["causal_label_diagnostic"][
            "maximum_selected_label_maturity_minus_decision"
        ]
        <= 0
        for asset in summary["assets"].values()
        for timeframe in asset["timeframes"].values()
    )
    checks["entries_after_signals"] = bool(
        (trades.entry_time > trades.signal_time).all()
    )
    checks["exits_after_entries"] = bool((trades.exit_time >= trades.entry_time).all())
    commission = trades.asset.map(
        {
            asset: values["commission_round_trip_price"]
            for asset, values in contract["costs"].items()
        }
    )
    expected_net = trades.direction * (trades.exit_fill - trades.entry_fill) - commission
    checks["trade_pnl_reconciles"] = bool(
        np.allclose(expected_net, trades.net_price, atol=1e-10)
    )
    expected_risk = trades.atr * float(contract["exit"]["initial_stop_atr"]) + trades.asset.map(
        {
            asset: values["slippage_side"] + values["commission_round_trip_price"]
            for asset, values in contract["costs"].items()
        }
    )
    checks["planned_risk_reconciles"] = bool(
        np.allclose(expected_risk, trades.planned_risk_price, atol=1e-10)
    )
    checks["trailing_stop_never_loosened"] = bool(
        (
            trades.direction * (trades.final_stop - trades.initial_stop)
            >= -1e-10
        ).all()
    )
    no_overlap = True
    summary_match = True
    for (asset, timeframe), group in trades.groupby(["asset", "timeframe"]):
        ordered = group.sort_values("entry_time")
        no_overlap &= bool(
            (
                ordered.entry_time.iloc[1:].to_numpy()
                >= ordered.exit_time.iloc[:-1].to_numpy()
            ).all()
        )
        expected = summary["assets"][asset]["timeframes"][timeframe]["runner"]
        summary_match &= len(group) == expected["trades"]
        summary_match &= np.isclose(group.net_r.sum(), expected["total_r"], atol=1e-9)
    checks["positions_do_not_overlap"] = bool(no_overlap)
    checks["trade_summary_matches"] = bool(summary_match)

    joined = accounts.merge(
        trades[["asset", "timeframe", "trade_id", "planned_loss_per_lot"]],
        on=["asset", "timeframe", "trade_id"],
        how="left",
        validate="many_to_one",
    )
    executed = joined.status.eq("EXECUTED")
    risk_used = joined.volume * joined.planned_loss_per_lot
    checks["sizing_never_exceeds_budget"] = bool(
        (risk_used.loc[executed] <= joined.loc[executed, "risk_budget_usd"] + 1e-8).all()
    )
    volume_valid = True
    skip_valid = True
    account_valid = True
    for (asset, timeframe, balance, risk), group in joined.groupby(
        ["asset", "timeframe", "initial_balance_usd", "risk_percent"]
    ):
        spec = contract["data"]["assets"][asset]
        live = group.loc[group.status.eq("EXECUTED")]
        volume_valid &= bool((live.volume >= float(spec["volume_min"]) - 1e-10).all())
        volume_valid &= bool(
            np.allclose(
                live.volume / float(spec["volume_step"]),
                np.round(live.volume / float(spec["volume_step"])),
                atol=1e-8,
            )
        )
        skip_valid &= bool((group.loc[group.status.eq("SKIP_MIN_LOT"), "volume"] == 0).all())
        expected = next(
            row
            for row in summary["assets"][asset]["timeframes"][timeframe]["accounts"]
            if row["initial_balance_usd"] == balance and row["risk_percent"] == risk
        )
        account_valid &= np.isclose(
            float(balance) + group.pnl_usd.sum(), expected["final_balance_usd"], atol=1e-8
        )
        account_valid &= int((group.status == "EXECUTED").sum()) == expected[
            "executed_trades"
        ]
    checks["broker_volume_rules_hold"] = bool(volume_valid)
    checks["minimum_lot_is_skipped_not_clamped"] = bool(skip_valid)
    checks["account_ledgers_reconcile"] = bool(account_valid)
    checks["verdict_matches_gates"] = (
        summary["verdict"] == "ATR_RUNNER_SMALL_ACCOUNT_CANDIDATE_SUPPORTED"
    ) == bool(summary["gates"]["all_pass"])
    result = {
        "checks": checks,
        "passed": int(sum(checks.values())),
        "total": len(checks),
        "all_pass": all(checks.values()),
    }
    (evidence / "validation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
