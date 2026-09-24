from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import build_trades, reprice_directions
from .data import load_asset_h4
from .signals import build_variants, official_outputs
from .statistics import bootstrap_months, calendar_tables, summary

ROOT = Path(__file__).resolve().parents[2]


def _json_default(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, (pd.Timestamp, pd.Period)):
        return str(value)
    raise TypeError(type(value).__name__)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _controls(
    trades: pd.DataFrame,
    point: float,
    profile: dict,
    weeks: float,
    replicates: int,
    seed: int,
) -> dict:
    if trades.empty:
        return {
            name: summary(np.array([]), weeks)
            for name in ("actual", "opposite", "always_long", "always_short")
        }
    actual_direction = trades["direction"].to_numpy(dtype=int)
    directions = {
        "actual": actual_direction,
        "opposite": -actual_direction,
        "always_long": np.ones(len(trades), dtype=int),
        "always_short": -np.ones(len(trades), dtype=int),
    }
    result = {
        name: summary(reprice_directions(trades, values, point, profile), weeks)
        for name, values in directions.items()
    }
    long_values = reprice_directions(trades, np.ones(len(trades), dtype=int), point, profile)
    short_values = reprice_directions(trades, -np.ones(len(trades), dtype=int), point, profile)
    rng = np.random.default_rng(seed)
    coin = rng.integers(0, 2, size=(replicates, len(trades)), dtype=np.int8)
    random_totals = np.where(coin == 1, long_values, short_values).sum(axis=1)
    actual_total = float(trades["base_net_bps"].sum())
    result["random_direction"] = {
        "replicates": replicates,
        "median_net_bps": float(np.median(random_totals)),
        "ci95_net_bps": [
            float(np.quantile(random_totals, 0.025)),
            float(np.quantile(random_totals, 0.975)),
        ],
        "actual_percentile": float((random_totals < actual_total).mean()),
        "one_sided_p_random_at_least_actual": float(
            (1 + np.sum(random_totals >= actual_total)) / (replicates + 1)
        ),
    }
    return result


def _blocks(trades: pd.DataFrame, blocks: list[list[str]]) -> list[dict]:
    output: list[dict] = []
    for start, end in blocks:
        first = pd.Timestamp(start, tz="UTC")
        last = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
        selected = trades.loc[(trades["entry_time"] >= first) & (trades["entry_time"] < last)]
        output.append(
            {
                "start": start,
                "end": end,
                "trades": len(selected),
                "net_bps": float(selected["base_net_bps"].sum()),
            }
        )
    return output


def _gate(summary_data: dict, contract: dict) -> dict:
    assets = tuple(contract["data"]["assets"])
    gate: dict[str, bool] = {}
    gate["official_positive_both"] = all(
        summary_data[asset]["variants"]["official_original"]["base"]["net_bps"] > 0
        and (summary_data[asset]["variants"]["official_original"]["base"]["profit_factor"] or 0)
        > 1
        for asset in assets
    )
    gate["causal_positive_both"] = all(
        summary_data[asset]["variants"]["causal_lorentzian"]["base"]["net_bps"] > 0
        and (summary_data[asset]["variants"]["causal_lorentzian"]["base"]["profit_factor"] or 0)
        > 1
        for asset in assets
    )
    gate["beats_euclidean_and_momentum_both"] = all(
        summary_data[asset]["variants"]["causal_lorentzian"]["base"]["net_bps"]
        > summary_data[asset]["variants"]["causal_euclidean"]["base"]["net_bps"]
        and summary_data[asset]["variants"]["causal_lorentzian"]["base"]["net_bps"]
        > summary_data[asset]["variants"]["simple_momentum4"]["base"]["net_bps"]
        for asset in assets
    )
    gate["minimum_100_trades_both"] = all(
        summary_data[asset]["variants"]["causal_lorentzian"]["base"]["trades"] >= 100
        for asset in assets
    )
    gate["both_blocks_positive_both_assets"] = all(
        all(
            block["net_bps"] > 0
            for block in summary_data[asset]["variants"]["causal_lorentzian"]["blocks"]
        )
        for asset in assets
    )
    gate["positive_ex_top5_both"] = all(
        summary_data[asset]["variants"]["causal_lorentzian"]["base"]["net_bps_ex_top5"] > 0
        for asset in assets
    )
    gate["bootstrap_lower_bound_positive_both"] = all(
        summary_data[asset]["variants"]["causal_lorentzian"]["monthly_bootstrap"]["ci95"][0] > 0
        for asset in assets
    )
    gate["stress_positive_both"] = all(
        summary_data[asset]["variants"]["causal_lorentzian"]["stress"]["net_bps"] > 0
        for asset in assets
    )
    gate["all_pass"] = all(gate.values())
    return gate


def main() -> None:
    contract_path = ROOT / "config" / "contract_v1.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    evidence = ROOT / "evidence" / "v1"
    evidence.mkdir(parents=True, exist_ok=True)
    eval_start = pd.Timestamp(contract["data"]["evaluation_start"])
    eval_end = pd.Timestamp(contract["data"]["evaluation_end_exclusive"])
    weeks = (eval_end - eval_start).total_seconds() / (7 * 86400)
    all_trades: list[pd.DataFrame] = []
    all_monthly: list[pd.DataFrame] = []
    all_annual: list[pd.DataFrame] = []
    source_manifest: dict[str, dict] = {}
    result: dict[str, dict] = {}

    for asset_number, (asset, asset_config) in enumerate(contract["data"]["assets"].items()):
        bars, source_diag = load_asset_h4(ROOT, asset, asset_config, contract["data"])
        source_manifest[asset] = source_diag
        official = official_outputs(bars, float(asset_config["price_scale"]))
        variants, signal_diagnostics = build_variants(bars, official)
        asset_result: dict[str, dict] = {
            "source": source_diag,
            "signal_diagnostics": signal_diagnostics,
            "variants": {},
        }

        for variant_number, (variant, signals) in enumerate(variants.items()):
            trades = build_trades(
                asset,
                variant,
                bars,
                signals,
                asset_config,
                contract["costs"][asset],
                eval_start,
                eval_end,
            )
            if trades.empty:
                trades = pd.DataFrame(
                    columns=[
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
                )
            all_trades.append(trades)
            base_values = trades["base_net_bps"].to_numpy(dtype=float)
            stress_values = trades["stress_net_bps"].to_numpy(dtype=float)
            gross_values = trades["gross_bps"].to_numpy(dtype=float)
            monthly, annual = calendar_tables(trades, "base_net_bps", eval_start, eval_end)
            monthly.insert(0, "variant", variant)
            monthly.insert(0, "asset", asset)
            annual.insert(0, "variant", variant)
            annual.insert(0, "asset", asset)
            all_monthly.append(monthly)
            all_annual.append(annual)
            variant_result = {
                "gross": summary(gross_values, weeks),
                "base": summary(base_values, weeks),
                "stress": summary(stress_values, weeks),
                "blocks": _blocks(trades, contract["statistics"]["blocks"]),
                "long_base_net_bps": float(
                    trades.loc[trades["direction"] == 1, "base_net_bps"].sum()
                ),
                "short_base_net_bps": float(
                    trades.loc[trades["direction"] == -1, "base_net_bps"].sum()
                ),
                "positive_month_fraction": float((monthly["net_bps"] > 0).mean()),
                "monthly_bootstrap": bootstrap_months(
                    monthly["net_bps"].to_numpy(dtype=float),
                    int(contract["statistics"]["monthly_block_bootstrap_replicates"]),
                    int(contract["statistics"]["seed"]) + asset_number * 100 + variant_number,
                ),
                "same_window_controls": _controls(
                    trades,
                    float(asset_config["point"]),
                    contract["costs"][asset]["base"],
                    weeks,
                    int(contract["statistics"]["random_direction_replicates"]),
                    int(contract["statistics"]["seed"]) + asset_number * 100 + variant_number,
                ),
            }
            asset_result["variants"][variant] = variant_result
        result[asset] = asset_result

    gates = _gate(result, contract)
    verdict = (
        contract["verdicts"]["pass"] if gates["all_pass"] else contract["verdicts"]["fail"]
    )
    output = {
        "study": contract["study"],
        "contract_sha256": _sha256(contract_path),
        "verdict": verdict,
        "gates": gates,
        "evaluation": {
            "start": str(eval_start),
            "end_exclusive": str(eval_end),
            "weeks": weeks,
        },
        "assets": result,
    }
    trades_output = pd.concat(all_trades, ignore_index=True)
    trades_output.to_csv(
        evidence / "trades.csv.gz", index=False, compression={"method": "gzip", "mtime": 0}
    )
    pd.concat(all_monthly, ignore_index=True).to_csv(evidence / "monthly.csv", index=False)
    pd.concat(all_annual, ignore_index=True).to_csv(evidence / "annual.csv", index=False)
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
