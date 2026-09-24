from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .backtest import build_trades
from .data import aggregate_timeframe, load_asset_minutes
from .run import _blocks, _controls, _json_default, _sha256
from .signals import build_full_history_variants, feature_kernel_outputs, official_outputs
from .statistics import bootstrap_months, calendar_tables, summary

ROOT = Path(__file__).resolve().parents[2]
TRADE_COLUMNS = [
    "asset",
    "variant",
    "trade_id",
    "signal_time",
    "entry_time",
    "exit_time",
    "holding_hours",
    "entry_bid",
    "exit_bid",
    "entry_spread_points",
    "exit_spread_points",
    "direction",
    "gross_points",
    "gross_bps",
    "base_spread_points",
    "base_slippage_points",
    "base_commission_points",
    "base_net_points",
    "base_net_bps",
    "stress_net_points",
    "stress_net_bps",
]


def _observed_duration(
    bars: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[float, int]:
    selected = bars.loc[(bars.index >= start) & (bars.index < end)]
    weeks = max((end - start).total_seconds() / (7 * 86400), 1 / 7)
    active_days = int(pd.Index(selected.index.normalize()).nunique())
    return weeks, active_days


def _execution_diagnostics(trades: pd.DataFrame, bars: pd.DataFrame) -> dict:
    if trades.empty:
        return {
            "first_entry": None,
            "last_entry": None,
            "median_holding_hours": None,
            "maximum_holding_hours": None,
            "minimum_signal_m1_rows": None,
            "minimum_entry_m1_rows": None,
            "minimum_exit_m1_rows": None,
        }
    signals = bars["m1_rows"].reindex(pd.DatetimeIndex(trades["signal_time"]))
    entries = bars["m1_rows"].reindex(pd.DatetimeIndex(trades["entry_time"]))
    exits = bars["m1_rows"].reindex(pd.DatetimeIndex(trades["exit_time"]))
    return {
        "first_entry": trades["entry_time"].min().isoformat(),
        "last_entry": trades["entry_time"].max().isoformat(),
        "median_holding_hours": float(trades["holding_hours"].median()),
        "maximum_holding_hours": float(trades["holding_hours"].max()),
        "minimum_signal_m1_rows": int(signals.min()),
        "minimum_entry_m1_rows": int(entries.min()),
        "minimum_exit_m1_rows": int(exits.min()),
    }


def _with_activity(metric: dict, active_days: int) -> dict:
    metric["trades_per_active_day"] = (
        metric["trades"] / active_days if active_days else 0.0
    )
    return metric


def _measure_variant(
    *,
    asset: str,
    asset_config: dict,
    timeframe: str,
    scope: str,
    variant: str,
    bars: pd.DataFrame,
    signals: pd.DataFrame,
    contract: dict,
    start: pd.Timestamp,
    end: pd.Timestamp,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    trades = build_trades(
        asset,
        variant,
        bars,
        signals,
        asset_config,
        contract["costs"][asset],
        start,
        end,
    )
    if trades.empty:
        trades = pd.DataFrame(columns=TRADE_COLUMNS)
    trades.insert(1, "timeframe", timeframe)
    trades.insert(2, "scope", scope)
    weeks, active_days = _observed_duration(bars, start, end)
    base_values = trades["base_net_bps"].to_numpy(dtype=float)
    stress_values = trades["stress_net_bps"].to_numpy(dtype=float)
    gross_values = trades["gross_bps"].to_numpy(dtype=float)
    top_n = int(contract["statistics"]["top_trades_removed"])
    monthly, annual = calendar_tables(trades, "base_net_bps", start, end)
    for table in (monthly, annual):
        table.insert(0, "variant", variant)
        table.insert(0, "scope", scope)
        table.insert(0, "timeframe", timeframe)
        table.insert(0, "asset", asset)
    result = {
        "scope": scope,
        "evaluation_start": start.isoformat(),
        "evaluation_end_exclusive": end.isoformat(),
        "observed_weeks": weeks,
        "active_days": active_days,
        "gross": _with_activity(summary(gross_values, weeks, top_n), active_days),
        "base": _with_activity(summary(base_values, weeks, top_n), active_days),
        "stress": _with_activity(summary(stress_values, weeks, top_n), active_days),
        "blocks": _blocks(trades, contract["statistics"]["year_blocks"]),
        "long_base_net_bps": float(
            trades.loc[trades["direction"] == 1, "base_net_bps"].sum()
        ),
        "short_base_net_bps": float(
            trades.loc[trades["direction"] == -1, "base_net_bps"].sum()
        ),
        "positive_month_fraction": float((monthly["net_bps"] > 0).mean()),
        "execution_diagnostics": _execution_diagnostics(trades, bars),
        "monthly_bootstrap": bootstrap_months(
            monthly["net_bps"].to_numpy(dtype=float),
            int(contract["statistics"]["monthly_block_bootstrap_replicates"]),
            seed,
        ),
        "same_window_controls": _controls(
            trades,
            float(asset_config["point"]),
            contract["costs"][asset]["base"],
            weeks,
            int(contract["statistics"]["random_direction_replicates"]),
            seed,
        ),
    }
    return trades, monthly, annual, result


def _primary_gate(assets: dict, contract: dict) -> dict[str, bool]:
    primary = contract["data"]["primary_timeframe"]
    candidate = "causal_lorentzian"
    asset_names = tuple(contract["data"]["assets"])

    def cell(asset: str, variant: str = candidate) -> dict:
        return assets[asset]["timeframes"][primary]["variants"][variant]

    gates: dict[str, bool] = {}
    gates["positive_pf_at_least_1_10_both"] = all(
        cell(asset)["base"]["net_bps"] > 0
        and (cell(asset)["base"]["profit_factor"] or 0) >= 1.10
        for asset in asset_names
    )
    gates["beats_all_simpler_comparators_both"] = all(
        all(
            cell(asset)["base"]["net_bps"]
            > cell(asset, comparator)["base"]["net_bps"]
            for comparator in (
                "causal_euclidean",
                "simple_momentum4",
                "filter_only_kernel",
            )
        )
        for asset in asset_names
    )
    gates["minimum_500_trades_both"] = all(
        cell(asset)["base"]["trades"] >= 500 for asset in asset_names
    )
    gates["all_year_blocks_positive_both"] = all(
        all(block["net_bps"] > 0 for block in cell(asset)["blocks"])
        for asset in asset_names
    )
    gates["positive_ex_top10_both"] = all(
        cell(asset)["base"]["net_bps_ex_top10"] > 0 for asset in asset_names
    )
    gates["bootstrap_lower_bound_positive_both"] = all(
        cell(asset)["monthly_bootstrap"]["ci95"][0] > 0 for asset in asset_names
    )
    gates["stress_positive_both"] = all(
        cell(asset)["stress"]["net_bps"] > 0 for asset in asset_names
    )
    gates["random_direction_p_below_0_05_both"] = all(
        cell(asset)["same_window_controls"]["random_direction"][
            "one_sided_p_random_at_least_actual"
        ]
        < 0.05
        for asset in asset_names
    )
    gates["all_pass"] = all(gates.values())
    return gates


def main() -> None:
    contract_path = ROOT / "config" / "contract_v2_lower_timeframes.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    evidence = ROOT / "evidence" / "v2_lower_timeframes"
    evidence.mkdir(parents=True, exist_ok=True)
    eval_start = pd.Timestamp(contract["data"]["evaluation_start"])
    eval_end = pd.Timestamp(contract["data"]["evaluation_end_exclusive"])
    recent_input = int(contract["official_recent_diagnostic"]["total_input_bars"])
    context_bars = int(contract["official_recent_diagnostic"]["context_bars"])
    all_trades: list[pd.DataFrame] = []
    all_monthly: list[pd.DataFrame] = []
    all_annual: list[pd.DataFrame] = []
    source_manifest: dict[str, dict] = {}
    result: dict[str, dict] = {}

    for asset_number, (asset, asset_config) in enumerate(
        contract["data"]["assets"].items()
    ):
        minutes, source_diag = load_asset_minutes(
            ROOT, asset, asset_config, contract["data"]
        )
        source_manifest[asset] = source_diag
        asset_result: dict[str, dict] = {"source": source_diag, "timeframes": {}}

        for timeframe_number, timeframe in enumerate(contract["data"]["timeframe_order"]):
            bars = aggregate_timeframe(
                minutes,
                timeframe,
                int(contract["data"]["minimum_m1_rows_per_bar"]),
            )
            timeframe_result: dict[str, dict] = {
                "bars": {
                    "count": len(bars),
                    "first": bars.index.min().isoformat(),
                    "last": bars.index.max().isoformat(),
                    "m1_rows_min": int(bars["m1_rows"].min()),
                    "m1_rows_median": float(bars["m1_rows"].median()),
                    "m1_rows_max": int(bars["m1_rows"].max()),
                },
                "signal_diagnostics": {},
                "variants": {},
            }

            feature_kernel = feature_kernel_outputs(
                bars, float(asset_config["price_scale"])
            )
            full_variants, signal_diagnostics = build_full_history_variants(
                bars, feature_kernel
            )
            timeframe_result["signal_diagnostics"] = signal_diagnostics
            for variant_number, (variant, signals) in enumerate(full_variants.items()):
                seed = (
                    int(contract["statistics"]["seed"])
                    + asset_number * 1000
                    + timeframe_number * 100
                    + variant_number
                )
                trades, monthly, annual, measured = _measure_variant(
                    asset=asset,
                    asset_config=asset_config,
                    timeframe=timeframe,
                    scope="full_history",
                    variant=variant,
                    bars=bars,
                    signals=signals,
                    contract=contract,
                    start=eval_start,
                    end=eval_end,
                    seed=seed,
                )
                all_trades.append(trades)
                all_monthly.append(monthly)
                all_annual.append(annual)
                timeframe_result["variants"][variant] = measured

            recent_bars = bars.tail(recent_input)
            if len(recent_bars) <= context_bars + 5:
                raise ValueError(f"Insufficient recent bars for {asset} {timeframe}")
            official = official_outputs(recent_bars, float(asset_config["price_scale"]))
            recent_start = max(eval_start, recent_bars.index[context_bars])
            recent_end = min(
                eval_end,
                recent_bars.index[-1] + pd.Timedelta(timeframe),
            )
            official_signals = official[
                ["prediction", "direction", "start_long", "start_short"]
            ].copy()
            seed = (
                int(contract["statistics"]["seed"])
                + asset_number * 1000
                + timeframe_number * 100
                + 90
            )
            trades, monthly, annual, measured = _measure_variant(
                asset=asset,
                asset_config=asset_config,
                timeframe=timeframe,
                scope="recent_2000_scored_bars",
                variant="official_original_recent",
                bars=recent_bars,
                signals=official_signals,
                contract=contract,
                start=recent_start,
                end=recent_end,
                seed=seed,
            )
            all_trades.append(trades)
            all_monthly.append(monthly)
            all_annual.append(annual)
            timeframe_result["variants"]["official_original_recent"] = measured
            timeframe_result["official_recent_diagnostic"] = {
                "input_bars": len(recent_bars),
                "context_bars": context_bars,
                "nominal_scored_bars": len(recent_bars) - context_bars,
                "start": recent_start.isoformat(),
                "end_exclusive": recent_end.isoformat(),
            }
            asset_result["timeframes"][timeframe] = timeframe_result
        result[asset] = asset_result

    gates = _primary_gate(result, contract)
    verdict = (
        contract["verdicts"]["pass"] if gates["all_pass"] else contract["verdicts"]["fail"]
    )
    output = {
        "study": contract["study"],
        "contract_sha256": _sha256(contract_path),
        "verdict": verdict,
        "gates": gates,
        "evaluation": {
            "start": eval_start.isoformat(),
            "end_exclusive": eval_end.isoformat(),
            "primary_timeframe": contract["data"]["primary_timeframe"],
        },
        "assets": result,
    }
    pd.concat(all_trades, ignore_index=True).to_csv(
        evidence / "trades.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    pd.concat(all_monthly, ignore_index=True).to_csv(
        evidence / "monthly.csv", index=False
    )
    pd.concat(all_annual, ignore_index=True).to_csv(
        evidence / "annual.csv", index=False
    )
    (evidence / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    (evidence / "summary.json").write_text(
        json.dumps(output, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"verdict": verdict, "gates": gates, "summary": str(evidence / "summary.json")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
