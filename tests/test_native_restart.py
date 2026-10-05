import importlib.util
from pathlib import Path

import pandas as pd
import pytest

path = Path(__file__).resolve().parents[1] / "scripts/report_native_restart.py"
spec = importlib.util.spec_from_file_location("report_native_restart", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample():
    return pd.DataFrame(
        dict(
            time=[0, 1800, 3600],
            online=[0, 1, 1],
            open=[100, 101, 102],
            high=[102, 103, 104],
            low=[99, 100, 101],
            close=[101, 102, 103],
            tick_volume=[10, 20, 30],
            vwap=[101, 102, 103],
            sigma=[0, 1, 1.5],
            prediction=[0, 2, 4],
            direction=[0, 1, 1],
            start=[0, 1, 0],
        )
    )


def test_restart_match_and_state_difference():
    running = sample()
    cold = sample().iloc[1:].copy()
    summary, differences = module.compare_streams(running, cold)
    assert summary["overlap_bars"] == 2
    assert summary["status"] == "MATCH_ON_THIS_REPLAY"
    assert differences.empty
    cold.loc[2, "prediction"] = -4
    cold.loc[2, "start"] = -1
    summary, differences = module.compare_streams(running, cold)
    assert summary["status"] == "RESTART_DEPENDENT"
    assert summary["prediction_mismatches"] == 1
    assert summary["direction_mismatches"] == 0
    assert summary["start_mismatches"] == 1
    assert differences.time.tolist() == [3600]


def test_restart_rejects_changed_feed():
    cold = sample()
    cold.loc[2, "close"] += 1
    with pytest.raises(ValueError, match="Market/benchmark changed"):
        module.compare_streams(sample(), cold)


def test_restart_rejects_missing_or_duplicate_timestamps():
    cold = sample()
    cold.loc[2, "time"] = 5400
    with pytest.raises(ValueError, match="outside"):
        module.compare_streams(sample(), cold)
    with pytest.raises(ValueError, match="Duplicate"):
        module.compare_streams(sample(), pd.concat([sample(), sample()]))
