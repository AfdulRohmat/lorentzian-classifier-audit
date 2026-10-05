# Running the MT5 audit

This runbook is for read-only scripts and local Strategy Tester only. The EA is deliberately disabled outside Strategy Tester. Do not use these files to start demo/real trading or Telegram.

## Prerequisites

Use Windows with MetaTrader 5 and MetaEditor. The existing environment is `../mt5-ea-research-lab/.venv/Scripts/python.exe`; install this repository's dependencies plus the official MetaTrader5 Python package if using another environment. Set `PYTHONPATH` to `src;vendor`. The Python package is not required by the MQL scripts themselves.

Compile the files under `mql5/Scripts` and `mql5/Experts` in MetaEditor, retaining the relative `Include` directory structure. Confirm zero errors/warnings; record compiler build and EX5 hashes. Compiled files and temporary outputs are ignored by Git. Do not overwrite unrelated installed EAs or scripts.

Install the compiled scripts to `MQL5/Scripts/LorentzianAudit/` and EA to `MQL5/Experts/LorentzianAudit/` within the selected terminal data folder. The terminal's File menu can show its data folder; do not assume it is the program installation folder.

## Reference parity

```powershell
$env:PYTHONPATH='src;vendor'
& ../mt5-ea-research-lab/.venv/Scripts/python.exe scripts/prepare_mt5_parity.py --output local_mt5/parity
```

This produces the anchored OHLC fixture and Python output. Copy `fixture.csv` to the terminal Common Files directory under `LorentzianAudit/`. Run `LorentzianParity` as a read-only script, or launch a closed terminal with the absolute path to `config/mt5_parity_script.ini`. It writes `mql_parity.csv` to Common Files. Run `LorentzianSelfTest` similarly for the 17 arithmetic/state checks.

Scripts refuse to overwrite their outputs. Preserve previous outputs before a rerun and use distinct fixture/output inputs or a newly named self-test artifact; do not silently replace evidence.

```powershell
& ../mt5-ea-research-lab/.venv/Scripts/python.exe scripts/check_mt5_parity.py --reference local_mt5/parity/python_reference.csv --actual '<Common Files>/LorentzianAudit/mql_parity.csv' --output local_mt5/parity/comparison.json
& ../mt5-ea-research-lab/.venv/Scripts/python.exe -m pytest -q
```

The checker also reads the compressed archived outputs in `evidence/us500_x100_mt5/`; use those two `.csv.gz` paths to revalidate the saved result without running MT5 or loading source data.

## Broker audit and tester

Sign in through MT5 yourself; never put account passwords or login IDs into this repo. Keep algo trading disabled for read-only scripts. The Python probe only queries metadata/history:

```powershell
& ../mt5-ea-research-lab/.venv/Scripts/python.exe scripts/audit_mt5_x100.py --output local_mt5/connected_audit.json
```

`LorentzianSymbolAudit` is an additional read-only MQL probe, but can return stale cached values while disconnected. A selected symbol alone is not connected-account validation. Reproducing the old Python baseline requires its original anchor, which current x100 native history does not cover. Later January-August 2026 experiments therefore declare their shorter native warm-up separately. The legacy EA's exact symbol gate is `US500_x100`, not automatic suffix substitution.

With the terminal closed and the tester-only EX5 deployed, run the fixed smoke configuration:

```powershell
& ../mt5-ea-research-lab/.venv/Scripts/python.exe scripts/run_mt5_native_audit.py --config config/mt5_native_smoke.ini --output local_mt5/native_smoke_new --timeout 300
```

The launcher refuses any pre-existing terminal, remote/cloud execution or unsafe configuration. It terminates only the terminal process it launched on timeout. MetaTester may remain as an idle local service afterward; do not terminate unrelated agents. Process exit does not mean a successful backtest: inspect tester logs, the expected HTML report and Common Files `native_smoke_events.csv` / `native_smoke_signals.csv`. Files must be newly created and error-free. Use a new run tag/report path for every subsequent test.

Only after the smoke gate passes should a new frozen full-period configuration run. Current native studies cover January-August 2026, not the unavailable 2024-start x100 history. Export complete tester deals, retain fees and swaps, compare exact-bar signals and reconcile native fills separately from signal parity. Do not compare this shorter native window with the whole 32-month Python return.

## VWAP and untouched official model study

The new `LorentzianVWAPAudit` is a separate tester-only EA, allowing only exact `US500` and `US500_x100` M30 charts. Its frozen [contract](TECH_PLAN_NATIVE_VWAP.md) records the 288-case grid and the difference between strict risk and fixed minimum volume. It does not replace the old EA or the historical Python baseline.

Compile the unchanged `vendor/official_mql5/indicators/LorentzianClassification/LorentzianClassification.mq5`, preserving its sibling `Include/` files. Install that EX5 to `MQL5/Indicators/LorentzianOfficial100/`. Compile the new wrapper with its existing relative include files and install it under `MQL5/Experts/LorentzianAudit/`. The compiled binary hashes used by the archived study are in `evidence/native_vwap_2026_v3/build/sha256.json`; source bytes are preserved in the adjacent ZIP. A different MetaEditor build need not produce an identical binary, and must receive separate provenance.

`prepare_native_vwap.py` creates immutable `.ini` and `.set` configurations. Copy only its named `.set` files into that terminal's `MQL5/Profiles/Tester/`, close the terminal after confirming the demo account is flat, and use `run_native_vwap.py` serially. Do not run two coordinators on the same terminal/profile. Existing Common Files run tags deliberately block silent overwrite: use newly named evidence/configuration tags for a fresh replay, rather than deleting old evidence. The launcher and deployment currently target this workstation's terminal path; another machine must explicitly configure and validate its own path.

Saved-evidence checks do not need MT5 and can run on macOS/Linux using the repository Python environment (`PYTHONPATH=src:vendor` there):

```powershell
$env:PYTHONPATH='src;vendor'
python scripts/report_native_vwap.py --evidence evidence/native_vwap_2026_v3 --output docs/RESULT_NATIVE_VWAP.md
python scripts/report_native_restart.py
python -m pytest -q
```

Native replay still requires the compatible Windows terminal, broker history and a signed-in account; it is not a portable Python fill simulator. Finally restore `config/mt5_audit_readonly.ini` and run `check_mt5_account_safety.py --output <new-sanitized-output.json>`. A failed API response is unknown status, never evidence of zero positions.

## Safety and known limitations

Native historical tests have now completed; see [x100 results](RESULT_NATIVE_X100_2026.md), [swing results](RESULT_NATIVE_SWING.md), and the latest VWAP evidence. Those validate their observed tester paths, not every possible broker rejection, partial fill, session change or live execution behavior. Source guard checks in pytest are structural tests, not substitutes for native execution tests. A production demo EA will additionally need restart state recovery, live calculation-cadence parity, loss controls, duplicate-order protection, notification secrets and forward-test authorization; none is activated here.
