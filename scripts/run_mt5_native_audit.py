"""Launch only a local Strategy Tester job, with immutable captured status.

Requires a closed terminal and already deployed tester-only EA. Never stops a
pre-existing terminal. Logs are deliberately NOT published wholesale: they may
contain account identifiers. A timeout terminates only the process we started.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from lorentzian_audit.mt5_audit import validate_tester_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    config = args.config.resolve()
    text = config.read_text()
    validate_tester_config(text)
    probe = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "@(Get-Process terminal64 -ErrorAction SilentlyContinue).Count",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    if int(probe.stdout.strip()) != 0:
        raise RuntimeError("Close the terminal before the test. Refusing to terminate it.")
    report = {
        "started_utc": datetime.now(UTC).isoformat(),
        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "status": "STARTED",
        "live_orders_authorized": False,
        "terminal_timeout_seconds": args.timeout,
        "model": "4 real ticks requested",
    }
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    with subprocess.Popen(
        [r"C:\Program Files\MetaTrader 5\terminal64.exe", f"/config:{config}"],
        startupinfo=startup,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) as process:
        try:
            report["exit_code"] = process.wait(timeout=args.timeout)
            report["status"] = "PROCESS_EXITED_NOT_YET_VALIDATED"
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=15)
            report["status"] = "TIMEOUT_NO_COMPLETED_TEST_CLAIMED"
    report["finished_utc"] = datetime.now(UTC).isoformat()
    (args.output / "launch.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(report["status"].startswith("TIMEOUT"))


if __name__ == "__main__":
    raise SystemExit(main())
