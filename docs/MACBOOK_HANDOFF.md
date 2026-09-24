# MacBook handoff

This document is the operational handoff for continuing the research on a new
machine. The canonical branch is `main`; the full v4 history is also retained on
`research/tail-robustness-v4`.

## What GitHub contains

- source code, frozen contracts, unit tests and the pinned upstream snapshot;
- compressed trade/account evidence and all summary/validation artifacts;
- complete v1-v4 technical plans and result reports;
- three reproducible README equity and Monte Carlo figures.

## What GitHub intentionally does not contain

- the large raw Exness M1 Parquet archives;
- the local September US500 cache under `local_data/`;
- a MetaTrader 5 terminal, account credentials or broker configuration;
- any secret, token, password or live/demo trading account state.

The old raw paths are documented in the frozen JSON contracts. Do not commit
raw data merely to make those paths work on macOS. If the archives are needed,
copy them using an external disk and verify their hashes against each evidence
`source_manifest.json`.

## First boot on macOS

```bash
git clone https://github.com/AfdulRohmat/lorentzian-classifier-audit.git
cd lorentzian-classifier-audit
git status --short --branch
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
PYTHONPATH=src:vendor python -m pytest
python -m ruff check src tests scripts
python scripts/generate_readme_figures.py
git status --short
```

The project declares Python `>=3.12,<3.15`. Figure regeneration should not
change the SVGs. If it does, inspect the evidence and script versions before
committing anything.

## MT5 boundary

The Python `MetaTrader5` integration used by the research is Windows-oriented
and should not be assumed to run natively on macOS. Keep responsibilities split:

- **MacBook:** source editing, unit tests, evidence analysis, documentation and
  report generation;
- **Windows laptop/VPS/VM:** MT5 terminal, broker login, read-only history pulls
  and future demo execution;
- **transfer boundary:** Parquet/CSV plus manifest hashes, never credentials.

For a full historical replay on the Mac, restore the raw archives and create a
new local path mapping or a new research contract. Do not edit a frozen contract
after its outcomes are known.

## Safe continuation order

1. Read `README.md` and all four result documents.
2. Read `config/contract_v3_atr_runner_sizing.json` and
   `config/contract_v4_tail_robustness.json` before touching the candidate.
3. Confirm the clean unit suite and chart regeneration.
4. Create a new branch and freeze a v5 demo-forward contract.
5. Implement signal export and MT5 demo reconciliation without changing the
   v3 entry/exit rules.
6. Review only at scheduled sample checkpoints; never tune after each loss.

## Current scientific boundary

Latest diagnostic: `docs/RESULT_TRADE_PATH_AUDIT.md` reconstructs the original
SP500/XAUUSD M30 paths. Gold shorts have smaller favorable excursions, with
nearly identical mean giveback to index shorts. This motivates examining
signal/payoff alignment, not an automatic stop/trailing adjustment. Run
`python -m lorentzian_audit.validate_trade_paths` without raw data, or
`python -m lorentzian_audit.audit_trade_paths` with the original raw archives.
No strategy rules were changed or new gold candidate promoted.

Read `docs/RESULT_RUNNER_ENTRY_COMPARISON.md` for the latest same-runner signal
comparison. Euclidean nearly matches Lorentzian on SP500 at base costs; all
four policies lose on XAUUSD. Incremental Lorentzian value is unconfirmed,
without replacing the frozen demo candidate. Run
`python -m lorentzian_audit.validate_entry_comparison` using saved evidence only;
full `run_entry_comparison` requires the original raw archives. This diagnostic
uses inspected history, not a new unseen extension.

XAUUSD's capital extension (USD 500/1,000/3,000; 1%-5%) is in
`docs/RESULT_XAUUSD_CAPITAL_SIZING.md`. All 15 M30 account scenarios lose money;
this does not alter the SP500 candidate. Its committed account/calendar evidence
can be regenerated and validated without MT5 using
`python -m lorentzian_audit.run_xau_sizing`.

The additional US500_x100 sizing study is in
`docs/RESULT_US500_X100_SIZING.md`. Its 75 scenario ledgers are committed and
can be regenerated with `python -m lorentzian_audit.run_x100` and checked with
`python -m lorentzian_audit.validate_x100` after installing the project. It needs
no raw market data. Verify its explicit contract/commission assumptions from a
live terminal before using x100 for demo execution; the study had IPC timeouts.

The repository does not contain a validated live strategy. It contains one
historically interesting SP500 M30 runner and negative evidence for the broader
Lorentzian/cross-asset claim. The September extension is negative and only nine
trades long. The correct next action is untouched forward observation, not a
new parameter search on the same historical interval.
