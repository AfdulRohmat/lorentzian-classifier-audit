"""Reconcile the user-requested native minimum-lot variation, without simulation."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

from lorentzian_audit.native_results import summarize_native


def main() -> None:
    root = Path("evidence/native_x100_2026_minimum")
    strict = json.loads(Path("evidence/native_x100_2026/validated_summary.json").read_text())
    rows = []
    for folder in sorted(root.glob("lc26m_b*")):
        saved = json.loads((folder / "result.json").read_text())
        stats = dict(pd.read_csv(folder / "stats.csv.gz").itertuples(index=False, name=None))
        if int(stats["minimum_lot_fallback"]) != 1:
            raise ValueError("Minimum lot variation not enabled in tester")
        result, monthly = summarize_native(
            stats, pd.read_csv(folder / "deals.csv.gz"), pd.read_csv(folder / "events.csv.gz")
        )
        for key in ["net_profit", "trades", "final_balance", "planned_actual_risk_percent_max"]:
            if abs(result[key] - saved[key]) > 1e-8:
                raise ValueError(f"Native summary mismatch: {key}")
        signal = hashlib.sha256(
            gzip.decompress((folder / "signals.csv.gz").read_bytes())
        ).hexdigest()
        if signal != strict["signal_sha256"]:
            raise ValueError("Classifier differs from strict comparison")
        if not saved["report_100_percent_real_ticks"]:
            raise ValueError("Real tick coverage not verified")
        result["monthly"] = monthly
        rows.append(result)
    if {int(r["deposit"]) for r in rows} != {500, 1000, 3000}:
        raise ValueError("Incomplete three-account variation")
    control = next(
        r for r in strict["results"] if r["deposit"] == 3000 and r["risk_percent"] == 1
    )
    variant = next(r for r in rows if r["deposit"] == 3000)
    if variant["minimum_lot_fallback_entries"] != 0:
        raise ValueError("No-fallback control unexpectedly changed")
    for key in ["trades", "final_balance", "net_profit", "equity_dd_percent"]:
        if abs(control[key] - variant[key]) > 1e-8:
            raise ValueError("New build changes no-fallback control result")
    output = {
        "status": "MINIMUM_LOT_VARIATION_RECONCILED_NOT_PROFITABLE",
        "same_signals_as_strict_matrix": True,
        "no_fallback_control_identical": True,
        "all_reports_100_percent_real_ticks": True,
        "results": sorted(rows, key=lambda x: x["deposit"]),
    }
    (root / "validated_summary.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
