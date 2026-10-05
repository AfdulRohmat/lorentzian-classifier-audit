"""Compare observed author signals after a cold restart, not portfolio returns."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from lorentzian_audit.native_vwap import audit_vwap


def compare_streams(running, cold):
    running = running.loc[running.online.eq(1)].set_index("time")
    cold = cold.loc[cold.online.eq(1)].set_index("time")
    if running.index.has_duplicates or cold.index.has_duplicates:
        raise ValueError("Duplicate observed timestamp")
    if not cold.index.isin(running.index).all():
        raise ValueError("Cold stream is outside continuous observation timestamps")
    left = running.loc[cold.index]
    for field in ("open", "high", "low", "close", "tick_volume", "vwap", "sigma"):
        if not np.allclose(left[field], cold[field], rtol=0, atol=2e-7):
            raise ValueError(f"Market/benchmark changed across restart: {field}")
    differences = pd.DataFrame(index=cold.index)
    summary = {"overlap_bars": len(cold)}
    for field in ("prediction", "direction", "start"):
        mismatch = left[field].ne(cold[field])
        summary[f"{field}_mismatches"] = int(mismatch.sum())
        differences[f"running_{field}"] = left[field]
        differences[f"cold_{field}"] = cold[field]
        differences[f"{field}_mismatch"] = mismatch
    mask = differences.filter(like="_mismatch").any(axis=1)
    summary["any_mismatches"] = int(mask.sum())
    summary["status"] = "RESTART_DEPENDENT" if mask.any() else "MATCH_ON_THIS_REPLAY"
    summary["running_starts"] = int(left.start.ne(0).sum())
    summary["cold_starts"] = int(cold.start.ne(0).sum())
    summary["active_start_union_bars"] = int((left.start.ne(0) | cold.start.ne(0)).sum())
    for label, stamp in (
        ("first_mismatch_utc", differences.index[mask].min()),
        ("last_mismatch_utc", differences.index[mask].max()),
    ):
        summary[label] = (
            str(pd.to_datetime(stamp, unit="s", utc=True)) if mask.any() else None
        )
    summary["first_overlap_utc"] = str(pd.to_datetime(cold.index.min(), unit="s", utc=True))
    summary["last_overlap_utc"] = str(pd.to_datetime(cold.index.max(), unit="s", utc=True))
    return summary, differences.loc[mask].reset_index()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--primary", type=Path, default=Path("evidence/native_vwap_2026_v3"))
    p.add_argument("--cold", type=Path, default=Path("evidence/native_vwap_restart"))
    p.add_argument("--output", type=Path, default=Path("docs/RESULT_NATIVE_VWAP_RESTART.md"))
    args = p.parse_args()
    summaries = []
    mismatches = []
    for symbol, suffix in (("US500", "u"), ("US500_x100", "x")):
        a = args.primary / f"lcv28_{suffix}_m1_v1_i0_b3000_r0"
        b = args.cold / f"lcv28_cold_{suffix}"
        results = [json.loads((folder / "result.json").read_text()) for folder in (a, b)]
        if any(
            results[0][field] != results[1][field]
            for field in ("ea_sha256", "indicator_sha256")
        ):
            raise ValueError("Cold diagnostic did not preserve compiled builds")
        streams = []
        for folder in (a, b):
            stats = dict(
                pd.read_csv(folder / "stats.csv.gz").itertuples(index=False, name=None)
            )
            signals = pd.read_csv(folder / "signals.csv.gz")
            audit_vwap(
                stats,
                pd.read_csv(folder / "deals.csv.gz"),
                pd.read_csv(folder / "events.csv.gz"),
                signals,
            )
            streams.append(signals)
        summary, differences = compare_streams(*streams)
        summary.update(
            symbol=symbol,
            running_tag=a.name,
            cold_tag=b.name,
            running_initial_bars=results[0]["initial_history_bars"],
            cold_initial_bars=results[1]["initial_history_bars"],
            running_history_first=results[0]["native_history_first"],
            cold_history_first=results[1]["native_history_first"],
            same_history_origin=(
                results[0]["native_history_first"] == results[1]["native_history_first"]
            ),
            running_source_sha=results[0]["ea_sha256"],
            indicator_sha=results[0]["indicator_sha256"],
        )
        summaries.append(summary)
        differences.insert(0, "symbol", symbol)
        mismatches.append(differences)
    (args.cold / "comparison.json").write_text(json.dumps(summaries, indent=2) + "\n")
    pd.concat(mismatches, ignore_index=True).to_csv(
        args.cold / "signal_differences.csv", index=False
    )
    lines = [
        "# Official model cold-restart diagnostic",
        "",
        "The same untouched indicator and tester wrapper run continuously from January, "
        "then separately cold-start in February. We compare only actually observed closed-bar "
        "predictions, directions and starts at common timestamps through August. "
        "Market bars, VWAP, sigma and compiled builds must remain identical.",
        "",
        "| Symbol | Overlap bars | Prediction changes | Direction changes | "
        "Start changes | Verdict |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['symbol']} | {s['overlap_bars']} | {s['prediction_mismatches']} | "
            f"{s['direction_mismatches']} | {s['start_mismatches']} | {s['status']} |"
        )
    lines += [
        "",
        "A mismatch is state/history-start dependence, not proof that previously observed "
        "online signals used future data. Endpoint-prefix and next-bar stability test other "
        "properties. A matching restart is also not proof of live every-tick "
        "calculation parity.",
        "The comparison JSON records the native history origin and initial bar count "
        "for both starts, so a preload-origin change is not misreported as pure "
        "ANN state dependence.",
        "",
        "These two runs are diagnostic only, not additional optimization candidates. "
        "Their portfolios start later and are not compared as investment performance. "
        "The generic runner's eight-month frequency/monthly summaries on these February-start "
        "artifacts are not used as seven-month performance statistics.",
        "",
        "Evidence: [comparison JSON](../evidence/native_vwap_restart/comparison.json), "
        "[every mismatching timestamp]"
        "(../evidence/native_vwap_restart/signal_differences.csv), "
        "[engineering notes](NATIVE_VWAP_ENGINEERING_NOTES.md).",
        "",
    ]
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
