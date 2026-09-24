from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import (
    aggregate_timeframe,
    load_asset_minutes,
    normalise_minutes,
    sha256_file,
)
from .run import _json_default
from .run_v3 import _describe
from .runner import build_runner_trades
from .signals import build_full_history_variants, feature_kernel_outputs
from .statistics import profit_factor

ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _quantiles(values: np.ndarray) -> list[float]:
    return [
        float(np.quantile(values, 0.025)),
        float(np.median(values)),
        float(np.quantile(values, 0.975)),
    ]


def tail_miss_simulation(
    values: np.ndarray,
    tail_threshold: float,
    probability: float,
    replicates: int,
    seed: int,
) -> dict:
    tail_positions = np.flatnonzero(values > tail_threshold)
    rng = np.random.default_rng(seed)
    missed = rng.random((replicates, len(tail_positions))) < probability
    tail_values = values[tail_positions]
    ordinary_total = float(values[values <= tail_threshold].sum())
    totals = ordinary_total + ((~missed) * tail_values).sum(axis=1)

    equity = np.ones(replicates, dtype=float)
    peaks = equity.copy()
    drawdowns = np.zeros(replicates, dtype=float)
    tail_column = {position: column for column, position in enumerate(tail_positions)}
    for position, outcome in enumerate(values):
        if position in tail_column:
            applied = np.where(missed[:, tail_column[position]], 0.0, outcome)
        else:
            applied = outcome
        equity *= 1.0 + 0.01 * applied
        peaks = np.maximum(peaks, equity)
        drawdowns = np.maximum(drawdowns, (peaks - equity) / peaks)
    return {
        "tail_miss_probability": probability,
        "replicates": replicates,
        "tail_trades": len(tail_positions),
        "total_r_ci95_median": _quantiles(totals),
        "probability_total_r_positive": float((totals > 0).mean()),
        "missed_tail_count_ci95_median": _quantiles(missed.sum(axis=1)),
        "one_percent_final_equity_multiple_ci95_median": _quantiles(equity),
        "one_percent_max_drawdown_fraction_ci95_median": _quantiles(drawdowns),
    }


def _historical_analysis(trades: pd.DataFrame, contract: dict) -> dict:
    values = trades.net_r.to_numpy(dtype=float)
    total = float(values.sum())
    full_weeks = (
        pd.Timestamp("2026-09-01", tz="UTC")
        - pd.Timestamp("2024-01-01", tz="UTC")
    ).total_seconds() / (7 * 86400)
    caps: dict[str, dict] = {}
    for cap in contract["tail_diagnostics"]["winner_caps_r"]:
        capped = np.minimum(values, float(cap))
        caps[f"cap_{cap}r"] = {
            "total_r": float(capped.sum()),
            "mean_r": float(capped.mean()),
            "profit_factor": profit_factor(capped),
            "annual": {
                str(year): float(
                    np.minimum(
                        trades.loc[trades.entry_time.dt.year.eq(year), "net_r"].to_numpy(
                            dtype=float
                        ),
                        float(cap),
                    ).sum()
                )
                for year in contract["tail_diagnostics"]["annual_groups"]
            },
        }
    sorted_values = np.sort(values)[::-1]
    concentration = {
        f"top_{n}": {
            "sum_r": float(sorted_values[:n].sum()),
            "share_of_net_percent": float(sorted_values[:n].sum() / total * 100.0),
            "total_without_r": float(total - sorted_values[:n].sum()),
        }
        for n in contract["tail_diagnostics"]["top_n_concentration"]
    }
    threshold = float(contract["tail_diagnostics"]["tail_threshold_r"])
    tail = trades.loc[trades.net_r > threshold].copy()
    tail_by_year = {
        str(year): {
            "trades": int((tail.entry_time.dt.year == year).sum()),
            "sum_r": float(tail.loc[tail.entry_time.dt.year.eq(year), "net_r"].sum()),
        }
        for year in contract["tail_diagnostics"]["annual_groups"]
    }
    partitions: dict[str, dict] = {}
    for name in ("development", "retrospective_holdout"):
        start, end = contract["temporal_partitions"][name]
        first, last = pd.Timestamp(start), pd.Timestamp(end)
        selected = trades.loc[
            (trades.entry_time >= first) & (trades.entry_time < last)
        ]
        weeks = (last - first).total_seconds() / (7 * 86400)
        partitions[name] = _describe(selected.net_r.to_numpy(dtype=float), weeks)
    monte_carlo = [
        tail_miss_simulation(
            values,
            threshold,
            float(probability),
            int(contract["monte_carlo"]["replicates"]),
            int(contract["monte_carlo"]["seed"]) + index,
        )
        for index, probability in enumerate(
            contract["monte_carlo"]["independent_tail_miss_probabilities"]
        )
    ]
    gates = {
        "cap_5r_positive": caps["cap_5r"]["total_r"] > 0,
        "tail_winners_in_every_year": all(
            row["trades"] > 0 for row in tail_by_year.values()
        ),
        "ten_percent_tail_miss_positive_probability_at_least_80pct": next(
            row for row in monte_carlo if row["tail_miss_probability"] == 0.1
        )["probability_total_r_positive"]
        >= 0.8,
        "retrospective_2026_positive": partitions["retrospective_holdout"]["total_r"]
        > 0,
    }
    gates["all_pass"] = all(gates.values())
    return {
        "base": _describe(values, full_weeks),
        "caps": caps,
        "concentration": concentration,
        "tail_threshold_r": threshold,
        "tail_trades": len(tail),
        "tail_sum_r": float(tail.net_r.sum()),
        "tail_by_year": tail_by_year,
        "partitions": partitions,
        "monte_carlo": monte_carlo,
        "assessment_gates": gates,
        "assessment": (
            "TAIL_STRUCTURE_SUPPORTED_EDGE_UNCONFIRMED"
            if gates["all_pass"]
            else "TAIL_STRUCTURE_NOT_ROBUST"
        ),
    }


def _new_holdout(contract: dict) -> tuple[pd.DataFrame, dict, dict]:
    v3 = json.loads(
        (ROOT / "config" / "contract_v3_atr_runner_sizing.json").read_text(
            encoding="utf-8"
        )
    )
    asset_config = v3["data"]["assets"]["sp500"]
    minutes, base_manifest = load_asset_minutes(ROOT, "sp500", asset_config, v3["data"])
    requested_cache = ROOT / contract["new_holdout"]["local_cache"]
    fallback_cache = (
        ROOT
        / ".."
        / "mt5-ea-research-lab"
        / "data"
        / "sp500_exness"
        / "raw"
        / "m1"
        / "2026-09.parquet"
    ).resolve()
    cache = requested_cache if requested_cache.is_file() else fallback_cache
    if not cache.is_file():
        return pd.DataFrame(), {
            "status": "UNAVAILABLE_MT5_IPC_TIMEOUT",
            "requested_start": contract["temporal_partitions"]["new_exness_holdout"][0],
            "requested_end_exclusive": contract["temporal_partitions"]["new_exness_holdout"][1],
        }, base_manifest
    extension = pd.read_parquet(cache)
    extension["time"] = pd.to_datetime(extension["time"], utc=True)
    requested_start, requested_end = map(
        pd.Timestamp, contract["temporal_partitions"]["new_exness_holdout"]
    )
    extension = extension.loc[
        (extension.time >= requested_start) & (extension.time < requested_end)
    ]
    if extension.empty:
        raise ValueError("September cache contains no requested holdout bars")
    combined, cleaning = normalise_minutes(
        pd.concat(
            [
                minutes.reset_index(),
                extension[
                    [
                        "time",
                        "open",
                        "high",
                        "low",
                        "close",
                        "spread",
                        "tick_volume",
                    ]
                ],
            ],
            ignore_index=True,
        )
    )
    last = extension.time.max()
    coverage_end = min(requested_end, last.normalize())
    if coverage_end <= requested_start:
        raise ValueError("September cache has no complete UTC day")
    bars = aggregate_timeframe(combined, "30min", 1)
    features = feature_kernel_outputs(bars, float(asset_config["price_scale"]))
    variants, diagnostics = build_full_history_variants(bars, features)
    trades = build_runner_trades(
        asset="sp500",
        timeframe="30min",
        bars=bars,
        minutes=combined,
        signals=variants["causal_lorentzian"],
        asset_config=asset_config,
        profile=v3["costs"]["sp500"],
        exit_config=v3["exit"],
        evaluation_start=requested_start,
        evaluation_end=coverage_end,
    )
    weeks = (coverage_end - requested_start).total_seconds() / (7 * 86400)
    manifest = {
        "status": (
            "COMPLETE_REQUESTED_WINDOW"
            if coverage_end >= requested_end
            else "PARTIAL_CACHE_AFTER_MT5_IPC_TIMEOUT"
        ),
        "path": str(cache),
        "sha256": sha256_file(cache),
        "rows_in_requested_window": len(extension),
        "first_bar": extension.time.min().isoformat(),
        "last_bar": last.isoformat(),
        "scored_start": requested_start.isoformat(),
        "scored_end_exclusive": coverage_end.isoformat(),
        "duplicate_rows_removed_when_combined": cleaning["duplicate_rows_removed"],
        "causal_label_diagnostic": diagnostics["causal_lorentzian"],
    }
    result = {
        "sample_status": "SUFFICIENT" if len(trades) >= 30 else "INSUFFICIENT_SAMPLE",
        "metrics": (
            _describe(trades.net_r.to_numpy(dtype=float), weeks)
            if not trades.empty
            else _describe(np.array([], dtype=float), weeks)
        ),
        "annualized_interpretation_forbidden": len(trades) < 30,
    }
    return trades, result, {"base_history": base_manifest, "extension": manifest}


def main() -> None:
    contract_path = ROOT / "config" / "contract_v4_tail_robustness.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    ledger_path = ROOT / contract["inputs"]["v3_trade_ledger"]
    if _sha256(ledger_path) != contract["inputs"]["v3_trade_ledger_sha256"]:
        raise ValueError("Frozen v3 ledger hash mismatch")
    trades = pd.read_csv(
        ledger_path, parse_dates=["signal_time", "entry_time", "exit_time"]
    )
    selected = trades.loc[
        trades.asset.eq(contract["inputs"]["asset"])
        & trades.timeframe.eq(contract["inputs"]["timeframe"])
    ].copy()
    historical = _historical_analysis(selected, contract)
    holdout_trades, holdout, source_manifest = _new_holdout(contract)
    output = {
        "study": contract["study"],
        "contract_sha256": _sha256(contract_path),
        "v3_trade_ledger_sha256": _sha256(ledger_path),
        "historical": historical,
        "new_holdout": holdout,
        "interpretation": (
            "Historical tail structure passes the declared diagnostics, "
            "but the edge remains unconfirmed."
            if historical["assessment_gates"]["all_pass"]
            else "Historical tail structure fails at least one declared diagnostic."
        ),
    }
    evidence = ROOT / "evidence" / "v4_tail_robustness"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "summary.json").write_text(
        json.dumps(output, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    (evidence / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    holdout_trades.to_csv(evidence / "new_holdout_trades.csv", index=False)
    print(
        json.dumps(
            {
                "assessment": historical["assessment"],
                "gates": historical["assessment_gates"],
                "new_holdout": holdout,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
