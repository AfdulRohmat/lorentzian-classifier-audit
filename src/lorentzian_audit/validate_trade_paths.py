"""Portable checks of saved audit evidence; no raw market files required."""

import json

import numpy as np
import pandas as pd

from .run_v3 import ROOT, _sha256


def main():
    folder = ROOT / "evidence/trade_path_audit"
    summary = json.loads((folder / "summary.json").read_text())
    ledger_path = ROOT / "evidence/v3_atr_runner_sizing/trades.csv.gz"
    assert _sha256(ledger_path) == summary["parent_ledger_sha256"]
    assert _sha256(ROOT / "docs/TRADE_PATH_AUDIT_PLAN.md") == summary["plan_sha256"]
    original = pd.read_csv(ledger_path)
    original = original.loc[original.timeframe.eq("30min")]
    paths = pd.read_csv(folder / "paths.csv.gz")
    shadows = pd.read_csv(folder / "shadow_windows.csv.gz")
    keys = ["asset", "trade_id"]
    pd.testing.assert_frame_equal(
        paths[original.columns].sort_values(keys).reset_index(drop=True),
        original.sort_values(keys).reset_index(drop=True),
        check_dtype=False,
    )
    np.testing.assert_allclose(paths.mfe_lower_r - paths.giveback_lower_r, paths.net_r)
    np.testing.assert_allclose(paths.mfe_upper_r - paths.giveback_upper_r, paths.net_r)
    assert (paths.mfe_upper_r >= paths.mfe_lower_r).all()
    assert (paths.mae_r <= paths.net_r + 1e-9).all()
    assert (paths.mfe_lower_r >= paths.net_r - 1e-9).all()
    assert (paths.peak_minutes.dropna() >= 0).all()
    assert (
        (paths.peak_minutes <= paths.holding_hours * 60 + 1e-8)
        .fillna(True)
        .loc[paths.peak_minutes.notna()]
        .all()
    )
    assert not shadows.duplicated([*keys, "horizon_minutes"]).any()
    assert len(shadows) == 3 * len(paths)
    assert shadows.loc[shadows.valid, "coverage"].ge(0.9).all()
    valid = shadows.loc[shadows.valid]
    assert valid.shadow_mfe_r.ge(valid.endpoint_net_r).all()
    assert valid.shadow_mae_r.le(valid.endpoint_net_r).all()
    for record in summary["metrics"]:
        rows = paths.loc[paths.asset.eq(record["asset"])]
        if record["side"] != "all":
            rows = rows.loc[rows.direction.eq(1 if record["side"] == "long" else -1)]
        assert len(rows) == record["trades"]
        for field, column in [
            ("mean_net_r", "net_r"),
            ("mean_mfe_lower_r", "mfe_lower_r"),
            ("mean_giveback_lower_r", "giveback_lower_r"),
        ]:
            assert np.isclose(record[field], rows[column].mean())
    result = {
        "passed": True,
        "unchanged_original_trades": len(paths),
        "shadow_rows": len(shadows),
        "scope": (
            "Saved evidence parity, bounds, accounting, coverage and summaries; "
            "raw-path reconstruction verified by the audit runner"
        ),
    }
    (folder / "artifact_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
