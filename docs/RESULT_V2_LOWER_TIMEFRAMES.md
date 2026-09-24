# Result - lower-timeframe Lorentzian audit v2

## Verdict

`NO_ROBUST_M30_CROSS_ASSET_LORENTZIAN_EDGE`

Lower timeframes solved the activity problem but not the edge problem. The
frozen M30 causal Lorentzian produced about five trades per calendar week per
asset, yet only SP500 was slightly positive and neither asset met the declared
quality requirements. Only the minimum-trade gate passed.

## Full-history causal result

Evaluation: January 2024 through August 2026. Results are after the frozen base
cost model and expressed in basis points of the underlying entry price. An
active day is a UTC date containing source bars, not necessarily a day with a
trade.

| Asset | TF | Trades | / week | / active day | Net bps | Mean bps | Win rate | PF | Max DD bps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SP500 | M15 | 1,352 | 9.72 | 1.62 | -1,621.7 | -1.199 | 46.4% | 0.859 | 1,737.3 |
| SP500 | M30 | 689 | 4.95 | 0.83 | +146.6 | +0.213 | 50.9% | 1.018 | 704.6 |
| SP500 | H1 | 342 | 2.46 | 0.41 | -236.2 | -0.691 | 48.0% | 0.961 | 1,144.4 |
| XAUUSD | M15 | 1,520 | 10.92 | 1.83 | -343.4 | -0.226 | 47.4% | 0.979 | 1,740.5 |
| XAUUSD | M30 | 754 | 5.42 | 0.91 | -434.6 | -0.576 | 47.6% | 0.958 | 1,208.6 |
| XAUUSD | H1 | 362 | 2.60 | 0.44 | +1,099.7 | +3.038 | 50.8% | 1.182 | 790.3 |

The M30 primary did not generalize across assets. SP500's small positive total
also failed every robustness check that matters: stress costs changed it to
-418.3 bps, removing the ten best trades changed it to -1,251.1 bps, and the
monthly-bootstrap interval was [-37.68, +51.11] bps. Its year blocks were
-307.1, +500.3 and -46.6 bps for 2024, 2025 and 2026 respectively. An always-long
direction on the exact same windows returned +1,378.8 bps, versus only +146.6
bps for the classifier directions.

XAUUSD M30 was negative, and its Euclidean, simple momentum and kernel-only
comparators all beat Lorentzian. Therefore the declared primary hypothesis is
not supported.

## The interesting H1 XAUUSD pocket

XAUUSD H1 is positive under base and stress costs and all three annual blocks
are positive:

- 2024: +7.8 bps from 134 trades;
- 2025: +222.9 bps from 159 trades;
- 2026 through August: +869.0 bps from 69 trades.

It is not promotion evidence. Removing the ten best trades changes +1,099.7 to
-401.9 bps; the monthly-bootstrap interval is [-25.74, +94.96] bps; its
random-direction p-value is 0.0855; and long trades contribute +1,362.3 bps
while short trades contribute -262.6 bps. Simple four-bar momentum returns
+1,446.8 bps on its own windows. Selecting XAUUSD H1 now would be a post-result
timeframe/asset choice, so this is only a separately testable future hypothesis.

## Exact-original recent diagnostic

The pinned original implementation was also run on 2,500 ending bars: 500 bars
of context plus approximately 2,000 scored bars. It is a recent chart diagnostic,
not multi-year evidence.

| Asset | TF | Scored date range | Trades | / week | Net bps | Win rate | PF |
|---|---:|---|---:|---:|---:|---:|---:|
| SP500 | M15 | 2026-07-31 to 2026-09-01 | 51 | 11.24 | -198.7 | 45.1% | 0.485 |
| SP500 | M30 | 2026-07-01 to 2026-09-01 | 62 | 7.04 | +83.7 | 58.1% | 1.166 |
| SP500 | H1 | 2026-04-30 to 2026-09-01 | 69 | 3.91 | -1,004.9 | 39.1% | 0.356 |
| XAUUSD | M15 | 2026-07-31 to 2026-09-01 | 62 | 13.67 | -30.7 | 50.0% | 0.960 |
| XAUUSD | M30 | 2026-07-01 to 2026-09-01 | 67 | 7.61 | +172.3 | 41.8% | 1.187 |
| XAUUSD | H1 | 2026-04-30 to 2026-09-01 | 60 | 3.40 | +631.0 | 53.3% | 1.693 |

The signal counts are broadly comparable to the supplied TradingView panels,
but the outcomes do not reproduce them. The screenshots report XAUUSD
M15/M30/H1 counts of 71/64/55 with win rates 63.4%/59.4%/58.2%; the Exness audit
has 62/67/60 trades with win rates 50.0%/41.8%/53.3%. This is not an exact
feed/window/execution replication: the screenshots use OANDA through 25
September, while the audit uses Exness through 31 August, next-bar Bid-open
execution and explicit costs. The panel's `WL Ratio` is wins divided by losses,
not profit factor.

## Gate result

| Frozen M30 gate | Pass |
|---|---:|
| Positive and PF at least 1.10 on both assets | No |
| Beats Euclidean, momentum and kernel on both assets | No |
| At least 500 trades on both assets | Yes |
| Every frozen year block positive on both assets | No |
| Positive after removing ten best trades on both | No |
| Monthly-bootstrap lower bound above zero on both | No |
| Positive under stress costs on both | No |
| Random-direction one-sided p below 0.05 on both | No |

## Engineering audit

- Seven unit tests pass, including exact equality between batched KNN and the
  transparent reference implementation and equality of the optimized
  feature/kernel path with the pinned upstream implementation.
- The evidence validator passes 11/11 checks: source hashes, causal label
  maturity, next-bar fills, exits, non-overlap, costs, bps, summary totals and
  verdict logic.
- A complete second run reproduced identical SHA-256 hashes for the summary,
  trade ledger, monthly table, annual table, source manifest and validation.

The evidence files are in `evidence/v2_lower_timeframes/`.
