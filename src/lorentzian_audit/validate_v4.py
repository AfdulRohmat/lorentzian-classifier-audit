from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import sha256_file
from .run_v4 import tail_miss_simulation

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    evidence = ROOT / "evidence" / "v4_tail_robustness"
    contract = json.loads(
        (ROOT / "config" / "contract_v4_tail_robustness.json").read_text(
            encoding="utf-8"
        )
    )
    summary = json.loads((evidence / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((evidence / "source_manifest.json").read_text(encoding="utf-8"))
    v3_path = ROOT / contract["inputs"]["v3_trade_ledger"]
    v3 = pd.read_csv(v3_path, parse_dates=["entry_time"])
    trades = v3.loc[v3.asset.eq("sp500") & v3.timeframe.eq("30min")].copy()
    holdout = pd.read_csv(
        evidence / "new_holdout_trades.csv",
        parse_dates=["signal_time", "entry_time", "exit_time"],
    )
    checks: dict[str, bool] = {}
    checks["input_ledger_hash_matches"] = (
        sha256_file(v3_path) == contract["inputs"]["v3_trade_ledger_sha256"]
    )
    checks["base_total_reconciles"] = np.isclose(
        trades.net_r.sum(), summary["historical"]["base"]["total_r"], atol=1e-10
    )
    cap_match = True
    for cap in contract["tail_diagnostics"]["winner_caps_r"]:
        cap_match &= np.isclose(
            np.minimum(trades.net_r.to_numpy(dtype=float), cap).sum(),
            summary["historical"]["caps"][f"cap_{cap}r"]["total_r"],
            atol=1e-10,
        )
    checks["cap_totals_reconcile"] = bool(cap_match)
    concentration_match = True
    ordered = np.sort(trades.net_r.to_numpy(dtype=float))[::-1]
    for n in contract["tail_diagnostics"]["top_n_concentration"]:
        concentration_match &= np.isclose(
            ordered[:n].sum(),
            summary["historical"]["concentration"][f"top_{n}"]["sum_r"],
            atol=1e-10,
        )
    checks["concentration_reconciles"] = bool(concentration_match)
    monte_carlo_match = True
    for index, expected in enumerate(summary["historical"]["monte_carlo"]):
        reproduced = tail_miss_simulation(
            trades.net_r.to_numpy(dtype=float),
            float(contract["tail_diagnostics"]["tail_threshold_r"]),
            float(expected["tail_miss_probability"]),
            int(contract["monte_carlo"]["replicates"]),
            int(contract["monte_carlo"]["seed"]) + index,
        )
        monte_carlo_match &= reproduced == expected
    checks["monte_carlo_replays_exactly"] = bool(monte_carlo_match)
    extension = manifest.get("extension", {})
    checks["extension_hash_matches"] = bool(
        extension.get("path")
        and sha256_file(Path(extension["path"])) == extension.get("sha256")
    )
    checks["holdout_causal_labels_mature"] = (
        extension["causal_label_diagnostic"][
            "maximum_selected_label_maturity_minus_decision"
        ]
        <= 0
    )
    checks["holdout_entries_after_signals"] = bool(
        (holdout.entry_time > holdout.signal_time).all()
    )
    ordered_holdout = holdout.sort_values("entry_time")
    checks["holdout_positions_do_not_overlap"] = bool(
        (
            ordered_holdout.entry_time.iloc[1:].to_numpy()
            >= ordered_holdout.exit_time.iloc[:-1].to_numpy()
        ).all()
    )
    holdout_summary = summary["new_holdout"]
    checks["holdout_summary_reconciles"] = (
        len(holdout) == holdout_summary["metrics"]["trades"]
        and np.isclose(
            holdout.net_r.sum(), holdout_summary["metrics"]["total_r"], atol=1e-10
        )
    )
    checks["small_holdout_not_overclaimed"] = (
        len(holdout) < 30
        and holdout_summary["sample_status"] == "INSUFFICIENT_SAMPLE"
        and holdout_summary["annualized_interpretation_forbidden"]
    )
    declared = summary["historical"]["assessment_gates"]
    checks["assessment_matches_gates"] = (
        summary["historical"]["assessment"]
        == (
            "TAIL_STRUCTURE_SUPPORTED_EDGE_UNCONFIRMED"
            if declared["all_pass"]
            else "TAIL_STRUCTURE_NOT_ROBUST"
        )
    )
    checks = {name: bool(passed) for name, passed in checks.items()}
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
