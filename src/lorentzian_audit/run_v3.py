from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from lorentzian_classification.core import calc_atr

from .data import aggregate_timeframe, load_asset_minutes
from .run import _json_default
from .runner import build_runner_trades, simulate_account
from .signals import build_full_history_variants, feature_kernel_outputs
from .statistics import bootstrap_months, max_drawdown, profit_factor

ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _describe(values: np.ndarray, weeks: float) -> dict:
    if len(values) == 0:
        return {
            "trades": 0,
            "trades_per_week": 0.0,
            "total_r": 0.0,
            "mean_r": None,
            "win_rate": None,
            "profit_factor": None,
            "max_drawdown_r": 0.0,
            "total_r_ex_top10": 0.0,
        }
    remove = min(10, len(values))
    keep = np.ones(len(values), dtype=bool)
    keep[np.argsort(values)[-remove:]] = False
    return {
        "trades": len(values),
        "trades_per_week": len(values) / weeks,
        "total_r": float(values.sum()),
        "mean_r": float(values.mean()),
        "median_r": float(np.median(values)),
        "win_rate": float((values > 0).mean()),
        "profit_factor": profit_factor(values),
        "max_drawdown_r": max_drawdown(values),
        "total_r_ex_top10": float(values[keep].sum()),
    }


def _calendar(
    trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[pd.DataFrame, list[dict]]:
    months = pd.period_range(
        start.tz_localize(None),
        (end - pd.Timedelta(days=1)).tz_localize(None),
        freq="M",
    )
    periods = trades["entry_time"].dt.tz_localize(None).dt.to_period("M")
    monthly = (
        trades.assign(month=periods)
        .groupby("month")
        .agg(total_r=("net_r", "sum"), trades=("net_r", "size"))
        .reindex(months, fill_value=0.0)
        .reset_index(names="month")
    )
    monthly["month"] = monthly["month"].astype(str)
    blocks: list[dict] = []
    for year in (2024, 2025, 2026):
        selected = trades.loc[trades.entry_time.dt.year.eq(year)]
        blocks.append(
            {
                "year": year,
                "trades": len(selected),
                "total_r": float(selected.net_r.sum()),
            }
        )
    return monthly, blocks


def _baseline_r(
    v2_trades: pd.DataFrame,
    asset: str,
    timeframe: str,
    bars: pd.DataFrame,
    contract: dict,
    weeks: float,
) -> dict:
    selected = v2_trades.loc[
        v2_trades.asset.eq(asset)
        & v2_trades.timeframe.eq(timeframe)
        & v2_trades.scope.eq("full_history")
        & v2_trades.variant.eq("causal_lorentzian")
    ].copy()
    atr = calc_atr(
        bars.high.astype(float).tolist(),
        bars.low.astype(float).tolist(),
        bars.close.astype(float).tolist(),
        int(contract["exit"]["atr_period"]),
    )
    atr_by_time = pd.Series(atr, index=bars.index)
    risk = (
        atr_by_time.reindex(pd.DatetimeIndex(selected.signal_time)).to_numpy(dtype=float)
        * float(contract["exit"]["initial_stop_atr"])
        + float(contract["costs"][asset]["slippage_side"])
        + float(contract["costs"][asset]["commission_round_trip_price"])
    )
    values = selected.base_net_points.to_numpy(dtype=float) / risk
    return _describe(values[np.isfinite(values)], weeks)


def _gate(assets: dict, contract: dict) -> dict[str, bool]:
    primary = contract["data"]["primary_timeframe"]
    names = tuple(contract["data"]["assets"])

    def cell(asset: str) -> dict:
        return assets[asset]["timeframes"][primary]

    gate: dict[str, bool] = {}
    gate["runner_beats_four_bar_total_r_and_pf_both"] = all(
        cell(asset)["runner"]["total_r"] > cell(asset)["four_bar_baseline"]["total_r"]
        and (cell(asset)["runner"]["profit_factor"] or 0)
        > (cell(asset)["four_bar_baseline"]["profit_factor"] or 0)
        for asset in names
    )
    gate["runner_pf_at_least_1_10_both"] = all(
        (cell(asset)["runner"]["profit_factor"] or 0) >= 1.10 for asset in names
    )
    gate["all_years_positive_both"] = all(
        all(block["total_r"] > 0 for block in cell(asset)["annual"])
        for asset in names
    )
    gate["positive_ex_top10_both"] = all(
        cell(asset)["runner"]["total_r_ex_top10"] > 0 for asset in names
    )
    gate["bootstrap_lower_positive_both"] = all(
        cell(asset)["monthly_bootstrap"]["ci95"][0] > 0 for asset in names
    )
    gate["usd500_risk1_half_executable_both"] = all(
        next(
            row
            for row in cell(asset)["accounts"]
            if row["initial_balance_usd"] == 500 and row["risk_percent"] == 1
        )["executable_fraction"]
        >= 0.5
        for asset in names
    )
    gate["no_account_ruin"] = all(
        not account["ruined"]
        for asset_data in assets.values()
        for timeframe_data in asset_data["timeframes"].values()
        for account in timeframe_data["accounts"]
    )
    gate["all_pass"] = all(gate.values())
    return gate


def main() -> None:
    contract_path = ROOT / "config" / "contract_v3_atr_runner_sizing.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    evidence = ROOT / "evidence" / "v3_atr_runner_sizing"
    evidence.mkdir(parents=True, exist_ok=True)
    evaluation_start = pd.Timestamp(contract["data"]["evaluation_start"])
    evaluation_end = pd.Timestamp(contract["data"]["evaluation_end_exclusive"])
    weeks = (evaluation_end - evaluation_start).total_seconds() / (7 * 86400)
    v2_trades = pd.read_csv(
        ROOT / "evidence" / "v2_lower_timeframes" / "trades.csv.gz",
        parse_dates=["signal_time", "entry_time", "exit_time"],
    )
    all_trades: list[pd.DataFrame] = []
    all_accounts: list[pd.DataFrame] = []
    all_monthly: list[pd.DataFrame] = []
    source_manifest: dict[str, dict] = {}
    assets_result: dict[str, dict] = {}

    for asset_number, (asset, asset_config) in enumerate(
        contract["data"]["assets"].items()
    ):
        minutes, source_diag = load_asset_minutes(
            ROOT, asset, asset_config, contract["data"]
        )
        source_manifest[asset] = source_diag
        asset_result: dict[str, dict] = {"timeframes": {}}
        for timeframe_number, timeframe in enumerate(contract["data"]["timeframe_order"]):
            bars = aggregate_timeframe(
                minutes,
                timeframe,
                int(contract["data"]["minimum_m1_rows_per_bar"]),
            )
            features = feature_kernel_outputs(bars, float(asset_config["price_scale"]))
            variants, diagnostics = build_full_history_variants(bars, features)
            signals = variants[contract["signal"]["variant"]]
            trades = build_runner_trades(
                asset=asset,
                timeframe=timeframe,
                bars=bars,
                minutes=minutes,
                signals=signals,
                asset_config=asset_config,
                profile=contract["costs"][asset],
                exit_config=contract["exit"],
                evaluation_start=evaluation_start,
                evaluation_end=evaluation_end,
            )
            if trades.empty:
                raise ValueError(f"No runner trades for {asset} {timeframe}")
            all_trades.append(trades)
            values = trades.net_r.to_numpy(dtype=float)
            monthly, annual = _calendar(trades, evaluation_start, evaluation_end)
            monthly.insert(0, "timeframe", timeframe)
            monthly.insert(0, "asset", asset)
            all_monthly.append(monthly)
            accounts: list[dict] = []
            for balance in contract["account_simulation"]["initial_balances_usd"]:
                for risk_percent in contract["account_simulation"][
                    "risk_percent_before_trade"
                ]:
                    account_ledger, account_summary = simulate_account(
                        trades,
                        asset_config,
                        float(balance),
                        float(risk_percent),
                        evaluation_start,
                        evaluation_end,
                    )
                    account_ledger.insert(0, "risk_percent", risk_percent)
                    account_ledger.insert(0, "initial_balance_usd", balance)
                    account_ledger.insert(0, "timeframe", timeframe)
                    account_ledger.insert(0, "asset", asset)
                    all_accounts.append(account_ledger)
                    accounts.append(account_summary)
            asset_result["timeframes"][timeframe] = {
                "runner": _describe(values, weeks),
                "four_bar_baseline": _baseline_r(
                    v2_trades, asset, timeframe, bars, contract, weeks
                ),
                "annual": annual,
                "monthly_bootstrap": bootstrap_months(
                    monthly.total_r.to_numpy(dtype=float),
                    5000,
                    20260925 + asset_number * 100 + timeframe_number,
                ),
                "positive_month_fraction": float((monthly.total_r > 0).mean()),
                "long_total_r": float(trades.loc[trades.direction.eq(1), "net_r"].sum()),
                "short_total_r": float(
                    trades.loc[trades.direction.eq(-1), "net_r"].sum()
                ),
                "trail_activation_fraction": float(trades.trail_activated.mean()),
                "median_holding_hours": float(trades.holding_hours.median()),
                "exit_reasons": {
                    str(key): int(value)
                    for key, value in trades.exit_reason.value_counts().items()
                },
                "causal_label_diagnostic": diagnostics["causal_lorentzian"],
                "accounts": accounts,
            }
        assets_result[asset] = asset_result

    gates = _gate(assets_result, contract)
    verdict = (
        contract["verdicts"]["pass"] if gates["all_pass"] else contract["verdicts"]["fail"]
    )
    output = {
        "study": contract["study"],
        "contract_sha256": _sha256(contract_path),
        "v2_trade_ledger_sha256": _sha256(
            ROOT / "evidence" / "v2_lower_timeframes" / "trades.csv.gz"
        ),
        "verdict": verdict,
        "gates": gates,
        "evaluation": {
            "start": evaluation_start.isoformat(),
            "end_exclusive": evaluation_end.isoformat(),
            "weeks": weeks,
        },
        "limitations": [
            "Historical margin availability is not modelled.",
            "Swap is not modelled for trades crossing rollover.",
            "Account sizing filters a frozen theoretical trade ledger; "
            "a skipped trade does not create an alternate re-entry path.",
        ],
        "assets": assets_result,
    }
    pd.concat(all_trades, ignore_index=True).to_csv(
        evidence / "trades.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    pd.concat(all_accounts, ignore_index=True).to_csv(
        evidence / "accounts.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    pd.concat(all_monthly, ignore_index=True).to_csv(
        evidence / "monthly.csv", index=False
    )
    (evidence / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    (evidence / "summary.json").write_text(
        json.dumps(output, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "gates": gates}, indent=2))


if __name__ == "__main__":
    main()
