"""Descriptive frozen-trade path audit; no new signals or optimized exits."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .data import aggregate_timeframe, load_asset_minutes
from .run import _json_default
from .run_v3 import ROOT, _sha256


def marks(frame, trade, spec, profile):
    spread = np.maximum(
        frame.spread.to_numpy(float) * spec["point"] * profile["spread_multiplier"],
        profile["spread_floor"],
    )
    side = trade.direction

    def mark(bid):
        price = np.asarray(bid, float) + (spread if side == -1 else 0)
        return (
            side * (price - trade.entry_fill)
            - profile["slippage_side"]
            - profile["commission_round_trip_price"]
        ) / trade.planned_risk_price

    return {
        "favorable": mark(frame.high if side == 1 else frame.low),
        "adverse": mark(frame.low if side == 1 else frame.high),
        "close": mark(frame.close),
        "open": mark(frame.open),
    }


def first_barrier(favorable, adverse):
    pos = np.flatnonzero(np.asarray(favorable) >= 1)
    neg = np.flatnonzero(np.asarray(adverse) <= -1)
    p, n = (int(pos[0]) if len(pos) else np.inf), (int(neg[0]) if len(neg) else np.inf)
    if p == n:
        return "NEITHER" if np.isinf(p) else "SAME_MINUTE_AMBIGUOUS"
    return "POSITIVE_FIRST" if p < n else "NEGATIVE_FIRST"


def position_path(minutes, trade, spec, profile):
    a, b = minutes.index.searchsorted([trade.entry_time, trade.exit_time])
    assert minutes.index[a] == trade.entry_time and minutes.index[b] == trade.exit_time
    before = minutes.iloc[a:b]
    m = marks(before, trade, spec, profile)
    favorable = m["favorable"]
    mfe = max(0.0, trade.net_r, favorable.max(initial=-np.inf))
    mae = min(0.0, trade.net_r, m["adverse"].min(initial=np.inf))
    peak_minutes = np.nan
    if mfe > 0:
        peak = (
            before.index[int(np.argmax(favorable))]
            if len(before) and favorable.max() >= trade.net_r
            else trade.exit_time
        )
        peak_minutes = (peak - trade.entry_time).total_seconds() / 60
    upper = mfe
    if trade.exit_reason.endswith("INTRAMINUTE"):
        upper = max(
            mfe, float(marks(minutes.iloc[b : b + 1], trade, spec, profile)["favorable"][0])
        )
    return {
        "mfe_lower_r": float(mfe),
        "mfe_upper_r": float(upper),
        "mae_r": float(mae),
        "giveback_lower_r": float(mfe - trade.net_r),
        "giveback_upper_r": float(upper - trade.net_r),
        "peak_minutes": peak_minutes,
        "observed_pre_exit_m1": len(before),
        "touched_1r_without_trail": bool(mfe >= 1 and not trade.trail_activated),
    }


def shadow_window(minutes, trade, spec, profile, horizon):
    deadline = trade.entry_time + pd.Timedelta(minutes=horizon)
    a, b = minutes.index.searchsorted([trade.entry_time, deadline])
    observed = minutes.iloc[a:b]
    coverage = len(observed) / horizon
    result = {"horizon_minutes": horizon, "coverage": coverage, "valid": False}
    if (
        a >= len(minutes)
        or minutes.index[a] != trade.entry_time
        or b >= len(minutes)
        or minutes.index[b] != deadline
        or coverage < 0.9
    ):
        return result
    m = marks(observed, trade, spec, profile)
    endpoint = float(marks(minutes.iloc[b : b + 1], trade, spec, profile)["open"][0])
    result.update(
        {
            "valid": True,
            "endpoint_net_r": endpoint,
            "shadow_mfe_r": float(max(0.0, endpoint, m["favorable"].max(initial=-np.inf))),
            "shadow_mae_r": float(min(0.0, endpoint, m["adverse"].min(initial=np.inf))),
            "first_barrier": first_barrier(m["favorable"], m["adverse"]),
        }
    )
    if horizon == 120:
        eligible = trade.exit_reason.startswith("STOP_") and trade.exit_time < deadline
        after = m["favorable"][observed.index > trade.exit_time]
        result["stopped_before_horizon"] = bool(eligible)
        result["recovered_after_stop_1r"] = bool(eligible and (after >= 1).any())
    return result


def group_metrics(rows):
    win = rows.loc[rows.net_r > 0]
    activated = rows.loc[rows.trail_activated]
    stopped = rows.loc[rows.exit_reason.str.startswith("STOP_")]
    return {
        "trades": len(rows),
        "mean_net_r": rows.net_r.mean(),
        "win_rate": (rows.net_r > 0).mean(),
        "mean_mfe_lower_r": rows.mfe_lower_r.mean(),
        "mean_mfe_upper_r": rows.mfe_upper_r.mean(),
        "mean_giveback_lower_r": rows.giveback_lower_r.mean(),
        "mean_giveback_upper_r": rows.giveback_upper_r.mean(),
        "median_mae_r": rows.mae_r.median(),
        "mfe_at_least_1r_fraction": (rows.mfe_lower_r >= 1).mean(),
        "mfe_at_least_3r_fraction": (rows.mfe_lower_r >= 3).mean(),
        "trail_activation_fraction": rows.trail_activated.mean(),
        "touch_1r_without_trail_fraction": rows.touched_1r_without_trail.mean(),
        "median_peak_minutes_positive_mfe": rows.peak_minutes.median(),
        "median_holding_minutes": rows.holding_hours.median() * 60,
        "mean_winner_r": win.net_r.mean(),
        "winner_mean_mfe_r": win.mfe_lower_r.mean(),
        "winner_mean_giveback_r": win.giveback_lower_r.mean(),
        "activated_count": len(activated),
        "activated_mean_net_r": activated.net_r.mean(),
        "activated_mean_mfe_r": activated.mfe_lower_r.mean(),
        "activated_mean_giveback_r": activated.giveback_lower_r.mean(),
        "initial_stop_count": len(stopped),
        "stopped_touch_1r_fraction": (stopped.mfe_lower_r >= 1).mean(),
        "median_preentry_120m_atr": rows.preentry_120m_atr.median(),
        "preentry_valid_count": int(rows.preentry_120m_atr.notna().sum()),
        "mean_intrabar_over_completed_peak_r": rows.intrabar_over_completed_peak_r.mean(),
    }


def main():
    contract_path = ROOT / "config/contract_v3_atr_runner_sizing.json"
    ledger_path = ROOT / "evidence/v3_atr_runner_sizing/trades.csv.gz"
    assert (
        _sha256(contract_path)
        == "873a16495f7e0b2bb4fb8e45c253d974e7051eb147d6512764b63d6e88ba3872"
    )
    assert (
        _sha256(ledger_path)
        == "20e8819c7ca94bd3217ac63dba0b5504c75810ab39dc189f19fda1666b72287d"
    )
    contract = json.loads(contract_path.read_text())
    old_manifest = json.loads(
        (ROOT / "evidence/v3_atr_runner_sizing/source_manifest.json").read_text()
    )
    ledger = pd.read_csv(ledger_path, parse_dates=["signal_time", "entry_time", "exit_time"])
    ledger = ledger.loc[ledger.timeframe.eq("30min")].copy()
    out = ROOT / "evidence/trade_path_audit"
    out.mkdir(parents=True, exist_ok=True)
    paths, shadows, sources = [], [], {}
    for asset, spec in contract["data"]["assets"].items():
        print(f"Auditing {asset}", flush=True)
        minutes, diag = load_asset_minutes(ROOT, asset, spec, contract["data"])
        sources[asset] = diag
        assert {f["name"]: f["sha256"] for f in diag["files"]} == {
            f["name"]: f["sha256"] for f in old_manifest[asset]["files"]
        }
        bars = aggregate_timeframe(minutes, "30min")
        profile = contract["costs"][asset]
        for t in ledger.loc[ledger.asset.eq(asset)].itertuples(index=False):
            tags = {
                "asset": asset,
                "trade_id": t.trade_id,
                "direction": t.direction,
                "year": t.entry_time.year,
            }
            audit = position_path(minutes, t, spec, profile)
            # Mirror only the runner's observation clock, without altering stops.
            a = bars.bar_end.searchsorted(t.entry_time, side="right")
            b = bars.bar_end.searchsorted(t.exit_time, side="right")
            sampled = bars.iloc[a:b].rename(columns={"spread_close_points": "spread"})
            completed = marks(sampled, t, spec, profile)["close"]
            best = float(completed.max()) if len(completed) else np.nan
            np.testing.assert_allclose(best, t.best_completed_net_r, atol=1e-9, equal_nan=True)
            # Include final R in both hindsight peak measures for comparable accounting.
            close_peak = max(0.0, t.net_r, best if np.isfinite(best) else 0.0)
            audit["completed_peak_r"] = close_peak
            audit["intrabar_over_completed_peak_r"] = audit["mfe_lower_r"] - close_peak
            assert audit["intrabar_over_completed_peak_r"] >= -1e-8
            start = t.entry_time - pd.Timedelta(minutes=120)
            ia, ib = minutes.index.searchsorted([start, t.entry_time])
            audit["preentry_120m_atr"] = np.nan
            if ib > ia and minutes.index[ia] == start and ib - ia >= 108:
                audit["preentry_120m_atr"] = (
                    t.direction * (minutes.close.iloc[ib - 1] - minutes.open.iloc[ia]) / t.atr
                )
            paths.append(t._asdict() | tags | audit)
            for horizon in (30, 120, 240):
                shadows.append(tags | shadow_window(minutes, t, spec, profile, horizon))
    path = pd.DataFrame(paths)
    shadow = pd.DataFrame(shadows)
    aggregates, annuals, shadow_stats = [], [], []
    for asset, asset_rows in path.groupby("asset"):
        for side, rows in [
            ("all", asset_rows),
            ("long", asset_rows.loc[asset_rows.direction.eq(1)]),
            ("short", asset_rows.loc[asset_rows.direction.eq(-1)]),
        ]:
            tags = {"asset": asset, "side": side}
            aggregates.append(tags | group_metrics(rows))
            for year, block in rows.groupby("year"):
                annuals.append(tags | {"year": int(year)} | group_metrics(block))
            chosen = shadow.loc[shadow.asset.eq(asset)]
            if side != "all":
                chosen = chosen.loc[chosen.direction.eq(1 if side == "long" else -1)]
            for horizon, subset in chosen.groupby("horizon_minutes"):
                valid = subset.loc[subset.valid]
                eligible = valid.loc[valid.stopped_before_horizon.eq(True)]
                stats = {
                    "horizon_minutes": int(horizon),
                    "candidates": len(subset),
                    "valid": len(valid),
                    "mean_endpoint_r": valid.endpoint_net_r.mean(),
                    "median_shadow_mfe_r": valid.shadow_mfe_r.median(),
                    "mean_shadow_mfe_r": valid.shadow_mfe_r.mean(),
                    "median_shadow_mae_r": valid.shadow_mae_r.median(),
                    "positive_endpoint_fraction": (valid.endpoint_net_r > 0).mean(),
                    "positive_first": int(valid.first_barrier.eq("POSITIVE_FIRST").sum()),
                    "negative_first": int(valid.first_barrier.eq("NEGATIVE_FIRST").sum()),
                    "ambiguous": int(valid.first_barrier.eq("SAME_MINUTE_AMBIGUOUS").sum()),
                    "neither": int(valid.first_barrier.eq("NEITHER").sum()),
                    "initial_stop_recovery_denominator": len(eligible),
                    "initial_stop_recovery_count": int(
                        eligible.recovered_after_stop_1r.eq(True).sum()
                    ),
                }
                shadow_stats.append(tags | stats)
    assert len(path) == 1433 and len(shadow) == 1433 * 3
    np.testing.assert_allclose(path.mfe_lower_r - path.giveback_lower_r, path.net_r)
    assert (path.mfe_upper_r >= path.mfe_lower_r).all()
    assert (path.mae_r <= path.net_r + 1e-9).all()
    for name, frame in [
        ("paths.csv.gz", path),
        ("shadow_windows.csv.gz", shadow),
        ("metrics.csv", pd.DataFrame(aggregates)),
        ("annual.csv", pd.DataFrame(annuals)),
        ("shadow_metrics.csv", pd.DataFrame(shadow_stats)),
    ]:
        frame.to_csv(out / name, index=False)
    summary = {
        "scope": "Retrospective frozen-ledger diagnostic, not new strategy returns",
        "metrics": aggregates,
        "shadow_metrics": shadow_stats,
        "plan_sha256": _sha256(ROOT / "docs/TRADE_PATH_AUDIT_PLAN.md"),
        "parent_ledger_sha256": _sha256(ledger_path),
    }
    validation = {
        "passed": True,
        "trades": len(path),
        "shadow_windows": len(shadow),
        "source_hashes_match": True,
        "completed_close_peaks_match_ledger": True,
        "excursion_bounds_and_decomposition": True,
    }
    for name, value in [
        ("summary", summary),
        ("source_manifest", sources),
        ("validation", validation),
    ]:
        (out / f"{name}.json").write_text(
            json.dumps(value, indent=2, default=_json_default) + "\n", encoding="utf-8"
        )
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
