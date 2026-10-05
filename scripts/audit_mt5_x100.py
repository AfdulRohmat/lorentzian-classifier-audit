"""Read-only terminal audit. Does not import or call order_send."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()
    import MetaTrader5 as mt5

    report = {
        "captured_utc": datetime.now(UTC).isoformat(),
        "read_only": True,
        "status": "NOT_CONNECTED",
        "orders_submitted": 0,
    }
    try:
        connected = mt5.initialize(
            r"C:\Program Files\MetaTrader 5\terminal64.exe", timeout=args.timeout_ms
        )
        if not connected:
            report["error"] = list(mt5.last_error())
            return_code = 2
        else:
            terminal = mt5.terminal_info()
            account = mt5.account_info()
            report["terminal"] = {
                k: getattr(terminal, k, None)
                for k in ["connected", "build", "maxbars", "trade_allowed", "tradeapi_disabled"]
            }
            report["account"] = {
                k: getattr(account, k, None)
                for k in [
                    "currency",
                    "leverage",
                    "trade_mode",
                    "margin_mode",
                    "margin_so_mode",
                    "margin_so_call",
                    "margin_so_so",
                ]
            }
            names = [s.name for s in (mt5.symbols_get() or ()) if "US500" in s.name.upper()]
            report["matching_symbols"] = names
            report["symbols"] = []
            for name in names:
                info = mt5.symbol_info(name)
                record = {
                    k: getattr(info, k, None)
                    for k in [
                        "name",
                        "digits",
                        "point",
                        "trade_contract_size",
                        "trade_tick_size",
                        "trade_tick_value",
                        "trade_tick_value_profit",
                        "trade_tick_value_loss",
                        "volume_min",
                        "volume_max",
                        "volume_step",
                        "volume_limit",
                        "trade_stops_level",
                        "trade_freeze_level",
                        "trade_calc_mode",
                        "trade_mode",
                        "filling_mode",
                        "order_mode",
                        "currency_base",
                        "currency_profit",
                        "currency_margin",
                        "margin_initial",
                        "margin_maintenance",
                        "swap_mode",
                        "swap_long",
                        "swap_short",
                        "swap_rollover3days",
                        "spread",
                        "spread_float",
                    ]
                }
                if name.upper() == "US500_X100":
                    mt5.symbol_select(name, True)
                    bars = mt5.copy_rates_from_pos(name, mt5.TIMEFRAME_M30, 0, 100)
                    record["recent_m30_count"] = 0 if bars is None else len(bars)
                    record["history_error"] = list(mt5.last_error())
                    if bars is not None and len(bars):
                        record["recent_m30_first_utc"] = datetime.fromtimestamp(
                            int(bars[0]["time"]), UTC
                        ).isoformat()
                        record["recent_m30_last_utc"] = datetime.fromtimestamp(
                            int(bars[-1]["time"]), UTC
                        ).isoformat()
                report["symbols"].append(record)
            report["status"] = (
                "CONNECTED_SYMBOL_FOUND"
                if any(n.upper() == "US500_X100" for n in names)
                else "SYMBOL_UNAVAILABLE"
            )
            if not report["terminal"]["connected"]:
                report["status"] = "DISCONNECTED_CACHED_METADATA_ONLY"
            return_code = 0 if report["status"] == "CONNECTED_SYMBOL_FOUND" else 2
    finally:
        mt5.shutdown()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
