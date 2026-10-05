from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from lorentzian_audit.mt5_parity import compare_frames


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reference = pd.read_csv(args.reference, index_col=0)
    reference.index = pd.to_datetime(reference.index, utc=True)
    actual = pd.read_csv(args.actual, index_col=0)
    actual.index = pd.to_datetime(actual.index, unit="s", utc=True)
    result = compare_frames(reference, actual)
    result["hashes"] = {
        label: hashlib.sha256(path.read_bytes()).hexdigest()
        for label, path in [("reference", args.reference), ("actual", args.actual)]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return int(result["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
