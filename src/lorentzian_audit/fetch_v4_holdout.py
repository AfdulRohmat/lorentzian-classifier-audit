from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TERMINAL = Path(r"C:\Program Files\MetaTrader 5\terminal64.exe")
OUTPUT = ROOT / "local_data" / "exness_us500_2026-09-01_2026-09-24_m1.parquet"
START = datetime(2026, 9, 1, tzinfo=UTC)
END = datetime(2026, 9, 24, tzinfo=UTC)
RATE_COLUMNS = [
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    import MetaTrader5 as mt5  # type: ignore[import-untyped]

    if not TERMINAL.is_file():
        raise FileNotFoundError(TERMINAL)
    if not mt5.initialize(str(TERMINAL), timeout=30_000):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        if terminal is None or not terminal.connected or account is None:
            raise RuntimeError("MT5 is not connected to an authorized broker session")
        if not mt5.symbol_select("US500", True):
            raise RuntimeError(f"symbol_select failed: {mt5.last_error()}")
        info = mt5.symbol_info("US500")
        if info is None:
            raise RuntimeError(f"symbol_info failed: {mt5.last_error()}")
        raw = mt5.copy_rates_range("US500", mt5.TIMEFRAME_M1, START, END)
        if raw is None:
            raise RuntimeError(f"copy_rates_range failed: {mt5.last_error()}")
        frame = pd.DataFrame(raw)
        missing = set(RATE_COLUMNS).difference(frame.columns)
        if missing:
            raise ValueError(f"MT5 rates missing fields: {sorted(missing)}")
        frame = frame[RATE_COLUMNS].copy()
        frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True)
        frame = frame.loc[(frame.time >= START) & (frame.time < END)]
        frame = frame.sort_values("time").drop_duplicates("time", keep="last")
        if frame.empty:
            raise ValueError("MT5 returned no September US500 bars")
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(OUTPUT, index=False)
        metadata = {
            "observed_at_utc": datetime.now(UTC).isoformat(),
            "broker_company": account.company,
            "broker_server": account.server,
            "terminal_build": terminal.build,
            "symbol": info.name,
            "symbol_path": info.path,
            "contract_size": info.trade_contract_size,
            "volume_min": info.volume_min,
            "volume_step": info.volume_step,
            "requested_start": START.isoformat(),
            "requested_end_exclusive": END.isoformat(),
            "rows": len(frame),
            "first_bar": frame.time.min().isoformat(),
            "last_bar": frame.time.max().isoformat(),
            "duplicate_rows_after_normalization": int(frame.time.duplicated().sum()),
            "sha256": _sha256(OUTPUT),
        }
        OUTPUT.with_suffix(".json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(metadata, indent=2, sort_keys=True))
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
