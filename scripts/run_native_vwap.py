"""Native-only sequential runs and independent export audits; no account orders."""

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

from lorentzian_audit.native_vwap import audit_vwap


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--configs", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--runs", type=Path, required=True)
    p.add_argument("--smoke-only", action="store_true")
    p.add_argument("--resume-archived", action="store_true")
    p.add_argument("--collect-existing", action="store_true")
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    common = Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files/LorentzianAudit"
    terminal = (
        Path.home() / "AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
    )
    rows = json.loads((args.configs / "matrix.json").read_text())
    results = []
    for n, row in enumerate(rows):
        if args.smoke_only and not row["smoke"]:
            continue
        tag = row["tag"]
        out = args.evidence / tag
        if (out / "result.json").exists():
            results.append(json.loads((out / "result.json").read_text()))
            continue
        resume = args.resume_archived and out.is_dir()
        collect = args.collect_existing and (args.runs / tag / "launch.json").exists()
        if any(common.glob(f"{tag}_*")) and not resume and not collect:
            raise FileExistsError(f"Unarchived immutable outputs {tag}")
        if not resume:
            print(f"START {n + 1}/{len(rows)} {tag}", flush=True)
            if not collect:
                subprocess.run(
                    [
                        sys.executable,
                        str(root / "scripts/run_mt5_native_audit.py"),
                        "--config",
                        str(args.configs / f"{tag}.ini"),
                        "--output",
                        str(args.runs / tag),
                        "--timeout",
                        "900",
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
            if out.exists() and any(out.iterdir()):
                raise FileExistsError("Nonempty evidence requires explicit archived resume")
            out.mkdir(parents=True, exist_ok=True)
            for suffix in ("stats", "events", "signals", "deals"):
                raw = (common / f"{tag}_{suffix}.csv").read_bytes()
                (out / f"{suffix}.csv.gz").write_bytes(gzip.compress(raw, mtime=0))
            for suffix in ("ini", "set"):
                shutil.copy2(args.configs / f"{tag}.{suffix}", out / f"config.{suffix}")
            shutil.copy2(args.runs / tag / "launch.json", out / "launch.json")
        else:
            for suffix in ("stats", "events", "signals", "deals"):
                if (
                    gzip.decompress((out / f"{suffix}.csv.gz").read_bytes())
                    != (common / f"{tag}_{suffix}.csv").read_bytes()
                ):
                    raise ValueError("Archived export changed")
        launch = json.loads((out / "launch.json").read_text())
        if (
            launch.get("exit_code") != 0
            or launch.get("status") != "PROCESS_EXITED_NOT_YET_VALIDATED"
        ):
            raise ValueError("Native process did not exit normally")
        for suffix in ("ini", "set"):
            if (out / f"config.{suffix}").read_bytes() != (
                args.configs / f"{tag}.{suffix}"
            ).read_bytes():
                raise ValueError("Settings changed")
        raw = (terminal / "reports/LorentzianAudit" / f"{tag}.htm").read_bytes()
        html = (
            raw.decode("utf-16")
            if raw.startswith((b"\xff\xfe", b"\xfe\xff"))
            else raw.decode("utf-8", errors="replace")
        )
        if "100% real ticks" not in html:
            raise ValueError("Native report does not confirm complete real ticks")
        stats = dict(pd.read_csv(out / "stats.csv.gz").itertuples(index=False, name=None))
        for field in (
            "model_kind",
            "use_vwap",
            "intraday",
            "fixed_minimum_lot",
            "stop_atr_multiplier",
            "max_holding_hours",
            "minimum_lot_fallback",
        ):
            if float(stats[field]) != float(row[field]):
                raise ValueError(f"Input not applied: {field}")
        if (
            float(stats["deposit"]) != row["balance"]
            or float(stats["risk_percent"]) != row["risk"]
        ):
            raise ValueError("Capital/risk not applied")
        result = audit_vwap(
            stats,
            pd.read_csv(out / "deals.csv.gz"),
            pd.read_csv(out / "events.csv.gz"),
            pd.read_csv(out / "signals.csv.gz"),
        )
        result.update(row)
        result.update(
            report_sha256=hashlib.sha256(raw).hexdigest(),
            report_100_percent_real_ticks=True,
            ea_sha256=hashlib.sha256(
                (root / "mql5/Experts/LorentzianVWAPAudit.ex5").read_bytes()
            ).hexdigest(),
            indicator_sha256=hashlib.sha256(
                (
                    root
                    / "vendor/official_mql5/indicators/LorentzianClassification"
                    / "LorentzianClassification.ex5"
                ).read_bytes()
            ).hexdigest(),
        )
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append(result)
        (args.evidence / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(
            f"PASS {tag} trades={int(result['trades'])} "
            f"net={result['net_profit']:.2f} PF={result['profit_factor']:.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
