"""Validate archived MT5 evidence and render the account matrix report."""
# ruff: noqa: E501 -- long Markdown table rows and report prose literals.

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

from lorentzian_audit.native_results import summarize_native


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, default=Path("evidence/native_x100_2026"))
    args = p.parse_args()
    results = []
    signal_hashes = set()
    for path in sorted(args.evidence.glob("lc26c_b*/result.json")):
        stored = json.loads(path.read_text())
        folder = path.parent
        stats = dict(pd.read_csv(folder / "stats.csv.gz").itertuples(index=False, name=None))
        events = pd.read_csv(folder / "events.csv.gz")
        actual, months = summarize_native(stats, pd.read_csv(folder / "deals.csv.gz"), events)
        for key in ["final_balance", "net_profit", "trades", "equity_dd_percent"]:
            if abs(actual[key] - stored[key]) > 1e-8:
                raise ValueError(f"Stored result mismatch: {path} {key}")
        if not stored["report_100_percent_real_ticks"]:
            raise ValueError("Real tick coverage not confirmed by report")
        signal_hashes.add(
            hashlib.sha256(
                gzip.decompress((folder / "signals.csv.gz").read_bytes())
            ).hexdigest()
        )
        signals = pd.read_csv(folder / "signals.csv.gz")
        stamps = pd.to_datetime(signals.time, unit="s", utc=True)
        warmup = int((stamps < pd.Timestamp("2026-01-01", tz="UTC")).sum())
        starts = signals.loc[stamps >= pd.Timestamp("2026-01-01", tz="UTC"), "start"]
        stored["warmup_bars"] = warmup
        stored["evaluation_long_starts"] = int(starts.eq(1).sum())
        stored["evaluation_short_starts"] = int(starts.eq(-1).sum())
        stored["monthly"] = months
        results.append(stored)
    expected = {(b, r) for b in [500, 1000, 3000] for r in range(1, 6)}
    if {(int(r["deposit"]), int(r["risk_percent"])) for r in results} != expected:
        raise ValueError("Incomplete account/risk matrix")
    if len(signal_hashes) != 1:
        raise ValueError("Signal stream changes between account scenarios")
    results.sort(key=lambda r: (r["deposit"], r["risk_percent"]))
    summary = {
        "status": "NATIVE_MATRIX_COMPLETE_NOT_A_ROBUST_EDGE_VALIDATION",
        "native_scenarios": len(results),
        "all_reconciled": True,
        "identical_signal_streams": True,
        "signal_sha256": next(iter(signal_hashes)),
        "all_reports_100_percent_real_ticks": True,
        "profitable_scenarios": sum(r["net_profit"] > 0 for r in results),
        "negative_scenarios": sum(r["net_profit"] < 0 for r in results),
        "no_trade_scenarios": sum(r["trades"] == 0 for r in results),
        "results": results,
    }
    (args.evidence / "validated_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [
        "# Native US500 x100 backtest results",
        "",
        "All fifteen account scenarios completed in MT5 Strategy Tester. These are native fills and account PnL, not a Python replay. The classifier anchor is 15 June 2025; evaluation is January through August 2026. All reports indicate 100% real ticks. All deal ledgers reconcile to native final balances.",
        "",
        "**Conclusion: the native run is operationally reproducible, but these results do not establish a robust profitable strategy. Do not promote the highest-return risk setting after inspection.**",
        "",
        "## Account matrix",
        "",
        "Sizing compounds from closed balance; sub-minimum positions are skipped. DD below is native maximum relative equity drawdown, including floating PnL. Monthly return is the arithmetic mean of eight realized-balance monthly returns, not total return divided by eight.",
        "",
        "| Deposit | Risk | Trades | Trades/week | Final balance | Return | PF | Equity DD | Mean month return | Mean month USD |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        pf = f"{r['profit_factor']:.3f}" if r["trades"] else "N/A"
        lines.append(
            f"| ${r['deposit']:,.0f} | {r['risk_percent']:.0f}% | {r['trades']:.0f} | {r['trades_per_week']:.2f} | ${r['final_balance']:,.2f} | {r['return_percent']:+.2f}% | {pf} | {r['equity_dd_percent']:.2f}% | {r['mean_monthly_return_percent']:+.2f}% | ${r['mean_monthly_profit_usd']:+.2f} |"
        )
    lines += [
        "",
        "## Every monthly realized return",
        "",
        "| Deposit | Risk | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        cells = " | ".join(f"{m['return_percent']:+.2f}%" for m in r["monthly"])
        lines.append(f"| ${r['deposit']:,.0f} | {r['risk_percent']:.0f}% | {cells} |")
    lines += [
        "",
        "## Trading activity and costs",
        "",
        "| Deposit | Risk | Trades/month | WR | Long net | Short net | Commission | Swap | Losses above budget | Min lot skips |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        wr = f"{r['win_rate_percent']:.1f}%" if r["trades"] else "N/A"
        lines.append(
            f"| ${r['deposit']:,.0f} | {r['risk_percent']:.0f}% | {r['trades_per_month']:.2f} | {wr} | ${r['long_net']:+.2f} | ${r['short_net']:+.2f} | ${r['commission']:.2f} | ${r['swap']:.2f} | {r['losses_exceeding_nominal_budget']} | {r['skips'].get('below_minimum', 0)} |"
        )
    lines += [
        "",
        "## Execution audit and limits",
        "",
        "- Same classifier signal stream in every full-period scenario; all used 6,458 warm-up bars. No entry/exit parameters were optimized.",
        "- Native minimum lot 0.01, contract size 100, step 0.01, maximum 20. The old conditional 0.03 assumption was not used.",
        "- Zero added execution delay; native tick prices, broker-side stops, commission and swap determine returns. Risk/trail calculations retain conservative legacy reserves of 0.02 points for exit slippage and 0.25 for round-trip commission; these reserves are not additional cash charges.",
        "- Native maximum loss can exceed the nominal budget because stop fills and costs are not guaranteed. The risk-percent input is not a guaranteed loss ceiling.",
        "- The initial smoke attempt was INVALID because an ordinary market-closed entry rejection halted the EA. The corrected implementation skips that entry; required exits are deferred while continuing classifier updates. The repeated smoke and all final scenarios passed without EA failure flags.",
        "- All eight months are previously inspected history, not an unseen holdout. Current tester symbol settings may not reproduce every historical change in broker fees, sessions or margin.",
        "- This new anchor, native price feed and tick execution differ from the earlier 2022-anchored Python study. The difference in performance has not been causally decomposed; do not attribute it to one factor without a matched audit.",
        "- No demo/real broker orders, Telegram, optimization or forward trading were activated. The EA refuses non-tester execution.",
        "",
        "## Reproduction",
        "",
        "See [the frozen plan](TECH_PLAN_NATIVE_X100_2026.md). Native exports, fixed INI/SET inputs, EX5 hash and launch metadata are archived under [evidence/native_x100_2026](../evidence/native_x100_2026/). The raw HTML reports remain in the local MT5 reports directory; their hashes and quality checks are retained without publishing account metadata.",
        "",
        "Run `scripts/report_native_matrix.py` to revalidate native exports. It does not simulate orders or recalculate fills. The report keeps verified outcomes separate from assumptions, following the document-writing review guidance.",
        "",
    ]
    Path("docs/RESULT_NATIVE_X100_2026.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    print("\n".join(lines[8:26]))


if __name__ == "__main__":
    main()
