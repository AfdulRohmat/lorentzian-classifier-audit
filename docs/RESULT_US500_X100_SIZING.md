# US500_x100 conditional account simulation

Status: `CONDITIONAL_SIZING_ONLY_LIVE_SPEC_UNVERIFIED`.

The larger contract does not multiply risk-normalized strategy returns by 100.
It makes the minimum exposure and lot increments coarser. The minimum volume
prevents meaningful participation for USD 500-1,000 at 1% risk. USD 3,000 at 1%
participates in 548/688 candidate trades, but still follows a different selected
trade sequence from the original US500 account.

## Scope and provenance

Reuse the v3 causal Lorentzian M30 ATR-runner ledger: 688 candidates, January
2024-August 2026, 32 calendar months. Entry, SL, trailing and exit price paths
remain those of the historical US500 model. This is a contract-sizing translation,
not a backtest of native x100 quotes, not a new holdout and not an edge upgrade.

Current [Exness index specifications](https://get.exness.help/hc/en-us/articles/17854383867548-Indices)
(accessed 25 September 2026) list x100 contract size 100, minimum 0.03 lot,
maximum 20 lots, normal margin 0.25% and high-margin rates of 1%-2%.
The broker page was updated 17 September 2026. Current rules are applied across
the historical sample; historical specification changes are not reconstructed.

MT5 returned `IPC timeout (-10005)` for both read-only connection attempts.
Consequently these assumptions remain unverified for the user's account:

- volume step 0.01 lot;
- identical underlying quote path, spread and slippage between US500 and x100;
- identical commission per exposure unit: USD 0.25 per regular lot round trip,
  modeled as USD 25 per x100 lot round trip;
- no swap, dividends or intratrade margin-call/stop-out model.

Sizing compounds from closed account equity after each completed trade. Minimum
lot is always skipped when it exceeds the risk budget. Every scenario filters
the frozen ledger; a skipped position does not enable new entry windows.

## Why small accounts skip so many trades

`0.03 x 100 = 3` index units, so a one-point price move has USD 3 gross PnL at
minimum x100 volume. Regular US500 minimum exposure is only 0.14 units.

Across the frozen candidates, planned minimum-lot loss ranges from USD 7.16 to
USD 259.62, with median USD 27.67. Thus:

- USD 500 at 1% has only a USD 5 budget: no candidate fits;
- USD 1,000 at 1% starts with USD 10: only six candidates fit along its resulting
  equity path, all in 2024;
- USD 3,000 at 1% starts with USD 30: substantially more candidates fit.

If a trade has a 10-point all-in planned loss and a USD 30 budget, equivalent
positions are 3 lots regular US500 or 0.03 lot x100. Both risk USD 30.

## All 15 primary scenarios

These results include the modeled fees and broker volume rules above. Static
1:400 entry-margin screening changes none of these results. Drawdown is measured
on closed balances, not floating intratrade equity. Monthly mean is the arithmetic
mean across all 32 months, including inactive months.

| Start | Risk cap | Executed / skipped | Final balance | Total return | Mean month | Max DD |
|---:|---:|---:|---:|---:|---:|---:|
| $500 | 1% | 0 / 688 | $500.00 | 0.00% | 0.00% | 0.00% |
| $500 | 2% | 6 / 682 | $509.61 | +1.92% | +0.07% | 5.30% |
| $500 | 3% | 194 / 494 | $1,140.02 | +128.00% | +3.36% | 42.57% |
| $500 | 4% | 572 / 116 | $3,006.69 | +501.34% | +8.95% | 61.38% |
| $500 | 5% | 182 / 506 | $293.08 | -41.38% | -0.91% | 69.98% |
| $1,000 | 1% | 6 / 682 | $1,009.61 | +0.96% | +0.03% | 2.75% |
| $1,000 | 2% | 489 / 199 | $3,741.79 | +274.18% | +5.10% | 36.32% |
| $1,000 | 3% | 603 / 85 | $3,639.91 | +263.99% | +6.26% | 50.40% |
| $1,000 | 4% | 613 / 75 | $2,746.24 | +174.62% | +7.14% | 68.22% |
| $1,000 | 5% | 640 / 48 | $2,809.30 | +180.93% | +9.39% | 75.76% |
| $3,000 | 1% | 548 / 140 | $5,854.98 | +95.17% | +2.35% | 18.21% |
| $3,000 | 2% | 670 / 18 | $8,267.67 | +175.59% | +4.26% | 38.28% |
| $3,000 | 3% | 679 / 9 | $9,260.36 | +208.68% | +6.05% | 56.67% |
| $3,000 | 4% | 680 / 8 | $9,645.97 | +221.53% | +8.09% | 69.24% |
| $3,000 | 5% | 679 / 9 | $8,223.46 | +174.12% | +9.96% | 79.15% |

The USD 500/4% gain is especially path-sensitive. Raising risk to 5% changes
the subset of affordable trades and the compounded balance path, leaving a
loss. Selecting 4% because its inspected PnL is largest would be another
historical selection decision, not evidence of a stable improvement.

## USD 3,000 at 1% detail

- 548 executed and 140 skipped trades: 3.94/week and 17.13/month;
- final balance USD 5,854.98, total profit USD 2,854.98;
- arithmetic mean monthly return +2.35%; geometric monthly return +2.11%;
- 19 positive and 13 negative months;
- max closed-balance drawdown 18.21%;
- average executed planned risk uses 90.43% of the 1% cap due to lot flooring;
- 46 of 53 greater-than-3R winners captured; seven skipped;
- two realized losses exceeded their planned risk budget due to the inherited
  gap/slippage behavior.

| Period | Start | End | Return | Executed trades |
|---|---:|---:|---:|---:|
| 2024 | $3,000.00 | $3,717.17 | +23.91% | 229 |
| 2025 | $3,717.17 | $4,861.61 | +30.79% | 188 |
| Jan-Aug 2026 | $4,861.61 | $5,854.98 | +20.43% | 131 |

There is no September holdout included in this account table.

## Equal-capital comparison at 1% risk

| Start | Regular US500: trades / final / DD | US500_x100: trades / final / DD |
|---:|---|---|
| $500 | 681 / $922.85 / 23.64% | 0 / $500.00 / 0.00% |
| $1,000 | 685 / $1,830.37 / 24.36% | 6 / $1,009.61 / 2.75% |
| $3,000 | 688 / $5,525.57 / 24.49% | 548 / $5,854.98 / 18.21% |

The x100 result for USD 3,000 is better in this sample because selection and
risk rounding changed. It does not establish a superior signal or an x100
profit multiplier. In particular, the seven skipped tails are a deterministic,
equity/volatility-dependent subset, unlike the independent tail misses in v4's
Monte Carlo; the v4 probabilities cannot simply be reused for this account.

## Static margin sensitivities

For each trade, proxy required margin is `entry price x contract x lots x rate`.
Skip if this amount plus modeled round-trip commission exceeds pre-entry equity.
Margin is collateral and is not deducted as trading loss. Positions are not
downsized after a margin rejection. This is only an entry screen; intratrade
spread effects, maintenance rules and stop-outs are not replayed.

At normal 1:400, every risk-sized x100 entry fits the proxy margin screen. At
constant 1:100, only the 5% scenarios change. At constant 1:50, some larger-risk
paths change drastically:

| Capital / risk | Final at 1:400 | Final at 1:100 | Final at 1:50 | 1:50 margin skips |
|---|---:|---:|---:|---:|
| $500 / 4% | $3,006.69 | $3,006.69 | $406.53 | 24 |
| $1,000 / 5% | $2,809.30 | $2,088.26 | $400.15 | 89 |
| $3,000 / 1% | $5,854.98 | $5,854.98 | $5,854.98 | 0 |
| $3,000 / 5% | $8,223.46 | $7,900.28 | $1,600.22 | 108 |

Constant high-margin scenarios are sensitivity tests, not assertions that these
rates applied throughout the historical interval. Rejections also change later
balances and lot eligibility, so their effect extends beyond the rejected trades.

## Engineering review and continuation

All five new focused tests pass (16 total), including dollar scaling without
price scaling, equal-exposure invariance, compounding, minimum lot rejection,
margin rejection and gap-loss behavior. The independent evidence validator
passes 12/12 checks, including all original USD 500/1,000 US500 account paths
matching v3. A repeated run reproduced the evidence files byte for byte.

Evidence: `evidence/us500_x100_sizing/` contains 75 account summaries, compressed
account ledgers, monthly and annual tables, provenance manifest and validation.
The run is reproducible from committed v3 evidence without MT5 or raw M1:

```bash
python -m lorentzian_audit.run_x100
python -m lorentzian_audit.validate_x100
```

Before demo automation on x100, collect a live redacted symbol snapshot and
confirm volume step, commission, stop levels, tick value, margin calculation
and quote equivalence. USD 500-1,000 at 1% does not reproduce the existing
strategy frequency under these specifications. USD 3,000 at 1% is a feasible
candidate for that execution audit, with 20.3% of historical candidates skipped;
it is not a replacement of the frozen regular-US500 forward-test contract.
