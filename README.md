# Lorentzian classifier cross-asset audit

Preregistered, cost-aware audit of the open-source Lorentzian Classification
indicator on Exness US500 and XAUUSD data. It tests the exact original signal,
a causally aligned Lorentzian KNN, an otherwise identical Euclidean KNN, and
simple controls. No MT5 order is placed and no raw market data is copied.

The hypothesis contract was frozen before outcome inspection in
[`config/contract_v1.json`](config/contract_v1.json). Read
[`docs/TECHNICAL_PLAN.md`](docs/TECHNICAL_PLAN.md) before interpreting results.

## Result

The frozen verdict is `NO_ROBUST_CROSS_ASSET_LORENTZIAN_EDGE`. The causal
Lorentzian variant was nominally positive on both assets, but failed stability,
concentration, bootstrap, activity, and incremental-value gates. On XAUUSD,
simple momentum and the classifier-free kernel/filter control substantially
outperformed it. See [`docs/RESULT.md`](docs/RESULT.md).

## Reproduce

From this directory, using the existing shared research environment:

```powershell
$env:PYTHONPATH='src;vendor'
& '..\mt5-ea-research-lab\.venv\Scripts\python.exe' -m pytest
& '..\mt5-ea-research-lab\.venv\Scripts\python.exe' -m ruff check src tests
& '..\mt5-ea-research-lab\.venv\Scripts\python.exe' -m lorentzian_audit.run
& '..\mt5-ea-research-lab\.venv\Scripts\python.exe' -m lorentzian_audit.validate
```

Evidence is stored under `evidence/v1/`. A complete replay produced identical
SHA-256 hashes for every result artifact.

