# Lorentzian classifier cross-asset audit

Preregistered, cost-aware audit of the open-source Lorentzian Classification
indicator on Exness US500 and XAUUSD data. It tests the exact original signal,
a causally aligned Lorentzian KNN, an otherwise identical Euclidean KNN, and
simple controls. No MT5 order is placed and no raw market data is copied.

The hypothesis contract was frozen before outcome inspection in
[`config/contract_v1.json`](config/contract_v1.json). Read
[`docs/TECHNICAL_PLAN.md`](docs/TECHNICAL_PLAN.md) before interpreting results.

