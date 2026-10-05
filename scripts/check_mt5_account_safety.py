"""Read-only final safety check; never exports login IDs or sends orders."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    import MetaTrader5 as mt5

    result = dict(captured_utc=datetime.now(UTC).isoformat(), read_only=True)
    try:
        if not mt5.initialize(r"C:\Program Files\MetaTrader 5\terminal64.exe", timeout=15000):
            raise RuntimeError(f"Terminal unavailable, error code {mt5.last_error()[0]}")
        terminal, account = mt5.terminal_info(), mt5.account_info()
        positions, orders = mt5.positions_get(), mt5.orders_get()
        if terminal is None or account is None or positions is None or orders is None:
            raise RuntimeError("Incomplete read-only account response; flat status is unknown")
        result.update(
            connected=bool(terminal.connected),
            algo_trading_enabled=bool(terminal.trade_allowed),
            demo_account=account.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO,
            currency=account.currency,
            positions_count=len(positions),
            pending_orders_count=len(orders),
            build=terminal.build,
        )
        passed = (
            result["connected"]
            and result["demo_account"]
            and not result["algo_trading_enabled"]
            and not positions
            and not orders
        )
        result["status"] = "PASS" if passed else "REVIEW_REQUIRED_NO_ACCOUNT_MUTATIONS"
    finally:
        mt5.shutdown()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
