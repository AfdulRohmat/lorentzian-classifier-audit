"""Predeclared cold-restart diagnostic; not an additional PnL optimization."""

import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / "local_mt5/matrix_vwap_v3"
    dest = root / "local_mt5/matrix_vwap_restart"
    dest.mkdir(exist_ok=False)
    rows = json.loads((source / "matrix.json").read_text())
    cold = []
    for symbol in ("US500", "US500_x100"):
        row = next(
            r
            for r in rows
            if r["symbol"] == symbol
            and r["model_kind"] == 1
            and r["use_vwap"]
            and not r["intraday"]
            and r["balance"] == 3000
            and r["sizing"] == 0
            and not r["smoke"]
        ).copy()
        old = row["tag"]
        row["tag"] = f"lcv28_cold_{'u' if symbol == 'US500' else 'x'}"
        row["cold_restart"] = True
        config = (source / f"{old}.ini").read_text().replace(old, row["tag"])
        config = config.replace("FromDate=2026.01.01", "FromDate=2026.02.01")
        (dest / f"{row['tag']}.ini").write_text(config)
        settings = (source / f"{old}.set").read_text(encoding="utf-16").replace(old, row["tag"])
        (dest / f"{row['tag']}.set").write_text(settings, encoding="utf-16")
        cold.append(row)
    (dest / "matrix.json").write_text(json.dumps(cold, indent=2) + "\n")
    print("Prepared two February cold-restart diagnostics, same source and predictive settings")


if __name__ == "__main__":
    main()
