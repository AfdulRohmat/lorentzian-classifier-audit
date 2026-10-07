"""Freeze the US500 native one-ATR, 24-hour tester comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lorentzian_audit.mt5_audit import validate_tester_config


def scenarios(prefix: str) -> list[dict]:
    rows = [
        dict(balance=3000, risk=1, smoke=True, minimum_lot_fallback=False)
    ] + [
        dict(balance=balance, risk=1, smoke=False, minimum_lot_fallback=fallback)
        for balance in (500, 1000, 3000)
        for fallback in (False, True)
    ]
    for row in rows:
        suffix = (
            "smoke"
            if row["smoke"]
            else f"b{row['balance']}_{'minimum' if row['minimum_lot_fallback'] else 'strict'}"
        )
        row.update(
            tag=f"{prefix}_{suffix}",
            symbol="US500",
            stop_atr_multiplier=1,
            max_holding_hours=24,
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prefix", default="lcu26")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    template = (
        root / "evidence/native_x100_2026_minimum/lc26m_b3000_r1/config.ini"
    ).read_text()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = scenarios(args.prefix)
    for row in rows:
        tag = row["tag"]
        config = template.replace("lc26m_b3000_r1", tag)
        config = config.replace("Symbol=US500_x100", "Symbol=US500")
        config = config.replace("Deposit=3000", f"Deposit={row['balance']}")
        if row["smoke"]:
            config = config.replace("ToDate=2026.09.01", "ToDate=2026.02.01")
        validate_tester_config(config)
        (args.output / f"{tag}.ini").write_text(config)
        settings = (
            f"RiskPercent=1.0\nRunTag={tag}\n"
            f"AllowMinimumLotFallback={str(row['minimum_lot_fallback']).lower()}\n"
            "StopATRMultiplier=1\nMaxHoldingHours=24\n"
        )
        (args.output / f"{tag}.set").write_text(settings, encoding="utf-16")
    (args.output / "matrix.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"Frozen {len(rows)} US500 cases at {args.output}")


if __name__ == "__main__":
    main()
