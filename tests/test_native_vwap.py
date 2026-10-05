import numpy as np
import pandas as pd
import pytest

from lorentzian_audit.mt5_audit import validate_tester_config
from lorentzian_audit.native_vwap import clock_eligible, gate, reconstruct_benchmark


def test_gate_boundaries():
    z = [-3.01, -3, -1, -0.99, 0, 0.99, 1, 3, 3.01]
    assert gate(z, True, 1).tolist() == [
        False,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        False,
    ]
    assert gate(z, True, -1).tolist() == [
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        False,
    ]
    assert not gate(0, False, 1)


@pytest.mark.parametrize(
    "date,open_utc", [("2026-01-05", 14), ("2026-03-09", 13), ("2026-11-02", 14)]
)
def test_dst_and_signal_close(date, open_utc):
    signal = pd.Timestamp(f"{date} {open_utc}:30", tz="UTC").timestamp()
    assert clock_eligible(signal + 1800, signal)
    assert not clock_eligible(signal, signal - 1800)  # premarket bar
    assert not clock_eligible(signal + 6 * 3600, signal + 5.5 * 3600)  # 15:30


def test_weighted_variance_daily_reset_and_prefix():
    p = np.array([100.0, 102.0, 104.0, 200.0, 202.0])
    df = pd.DataFrame(
        dict(
            time=[0, 1800, 3600, 86400, 88200],
            high=p,
            low=p,
            close=p,
            tick_volume=[1, 3, 2, 1, 1],
        )
    )
    mean, sd, _, valid = reconstruct_benchmark(df)
    assert mean.iloc[1] == 101.5
    assert sd.iloc[1] == pytest.approx(np.sqrt(0.75))
    assert mean.iloc[3] == 200 and not valid.iloc[3]
    short = reconstruct_benchmark(df.iloc[:3])
    assert np.allclose(short[0], mean.iloc[:3])
    assert np.allclose(short[1], sd.iloc[:3])


def test_native_allowlist():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[1] / "config/mt5_native_smoke.ini").read_text()
    text = text.replace("LorentzianX100Audit.ex5", "LorentzianVWAPAudit.ex5")
    validate_tester_config(text.replace("Symbol=US500_x100", "Symbol=US500"))
    with pytest.raises(ValueError):
        validate_tester_config(text.replace("Symbol=US500_x100", "Symbol=XAUUSD"))
    with pytest.raises(ValueError):
        validate_tester_config(text.replace("AllowLiveTrading=0", "AllowLiveTrading=1"))


@pytest.mark.parametrize(
    "day", ["2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03"]
)
def test_intraday_holidays(day):
    signal = pd.Timestamp(day + " 10:00", tz="America/New_York").timestamp()
    assert not clock_eligible(signal + 1800, signal)


def test_sizing_matrix_is_complete():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts/prepare_native_vwap.py"
    spec = importlib.util.spec_from_file_location("matrix", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.scenarios()
    primary = [r for r in rows if not r["smoke"]]
    assert len(primary) == len({r["tag"] for r in primary}) == 288
    assert sum(r["fixed_minimum_lot"] for r in primary) == 48
    assert all(not r["minimum_lot_fallback"] for r in primary)


def test_zero_tick_volume_skips_without_polluting_weighted_history():
    p = np.array([100.0, 102.0, 104.0, 200.0])
    df = pd.DataFrame(
        dict(time=[0, 1800, 3600, 86400], high=p, low=p, close=p, tick_volume=[1, 0, 1, 0])
    )
    mean, sd, z, valid = reconstruct_benchmark(df)
    assert np.allclose(mean, [100, 100, 102, 0])
    assert np.allclose(sd, [0, 0, 2, 0])
    assert np.allclose(z, [0, 0, 1, 0])
    assert valid.tolist() == [False, False, True, False]


def test_native_budget_is_independently_reconciled():
    from pathlib import Path

    from lorentzian_audit.native_vwap import audit_vwap

    root = Path(__file__).resolve().parents[1]
    folder = root / "evidence/native_vwap_2026_v3/lcv28_smoke_u_m0"
    stats = dict(pd.read_csv(folder / "stats.csv.gz").itertuples(index=False, name=None))
    events = pd.read_csv(folder / "events.csv.gz")
    deals = pd.read_csv(folder / "deals.csv.gz")
    signals = pd.read_csv(folder / "signals.csv.gz")
    assert audit_vwap(stats, deals, events, signals)["vwap_audit"] == "PASS"
    idx = events.index[events.event.eq("ENTRY_BUDGET")][0]
    events.loc[idx, "value"] += 0.01
    with pytest.raises(ValueError, match="pre-entry closed balance"):
        audit_vwap(stats, deals, events, signals)


def test_native_rejects_out_of_range_model_buffer():
    from pathlib import Path

    from lorentzian_audit.native_vwap import audit_vwap

    folder = (
        Path(__file__).resolve().parents[1] / "evidence/native_vwap_2026_v3/lcv28_smoke_u_m1"
    )
    stats = dict(pd.read_csv(folder / "stats.csv.gz").itertuples(index=False, name=None))
    events = pd.read_csv(folder / "events.csv.gz")
    deals = pd.read_csv(folder / "deals.csv.gz")
    signals = pd.read_csv(folder / "signals.csv.gz")
    signals.loc[signals.online.eq(1), "prediction"] = 9
    with pytest.raises(ValueError, match="eight-neighbor model output"):
        audit_vwap(stats, deals, events, signals)
