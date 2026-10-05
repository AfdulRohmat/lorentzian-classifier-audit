"""Generate fixed native-test configurations; does not run orders or optimize."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lorentzian_audit.mt5_audit import validate_tester_config


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--prefix", default="lc26")
    p.add_argument("--minimum-lot-fallback", action="store_true")
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    configs = []
    scenarios = [(3000, 1, True)] + [
        (b, r, False) for b in [500, 1000, 3000] for r in range(1, 6)
    ]
    if args.minimum_lot_fallback:
        scenarios = [(3000, 1, True)] + [(b, 1, False) for b in [500, 1000, 3000]]
    for balance, risk, smoke in scenarios:
        tag = f"{args.prefix}_smoke" if smoke else f"{args.prefix}_b{balance}_r{risk}"
        params = f"{tag}.set"
        content = "\n".join(
            [
                "[Experts]",
                "Enabled=1",
                "AllowLiveTrading=0",
                "AllowDllImport=0",
                "[Tester]",
                r"Expert=LorentzianAudit\LorentzianX100Audit.ex5",
                f"ExpertParameters={params}",
                "Symbol=US500_x100",
                "Period=M30",
                "Model=4",
                "ExecutionMode=0",
                "Optimization=0",
                "FromDate=2026.01.01",
                "ToDate=2026.02.01" if smoke else "ToDate=2026.09.01",
                "ForwardMode=0",
                f"Report=reports\\LorentzianAudit\\{tag}.htm",
                "ReplaceReport=0",
                "ShutdownTerminal=1",
                f"Deposit={balance}",
                "Currency=USD",
                "Leverage=1:400",
                "UseLocal=1",
                "UseRemote=0",
                "UseCloud=0",
                "Visual=0",
                "",
            ]
        )
        validate_tester_config(content)
        (args.output / f"{tag}.ini").write_text(content, encoding="utf-8")
        (args.output / params).write_text(
            f"RiskPercent={risk}.0\nRunTag={tag}\n"
            f"AllowMinimumLotFallback={'true' if args.minimum_lot_fallback else 'false'}\n",
            encoding="utf-16",
        )
        configs.append(
            {
                "tag": tag,
                "balance": balance,
                "risk": risk,
                "smoke": smoke,
                "minimum_lot_fallback": args.minimum_lot_fallback,
            }
        )
    (args.output / "matrix.json").write_text(json.dumps(configs, indent=2) + "\n")
    print(json.dumps(configs, indent=2))


if __name__ == "__main__":
    main()
