"""Sequential local MT5 batch. Fail on invalid native exports, not on losses."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from lorentzian_audit.native_results import summarize_native


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--configs", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--runs", type=Path, required=True)
    p.add_argument("--smoke-only", action="store_true")
    p.add_argument("--resume-archived", action="store_true")
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    common = Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files/LorentzianAudit"
    terminal = (
        Path.home() / "AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
    )
    scenarios = json.loads((args.configs / "matrix.json").read_text())
    results = []
    for scenario in scenarios:
        if args.smoke_only and not scenario["smoke"]:
            continue
        tag = scenario["tag"]
        output = args.evidence / tag
        if (output / "result.json").exists():
            results.append(json.loads((output / "result.json").read_text()))
            print(f"Already archived {tag}", flush=True)
            continue
        resume = args.resume_archived and output.is_dir()
        if any(common.glob(f"{tag}_*")) and not resume:
            raise FileExistsError(f"Unarchived common output already exists for {tag}")
        if resume:
            print(f"RESUMMARIZE immutable exports {tag}", flush=True)
            for suffix in ("stats", "events", "signals", "deals"):
                if (
                    gzip.decompress((output / f"{suffix}.csv.gz").read_bytes())
                    != (common / f"{tag}_{suffix}.csv").read_bytes()
                ):
                    raise ValueError("Archived exports differ from common originals")
            for suffix in ("ini", "set"):
                if (output / f"config.{suffix}").read_bytes() != (
                    args.configs / f"{tag}.{suffix}"
                ).read_bytes():
                    raise ValueError("Archived configuration changed")
            launch = json.loads((output / "launch.json").read_text())
            if (
                launch.get("exit_code") != 0
                or launch.get("status") != "PROCESS_EXITED_NOT_YET_VALIDATED"
            ):
                raise ValueError("Archived launch did not exit successfully")
        else:
            print(f"START {tag}", flush=True)
            launched = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts/run_mt5_native_audit.py"),
                    "--config",
                    str(args.configs / f"{tag}.ini"),
                    "--output",
                    str(args.runs / tag),
                    "--timeout",
                    "1800",
                ],
                check=False,
            )
            if launched.returncode:
                raise RuntimeError(f"Terminal launch failed for {tag}")
        report = terminal / "reports/LorentzianAudit" / f"{tag}.htm"
        if not report.exists():
            raise RuntimeError(f"Missing native tester report for {tag}")
        if not resume:
            output.mkdir(parents=True, exist_ok=False)
            for suffix in ["stats", "events", "signals", "deals"]:
                source = common / f"{tag}_{suffix}.csv"
                if not source.exists():
                    raise RuntimeError(f"Missing MT5 export: {source.name}")
                (output / f"{suffix}.csv.gz").write_bytes(
                    gzip.compress(source.read_bytes(), mtime=0)
                )
            for suffix in ["ini", "set"]:
                shutil.copy2(args.configs / f"{tag}.{suffix}", output / f"config.{suffix}")
            shutil.copy2(args.runs / tag / "launch.json", output / "launch.json")
        # HTML remains local; may contain broker/account metadata. Retain hash +
        # selected quality field, not wholesale account information in the repo.
        raw = report.read_bytes()
        html = (
            raw.decode("utf-16")
            if raw.startswith((b"\xff\xfe", b"\xfe\xff"))
            else raw.decode("utf-8", errors="replace")
        )
        stats = dict(
            pd.read_csv(common / f"{tag}_stats.csv").itertuples(index=False, name=None)
        )
        deals = pd.read_csv(common / f"{tag}_deals.csv")
        events = pd.read_csv(common / f"{tag}_events.csv")
        if (
            float(stats["deposit"]) != scenario["balance"]
            or float(stats["risk_percent"]) != scenario["risk"]
        ):
            raise ValueError("Tester did not apply requested scenario settings")
        for field in ("minimum_lot_fallback", "stop_atr_multiplier", "max_holding_hours"):
            if field in scenario and float(stats[field]) != float(scenario[field]):
                raise ValueError(f"Tester did not apply {field}")
        result, monthly = summarize_native(stats, deals, events)
        result.update(scenario)
        result["report_sha256"] = hashlib.sha256(raw).hexdigest()
        result["report_100_percent_real_ticks"] = "100% real ticks" in html
        result["monthly"] = monthly
        result["ea_sha256"] = hashlib.sha256(
            (root / "mql5/Experts/LorentzianX100Audit.ex5").read_bytes()
        ).hexdigest()
        if "stop_atr_multiplier" in scenario:
            from lorentzian_audit.native_swing import audit_swing, validate_coverage

            signal_bytes = (output / "signals.csv.gz").read_bytes()
            result.update(
                audit_swing(stats, deals, events, pd.read_csv(output / "signals.csv.gz"))
            )
            if not scenario["smoke"] and scenario.get("symbol", "US500_x100") == "US500_x100":
                baseline = (
                    root / f"evidence/native_x100_2026_minimum/lc26m_b{scenario['balance']}_r1"
                )
                result["coverage"] = validate_coverage(
                    stats,
                    deals,
                    gzip.decompress(signal_bytes),
                    gzip.decompress((baseline / "signals.csv.gz").read_bytes()),
                    json.loads((baseline / "result.json").read_text()),
                )
                if scenario.get("control"):
                    if (output / "deals.csv.gz").read_bytes() != (
                        baseline / "deals.csv.gz"
                    ).read_bytes():
                        raise ValueError("Legacy native deals changed on the swing build")
                    old = json.loads((baseline / "result.json").read_text())
                    for field in (
                        "net_profit",
                        "trades",
                        "equity_dd_percent",
                        "swap",
                        "commission",
                    ):
                        if abs(result[field] - old[field]) > 1e-8:
                            raise ValueError(f"Legacy control drift in {field}")
                    result["legacy_regression"] = "PASS"
            if not result["report_100_percent_real_ticks"]:
                raise ValueError("Native report does not confirm 100 percent real ticks")
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append(result)
        print(
            f"PASS {tag}: trades={int(result['trades'])} "
            f"balance={result['final_balance']:.2f} PF={result['profit_factor']:.3f} "
            f"real_ticks_100={result['report_100_percent_real_ticks']}",
            flush=True,
        )
    args.evidence.mkdir(parents=True, exist_ok=True)
    (args.evidence / "results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
