from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lorentzian_audit.mt5_audit import validate_tester_config
from lorentzian_audit.mt5_parity import DISCRETE_FIELDS, FLOAT_FIELDS, compare_frames


def frames():
    data = pd.DataFrame({key: [np.nan, 0.1, 0.2] for key in FLOAT_FIELDS})
    for key in DISCRETE_FIELDS:
        data[key] = [0, 1, -1]
    data.index = pd.date_range("2024-01-01", periods=3, freq="30min", tz="UTC")
    return data, data.copy()


def test_identical_passes_and_empty_value_is_missing():
    expected, actual = frames()
    actual.loc[actual.index[0], FLOAT_FIELDS] = np.finfo(float).max
    assert compare_frames(expected, actual)["status"] == "PASS"


def test_prediction_mismatch_is_not_waived_by_float_tolerance():
    expected, actual = frames()
    actual.loc[actual.index[1], "prediction"] = 0
    result = compare_frames(expected, actual)
    assert result["status"] == "FAIL"
    assert result["fields"]["prediction"]["mismatches"] == 1


def test_missing_and_misaligned_rows_fail():
    expected, actual = frames()
    assert compare_frames(expected, actual.iloc[1:])["status"] == "FAIL_TIME_ALIGNMENT"


def test_finite_feature_cannot_be_missing():
    expected, actual = frames()
    actual.loc[actual.index[2], "f1"] = np.nan
    assert compare_frames(expected, actual)["status"] == "FAIL"


def test_empty_and_duplicate_data_fail():
    expected, actual = frames()
    assert compare_frames(expected.iloc[:0], actual.iloc[:0])["status"] == "FAIL_EMPTY"
    assert (
        compare_frames(pd.concat([expected, expected]), actual)["status"]
        == "FAIL_DUPLICATE_TIME"
    )


def test_tester_config_disallows_wrong_ea_live_trading_and_cloud():
    root = Path(__file__).resolve().parents[1]
    text = (root / "config/mt5_native_smoke.ini").read_text()
    validate_tester_config(text)
    for before, after in [
        ("AllowLiveTrading=0", "AllowLiveTrading=1"),
        ("UseCloud=0", "UseCloud=1"),
        ("LorentzianX100Audit.ex5", "AnotherEA.ex5"),
        ("[Experts]", "[StartUp]\nExpert=Other\n[Experts]"),
    ]:
        with pytest.raises(ValueError):
            validate_tester_config(text.replace(before, after))


def test_tester_config_allows_exact_us500_but_not_other_symbols():
    root = Path(__file__).resolve().parents[1]
    text = (root / "config/mt5_native_smoke.ini").read_text()
    validate_tester_config(text.replace("Symbol=US500_x100", "Symbol=US500"))
    with pytest.raises(ValueError):
        validate_tester_config(text.replace("Symbol=US500_x100", "Symbol=XAUUSD"))


def test_ea_has_non_optional_tester_guards_and_no_network_calls():
    root = Path(__file__).resolve().parents[1]
    ea = (root / "mql5/Experts/LorentzianX100Audit.mq5").read_text()
    assert ea.count("!MQLInfoInteger(MQL_TESTER)") >= 4
    assert ea.count("OrderSend(") == 1
    assert "WebRequest(" not in ea
    assert "request.tp=0" in ea
    assert "volume<minimum-1e-12" in ea
    # Structural guard test only; not evidence of runtime execution correctness.
