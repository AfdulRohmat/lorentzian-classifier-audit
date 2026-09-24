from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

OHLC = ["open", "high", "low", "close"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _month_in_scope(path: Path, start: pd.Timestamp, end: pd.Timestamp) -> bool:
    try:
        month = pd.Period(path.stem, freq="M")
    except ValueError:
        return False
    naive_start = start.tz_localize(None) if start.tzinfo is not None else start
    naive_end = end.tz_localize(None) if end.tzinfo is not None else end
    return month >= naive_start.to_period("M") and month < naive_end.to_period("M")


def normalise_minutes(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    data = frame.copy()
    data["time"] = pd.to_datetime(data["time"], utc=True)
    data = data.sort_values("time")
    duplicate_rows = int(data["time"].duplicated(keep="last").sum())
    data = data.drop_duplicates("time", keep="last").set_index("time")
    finite = np.isfinite(data[[*OHLC, "spread"]]).all(axis=1)
    coherent = (
        (data[OHLC] > 0).all(axis=1)
        & (data["spread"] >= 0)
        & (data["high"] >= data[["open", "close"]].max(axis=1))
        & (data["low"] <= data[["open", "close"]].min(axis=1))
    )
    invalid_rows = int((~(finite & coherent)).sum())
    data = data.loc[finite & coherent, [*OHLC, "spread", "tick_volume"]]
    return data, {
        "duplicate_rows_removed": duplicate_rows,
        "invalid_rows_removed": invalid_rows,
    }


def aggregate_h4(minutes: pd.DataFrame, minimum_rows: int = 1) -> pd.DataFrame:
    bars = minutes.resample("4h", label="left", closed="left", origin="epoch").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        spread_points=("spread", "first"),
        tick_volume=("tick_volume", "sum"),
        m1_rows=("close", "count"),
    )
    bars = bars.loc[bars["m1_rows"] >= minimum_rows].copy()
    bars.index.name = "time"
    bars["bar_end"] = bars.index + pd.Timedelta(hours=4)
    return bars


def load_asset_h4(
    root: Path, asset: str, asset_config: dict, data_config: dict
) -> tuple[pd.DataFrame, dict]:
    source = (root / asset_config["path"]).resolve()
    start = pd.Timestamp(data_config["source_start"])
    end = pd.Timestamp(data_config["source_end_exclusive"])
    files = [
        path for path in sorted(source.glob("*.parquet")) if _month_in_scope(path, start, end)
    ]
    if not files:
        raise FileNotFoundError(f"No source files for {asset}: {source}")

    frames: list[pd.DataFrame] = []
    manifest: list[dict] = []
    for path in files:
        frame = pd.read_parquet(
            path,
            columns=["time", "open", "high", "low", "close", "tick_volume", "spread"],
        )
        frames.append(frame)
        manifest.append(
            {
                "path": str(path),
                "name": path.name,
                "bytes": path.stat().st_size,
                "rows": len(frame),
                "sha256": sha256_file(path),
            }
        )

    minutes, cleaning = normalise_minutes(pd.concat(frames, ignore_index=True))
    minutes = minutes.loc[(minutes.index >= start) & (minutes.index < end)]
    h4 = aggregate_h4(minutes, int(data_config["minimum_m1_rows_per_bar"]))
    diagnostics = {
        "asset": asset,
        "source_path": str(source),
        "files": manifest,
        "file_count": len(files),
        "raw_rows": int(sum(item["rows"] for item in manifest)),
        "minute_rows": len(minutes),
        "first_minute": minutes.index.min().isoformat(),
        "last_minute": minutes.index.max().isoformat(),
        "h4_bars": len(h4),
        "first_h4": h4.index.min().isoformat(),
        "last_h4": h4.index.max().isoformat(),
        "h4_m1_rows_min": int(h4["m1_rows"].min()),
        "h4_m1_rows_median": float(h4["m1_rows"].median()),
        "h4_m1_rows_max": int(h4["m1_rows"].max()),
        **cleaning,
    }
    return h4, diagnostics
