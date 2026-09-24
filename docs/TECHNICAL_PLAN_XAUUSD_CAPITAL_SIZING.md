# XAUUSD M30 capital extension

The user requested the same compounded account simulation with USD 3,000 added
to USD 500 and USD 1,000, each at 1%-5% risk. Keep M30 as the primary timeframe,
using the frozen causal Lorentzian entries and v3 ATR runner (1 ATR initial SL,
no TP, +1 net R trail activation, 1R completed-close trail, opposite/24h exits).

Use the already cost-adjusted XAUUSD v3 ledger from January 2024-August 2026.
Contract size is 100 ounces; minimum and step are 0.01 lot. These are the frozen
v3 assumptions, not a fresh live-broker audit. Do not multiply the gold price
or dollar returns by another 100.

The USD 500/1,000 outcomes have been inspected before. The new USD 3,000 grid
is declared before account outcomes are opened. Reuse `runner.simulate_account`
and record all 15 ledgers, summaries, calendar-month returns and calendar-year
returns. Show trade participation and tail capture to distinguish lot feasibility
from strategy expectancy.

Checks: input hashes, all scenario identities, cashflow/compounding, risk caps,
floor/skip behavior, unchanged fills, summary/calendar reconciliation, exact
reproduction of the original ten accounts, and deterministic output replay.
No new market-data download, broker order or native MT5 strategy test is needed.

Interpretation remains limited by v3's missing margin/swap/intratrade equity
model and frozen-ledger skips. Publish the full table in README and a dedicated
report; retain earlier research verdicts without selecting a different timeframe.
