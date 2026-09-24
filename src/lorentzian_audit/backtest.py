from __future__ import annotations

import numpy as np
import pandas as pd


def event_windows(signals: pd.DataFrame, bar_count: int) -> list[tuple[int, int, int, int]]:
    events = [
        (i, 1 if bool(row.start_long) else -1)
        for i, row in enumerate(signals.itertuples())
        if bool(row.start_long) or bool(row.start_short)
    ]
    windows: list[tuple[int, int, int, int]] = []
    pointer = 0
    while pointer < len(events):
        signal_index, direction = events[pointer]
        entry_index = signal_index + 1
        if entry_index >= bar_count:
            break
        fixed_exit_signal = signal_index + 4
        opposite_pointer: int | None = None
        scan = pointer + 1
        while scan < len(events) and events[scan][0] <= fixed_exit_signal:
            if events[scan][1] != direction:
                opposite_pointer = scan
                break
            scan += 1
        exit_signal = (
            events[opposite_pointer][0] if opposite_pointer is not None else fixed_exit_signal
        )
        exit_index = exit_signal + 1
        if exit_index >= bar_count:
            break
        windows.append((signal_index, entry_index, exit_index, direction))
        if opposite_pointer is not None:
            pointer = opposite_pointer
        else:
            pointer += 1
            while pointer < len(events) and events[pointer][0] <= exit_signal:
                pointer += 1
    return windows


def _spread(raw_points: float, point: float, profile: dict) -> float:
    return max(
        raw_points * point * float(profile["spread_multiplier"]), float(profile["spread_floor"])
    )


def price_trade(
    row: pd.Series, direction: int, point: float, profile: dict
) -> dict[str, float]:
    entry_bid = float(row["entry_bid"])
    exit_bid = float(row["exit_bid"])
    entry_spread = _spread(float(row["entry_spread_points"]), point, profile)
    exit_spread = _spread(float(row["exit_spread_points"]), point, profile)
    slippage = float(profile["slippage_side"])
    commission = float(profile["commission_round_trip_price"])
    gross = direction * (exit_bid - entry_bid)
    paid_spread = entry_spread if direction > 0 else exit_spread
    net = gross - paid_spread - 2.0 * slippage - commission
    return {
        "direction": direction,
        "gross_points": gross,
        "paid_spread_points": paid_spread,
        "slippage_points": 2.0 * slippage,
        "commission_points": commission,
        "net_points": net,
        "gross_bps": gross / entry_bid * 10000.0,
        "net_bps": net / entry_bid * 10000.0,
    }


def build_trades(
    asset: str,
    variant: str,
    bars: pd.DataFrame,
    signals: pd.DataFrame,
    asset_config: dict,
    costs: dict,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
) -> pd.DataFrame:
    rows: list[dict] = []
    for signal_index, entry_index, exit_index, direction in event_windows(signals, len(bars)):
        entry_time = bars.index[entry_index]
        exit_time = bars.index[exit_index]
        if entry_time < evaluation_start or exit_time >= evaluation_end:
            continue
        raw = pd.Series(
            {
                "entry_bid": bars.iloc[entry_index]["open"],
                "exit_bid": bars.iloc[exit_index]["open"],
                "entry_spread_points": bars.iloc[entry_index]["spread_points"],
                "exit_spread_points": bars.iloc[exit_index]["spread_points"],
            }
        )
        base = price_trade(raw, direction, float(asset_config["point"]), costs["base"])
        stress = price_trade(raw, direction, float(asset_config["point"]), costs["stress"])
        rows.append(
            {
                "asset": asset,
                "variant": variant,
                "trade_id": len(rows) + 1,
                "signal_time": bars.index[signal_index],
                "entry_time": entry_time,
                "exit_time": exit_time,
                "holding_hours": (exit_time - entry_time).total_seconds() / 3600.0,
                "entry_bid": float(raw["entry_bid"]),
                "exit_bid": float(raw["exit_bid"]),
                "entry_spread_points": float(raw["entry_spread_points"]),
                "exit_spread_points": float(raw["exit_spread_points"]),
                "direction": direction,
                "gross_points": base["gross_points"],
                "gross_bps": base["gross_bps"],
                "base_spread_points": base["paid_spread_points"],
                "base_slippage_points": base["slippage_points"],
                "base_commission_points": base["commission_points"],
                "base_net_points": base["net_points"],
                "base_net_bps": base["net_bps"],
                "stress_net_points": stress["net_points"],
                "stress_net_bps": stress["net_bps"],
            }
        )
    return pd.DataFrame(rows)


def reprice_directions(
    trades: pd.DataFrame, directions: np.ndarray, point: float, profile: dict
) -> np.ndarray:
    values = np.zeros(len(trades), dtype=float)
    for i, (row, direction) in enumerate(
        zip(trades.to_dict("records"), directions, strict=True)
    ):
        priced = price_trade(pd.Series(row), int(direction), point, profile)
        values[i] = priced["net_bps"]
    return values
