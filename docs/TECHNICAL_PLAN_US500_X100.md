# US500_x100 account-sizing extension

Freeze the existing causal Lorentzian M30 signals and v3 ATR-runner exits. Reuse
its 688 completed SP500 trade windows over January 2024-August 2026. This study
measures contract sizing and selection, not out-of-sample edge.

The MT5 read-only connection returned IPC timeout twice. Current official
[Exness specifications](https://get.exness.help/hc/en-us/articles/17854383867548-Indices)
confirm x100 contract size 100, minimum volume 0.03 and maximum volume 20.
The 0.01 step is an explicit assumption pending a live terminal snapshot.
The x100 quote/cost equivalence is also assumed: multiply dollar profit and
planned dollar loss per lot by 100, without multiplying price or R.

Before inspecting results, freeze USD 500/1,000/3,000 and 1%-5% current-balance
risk in `config/contract_us500_x100_sizing.json`. Run 15 US500 reference accounts
and 60 x100 accounts: no-margin historical comparison, plus static entry-margin
sensitivities at 1:400, 1:100 and 1:50. The latter are proxies, not reconstructions
of historical broker high-margin windows or stop-out behavior.

Never round a position up to minimum lot. At x100 minimum lot, exposure is
3 index units and each one-point move changes gross PnL by USD 3. A bigger
contract should only alter granularity and selection at equal risk budgets.

Implementation sequence:

1. Hash and load the frozen source ledger; check chronological non-overlap.
2. Recalculate dollar-per-lot fields from unchanged price-unit fields.
3. Simulate compounding independently for each capital/risk/margin scenario.
4. Record candidate, executed and skipped trades, risk utilization, tail capture,
   drawdown, monthly and annual account returns.
5. Reconcile US500 accounts against v3; test equal-exposure invariance, minimum
   lot rejection, compounding, and margin rejection with synthetic trades.
6. Validate all ledgers, repeat for deterministic outputs, then publish results
   and update README/Mac handoff. Preserve v1-v4 contracts and evidence.

This is a conditional simulation until terminal-specific contract, lot step,
commission and historical quote equivalence are confirmed. The simulator makes
no MT5 orders. It can run on macOS from committed evidence alone.
