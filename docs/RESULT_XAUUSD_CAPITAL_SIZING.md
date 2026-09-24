# XAUUSD M30: USD 500, 1,000 and 3,000 capital simulation

All 15 account scenarios lose money over January 2024-August 2026 (32 months).
Adding USD 3,000 reduces minimum-lot skips but does not repair the frozen M30
strategy's negative historical expectancy. At USD 3,000/1%, 720 of 745 trades
execute, including all 33 winners above +3R, yet the final balance is USD 2,190.02.

## Unchanged strategy and assumptions

Reuse the v3 causal Lorentzian M30 signal ledger, with next-bar entry, 1 ATR(14)
initial stop, no fixed TP, a completed-close trail activated at +1 net R and
set one R below the best completed-close result, opposite-signal/24-hour exits.
The underlying 745 trades return -32.48R, mean -0.0436R and PF 0.927 after
modeled costs. The ten USD 500/1,000 scenarios were previously inspected; the
USD 3,000 grid was declared before its account outcomes were inspected.

The frozen XAUUSD contract is 100 ounces per lot with 0.01 minimum/step and
200 maximum lots. Compounding sizes planned risk from the closed account
balance after each trade. Round down to lot step; skip if the minimum lot is
too large. There is no extra x100 multiplier applied to gold prices or PnL.

The inherited model includes historical spread, USD 0.02 price slippage per
side and USD 0.07/oz round-trip commission (USD 7 per standard lot). It excludes
margin, swap and intratrade equity/stop-outs. These are the same v3 assumptions,
not a new live broker specification audit. Skips filter a frozen trade ledger
and do not create new entry windows. No new market holdout is introduced.

## All account scenarios

Monthly means are arithmetic across all 32 months, including inactive ones.
Drawdown is measured on closed balances, not floating intratrade equity.

| Start | Risk cap | Executed / skipped | Final balance | Total return | Mean monthly | Max balance DD |
|---:|---:|---:|---:|---:|---:|---:|
| $500 | 1% | 171 / 574 | $445.84 | -10.83% | -0.32% | 24.66% |
| $500 | 2% | 394 / 351 | $381.21 | -23.76% | -0.54% | 42.98% |
| $500 | 3% | 407 / 338 | $265.92 | -46.82% | -1.23% | 66.10% |
| $500 | 4% | 468 / 277 | $307.31 | -38.54% | +0.04% | 76.35% |
| $500 | 5% | 469 / 276 | $241.92 | -51.62% | +0.15% | 81.53% |
| $1,000 | 1% | 424 / 321 | $777.46 | -22.25% | -0.71% | 30.21% |
| $1,000 | 2% | 589 / 156 | $638.18 | -36.18% | -0.79% | 52.10% |
| $1,000 | 3% | 520 / 225 | $414.46 | -58.55% | -1.67% | 77.43% |
| $1,000 | 4% | 498 / 247 | $310.08 | -68.99% | -1.73% | 84.63% |
| $1,000 | 5% | 478 / 267 | $242.18 | -75.78% | -1.87% | 90.15% |
| $3,000 | 1% | 720 / 25 | $2,190.02 | -27.00% | -0.78% | 35.37% |
| $3,000 | 2% | 734 / 11 | $1,353.62 | -54.88% | -1.66% | 64.62% |
| $3,000 | 3% | 724 / 21 | $721.53 | -75.95% | -2.52% | 82.36% |
| $3,000 | 4% | 655 / 90 | $328.08 | -89.06% | -4.20% | 91.80% |
| $3,000 | 5% | 593 / 152 | $230.63 | -92.31% | -4.35% | 94.23% |

The two positive arithmetic means at USD 500/4%-5% coexist with large total
losses because of compounding drag. Their geometric monthly returns are -1.51%
and -2.24%, respectively. Neither is a profitable account.

## USD 3,000 at 1% detail

- 720 executed trades (96.6% participation), 25 minimum-lot skips;
- 5.17 trades per calendar week and 22.50 per calendar month;
- USD 809.98 loss, -27.00% total return;
- -0.78% arithmetic mean month, -0.98% geometric monthly growth;
- 12 positive months and 20 negative months;
- all 33 tail winners above +3R executed;
- one realized loss exceeds planned budget, approximately 1.60 times its budget;
- maximum closed-balance drawdown 35.37%.

| Period | Start balance | End balance | Return | Executed trades |
|---|---:|---:|---:|---:|
| 2024 | $3,000.00 | $2,484.46 | -17.18% | 285 |
| 2025 | $2,484.46 | $2,403.26 | -3.27% | 281 |
| Jan-Aug 2026 | $2,403.26 | $2,190.02 | -8.87% | 154 |

All 25 skipped trades in this scenario occur in 2026. Sufficient starting
capital improves participation, but declining equity can later make more
trades unaffordable, especially at higher risk fractions.

## Interpretation and engineering checks

This extension strengthens the existing conclusion about this specific M30
implementation: minimum lot is not the sole explanation for its losses.
Higher capital captures every large winner at 1% risk, yet ordinary losses
still outweigh them after costs. This does not establish that all XAUUSD
strategies fail; it leaves the SP500 demo candidate and its rules unchanged.

The original account simulator was reused. All 16 existing unit tests and
lint pass; the extension's nine evidence checks cover source/contract hashes,
scenario coverage, volume/risk rules, cashflows, calendars, summary totals and
matching the original ten account paths. Repeated generation reproduces all
six evidence artifacts byte for byte.

Files in `evidence/xauusd_capital_sizing/` include account summaries, compressed
trade-by-trade accounts, monthly/annual tables, manifest and validation.
Reproduce and validate with the installed project, without MT5 or raw M1:

```bash
python -m lorentzian_audit.run_xau_sizing
```

The contract is `config/contract_xauusd_capital_sizing.json`; the technical
plan is `docs/TECHNICAL_PLAN_XAUUSD_CAPITAL_SIZING.md`.
