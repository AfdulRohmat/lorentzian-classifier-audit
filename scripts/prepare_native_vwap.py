"""Freeze the bounded 288-scenario native VWAP matrix before inspecting PnL."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from lorentzian_audit.mt5_audit import validate_tester_config


def scenarios():
    rows = []
    for symbol, model, vwap, intraday, balance, sizing in itertools.product(
        ("US500", "US500_x100"),
        (0, 1),
        (False, True),
        (False, True),
        (500, 1000, 3000),
        range(6),
    ):
        rows.append(
            dict(
                tag=(
                    f"lcv28_{'u' if symbol == 'US500' else 'x'}_m{model}"
                    f"_v{int(vwap)}_i{int(intraday)}_b{balance}_r{sizing}"
                ),
                symbol=symbol,
                model_kind=model,
                use_vwap=vwap,
                intraday=intraday,
                balance=balance,
                risk=max(1, sizing),
                fixed_minimum_lot=sizing == 0,
                sizing=sizing,
                smoke=False,
                stop_atr_multiplier=3,
                max_holding_hours=0,
                minimum_lot_fallback=False,
            )
        )
    smoke = []
    for symbol, model in itertools.product(("US500", "US500_x100"), (0, 1)):
        row = next(
            r
            for r in rows
            if r["symbol"] == symbol
            and r["model_kind"] == model
            and r["use_vwap"]
            and r["intraday"]
            and r["balance"] == 3000
            and r["sizing"] == 0
        ).copy()
        row.update(tag=f"lcv28_smoke_{'u' if symbol == 'US500' else 'x'}_m{model}", smoke=True)
        smoke.append(row)
    return smoke + rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    template = (
        root / "evidence/native_x100_2026_minimum/lc26m_b3000_r1/config.ini"
    ).read_text()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = scenarios()
    for row in rows:
        tag = row["tag"]
        text = template.replace("lc26m_b3000_r1", tag).replace(
            "Deposit=3000", f"Deposit={row['balance']}"
        )
        text = text.replace("LorentzianX100Audit.ex5", "LorentzianVWAPAudit.ex5")
        text = text.replace("Symbol=US500_x100", f"Symbol={row['symbol']}")
        if row["smoke"]:
            text = text.replace("ToDate=2026.09.01", "ToDate=2026.02.01")
        validate_tester_config(text)
        (args.output / f"{tag}.ini").write_text(text)
        settings = dict(
            ModelKind=row["model_kind"],
            UseVWAP=row["use_vwap"],
            Intraday=row["intraday"],
            FixedMinimumLot=row["fixed_minimum_lot"],
            RiskPercent=row["risk"],
            RunTag=tag,
            StopATRMultiplier=3,
            MaxHoldingHours=0,
            AllowMinimumLotFallback=False,
        )
        (args.output / f"{tag}.set").write_text(
            "".join(
                f"{k}={str(v).lower() if isinstance(v, bool) else v}\n"
                for k, v in settings.items()
            ),
            encoding="utf-16",
        )
    (args.output / "matrix.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"Frozen {len(rows)} cases including four smokes")


if __name__ == "__main__":
    main()
