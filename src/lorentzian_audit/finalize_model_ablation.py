"""Rebuild annual reporting denominators and canonicalize portable evidence."""

from __future__ import annotations

import json

import pandas as pd

from .run_v3 import ROOT, _describe, _sha256


def annual_statistics(trades, start, end):
    rows = []
    for (asset, cost, model, year), group in trades.groupby(
        ["asset", "cost", "model", trades.exit_time.dt.year]
    ):
        left = max(start, pd.Timestamp(year=int(year), month=1, day=1, tz="UTC"))
        right = min(end, pd.Timestamp(year=int(year) + 1, month=1, day=1, tz="UTC"))
        weeks = (right - left).total_seconds() / (7 * 86400)
        rows.append(
            {
                "asset": asset,
                "cost": cost,
                "model": model,
                "year": int(year),
                "calendar_weeks": weeks,
                **_describe(group.net_r.to_numpy(), weeks),
            }
        )
    return pd.DataFrame(rows)


def main():
    out = ROOT / "evidence/model_ablation"
    parent = json.loads((ROOT / "config/contract_v3_atr_runner_sizing.json").read_text())
    start, end = (
        pd.Timestamp(parent["data"][key])
        for key in ("evaluation_start", "evaluation_end_exclusive")
    )
    trades = pd.read_csv(out / "trades.csv.gz", parse_dates=["exit_time"])
    protected = {
        name: _sha256(out / name)
        for name in ("observations.csv.gz", "trades.csv.gz", "accounts.csv.gz")
    }
    annual_statistics(trades, start, end).to_csv(
        out / "annual.csv", index=False, lineterminator="\n"
    )
    # Windows-generated text and Git's LF checkout must have identical manifest hashes.
    for path in out.iterdir():
        if path.suffix in {".csv", ".json"}:
            content = path.read_text(encoding="utf-8")
            path.write_text(content, encoding="utf-8", newline="\n")
    for name, digest in protected.items():
        assert _sha256(out / name) == digest, "Reporting repair changed forecasts or ledgers"
    manifest = json.loads((out / "manifest.json").read_text())
    manifest["inputs"] = {
        key.replace("\\", "/"): value for key, value in manifest["inputs"].items()
    }
    manifest["reporting_finalization"] = {
        "annual_frequency": "per-year calendar exposure, partial 2026 through August",
        "text_format": "UTF-8 LF, portable hash agreement with Git checkout",
        "forecast_and_trade_ledger_bytes_unchanged": True,
    }
    for source in (
        "src/lorentzian_audit/model_ablation.py",
        "src/lorentzian_audit/finalize_model_ablation.py",
    ):
        manifest["inputs"][source] = _sha256(ROOT / source)
    manifest["outputs"] = {
        p.name: _sha256(p)
        for p in out.iterdir()
        if p.name not in {"manifest.json", "validation.json"}
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        "Annual denominators and portable LF hashes finalized; "
        "forecasts/trades unchanged."
    )


if __name__ == "__main__":
    main()
