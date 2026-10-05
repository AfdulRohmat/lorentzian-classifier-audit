"""Re-audit all native evidence and write the comparison, never simulate fills."""
# ruff: noqa: E501 -- long generated Markdown paragraphs and table rows

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from lorentzian_audit.native_swing import validate_coverage
from lorentzian_audit.native_vwap import audit_vwap, gate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trade_table(folder):
    deals = pd.read_csv(folder / "deals.csv.gz")
    signals = pd.read_csv(folder / "signals.csv.gz")
    events = pd.read_csv(folder / "events.csv.gz")
    budgets = events.loc[events.event.eq("ENTRY_PLANNED_RISK")].set_index("time").value
    rows = []
    for _, group in deals.groupby("position_id"):
        entry = group.loc[group.entry.eq(0)].iloc[0]
        stamp = int(entry.time)
        signal = signals.loc[signals.time <= stamp // 1800 * 1800 - 1800].iloc[-1]
        side = 1 if entry["type"] == 0 else -1
        valid = bool(signal.vwap_valid)
        z = float(signal.z)
        bucket = (
            "undefined"
            if not valid
            else "beyond_3"
            if abs(z) > 3
            else "center"
            if abs(z) < 1
            else "toward_vwap"
            if gate(z, valid, side)
            else "away_from_vwap"
        )
        net = float(group[["profit", "commission", "fee", "swap"]].to_numpy().sum())
        rows.append(
            dict(
                entry_time=stamp,
                exit_time=int(group.time.max()),
                side=side,
                volume=float(entry.volume),
                net=net,
                r=net / float(budgets.loc[stamp]),
                z=z,
                bucket=bucket,
                gate_allowed=bool(gate(z, valid, side)),
            )
        )
    return pd.DataFrame(
        rows,
        columns=[
            "entry_time",
            "exit_time",
            "side",
            "volume",
            "net",
            "r",
            "z",
            "bucket",
            "gate_allowed",
        ],
    )


def net_metrics(trades):
    win = trades.loc[trades.net.gt(0), "net"].sum()
    loss = -trades.loc[trades.net.lt(0), "net"].sum()
    return dict(
        net_profit_factor=float(win / loss) if loss > 0 else None,
        net_win_rate=float(trades.net.gt(0).mean() * 100) if len(trades) else None,
    )


def bootstrap_difference(off_dir, on_dir, capital, seed=1006):
    index = pd.date_range("2026-01-01", "2026-08-31", tz="UTC")
    values = []
    for folder in (off_dir, on_dir):
        d = pd.read_csv(folder / "deals.csv.gz")
        d["net"] = d[["profit", "commission", "fee", "swap"]].sum(axis=1)
        d["day"] = pd.to_datetime(d.time, unit="s", utc=True).dt.normalize()
        values.append(d.groupby("day").net.sum().reindex(index, fill_value=0).to_numpy())
    diff = values[1] - values[0]
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(diff), size=(2000, (len(diff) + 6) // 7))
    picks = ((starts[..., None] + np.arange(7)) % len(diff)).reshape(2000, -1)[:, : len(diff)]
    sums = diff[picks].sum(axis=1) / capital * 100
    lo, hi = np.quantile(sums, [0.025, 0.975])
    return dict(
        delta_return_pp=float(diff.sum() / capital * 100),
        block_low_pp=float(lo),
        block_high_pp=float(hi),
    )


def fmt(x, digits=2):
    return "n/a" if x is None or pd.isna(x) else f"{x:,.{digits}f}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    rows = json.loads((args.evidence / "frozen_matrix.json").read_text())
    records, trades_by_tag, raw_by_tag = [], {}, {}
    stream_pool = {}
    for row in rows:
        folder = args.evidence / row["tag"]
        saved = json.loads((folder / "result.json").read_text())
        stats = dict(pd.read_csv(folder / "stats.csv.gz").itertuples(index=False, name=None))
        signals = pd.read_csv(folder / "signals.csv.gz")
        deals, events = (
            pd.read_csv(folder / "deals.csv.gz"),
            pd.read_csv(folder / "events.csv.gz"),
        )
        result = audit_vwap(stats, deals, events, signals)
        for field in (
            "net_profit",
            "trades",
            "final_balance",
            "equity_dd_percent",
            "raw_starts",
        ):
            if abs(float(result[field]) - float(saved[field])) > 1e-8:
                raise ValueError(f"Saved result drift {row['tag']} {field}")
        result.update(row)
        result.update(
            {
                key: saved[key]
                for key in ("ea_sha256", "indicator_sha256", "report_100_percent_real_ticks")
            }
        )
        t = trade_table(folder)
        result.update(net_metrics(t))
        if row["fixed_minimum_lot"]:
            result["losses_exceeding_1pct_reference"] = result[
                "losses_exceeding_nominal_budget"
            ]
            result["losses_exceeding_nominal_budget"] = None
        trades_by_tag[row["tag"]] = t
        signal_bytes = gzip.decompress((folder / "signals.csv.gz").read_bytes())
        signal_hash = hashlib.sha256(signal_bytes).hexdigest()
        raw_by_tag[row["tag"]] = stream_pool.setdefault(signal_hash, signal_bytes)
        records.append(result)
    primary = [r for r in records if not r["smoke"]]
    legacy_checks = []
    for r in primary:
        if (
            r["symbol"] != "US500_x100"
            or r["model_kind"]
            or r["use_vwap"]
            or r["intraday"]
            or r["sizing"] < 2
        ):
            continue
        old = (
            args.evidence.parent
            / "native_x100_swing_2026"
            / f"lcs26_k3_b{r['balance']}_r{r['sizing']}"
        )
        if gzip.decompress((old / "deals.csv.gz").read_bytes()) != gzip.decompress(
            (args.evidence / r["tag"] / "deals.csv.gz").read_bytes()
        ):
            raise ValueError(f"Legacy k3 x100 deal regression: {r['tag']}")
        legacy_checks.append(r["tag"])
    if len(primary) != 288 or len({r["tag"] for r in primary}) != 288:
        raise ValueError("Full frozen matrix not present")
    if (
        len({r["ea_sha256"] for r in records}) != 1
        or len({r["indicator_sha256"] for r in records}) != 1
    ):
        raise ValueError("Mixed binary builds in primary evidence")
    coverage = {}
    prefixes = []
    for symbol in ("US500", "US500_x100"):
        initial = {
            (r["native_history_first"], r["initial_history_bars"])
            for r in records
            if r["symbol"] == symbol
        }
        if len(initial) != 1:
            raise ValueError("Model runs did not share chart history")
        for model in (0, 1):
            group = [r for r in primary if r["symbol"] == symbol and r["model_kind"] == model]
            reference = max(group, key=lambda r: r["last_tick"])
            if int(reference["last_tick"]) < int(
                pd.Timestamp("2026-08-31 20:00", tz="UTC").timestamp()
            ):
                raise ValueError("No complete August endpoint")
            for r in group:
                status = validate_coverage(
                    r,
                    pd.read_csv(args.evidence / r["tag"] / "deals.csv.gz"),
                    raw_by_tag[r["tag"]],
                    raw_by_tag[reference["tag"]],
                    reference,
                )
                r["coverage"] = status
                coverage[r["tag"]] = status
            smoke = next(
                r
                for r in records
                if r["smoke"] and r["symbol"] == symbol and r["model_kind"] == model
            )
            if not raw_by_tag[reference["tag"]].startswith(raw_by_tag[smoke["tag"]]):
                raise ValueError("Full replay changed January signal prefix")
            prefixes.append(
                dict(
                    symbol=symbol,
                    model=model,
                    january_prefix="PASS",
                    first_history=reference["native_history_first"],
                    initial_bars=reference["initial_history_bars"],
                )
            )
    df = pd.DataFrame(primary)
    lookup = {r["tag"]: r for r in primary}
    market_cols = [
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "real_volume",
        "atr",
        "vwap",
        "sigma",
        "z",
        "vwap_valid",
        "online",
    ]
    for suffix in ("u", "x"):
        paired_inputs = [
            pd.read_csv(
                args.evidence / f"lcv28_{suffix}_m{model}_v0_i0_b3000_r0/signals.csv.gz"
            )[market_cols]
            for model in (0, 1)
        ]
        if not paired_inputs[0].equals(paired_inputs[1]):
            raise ValueError(f"Model comparison market/ATR/VWAP input drift: {suffix}")
    cross_symbol = []
    for model in (0, 1):
        observed = []
        for suffix in ("u", "x"):
            data = pd.read_csv(
                args.evidence / f"lcv28_{suffix}_m{model}_v0_i0_b3000_r0/signals.csv.gz"
            )
            observed.append(data.loc[data.online.eq(1)].set_index("time"))
        a, b = observed
        joined = a.join(b, how="inner", lsuffix="_u", rsuffix="_x")
        record = dict(
            model=model, overlap_bars=len(joined), us500_bars=len(a), x100_bars=len(b)
        )
        for field in (
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "prediction",
            "direction",
            "start",
        ):
            record[field + "_differences"] = int(
                joined[field + "_u"].ne(joined[field + "_x"]).sum()
            )
        cross_symbol.append(record)
    (args.evidence / "cross_symbol_observed_comparison.json").write_text(
        json.dumps(cross_symbol, indent=2) + "\n"
    )
    pairs = []
    for r in primary:
        if not r["use_vwap"]:
            continue
        off_tag = r["tag"].replace("_v1_", "_v0_")
        off = lookup[off_tag]
        pair = {
            k: r[k] for k in ("symbol", "model_kind", "intraday", "balance", "sizing", "tag")
        }
        pair.update(
            off_tag=off_tag,
            delta_return_pp=r["return_percent"] - off["return_percent"],
            delta_trades=r["trades"] - off["trades"],
            delta_dd_pp=r["equity_dd_percent"] - off["equity_dd_percent"],
        )
        if r["balance"] == 3000 and r["sizing"] == 0:
            pair.update(
                bootstrap_difference(args.evidence / off_tag, args.evidence / r["tag"], 3000)
            )
        pairs.append(pair)
    pairs_df = pd.DataFrame(pairs)
    model_pairs = []
    for r in primary:
        if r["model_kind"] != 1:
            continue
        modified = lookup[r["tag"].replace("_m1_", "_m0_")]
        model_pairs.append(
            dict(
                symbol=r["symbol"],
                use_vwap=r["use_vwap"],
                intraday=r["intraday"],
                balance=r["balance"],
                sizing=r["sizing"],
                delta_return_pp=r["return_percent"] - modified["return_percent"],
                delta_trades=r["trades"] - modified["trades"],
            )
        )
    model_pairs_df = pd.DataFrame(model_pairs)
    matrix_cols = [
        "symbol",
        "model_kind",
        "use_vwap",
        "intraday",
        "balance",
        "sizing",
        "trades",
        "return_percent",
        "net_profit",
        "gross_price_profit",
        "commission",
        "fee",
        "swap",
        "net_profit_factor",
        "profit_factor",
        "net_win_rate",
        "equity_dd_percent",
        "trades_per_week",
        "trades_per_month",
        "mean_monthly_profit_usd",
        "mean_monthly_return_percent",
        "geometric_monthly_return_percent",
        "mean_holding_hours",
        "mean_realized_r",
        "long_trades",
        "short_trades",
        "long_net",
        "short_net",
        "initial_stop_trades",
        "trailing_stop_trades",
        "overnight_trades",
        "weekend_trades",
        "planned_actual_risk_percent_mean",
        "planned_actual_risk_percent_max",
        "stopout_deals",
        "losses_exceeding_nominal_budget",
        "losses_exceeding_1pct_reference",
        "coverage",
        "tag",
    ]
    df.reindex(columns=matrix_cols).to_csv(args.evidence / "matrix_summary.csv", index=False)
    pairs_df.to_csv(args.evidence / "paired_vwap_comparison.csv", index=False)
    model_pairs_df.to_csv(args.evidence / "paired_model_comparison.csv", index=False)
    monthly = [dict(tag=r["tag"], **m) for r in primary for m in r["monthly"]]
    pd.DataFrame(monthly).to_csv(args.evidence / "monthly_results.csv", index=False)
    trade_rows = [
        dict(tag=tag, **t)
        for tag, table in trades_by_tag.items()
        if not lookup.get(tag, {"smoke": True}).get("smoke", True)
        for t in table.to_dict("records")
    ]
    pd.DataFrame(trade_rows).to_csv(
        args.evidence / "trade_location_diagnostics.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    band_events = [
        dict(tag=r["tag"], symbol=r["symbol"], model=r["model_kind"], **trade)
        for r in primary
        if r["balance"] == 3000 and r["sizing"] == 0 and r["use_vwap"]
        for trade in trades_by_tag[r["tag"]].to_dict("records")
        if trade["bucket"] == "toward_vwap"
    ]
    band_unique = {(r["entry_time"], r["side"]) for r in band_events}
    (args.evidence / "band_reversion_events.json").write_text(
        json.dumps(dict(unique_entry_events=len(band_unique), executions=band_events), indent=2)
        + "\n"
    )
    validation = dict(
        cases=len(primary),
        legacy_x100_exact_deal_regressions=len(legacy_checks),
        smokes=4,
        source_builds=1,
        paired_streams="PASS",
        paired_model_market_atr_vwap_inputs="PASS",
        prefix_checks=prefixes,
        coverage=coverage,
        positive=int(df.net_profit.gt(0).sum()),
        negative=int(df.net_profit.lt(0).sum()),
        no_trade=int(df.trades.eq(0).sum()),
        real_ticks_all=bool(df.report_100_percent_real_ticks.all()),
        band_reversion_unique_entry_events=len(band_unique),
    )
    (args.evidence / "validated_summary.json").write_text(
        json.dumps(validation, indent=2) + "\n"
    )
    (args.evidence / "validated_results.json").write_text(json.dumps(records, indent=2) + "\n")

    lines = [
        "# Native MT5 Lorentzian and VWAP results",
        "",
        "Actual MT5 Strategy Tester runs on Exness US500 and US500_x100, January through August 2026. This is an exploratory comparison on previously inspected history, not an unseen holdout or an approval to forward/live trade.",
        "",
        f"Completed and independently re-audited: **288 scenarios plus four smoke tests**. {validation['positive']} positive, {validation['negative']} negative, {validation['no_trade']} without trades. All completed native reports state 100% real ticks. Full versus January-only signal prefixes match for both models and symbols.",
        "",
        "## What was tested",
        "",
        "M30. Modified causal exact KNN versus the untouched official MQL5 v1.00 indicator source. Same 3 ATR14 initial stop, +1R activation and 1R trailing distance, no fixed TP, raw opposite-start exits. VWAP filters only entries: both directions within one sigma, long only from the lower 1-3 sigma region, short only from the upper 1-3 sigma region, and skip beyond three sigma. HLC3 is weighted by broker tick volume, reset at midnight UTC. No positive real-volume bars were present in this feed.",
        "",
        "Intraday entries require a closed in-session bar and a next quote before 15:30 New York; holidays are skipped and positions flatten at 15:45. Swing entries run across broker sessions and can hold overnight/weekends. The two styles differ in both trading hours and exit horizon; only VWAP-on versus off within the SAME style isolates the filter.",
        "",
        "Sizing 0 means fixed broker minimum volume (US500 0.14, x100 0.01), NOT a fixed percentage risk. Sizing 1-5 means a strict percentage of current closed balance with lot flooring and minimum-lot skips. Actual stop gaps, swap and commission can exceed planned risk. Current contract/session/swap settings in historical tester runs are not independent proof of historical broker execution conditions. Intraday is checked for no exposure past the daily cutoff.",
        "",
        "## Aggregate paired filter comparison",
        "",
        "Each row pools 18 capital/sizing pairs on the SAME history. These are correlated implementation sensitivities, not 18 independent confirmations. Positive delta means the filtered strategy beat its unfiltered counterpart, not necessarily that either is profitable.",
        "",
        "Pairs with no executable trades can be ties; they are not evidence that a filter lacks predictive value. Consult the complete trade counts and the fixed-volume comparison rather than interpreting improved/18 as a probability of success.",
        "",
        "| Symbol | Model | Style | VWAP improved / 18 | Median return delta pp | Median trade delta | Median DD delta pp |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for (symbol, model, intraday), group in pairs_df.groupby(
        ["symbol", "model_kind", "intraday"]
    ):
        lines.append(
            f"| {symbol} | {'Author' if model else 'Modified'} | {'Intraday' if intraday else 'Swing'} | {int(group.delta_return_pp.gt(0).sum())} | {fmt(group.delta_return_pp.median())} | {fmt(group.delta_trades.median(), 0)} | {fmt(group.delta_dd_pp.median())} |"
        )
    lines += [
        "",
        "## Author versus modified model",
        "",
        "Author minus modified within the same symbol, entry filter, holding style, capital and sizing policy. These are correlated historical comparisons, not model prediction-accuracy scores.",
        "",
        "| Symbol | VWAP | Style | Author better / 18 | Median return delta pp | Median trade delta |",
        "|---|---|---|---:|---:|---:|",
    ]
    for (symbol, vwap, intraday), group in model_pairs_df.groupby(
        ["symbol", "use_vwap", "intraday"]
    ):
        lines.append(
            f"| {symbol} | {int(vwap)} | {'Intraday' if intraday else 'Swing'} | {int(group.delta_return_pp.gt(0).sum())} | {fmt(group.delta_return_pp.median())} | {fmt(group.delta_trades.median(), 0)} |"
        )
    lines += [
        "",
        "## Fixed minimum lot comparisons",
        "",
        "The USD 3000 fixed-minimum rows keep position volume constant. They are the cleanest diagnostic here for separating the entry-location rule from percentage-compounding and minimum-size eligibility effects; the two SYMBOLS still have different exposures.",
        "",
        "| Symbol | Model | Style | VWAP | Trades | Net USD | Return % | Net PF | Equity DD % | Trades/week | Mean USD/month | Geometric %/month |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    focus = df.loc[df.balance.eq(3000) & df.sizing.eq(0)]
    for r in focus.to_dict("records"):
        lines.append(
            f"| {r['symbol']} | {'Author' if r['model_kind'] else 'Modified'} | {'Intraday' if r['intraday'] else 'Swing'} | {'On' if r['use_vwap'] else 'Off'} | {int(r['trades'])} | {fmt(r['net_profit'])} | {fmt(r['return_percent'])} | {fmt(r['net_profit_factor'], 3)} | {fmt(r['equity_dd_percent'])} | {fmt(r['trades_per_week'])} | {fmt(r['mean_monthly_profit_usd'])} | {fmt(r['geometric_monthly_return_percent'])} |"
        )
    lines += [
        "",
        "## Uncertainty of fixed minimum lot differences",
        "",
        "Descriptive 95% intervals from 2000 paired seven-calendar-day moving-block resamples of daily CLOSED-deal cash PnL, seed 1006. These are not independent OOS significance tests, and cash booking of multi-day positions limits interpretation. No inference that an interval excluding zero survives the wider strategy search.",
        "",
        "| Symbol | Model | Style | Filter delta pp | Lower pp | Upper pp |",
        "|---|---|---|---:|---:|---:|",
    ]
    for r in pairs_df.loc[pairs_df.balance.eq(3000) & pairs_df.sizing.eq(0)].to_dict("records"):
        lines.append(
            f"| {r['symbol']} | {'Author' if r['model_kind'] else 'Modified'} | {'Intraday' if r['intraday'] else 'Swing'} | {fmt(r['delta_return_pp'])} | {fmt(r['block_low_pp'])} | {fmt(r['block_high_pp'])} |"
        )
    lines += [
        "",
        "## Baseline trades rejected by the VWAP rule",
        "",
        "This diagnoses executed unfiltered trades at USD 3000 minimum lot. It is NOT the filtered portfolio PnL: skipping a trade can free the account for a different later signal. Positive rejected net PnL means the gate would have excluded a profitable baseline cohort.",
        "",
        "| Symbol | Model | Style | Rejected trades | Rejected winners | Rejected net USD | Rejected winners above 3R |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in focus.loc[~focus.use_vwap].to_dict("records"):
        t = trades_by_tag[r["tag"]]
        rejected = t.loc[~t.gate_allowed.astype(bool)]
        lines.append(
            f"| {r['symbol']} | {'Author' if r['model_kind'] else 'Modified'} | {'Intraday' if r['intraday'] else 'Swing'} | {len(rejected)} | {int(rejected.net.gt(0).sum())} | {fmt(rejected.net.sum())} | {int(rejected.r.gt(3).sum())} |"
        )
    lines += [
        "",
        "## Executed filtered trade locations",
        "",
        "USD 3000 fixed-minimum runs. This separates central entries from the hypothesized band-to-VWAP reversion entries; total strategy PnL alone cannot establish that both mechanisms work.",
        "",
        f"Distinct entry-time/direction band events across these reference runs: **{len(band_unique)}**. The same underlying event appearing on US500 and US500_x100 is not two independent confirmations. See the exact timestamps in `band_reversion_events.json`.",
        "",
        "| Symbol | Model | Style | Location | Trades | Net USD | Mean R |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for r in focus.loc[focus.use_vwap].to_dict("records"):
        t = trades_by_tag[r["tag"]]
        for bucket in ("center", "toward_vwap"):
            g = t.loc[t.bucket.eq(bucket)]
            lines.append(
                f"| {r['symbol']} | {'Author' if r['model_kind'] else 'Modified'} | {'Intraday' if r['intraday'] else 'Swing'} | {bucket} | {len(g)} | {fmt(g.net.sum())} | {fmt(g.r.mean(), 3)} |"
            )
    lines += [
        "",
        "## Minimum lot risk exposure",
        "",
        "Maximum planned initial loss as percent of balance, across the eight fixed-minimum model/filter/style combinations per symbol and capital. These volumes have NO percentage ceiling. The CSV distinguishes strict-budget loss breaches from losses exceeding a 1% reference in the uncapped minimum-lot policy.",
        "",
        "| Symbol | Starting capital | Highest planned risk % | Insolvency-stopped cases |",
        "|---|---:|---:|---:|",
    ]
    for (symbol, capital), group in df.loc[df.sizing.eq(0)].groupby(["symbol", "balance"]):
        lines.append(
            f"| {symbol} | {capital} | {fmt(group.planned_actual_risk_percent_max.max())} | {int(group.coverage.eq('STOPPED_EARLY_INSOLVENT').sum())} |"
        )
    lines += [
        "",
        "## Cross-symbol price and signal differences",
        "",
        "Matched observed bar timestamps from USD 3000 unfiltered minimum-lot swing runs. Price feeds are similar, but the histories available before January differ, and model signals are NOT interchangeable between symbols. Counts below are descriptive; this is not a causal decomposition of history versus feed effects.",
        "",
        "| Model | Matched bars | Open differences | High differences | Low differences | Close differences | Tick-volume differences | Prediction differences | Start differences |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in cross_symbol:
        lines.append(
            f"| {'Author' if r['model'] else 'Modified'} | {r['overlap_bars']} | {r['open_differences']} | {r['high_differences']} | {r['low_differences']} | {r['close_differences']} | {r['tick_volume_differences']} | {r['prediction_differences']} | {r['start_differences']} |"
        )
    lines += [
        "",
        "## Complete capital and risk matrix",
        "",
        "All 288 cases follow; do not select the best row and call it a validated setting. Net PF and win rate are recomputed from closed-position PnL AFTER commission, fees and swap, which may differ from native tester summary PF. Monthly arithmetic/geometric returns and all 2304 monthly cash records are also in the CSV evidence. They are not month-end marked-to-market returns or promised income.",
        "",
        "A net PF of n/a means no measurable losing-position denominator (including no-trade cases), not a risk-free system. A high PF from one or a few closed trades is not robust evidence.",
        "",
        "| Symbol | Model | Style | VWAP | Capital | Sizing | Trades | Return % | Net PF | Net WR % | Equity DD % | Trades/week | Mean USD/month | Geometric %/month |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in primary:
        lines.append(
            f"| {r['symbol']} | {'A' if r['model_kind'] else 'M'} | {'I' if r['intraday'] else 'S'} | {int(r['use_vwap'])} | {r['balance']} | {'min' if r['sizing'] == 0 else str(r['sizing']) + '%'} | {int(r['trades'])} | {fmt(r['return_percent'])} | {fmt(r['net_profit_factor'], 3)} | {fmt(r['net_win_rate'])} | {fmt(r['equity_dd_percent'])} | {fmt(r['trades_per_week'])} | {fmt(r['mean_monthly_profit_usd'])} | {fmt(r['geometric_monthly_return_percent'])} |"
        )
    lines += [
        "",
        "## Provenance and limitations",
        "",
        "Author source: official release `mql5-v1.00`, commit `a23a2301bbad66a6136ffa4b838eceb46ae2db1f`, compiled unchanged. It is not proven binary-identical to Market or the supplied TradingView chart. See `vendor/official_mql5/UPSTREAM.md`. Existing causal core is unchanged. Both models within each symbol start from exactly the same available native history; US500 has longer prehistory than x100, so cross-symbol differences are not attributable only to contract size.",
        "",
        "The official source uses its own backward-window labels and stateful ANN exactly as supplied. It is materially different from the modified forward-label exact KNN. All decisions consume recorded closed-bar buffers during the chronological tester run; no final-chart arrows are used retroactively. January endpoint prefix checks and next-bar buffer stability passed, but neither proves cold-restart invariance. See the [separate restart diagnostic](RESULT_NATIVE_VWAP_RESTART.md) for that test.",
        "",
        "Live calculation cadence is not certified: this nonvisual tester requests the official buffers once per M30 boundary, whereas live indicators normally calculate on ticks. The author's forming-bar normalization state makes that a separate parity gate, not something proven by the closed-bar checks. The official source was not modified to force a different calculation cadence. See the [engineering notes](NATIVE_VWAP_ENGINEERING_NOTES.md) and [MetaQuotes documentation](https://www.mql5.com/en/docs/runtime/testing).",
        "",
        "There is no new unseen holdout, external-feed validation, live execution, or Telegram deployment in this study. Broker tick volume is only a feed proxy. The 3 ATR width and UTC anchor are one explicit operationalization; M15 and NY-anchored VWAP were not tested. Historical commission/session/swap fidelity and added latency remain unverified. Risk 5% and minimum lot at small capital can be highly aggressive.",
        "",
        "The [official listing](https://www.mql5.com/en/market/product/185048) was published in July 2026 and describes feature defaults aimed at higher timeframes. This common-M30 test is not a universal verdict on that indicator or a pre-January published trading system.",
        "",
        "Lower drawdown can partly follow mechanically from fewer trades and less market exposure. No frequency-matched random entry-gate control was run; the paired comparison measures the complete filter's historical effect, not a certified informational edge independent of exposure reduction.",
        "",
        "## Evidence and reproduction",
        "",
        "[Frozen plan](TECH_PLAN_NATIVE_VWAP.md), [matrix CSV](../evidence/native_vwap_2026_v3/matrix_summary.csv), [monthly CSV](../evidence/native_vwap_2026_v3/monthly_results.csv), [paired comparisons](../evidence/native_vwap_2026_v3/paired_vwap_comparison.csv), and [validation](../evidence/native_vwap_2026_v3/validated_summary.json). Immutable native deals, signal/volume exports, settings, native statistics and sanitized launch records are under each scenario. Native HTML is kept local because it can include account metadata; only its hash and real-tick quality flag are published.",
        "",
        "Run `python scripts/report_native_vwap.py --evidence evidence/native_vwap_2026_v3 --output docs/RESULT_NATIVE_VWAP.md` with `PYTHONPATH=src;vendor` to independently regenerate this report from saved evidence. Full native replay additionally needs the broker terminal and history. No order-capable upstream example EA is deployed.",
        "",
    ]
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: v for k, v in validation.items() if k != "coverage"}, indent=2))


if __name__ == "__main__":
    main()
