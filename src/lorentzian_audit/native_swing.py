"""Execution-path audit of exported native swing ledgers; no synthetic trades."""

from __future__ import annotations

import numpy as np
import pandas as pd


def validate_coverage(stats, deals, signals_raw, expected_raw, expected_stats):
    if float(stats["first_tick"]) != float(expected_stats["first_tick"]):
        raise ValueError("Native test started at a different time")
    full_fields = ("last_tick", "tick_count", "classifier_bars")
    if all(float(stats[k]) == float(expected_stats[k]) for k in full_fields):
        if signals_raw != expected_raw:
            raise ValueError("Classifier signal stream changed")
        return "FULL_WINDOW"
    exits = deals.loc[deals.entry.isin([1, 3])].sort_values("time")
    if (
        exits.empty
        or float(stats["final_balance"]) > 0
        or int(exits.iloc[-1].reason) != 6
        # Tester can stop out before delivering that quote to the EA OnTick.
        or not 0 <= int(exits.iloc[-1].time) - int(stats["last_tick"]) <= 60
        or int(stats["last_tick"]) >= int(expected_stats["last_tick"])
        or int(stats["tick_count"]) >= int(expected_stats["tick_count"])
        or int(stats["classifier_bars"]) >= int(expected_stats["classifier_bars"])
        or not signals_raw
        or not expected_raw.startswith(signals_raw)
    ):
        raise ValueError("Early end without verified insolvent stop-out and signal prefix")
    return "STOPPED_EARLY_INSOLVENT"


def audit_swing(
    stats: dict, deals: pd.DataFrame, events: pd.DataFrame, signals: pd.DataFrame
) -> dict:
    k = int(stats["stop_atr_multiplier"])
    if not 1 <= k <= 10:
        raise ValueError("Invalid stop multiplier")
    if (
        int(stats["max_holding_hours"]) == 0
        and (events.event.eq("EXIT") & events.detail.eq("time_24h")).any()
    ):
        raise ValueError("Time exit in swing variant")
    if (deals.entry.isin([1, 3]) & deals.reason.eq(5)).any():
        raise ValueError("Fixed TP execution in no-TP strategy")

    def known_start(stamp: int) -> int:
        known = signals.loc[signals.time <= stamp - stamp % 1800 - 1800]
        return int(known.iloc[-1].start) if len(known) else 0

    entries = events.index[events.event.eq("ENTRY")].tolist()
    specifications = dict(
        events.loc[events.event.eq("SPEC"), ["detail", "value"]].itertuples(
            index=False, name=None
        )
    )
    paths = {}
    for n, start in enumerate(entries):
        stop = entries[n + 1] if n + 1 < len(entries) else len(events)
        block = events.iloc[start:stop]
        side = int(float(block.iloc[0].detail))
        stamp = int(block.iloc[0].time)
        if known_start(stamp) != side:
            raise ValueError("Entry lacks a matching completed-bar start")
        initial = float(block.loc[block.event.eq("ENTRY_INITIAL_STOP"), "value"].iloc[0])
        atr = float(block.loc[block.event.eq("ENTRY_ATR"), "value"].iloc[0])
        risk = float(block.loc[block.event.eq("ENTRY_RISK_PRICE"), "value"].iloc[0])
        planned = float(block.loc[block.event.eq("ENTRY_PLANNED_RISK"), "value"].iloc[0])
        budget = float(block.loc[block.event.eq("ENTRY_BUDGET"), "value"].iloc[0])
        fill = deals.loc[deals.entry.eq(0) & deals.time.eq(stamp)]
        if len(fill) != 1 or (side == 1) != (int(fill.iloc[0]["type"]) == 0):
            raise ValueError("Entry journal and deal mismatch")
        distance = side * (float(fill.iloc[0].price) - initial)
        if not -1e-7 <= distance - k * atr <= 0.010001:
            raise ValueError("Stop does not match frozen ATR multiplier")
        if abs(risk - distance - 0.27) > 1e-7:
            raise ValueError("Risk distance does not include frozen reserve")
        volume = float(fill.iloc[0].volume)
        contract = float(specifications.get("contract_size", 100))
        minimum = float(specifications.get("volume_min", 0.01))
        step = float(specifications.get("volume_step", 0.01))
        maximum = float(specifications.get("volume_max", 20))
        if abs(planned - risk * volume * contract) > 1e-6:
            raise ValueError("Planned monetary risk differs from native symbol contract")
        expected_volume = (
            np.floor(min(budget / (risk * contract), maximum) / step + 1e-12) * step
        )
        if expected_volume < minimum - 1e-12:
            expected_volume = minimum if int(stats.get("minimum_lot_fallback", 0)) else 0
        if int(stats.get("fixed_minimum_lot", 0)):
            expected_volume = minimum
        if abs(volume - expected_volume) > 1e-8:
            raise ValueError("Position size differs from risk and minimum-lot policy")
        trail = block.loc[block.event.eq("TRAIL"), "value"].to_numpy(float)
        if (side * np.diff(np.r_[initial, trail]) <= 0).any():
            raise ValueError("Trailing stop loosened")
        marks = block.loc[block.event.eq("MARK_R"), "value"].to_numpy(float)
        if len(trail) and (not len(marks) or max(marks) < 1):
            raise ValueError("Trail activated without completed-bar +1R")
        peak = -np.inf
        for row in block.itertuples():
            if row.event == "MARK_R":
                peak = max(peak, float(row.value))
            elif row.event == "TRAIL":
                expected = float(fill.iloc[0].price) + side * ((peak - 1) * risk + 0.27)
                if peak < 1 or not -1e-7 <= side * (expected - float(row.value)) <= 0.010001:
                    raise ValueError("Trail activation or width differs from initial R")
            elif row.event == "EXIT" and row.detail == "opposite":
                deferred = block.loc[
                    (block.time <= row.time) & block.event.eq("CLOSE_DEFERRED")
                ]
                trigger = int(deferred.iloc[0].time) if len(deferred) else int(row.time)
                if known_start(trigger) != -side:
                    raise ValueError("Exit not triggered by an opposite completed-bar start")
        paths[stamp] = (planned, max(0.0, max(marks)) if len(marks) else 0.0, len(trail) > 0)
    durations, realized_r, giveback = [], [], []
    overnight, weekend = 0, 0
    initial_stops, trailing_stops = 0, 0
    for _, group in deals.groupby("position_id"):
        entry = int(group.loc[group.entry.eq(0), "time"].min())
        end = int(group.loc[group.entry.isin([1, 3]), "time"].max())
        duration = (end - entry) / 3600
        durations.append(duration)
        begin_dt, end_dt = pd.to_datetime([entry, end], unit="s", utc=True)
        overnight += begin_dt.date() != end_dt.date()
        weekend += any(
            day.weekday() >= 5
            for day in pd.date_range(begin_dt.normalize(), end_dt.normalize())
        )
        pnl = float(group[["profit", "commission", "fee", "swap"]].to_numpy().sum())
        planned, peak, trailed = paths[entry]
        sl_exit = (group.entry.isin([1, 3]) & group.reason.eq(4)).any()
        initial_stops += int(sl_exit and not trailed)
        trailing_stops += int(sl_exit and trailed)
        r = pnl / planned
        realized_r.append(r)
        giveback.append(max(0.0, peak - r))
    return dict(
        path_audit="PASS",
        mean_holding_hours=float(np.mean(durations)) if durations else None,
        median_holding_hours=float(np.median(durations)) if durations else None,
        max_holding_hours_observed=max(durations) if durations else None,
        trades_over_24h=sum(h > 24 for h in durations),
        overnight_trades=int(overnight),
        weekend_trades=int(weekend),
        mean_realized_r=float(np.mean(realized_r)) if realized_r else None,
        mean_completed_bar_giveback_r=float(np.mean(giveback)) if giveback else None,
        initial_stop_trades=initial_stops,
        trailing_stop_trades=trailing_stops,
        exits=events.loc[events.event.eq("EXIT"), "detail"].value_counts().to_dict(),
        native_sl_deals=int((deals.entry.isin([1, 3]) & deals.reason.eq(4)).sum()),
    )
