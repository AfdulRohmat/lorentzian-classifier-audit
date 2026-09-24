from __future__ import annotations

import math

import numpy as np
import pandas as pd
from lorentzian_classification.core import calc_atr


def effective_spread(raw_points: float, point: float, profile: dict) -> float:
    return max(
        raw_points * point * float(profile["spread_multiplier"]),
        float(profile["spread_floor"]),
    )


def floor_volume(risk_budget: float, loss_per_lot: float, spec: dict) -> float:
    if risk_budget <= 0 or loss_per_lot <= 0:
        return 0.0
    step = float(spec["volume_step"])
    raw = min(risk_budget / loss_per_lot, float(spec["volume_max"]))
    volume = math.floor(raw / step + 1e-12) * step
    if volume + 1e-12 < float(spec["volume_min"]):
        return 0.0
    return round(volume, 8)


def stop_exit(
    row: pd.Series,
    side: int,
    stop: float,
    point: float,
    profile: dict,
) -> tuple[float, str] | None:
    spread = effective_spread(float(row.spread), point, profile)
    slip = float(profile["slippage_side"])
    if side == 1:
        if float(row.open) <= stop:
            return float(row.open) - slip, "STOP_GAP"
        if float(row.low) <= stop:
            return stop - slip, "STOP_INTRAMINUTE"
    else:
        ask_open = float(row.open) + spread
        ask_high = float(row.high) + spread
        if ask_open >= stop:
            return ask_open + slip, "STOP_GAP"
        if ask_high >= stop:
            return stop + slip, "STOP_INTRAMINUTE"
    return None


def market_exit_fill(
    row: pd.Series, side: int, point: float, profile: dict
) -> float:
    spread = effective_spread(float(row.spread), point, profile)
    slip = float(profile["slippage_side"])
    return (
        float(row.open) - slip
        if side == 1
        else float(row.open) + spread + slip
    )


def proposed_trailing_stop(
    *,
    entry_fill: float,
    side: int,
    locked_net_r: float,
    planned_risk_price: float,
    profile: dict,
) -> float:
    exit_friction = float(profile["slippage_side"]) + float(
        profile["commission_round_trip_price"]
    )
    return entry_fill + side * (locked_net_r * planned_risk_price + exit_friction)


def tighten_stop(current: float, proposed: float, side: int) -> float:
    return proposed if side * (proposed - current) > 0 else current


def _entry_events(
    bars: pd.DataFrame,
    signals: pd.DataFrame,
    minutes: pd.DataFrame,
    atr_period: int,
) -> list[dict]:
    atr = np.asarray(
        calc_atr(
            bars["high"].astype(float).tolist(),
            bars["low"].astype(float).tolist(),
            bars["close"].astype(float).tolist(),
            atr_period,
        ),
        dtype=float,
    )
    minute_ns = minutes.index.as_unit("ns").asi8
    events: list[dict] = []
    for signal_index, row in enumerate(signals.itertuples(index=False)):
        side = 1 if bool(row.start_long) else -1 if bool(row.start_short) else 0
        if side == 0 or signal_index + 1 >= len(bars) or not np.isfinite(atr[signal_index]):
            continue
        next_bar = bars.iloc[signal_index + 1]
        label = bars.index[signal_index + 1]
        position = int(np.searchsorted(minute_ns, label.value, side="left"))
        if position >= len(minutes) or minutes.index[position] >= next_bar.bar_end:
            continue
        events.append(
            {
                "signal_time": bars.index[signal_index],
                "entry_time": minutes.index[position],
                "entry_position": position,
                "direction": side,
                "atr": float(atr[signal_index]),
            }
        )
    return events


def _mark_net_r(
    bid_close: float,
    raw_spread: float,
    side: int,
    entry_fill: float,
    planned_risk_price: float,
    point: float,
    profile: dict,
) -> float:
    liquidation = bid_close
    if side == -1:
        liquidation += effective_spread(raw_spread, point, profile)
    hypothetical_fill = liquidation - side * float(profile["slippage_side"])
    net_price = (
        side * (hypothetical_fill - entry_fill)
        - float(profile["commission_round_trip_price"])
    )
    return net_price / planned_risk_price


def build_runner_trades(
    *,
    asset: str,
    timeframe: str,
    bars: pd.DataFrame,
    minutes: pd.DataFrame,
    signals: pd.DataFrame,
    asset_config: dict,
    profile: dict,
    exit_config: dict,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
) -> pd.DataFrame:
    events = _entry_events(
        bars, signals, minutes, int(exit_config["atr_period"])
    )
    events = [
        event
        for event in events
        if evaluation_start <= event["entry_time"] < evaluation_end
    ]
    if not events:
        return pd.DataFrame()

    point = float(asset_config["point"])
    contract_size = float(asset_config["contract_size"])
    stop_atr = float(exit_config["initial_stop_atr"])
    activation = float(exit_config["trail_activation_net_r"])
    distance = float(exit_config["trail_distance_net_r"])
    maximum_hold = pd.Timedelta(hours=float(exit_config["maximum_holding_hours"]))
    slip = float(profile["slippage_side"])
    commission = float(profile["commission_round_trip_price"])
    minute_ns = minutes.index.as_unit("ns").asi8
    event_ns = np.asarray([event["entry_time"].value for event in events], dtype=np.int64)
    update_ns = bars["bar_end"].array.as_unit("ns").asi8
    rows: list[dict] = []
    pointer = 0

    while pointer < len(events):
        event = events[pointer]
        entry_time = event["entry_time"]
        if entry_time >= evaluation_end:
            break
        side = int(event["direction"])
        entry_position = int(event["entry_position"])
        entry_row = minutes.iloc[entry_position]
        spread = effective_spread(float(entry_row.spread), point, profile)
        entry_fill = (
            float(entry_row.open) + spread + slip
            if side == 1
            else float(entry_row.open) - slip
        )
        atr_distance = float(event["atr"]) * stop_atr
        if not np.isfinite(atr_distance) or atr_distance <= 0:
            pointer += 1
            continue
        planned_risk_price = atr_distance + slip + commission
        initial_stop = entry_fill - side * atr_distance
        stop = initial_stop
        best_net_r = -np.inf
        trail_updates = 0
        trail_activated = False
        deadline = entry_time + maximum_hold

        opposite_index: int | None = None
        for candidate in range(pointer + 1, len(events)):
            if int(events[candidate]["direction"]) != side:
                opposite_index = candidate
                break
        opposite_time = (
            events[opposite_index]["entry_time"] if opposite_index is not None else None
        )
        update_pointer = int(np.searchsorted(update_ns, entry_time.value, side="right"))
        exit_time: pd.Timestamp | None = None
        exit_fill: float | None = None
        exit_reason: str | None = None
        final_position = int(
            np.searchsorted(minute_ns, evaluation_end.value, side="left")
        )

        for minute_position in range(entry_position, final_position):
            stamp = minutes.index[minute_position]
            minute_row = minutes.iloc[minute_position]
            while update_pointer < len(bars) and update_ns[update_pointer] <= stamp.value:
                update_bar = bars.iloc[update_pointer]
                mark_r = _mark_net_r(
                    float(update_bar.close),
                    float(update_bar.spread_close_points),
                    side,
                    entry_fill,
                    planned_risk_price,
                    point,
                    profile,
                )
                best_net_r = max(best_net_r, mark_r)
                if best_net_r >= activation:
                    locked = best_net_r - distance
                    proposed = proposed_trailing_stop(
                        entry_fill=entry_fill,
                        side=side,
                        locked_net_r=locked,
                        planned_risk_price=planned_risk_price,
                        profile=profile,
                    )
                    tightened = tighten_stop(stop, proposed, side)
                    if tightened != stop:
                        stop = tightened
                        trail_updates += 1
                        trail_activated = True
                update_pointer += 1

            stopped = stop_exit(minute_row, side, stop, point, profile)
            if stopped is not None:
                exit_fill, exit_reason = stopped
                if trail_activated:
                    exit_reason = exit_reason.replace("STOP", "TRAIL_STOP", 1)
                exit_time = stamp
                break
            if stamp >= deadline:
                exit_fill = market_exit_fill(minute_row, side, point, profile)
                exit_reason = "TIME_24H"
                exit_time = stamp
                break
            if opposite_time is not None and stamp >= opposite_time:
                exit_fill = market_exit_fill(minute_row, side, point, profile)
                exit_reason = "OPPOSITE"
                exit_time = stamp
                break

        if exit_time is None or exit_fill is None or exit_reason is None:
            break
        net_price = side * (exit_fill - entry_fill) - commission
        net_r = net_price / planned_risk_price
        rows.append(
            {
                "asset": asset,
                "timeframe": timeframe,
                "trade_id": len(rows) + 1,
                "signal_time": event["signal_time"],
                "entry_time": entry_time,
                "exit_time": exit_time,
                "direction": side,
                "entry_fill": entry_fill,
                "exit_fill": exit_fill,
                "atr": float(event["atr"]),
                "initial_stop": initial_stop,
                "final_stop": stop,
                "planned_risk_price": planned_risk_price,
                "planned_loss_per_lot": planned_risk_price * contract_size,
                "net_price": net_price,
                "net_per_lot_usd": net_price * contract_size,
                "net_r": net_r,
                "holding_hours": (exit_time - entry_time).total_seconds() / 3600.0,
                "exit_reason": exit_reason,
                "trail_activated": trail_activated,
                "trail_updates": trail_updates,
                "best_completed_net_r": (
                    best_net_r if np.isfinite(best_net_r) else None
                ),
            }
        )

        if opposite_index is not None and exit_time == opposite_time:
            pointer = opposite_index
        else:
            pointer = int(np.searchsorted(event_ns, exit_time.value, side="right"))

    return pd.DataFrame(rows)


def simulate_account(
    trades: pd.DataFrame,
    asset_config: dict,
    initial_balance: float,
    risk_percent: float,
    evaluation_start: pd.Timestamp,
    evaluation_end: pd.Timestamp,
) -> tuple[pd.DataFrame, dict]:
    equity = float(initial_balance)
    peak = equity
    maximum_drawdown = 0.0
    executed = 0
    skipped = 0
    breached = 0
    rows: list[dict] = []
    worst_loss_budget_ratio = 0.0
    for trade in trades.itertuples(index=False):
        before = equity
        budget = before * risk_percent / 100.0
        volume = floor_volume(budget, float(trade.planned_loss_per_lot), asset_config)
        if volume == 0:
            skipped += 1
            rows.append(
                {
                    "trade_id": trade.trade_id,
                    "entry_time": trade.entry_time,
                    "exit_time": trade.exit_time,
                    "equity_before": before,
                    "risk_budget_usd": budget,
                    "volume": 0.0,
                    "pnl_usd": 0.0,
                    "equity_after": before,
                    "status": "SKIP_MIN_LOT",
                }
            )
            continue
        pnl = float(trade.net_per_lot_usd) * volume
        equity += pnl
        executed += 1
        if pnl < -budget - 1e-9:
            breached += 1
        if pnl < 0 and budget > 0:
            worst_loss_budget_ratio = max(worst_loss_budget_ratio, -pnl / budget)
        peak = max(peak, equity)
        if peak > 0:
            maximum_drawdown = max(maximum_drawdown, (peak - equity) / peak)
        rows.append(
            {
                "trade_id": trade.trade_id,
                "entry_time": trade.entry_time,
                "exit_time": trade.exit_time,
                "equity_before": before,
                "risk_budget_usd": budget,
                "volume": volume,
                "pnl_usd": pnl,
                "equity_after": equity,
                "status": "EXECUTED",
            }
        )
        if equity <= 0:
            break
    ledger = pd.DataFrame(rows)
    months = pd.period_range(
        evaluation_start.tz_localize(None),
        (evaluation_end - pd.Timedelta(days=1)).tz_localize(None),
        freq="M",
    )
    if ledger.empty:
        month_pnl = pd.Series(0.0, index=months)
    else:
        executed_rows = ledger.loc[ledger.status.eq("EXECUTED")].copy()
        if executed_rows.empty:
            month_pnl = pd.Series(0.0, index=months)
        else:
            executed_rows["month"] = (
                pd.to_datetime(executed_rows.exit_time)
                .dt.tz_localize(None)
                .dt.to_period("M")
            )
            month_pnl = executed_rows.groupby("month").pnl_usd.sum().reindex(
                months, fill_value=0.0
            )
    rolling_equity = float(initial_balance)
    monthly_returns: list[float] = []
    for pnl in month_pnl.to_numpy(dtype=float):
        monthly_returns.append(pnl / rolling_equity * 100.0 if rolling_equity > 0 else -100.0)
        rolling_equity += pnl
    mean_monthly = float(np.mean(monthly_returns)) if monthly_returns else 0.0
    result = {
        "initial_balance_usd": initial_balance,
        "risk_percent": risk_percent,
        "candidate_trades": len(trades),
        "executed_trades": executed,
        "skipped_min_lot": skipped,
        "executable_fraction": executed / len(trades) if len(trades) else 0.0,
        "final_balance_usd": equity,
        "return_percent": (equity / initial_balance - 1.0) * 100.0,
        "maximum_balance_drawdown_percent": maximum_drawdown * 100.0,
        "mean_monthly_return_percent": mean_monthly,
        "risk_budget_breaches": breached,
        "worst_realized_loss_over_budget": worst_loss_budget_ratio,
        "ruined": equity <= 0,
    }
    return ledger, result
