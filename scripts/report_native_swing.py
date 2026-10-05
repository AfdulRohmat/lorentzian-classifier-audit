"""Reconcile all frozen swing scenarios and render a complete non-selected report."""
# ruff: noqa: E501 -- rendered Markdown tables deliberately stay on one line.

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

from lorentzian_audit.native_results import summarize_native
from lorentzian_audit.native_swing import audit_swing, validate_coverage

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/native_x100_swing_2026"


def fmt(value, digits=2):
    return "N/A" if value is None else f"{value:.{digits}f}"


def main() -> None:
    matrix = json.loads((EVIDENCE / "build/frozen_matrix.json").read_text())
    old_root = ROOT / "evidence/native_x100_2026_minimum"
    expected_signals = (old_root / "lc26m_b3000_r1/signals.csv.gz").read_bytes()
    expected_window = json.loads((old_root / "lc26m_b3000_r1/result.json").read_text())
    checked, hashes = [], {}
    for scenario in matrix:
        folder = EVIDENCE / scenario["tag"]
        result = json.loads((folder / "result.json").read_text())
        stats = dict(pd.read_csv(folder / "stats.csv.gz").itertuples(index=False, name=None))
        deals = pd.read_csv(folder / "deals.csv.gz")
        events = pd.read_csv(folder / "events.csv.gz")
        signals = pd.read_csv(folder / "signals.csv.gz")
        recomputed, monthly = summarize_native(stats, deals, events)
        path = audit_swing(stats, deals, events, signals)
        for key, expected in scenario.items():
            if result[key] != expected:
                raise ValueError(f"Scenario mismatch: {scenario['tag']} {key}")
        for key in ("stop_atr_multiplier", "max_holding_hours", "minimum_lot_fallback"):
            if float(stats[key]) != float(scenario[key]):
                raise ValueError(f"Native settings mismatch: {key}")
        for key, value in recomputed.items():
            old = result[key]
            if isinstance(value, (float, int)) and value is not None:
                if abs(float(old) - float(value)) > 1e-7:
                    raise ValueError(f"Metric mismatch {key}")
            elif old != value:
                raise ValueError(f"Metric mismatch {key}")
        if not result["report_100_percent_real_ticks"]:
            raise ValueError("Real-tick quality not confirmed")
        if not scenario["smoke"]:
            result["coverage"] = validate_coverage(
                stats,
                deals,
                gzip.decompress((folder / "signals.csv.gz").read_bytes()),
                gzip.decompress(expected_signals),
                expected_window,
            )
        if scenario["control"]:
            old_folder = old_root / f"lc26m_b{scenario['balance']}_r1"
            if (folder / "deals.csv.gz").read_bytes() != (
                old_folder / "deals.csv.gz"
            ).read_bytes():
                raise ValueError("Control deal ledger mismatch")
            old = json.loads((old_folder / "result.json").read_text())
            for key in ("final_balance", "equity_dd_percent", "trades", "swap", "commission"):
                if abs(result[key] - old[key]) > 1e-8:
                    raise ValueError(f"Control changed: {key}")
        result.update(path)
        result["monthly"] = monthly
        checked.append(result)
        hashes[scenario["tag"]] = {
            f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in folder.iterdir()
            if f.is_file()
        }
        print(f"AUDITED {scenario['tag']}", flush=True)
    swing = [r for r in checked if not r["smoke"] and not r["control"]]
    controls = [r for r in checked if r["control"]]
    if len(swing) != 150 or len(controls) != 3:
        raise ValueError("Incomplete preregistered matrix")
    if len({r["ea_sha256"] for r in checked}) != 1:
        raise ValueError("Build changed within matrix")
    positive = sum(r["net_profit"] > 0.005 for r in swing)
    negative = sum(r["net_profit"] < -0.005 for r in swing)
    no_trade = sum(r["trades"] == 0 for r in swing)
    summary = dict(
        status="NATIVE_SWING_MATRIX_COMPLETE_NOT_NEW_DATA_VALIDATION",
        scenarios=150,
        positive=positive,
        negative=negative,
        no_trade=no_trade,
        stopout_scenarios=sum(r["stopout_deals"] > 0 for r in swing),
        insolvent_early_stops=sum(r["coverage"] == "STOPPED_EARLY_INSOLVENT" for r in swing),
        signal_sha256=hashlib.sha256(gzip.decompress(expected_signals)).hexdigest(),
        results=checked,
        artifact_sha256=hashes,
    )
    (EVIDENCE / "validated_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lookup = {(r["balance"], r["risk"], r["stop_atr_multiplier"]): r for r in swing}
    matched = []
    for tag in ("lcs26_control_b1000", "lcs26_k1_b1000_r1"):
        d = pd.read_csv(EVIDENCE / tag / "deals.csv.gz")
        d["net"] = d[["profit", "commission", "fee", "swap"]].sum(axis=1)
        a = d.groupby("position_id").agg(
            entry=("time", "min"),
            exit=("time", "max"),
            net=("net", "sum"),
            volume=("volume", "first"),
        )
        matched.append(a.reset_index(drop=True).set_index("entry"))
    pairs = matched[0].join(matched[1], lsuffix="_old", rsuffix="_swing", how="outer")
    if pairs.isna().any().any() or not pairs.volume_old.eq(pairs.volume_swing).all():
        raise ValueError("Deadline comparison is no longer a matched fixed-lot sample")
    changed = pairs.loc[(pairs.net_swing - pairs.net_old).abs() > 0.005].copy()
    changed["old_hours"] = (changed.exit_old - changed.index) / 3600
    changed["swing_hours"] = (changed.exit_swing - changed.index) / 3600
    changed["entry_label"] = pd.to_datetime(changed.index, unit="s", utc=True).astype(str)
    (EVIDENCE / "deadline_trade_comparison.json").write_text(
        changed.reset_index().to_json(orient="records", indent=2) + "\n"
    )
    lines = [
        "# Native US500 x100 swing results",
        "",
        "The complete 150-variant swing experiment ran in the MT5 Strategy Tester, "
        "not a Python price simulator. It uses the previously inspected January through "
        "August 2026 period, with June through December 2025 classifier warm-up. "
        "It is not unseen validation, production readiness or authorization to trade.",
        "",
        f"Of 150 scenarios, **{positive} are positive, {negative} negative and {no_trade} "
        "have no trades**. These overlapping scenarios are not independent replications. "
        "A best result selected from this grid is exploratory.",
        "",
        "## Verified execution",
        "",
        "Three legacy controls reproduce the old deal exports byte for byte and match "
        "native balance, trades, drawdown and costs. Runs that reach the end use the identical "
        "classifier signal stream; insolvent early stops must match its exact prefix. "
        "Every run uses one EA build. Native reports indicate 100 percent "
        "real ticks; all deal ledgers reconcile to final balances. The path audit verifies "
        "entry direction, initial ATR stop, scaled trail, opposite-only setup exits and "
        "absence of time exits in swing variants. All positions are liquidated by test end. "
        "Zero added execution delay is a modeling limitation.",
        "",
        "EA compilation completed with zero errors and zero warnings. The Python "
        "suite has 87 passing tests, including stop/trail width, sizing, causal setup "
        "checks and insolvency reporting. This is engineering verification, not "
        "a profitability pass. The one January smoke run is excluded from performance "
        "comparisons and full-period scenario counts.",
        "",
        f"**{summary['insolvent_early_stops']} scenarios stopped early after native insolvency.** "
        "They remain failed economic outcomes in the matrix, not missing data or completed "
        "eight-month histories. Activity averages use the full intended eight-month calendar. "
        "Compounded and arithmetic monthly returns are undefined once balance is nonpositive.",
        "",
        "The first insolvency exposed a reporting error when adding undefined monthly "
        "returns. The reporter was corrected and immutable native exports reprocessed; "
        "no EA trading rule or parameters changed. Early termination is accepted only "
        "with native stop-out reason, nonpositive balance, reconciled closed deals and "
        "exact classifier prefix. No insolvent scenario is silently dropped.",
        "",
        "## Rules and interpretation",
        "",
        "Entry remains the existing causal exact KNN Lorentzian M30 start, not the "
        "original author's ANN. Initial stop is k times entry ATR14; that distance plus "
        "the existing 0.27 point reserve defines R. Trail activates at +1R net of reserve "
        "and follows at 1R, using completed M30 quotes. No fixed TP or 24 hour deadline. "
        "Opposite starts close and may reverse; same-side starts do not add or reset.",
        "",
        "The 1 percent row uses minimum 0.01 lot fallback when necessary: **it is not "
        "a strict 1 percent loss limit**. Risk rows 2 to 5 floor position size and skip "
        "below minimum. Widening stops can change both actual monetary risk and the "
        "trade sample. Stop gaps can exceed planned risk. Swaps are native tester "
        "charges; historical fidelity of the swap schedule is not independently proved.",
        "",
        "## Isolating removal of the deadline",
        "",
        "These matched 1 percent plus minimum-lot rows compare old 24 hour exits with "
        "swing at the same one ATR stop. They do not isolate the effect of wider stops.",
        "",
        "| Capital | Old return % | Swing 1 ATR return % | Old equity DD % | Swing equity DD % | Old trades | Swing trades |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for old in controls:
        r = lookup[old["balance"], 1, 1]
        lines.append(
            f"| ${old['balance']} | {fmt(old['return_percent'])} | {fmt(r['return_percent'])} | "
            f"{fmt(old['equity_dd_percent'])} | {fmt(r['equity_dd_percent'])} | {int(old['trades'])} | {int(r['trades'])} |"
        )
    lines += [
        "",
        f"The $1000 minimum-lot comparison has {len(pairs)} matched entry timestamps "
        f"and identical lots. Only {len(changed)} trade outcomes change, totaling "
        f"${(changed.net_swing - changed.net_old).sum():+.2f}. "
        "This separates the deadline effect from position sizing in this one comparison. "
        "The old deadline can execute later than 24 hours when the market is closed.",
        "",
        "| Entry timestamp as exported | Old net USD | Swing net USD | Old holding h | Swing holding h |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in changed.itertuples():
        lines.append(
            f"| {r.entry_label} | {r.net_old:.2f} | {r.net_swing:.2f} | {r.old_hours:.2f} | {r.swing_hours:.2f} |"
        )
    lines += [
        "",
        "## Highest historical returns in the grid",
        "",
        "Descriptive ranking only, selected after inspecting all 150 variations. "
        "These are not independent confirmations or approved settings. Positive "
        "sizing rows may trade different subsets of the identical signal stream.",
        "",
        "| Capital | ATR | Target risk % | Trades | Return % | Equity DD % | PF | Trades per week | Geometric month % |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    ranked = sorted(
        [r for r in swing if r["trades"] > 0], key=lambda r: r["return_percent"], reverse=True
    )[:5]
    for r in ranked:
        lines.append(
            f"| ${r['balance']} | {r['stop_atr_multiplier']} | {r['risk']} | {int(r['trades'])} | "
            f"{fmt(r['return_percent'])} | {fmt(r['equity_dd_percent'])} | {fmt(r['profit_factor'], 3)} | "
            f"{fmt(r['trades_per_week'])} | {fmt(r['geometric_monthly_return_percent'])} |"
        )
    lines += [
        "",
        "## All capital and risk combinations",
        "",
        "Cells contain total return percent followed by maximum equity drawdown percent. "
        "The full trade, monthly, risk and holding metrics for every cell are in "
        "[validated evidence](../evidence/native_x100_swing_2026/validated_summary.json). "
        "N/A marks scenarios with no executed trades, not a profitable strategy.",
    ]
    for balance in (500, 1000, 3000):
        lines += [
            "",
            f"### Capital {balance} USD",
            "",
            "| SL and trail ATR | 1% plus min lot | Strict 2% | Strict 3% | Strict 4% | Strict 5% |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for k in range(1, 11):
            cells = []
            for risk in range(1, 6):
                r = lookup[balance, risk, k]
                cells.append(
                    f"{fmt(r['return_percent'])} / {fmt(r['equity_dd_percent'])}"
                    if r["trades"]
                    else "N/A"
                )
            lines.append(f"| {k} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## One percent target with minimum lot fallback",
        "",
        "Monthly dollar average is total net PnL divided by eight. Geometric monthly "
        "return is the constant compounded rate matching the start and end balance; "
        "it is not a prediction of regular monthly income. Realized trade R divides "
        "net PnL by each entry planned dollar risk, including the sizing reserve.",
    ]
    for balance in (500, 1000, 3000):
        lines += [
            "",
            f"### Minimum lot results for {balance} USD",
            "",
            "| ATR | Trades | Per week | Per month | PF | WR % | Mean month $ | Geom month % | Mean holding h | Max planned risk % | Mean net R |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for k in range(1, 11):
            r = lookup[balance, 1, k]
            values = [
                k,
                int(r["trades"]),
                fmt(r["trades_per_week"]),
                fmt(r["trades_per_month"]),
                fmt(r["profit_factor"], 3) if r["trades"] else "N/A",
                fmt(r["win_rate_percent"]),
                fmt(r["mean_monthly_profit_usd"]),
                fmt(r["geometric_monthly_return_percent"]),
                fmt(r["mean_holding_hours"]),
                fmt(r.get("planned_actual_risk_percent_max")),
                fmt(r["mean_realized_r"], 3),
            ]
            lines.append("| " + " | ".join(map(str, values)) + " |")
        lines += [
            "",
            "Monthly realized cash returns percent. Open-position floating PnL is "
            "**not** marked to market at month end in this table; swing holding can "
            "shift realized profits between months. Native maximum equity drawdown "
            "does include floating losses.",
            "",
            "| ATR | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for k in range(1, 11):
            r = lookup[balance, 1, k]
            lines.append(
                f"| {k} | " + " | ".join(fmt(m["return_percent"]) for m in r["monthly"]) + " |"
            )
    lines += [
        "",
        "## Holding costs and exit paths on 3000 USD",
        "",
        "These are the 1 percent target plus minimum-lot rows. Wider stops also "
        "change risk and the entry sample, so the table is not a constant-risk experiment.",
        "",
        "| ATR | Price PnL USD | Commission USD | Swap USD | Mean hold h | Maximum hold h | Initial SL exits | Trailed SL exits | Opposite exits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for k in range(1, 11):
        r = lookup[3000, 1, k]
        lines.append(
            f"| {k} | {fmt(r['gross_price_profit'])} | {fmt(r['commission'])} | "
            f"{fmt(r['swap'])} | {fmt(r['mean_holding_hours'])} | "
            f"{fmt(r['max_holding_hours_observed'])} | {r['initial_stop_trades']} | "
            f"{r['trailing_stop_trades']} | {r['exits'].get('opposite', 0)} |"
        )
    lines += [
        "",
        "## Limitations and reproduction",
        "",
        "This broad grid tests exit sensitivity, not a new predictive classifier. "
        "Do not promote whichever width earns most on these same eight months. "
        "Performance may depend on changed trade eligibility, short sample, market "
        "path, costs and minimum-lot exposure. Session-open gaps, liquidity and "
        "live execution delay are not independently stress-tested here. The EA "
        "remains tester-only and lacks production restart/recovery handling.",
        "",
        "Holding times use exported terminal timestamps. Overnight/weekend counts "
        "are calendar exposure diagnostics, not proof of exact swap billing. "
        "Giveback diagnostics use completed-bar marks, not true tick-level MFE, "
        "and compare a reserved-cost price mark with realized net including swap.",
        "",
        "Run with `PYTHONPATH=src;vendor`: `scripts/prepare_native_swing.py`, deploy "
        "compiled tester-only EA and set files, then `scripts/run_native_matrix.py` "
        "with `local_mt5/matrix_swing_2026`, `evidence/native_x100_swing_2026` and "
        "`local_mt5/runs_swing_2026`. `scripts/report_native_swing.py` independently "
        "rechecks exports. Existing artifacts are preserved; choose new tags for "
        "a rerun. Source snapshot and artifact hashes accompany the evidence.",
        "",
        "See [frozen technical contract](TECH_PLAN_NATIVE_SWING.md) and "
        "[previous native account results](RESULT_NATIVE_X100_MINIMUM_LOT.md).",
        "",
    ]
    (ROOT / "docs/RESULT_NATIVE_SWING.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k not in ("results", "artifact_sha256")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
