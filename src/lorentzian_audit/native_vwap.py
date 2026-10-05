"""Independent reconstruction of native bar-benchmark and entry eligibility."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lorentzian_audit.native_results import summarize_native
from lorentzian_audit.native_swing import audit_swing


def gate(z, valid, side):
    z, valid, side = np.asarray(z), np.asarray(valid, bool), np.asarray(side)
    return (
        valid
        & (np.abs(z) <= 3)
        & ((np.abs(z) < 1) | ((z <= -1) & (side == 1)) | ((z >= 1) & (side == -1)))
    )


def clock_eligible(quote, signal):
    q = pd.to_datetime(quote, unit="s", utc=True).tz_convert("America/New_York")
    s = pd.to_datetime(signal, unit="s", utc=True).tz_convert("America/New_York")
    qm, sm = q.hour * 60 + q.minute, s.hour * 60 + s.minute
    if (
        q.year != 2026
        or q.weekday() >= 5
        or q.strftime("%m-%d")
        in {
            "01-01",
            "01-19",
            "02-16",
            "04-03",
            "05-25",
            "06-19",
            "07-03",
        }
    ):
        return False
    return (qm >= 570) & (qm < 930) & (sm >= 570) & (q.date() == s.date())


def reconstruct_benchmark(signals):
    src = signals.copy()
    day = src.time // 86400
    w = src.tick_volume.astype(float)
    p = (src.high + src.low + src.close) / 3
    # Center each day to avoid catastrophic cancellation in independent variance.
    origin = p.groupby(day).transform("first")
    total = w.groupby(day).cumsum()
    delta = p - origin
    mu = (w * delta).groupby(day).cumsum() / total
    var = (w * delta**2).groupby(day).cumsum() / total - mu**2
    mean = (mu + origin).where(total > 0, 0)
    sd = np.sqrt(np.maximum(var.fillna(0), 0)).where(w > 0, 0)
    valid = (sd > 1e-9) & (w > 0)
    z = np.where(valid, (src.close - mean) / sd.where(sd > 0), 0)
    return mean, sd, z, valid


def audit_vwap(stats, deals, events, signals):
    summary, monthly = summarize_native(stats, deals, events)
    summary.update(audit_swing(stats, deals, events, signals))
    ordered = deals.sort_values("ticket").copy()
    cash = ordered[["profit", "commission", "fee", "swap"]].sum(axis=1)
    before = float(stats["deposit"]) + cash.cumsum().shift(1, fill_value=0)
    budgets = events.loc[events.event.eq("ENTRY_BUDGET")].set_index("time").value
    for idx, row in ordered.loc[ordered.entry.eq(0)].iterrows():
        expected = before.loc[idx] * float(stats["risk_percent"]) / 100
        if abs(expected - float(budgets.loc[int(row.time)])) > 1e-6:
            raise ValueError("Risk budget not based on actual pre-entry closed balance")
    mean, sd, z, valid = reconstruct_benchmark(signals)
    if not (
        np.allclose(mean, signals.vwap, atol=2e-8, rtol=0)
        and np.allclose(sd, signals.sigma, atol=2e-7, rtol=0)
        and np.allclose(z, signals.z, atol=2e-6, rtol=0)
        and np.array_equal(valid, signals.vwap_valid.astype(bool))
    ):
        raise ValueError("Independent VWAP calculation differs")
    online = signals.loc[signals.online.eq(1)].copy()
    if online.time.duplicated().any():
        raise ValueError("Duplicate observed bar")
    if (
        not online.time.is_monotonic_increasing
        or not online.prediction.between(-8, 8).all()
        or not online.prediction.mod(1).eq(0).all()
        or not online.direction.isin([-1, 0, 1]).all()
        or not online.start.isin([-1, 0, 1]).all()
    ):
        raise ValueError("Invalid online eight-neighbor model output or chronology")
    if (
        int(stats["model_kind"]) == 1
        and int(stats["official_stability_checks"]) != len(online) - 1
    ):
        raise ValueError("Official buffer stability checks incomplete")
    entries = deals.loc[deals.entry.eq(0)].copy()
    for row in entries.itertuples():
        known = online.loc[online.time <= int(row.time) // 1800 * 1800 - 1800].iloc[-1]
        side = 1 if row.type == 0 else -1
        if side != int(known.start):
            raise ValueError("Entry is not an observed closed-bar signal")
        if int(stats["use_vwap"]) and not gate(known.z, known.vwap_valid, side):
            raise ValueError("Entry violates frozen VWAP gate")
        if int(stats["intraday"]) and not clock_eligible(row.time, known.time):
            raise ValueError("Entry outside the NY session")
    if int(stats["intraday"]):
        for _, group in deals.groupby("position_id"):
            a = int(group.loc[group.entry.eq(0), "time"].min())
            b = int(group.loc[group.entry.isin([1, 3]), "time"].max())
            local = pd.to_datetime([a, b], unit="s", utc=True).tz_convert("America/New_York")
            # Close is on first available tick, allow a one-minute quote delay.
            if local[0].date() != local[1].date() or local[1].hour * 60 + local[1].minute > 946:
                raise ValueError("Intraday exposure survived the flatten boundary")
    candidates = online.loc[online.start.ne(0)]
    summary.update(
        vwap_audit="PASS",
        observed_bars=len(online),
        raw_starts=len(candidates),
        real_volume_positive_bars=int(signals.real_volume.gt(0).sum()),
        vwap_allowed_raw_starts=int(
            gate(candidates.z, candidates.vwap_valid, candidates.start).sum()
        ),
        fixed_minimum_entries=int(events.event.eq("ENTRY_FIXED_MINIMUM").sum()),
    )
    summary["monthly"] = monthly
    return summary
