"""Archive safe audit outputs only; never copy account logs or credentials."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    common = Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files/LorentzianAudit"
    output = root / "evidence/us500_x100_mt5"
    manifest = {
        "files": {},
        "source_anchor": "2022-01-01",
        "broker_connection_verified": False,
        "native_backtest_completed": False,
        "forward_test_started": False,
        "broker_orders_submitted": 0,
    }
    sources = {
        "mql_parity.csv.gz": common / "mql_parity.csv",
        "symbol_audit_cached.csv": common / "symbol_audit.csv",
        "mql_self_test_final.csv": common / "self_test_final.csv",
        "python_reference.csv.gz": root / "local_mt5/parity/python_reference.csv",
        "native_smoke_launch.json": root / "local_mt5/native_smoke_retry/launch.json",
    }
    for name, source in sources.items():
        raw = source.read_bytes()
        content = gzip.compress(raw, mtime=0) if name.endswith(".gz") else raw
        target = output / name
        if target.exists() and target.read_bytes() != content:
            raise FileExistsError(f"Refuse to replace different evidence: {target}")
        target.write_bytes(content)
        manifest["files"][name] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(content),
        }
    manifest["compile"] = {}
    for name in ["parity", "ea", "symbol", "selftest"]:
        lines = (
            (root / f"local_mt5/{name}_compile.log").read_text(encoding="utf-16").splitlines()
        )
        manifest["compile"][name] = next(
            line for line in reversed(lines) if line.startswith("Result:")
        )
    manifest["source_sha256"] = {
        str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted((root / "mql5").rglob("*"))
        if path.suffix in [".mq5", ".mqh", ".ex5"]
    }
    manifest["baseline_sha256"] = {
        str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in [
            root / "config/contract_v3_atr_runner_sizing.json",
            root / "evidence/v3_atr_runner_sizing/trades.csv.gz",
        ]
    }
    (output / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"archived": list(sources), "compile": manifest["compile"]}, indent=2))


if __name__ == "__main__":
    main()
