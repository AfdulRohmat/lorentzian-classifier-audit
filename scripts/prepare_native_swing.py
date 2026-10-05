"""Generate the preregistered 150 swing variants and three legacy controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lorentzian_audit.mt5_audit import validate_tester_config


def scenarios(prefix: str) -> list[dict]:
    rows = [
        dict(
            balance=3000,
            risk=1,
            smoke=True,
            stop_atr_multiplier=10,
            max_holding_hours=0,
            control=False,
        )
    ]
    rows += [
        dict(
            balance=b,
            risk=1,
            smoke=False,
            stop_atr_multiplier=1,
            max_holding_hours=24,
            control=True,
        )
        for b in (500, 1000, 3000)
    ]
    rows += [
        dict(
            balance=b,
            risk=r,
            smoke=False,
            stop_atr_multiplier=k,
            max_holding_hours=0,
            control=False,
        )
        for k in range(1, 11)
        for b in (500, 1000, 3000)
        for r in range(1, 6)
    ]
    for row in rows:
        suffix = (
            "smoke"
            if row["smoke"]
            else f"control_b{row['balance']}"
            if row["control"]
            else f"k{row['stop_atr_multiplier']}_b{row['balance']}_r{row['risk']}"
        )
        row["tag"] = f"{prefix}_{suffix}"
        row["minimum_lot_fallback"] = row["risk"] == 1
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--prefix", default="lcs26")
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    template = (
        root / "evidence/native_x100_2026_minimum/lc26m_b3000_r1/config.ini"
    ).read_text()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = scenarios(args.prefix)
    for row in rows:
        tag = row["tag"]
        config = template.replace("lc26m_b3000_r1", tag).replace(
            "Deposit=3000", f"Deposit={row['balance']}"
        )
        if row["smoke"]:
            config = config.replace("ToDate=2026.09.01", "ToDate=2026.02.01")
        validate_tester_config(config)
        (args.output / f"{tag}.ini").write_text(config)
        settings = (
            f"RiskPercent={row['risk']}.0\nRunTag={tag}\n"
            f"AllowMinimumLotFallback={'true' if row['minimum_lot_fallback'] else 'false'}\n"
            f"StopATRMultiplier={row['stop_atr_multiplier']}\n"
            f"MaxHoldingHours={row['max_holding_hours']}\n"
        )
        (args.output / f"{tag}.set").write_text(settings, encoding="utf-16")
    (args.output / "matrix.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"Prepared {len(rows)} scenarios at {args.output}")


if __name__ == "__main__":
    main()
