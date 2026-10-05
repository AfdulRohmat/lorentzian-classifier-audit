"""Strict identical-bar parity checks; no outcome-based parameter selection."""

from __future__ import annotations

import numpy as np
import pandas as pd

FLOAT_FIELDS = ["f1", "f2", "f3", "f4", "f5", "kernel", "atr"]
DISCRETE_FIELDS = ["filter", "prediction", "direction", "start"]


def compare_frames(reference: pd.DataFrame, actual: pd.DataFrame) -> dict:
    if reference.empty or actual.empty:
        return {"status": "FAIL_EMPTY"}
    if reference.index.has_duplicates or actual.index.has_duplicates:
        return {"status": "FAIL_DUPLICATE_TIME"}
    if not reference.index.equals(actual.index):
        return {
            "status": "FAIL_TIME_ALIGNMENT",
            "reference_rows": len(reference),
            "actual_rows": len(actual),
        }
    details = {}
    passed = True
    for field in FLOAT_FIELDS:
        expected = reference[field].to_numpy(dtype=float)
        measured = actual[field].to_numpy(dtype=float, copy=True)
        measured[measured > 1e300] = np.nan  # MQL EMPTY_VALUE, not a valid feature.
        finite = np.isfinite(expected) & np.isfinite(measured)
        good = np.isclose(expected, measured, rtol=1e-11, atol=1e-10, equal_nan=True)
        bad = ~good
        details[field] = {
            "mismatches": int(bad.sum()),
            "max_abs_error": float(np.abs(expected[finite] - measured[finite]).max())
            if finite.any()
            else None,
        }
        passed &= not bad.any()
    for field in DISCRETE_FIELDS:
        bad = reference[field].to_numpy() != actual[field].to_numpy()
        details[field] = {
            "mismatches": int(bad.sum()),
            "first_mismatch": str(reference.index[np.flatnonzero(bad)[0]])
            if bad.any()
            else None,
        }
        passed &= not bad.any()
    return {
        "status": "PASS" if passed else "FAIL",
        "bars": len(reference),
        "fields": details,
        "start_long": int((reference.start == 1).sum()),
        "start_short": int((reference.start == -1).sum()),
        "boundary_tie_rows": int(actual.get("boundary_ties", pd.Series(dtype=int)).sum()),
    }
