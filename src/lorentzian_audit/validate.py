from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import sha256_file

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    evidence = ROOT / "evidence" / "v1"
    summary = json.loads((evidence / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((evidence / "source_manifest.json").read_text(encoding="utf-8"))
    trades = pd.read_csv(
        evidence / "trades.csv.gz", parse_dates=["signal_time", "entry_time", "exit_time"]
    )
    checks: dict[str, bool] = {}

    checks["all_source_hashes_match"] = all(
        sha256_file(Path(item["path"])) == item["sha256"]
        for asset in manifest.values()
        for item in asset["files"]
    )
    checks["all_fills_after_signal"] = bool(
        (trades["entry_time"] > trades["signal_time"]).all()
    )
    checks["all_exits_after_entry"] = bool((trades["exit_time"] > trades["entry_time"]).all())
    reconciled = (
        trades["gross_points"]
        - trades["base_spread_points"]
        - trades["base_slippage_points"]
        - trades["base_commission_points"]
    )
    checks["base_cost_reconciliation"] = bool(
        np.allclose(reconciled, trades["base_net_points"], atol=1e-10)
    )
    expected_bps = trades["base_net_points"] / trades["entry_bid"] * 10000.0
    checks["base_bps_reconciliation"] = bool(
        np.allclose(expected_bps, trades["base_net_bps"], atol=1e-10)
    )
    checks["causal_labels_mature"] = all(
        summary["assets"][asset]["signal_diagnostics"][variant][
            "maximum_selected_label_maturity_minus_decision"
        ]
        <= 0
        for asset in summary["assets"]
        for variant in ("causal_lorentzian", "causal_euclidean")
    )
    count_match = True
    totals_match = True
    no_overlap = True
    for (asset, variant), group in trades.groupby(["asset", "variant"], sort=False):
        expected = summary["assets"][asset]["variants"][variant]["base"]
        count_match &= len(group) == expected["trades"]
        totals_match &= np.isclose(group["base_net_bps"].sum(), expected["net_bps"], atol=1e-9)
        ordered = group.sort_values("entry_time")
        no_overlap &= bool(
            (
                ordered["entry_time"].iloc[1:].to_numpy()
                >= ordered["exit_time"].iloc[:-1].to_numpy()
            ).all()
        )
    checks["trade_counts_match_summary"] = bool(count_match)
    checks["trade_totals_match_summary"] = bool(totals_match)
    checks["positions_do_not_overlap"] = bool(no_overlap)
    checks["verdict_matches_gates"] = (
        summary["verdict"] == "ROBUST_CROSS_ASSET_LORENTZIAN_EDGE_SUPPORTED"
    ) == bool(summary["gates"]["all_pass"])
    output = {
        "checks": checks,
        "passed": int(sum(checks.values())),
        "total": len(checks),
        "all_pass": all(checks.values()),
    }
    (evidence / "validation.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, indent=2))
    if not output["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
