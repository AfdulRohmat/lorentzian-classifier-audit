"""Create full anchored reference fixture, without querying the broker."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from lorentzian_classification.core import calc_atr

from lorentzian_audit.data import aggregate_timeframe, load_asset_minutes
from lorentzian_audit.signals import (
    FEATURE_COLUMNS,
    causal_knn_prediction_pair_batched,
    default_filter_mask,
    feature_kernel_outputs,
    start_events_from_predictions,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("local_mt5/parity"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "config/contract_v3_atr_runner_sizing.json").read_text())
    minutes, manifest = load_asset_minutes(
        root, "sp500", contract["data"]["assets"]["sp500"], contract["data"]
    )
    bars = aggregate_timeframe(minutes, "30min")
    outputs = feature_kernel_outputs(bars, 100.0)
    prediction, diagnostic = causal_knn_prediction_pair_batched(
        outputs[FEATURE_COLUMNS].to_numpy(), bars.close.to_numpy()
    )
    filters = default_filter_mask(bars)
    signals = start_events_from_predictions(
        prediction["lorentzian"], filters, outputs.kernel.to_numpy()
    )
    signals.index = bars.index
    outputs["atr"] = calc_atr(bars.high.tolist(), bars.low.tolist(), bars.close.tolist(), 14)
    outputs["filter"] = filters.astype(int)
    outputs["prediction"] = signals.prediction
    outputs["direction"] = signals.direction
    outputs["start"] = signals.start_long.astype(int) - signals.start_short.astype(int)
    outputs.to_csv(args.output / "python_reference.csv", float_format="%.17g")
    fixture = bars[["open", "high", "low", "close"]].copy()
    fixture.index = bars.index.asi8 // 1_000_000_000
    # pandas version may use microsecond indices; Timestamp.timestamp is explicit.
    fixture.index = np.array([int(t.timestamp()) for t in bars.index])
    fixture.to_csv(args.output / "fixture.csv", header=False, float_format="%.17g")
    report = {
        "bars": len(bars),
        "first": str(bars.index[0]),
        "last": str(bars.index[-1]),
        "diagnostics": diagnostic,
        "source_manifest": manifest,
        "files_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in args.output.glob("*.csv")
        },
    }
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(
        json.dumps({k: report[k] for k in ["bars", "first", "last", "files_sha256"]}, indent=2)
    )


if __name__ == "__main__":
    main()
