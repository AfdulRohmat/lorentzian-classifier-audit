# Native US500 M30, one ATR stop and 24-hour exit

## Result

**All six full-period MT5 Strategy Tester runs are negative.** The historical
US500 Python runner's positive 2024-August 2026 result does not carry over to
this shorter native January-August 2026 test. The native result is not a clean
causal explanation: it also changes the data feed, warm-up anchor, tick-level
fills and evaluation period. The same 2026 window on `US500_x100` was negative
as well. This is an inspected historical slice, not an unseen holdout.

The contract is [frozen here](TECH_PLAN_NATIVE_US500_1ATR24H.md). It uses the
causal modified Lorentzian M30 start, no VWAP, 1 x ATR14 initial broker stop,
no TP, +1R completed-bar trailing at 1R distance, opposite start exits and a
24-hour deadline at the next tradable quote. History is anchored to 15 June
2025; evaluation is 1 January through 31 August 2026. The only pre-result EA
change permitted exact `US500` in its tester-only symbol gate. USD accounts,
simulated leverage 1:400, native broker Bid/Ask tick fills, commission and swap.

| Start | Sizing policy | Trades | Final balance | Net PnL | Return | Net PF | Win rate | Max equity DD | Trades/week |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| $500 | Strict 1% | 167 | $458.20 | -$41.80 | -8.36% | 0.925 | 34.13% | 35.87% | 4.81 |
| $500 | 1% + minimum fallback | 167 | $458.20 | -$41.80 | -8.36% | 0.925 | 34.13% | 35.87% | 4.81 |
| $1,000 | Strict 1% | 167 | $913.98 | -$86.02 | -8.60% | 0.924 | 34.13% | 36.11% | 4.81 |
| $1,000 | 1% + minimum fallback | 167 | $913.98 | -$86.02 | -8.60% | 0.924 | 34.13% | 36.11% | 4.81 |
| $3,000 | Strict 1% | 167 | $2,739.29 | -$260.71 | -8.69% | 0.923 | 34.13% | 36.23% | 4.81 |
| $3,000 | 1% + minimum fallback | 167 | $2,739.29 | -$260.71 | -8.69% | 0.923 | 34.13% | 36.23% | 4.81 |

The 167 trades average **20.88 per month**. No trade needed the US500 minimum
lot fallback in this sample; within each balance, the strict and fallback
deal exports are byte-identical. The maximum planned stop risk remained below
1% of closed balance, but 12 / 17 / 28 realized losses at $500 / $1,000 /
$3,000 exceeded the nominal budget after market fills and costs. A protective
stop is not a guaranteed monetary loss ceiling.

## Monthly cash result for the $1,000 strict-risk reference

Returns below are changes in *closed balance*, not marked-to-market monthly
equity returns. The strategy held positions across some calendar boundaries.

| Month 2026 | Trades | Cash PnL | Closed-balance return |
|---|---:|---:|---:|
| January | 21 | +$6.14 | +0.61% |
| February | 17 | +$83.19 | +8.27% |
| March | 21 | -$4.32 | -0.40% |
| April | 25 | +$57.49 | +5.30% |
| May | 22 | -$143.35 | -12.55% |
| June | 17 | -$112.32 | -11.24% |
| July | 25 | -$86.86 | -9.79% |
| August | 19 | +$114.01 | +14.25% |

For the same $1,000 run, long deals contributed +$33.40 and shorts -$119.42.
Native commission was -$18.69 and swap -$18.95, already included in net PnL.
The mean hold was 4.16 hours. Five exits happened after 24 clock hours because
the deadline can only be acted on at an available quote; the EA cannot force a
fill at the exact 24-hour mark.
These observations do not authorize selecting only long trades after inspection.

## Reading US500 against US500_x100

The previously completed [native x100 minimum-lot test](RESULT_NATIVE_X100_MINIMUM_LOT.md)
uses the same classifier, 1 x ATR stop and 24-hour rule on the same evaluation
months. The two saved 2026 signal streams contain **172 raw starts each**, with
all 172 timestamp-and-direction starts shared; each $1,000 run executed 167
trades. This is signal agreement on the compared 2026 window, not proof that
the full feature histories, broker quotes, stops or sizing are identical.

| Symbol, $1,000 | Position sizing | Net PnL | Return | Net PF | Max equity DD |
|---|---|---:|---:|---:|---:|
| US500 | Strict 1%, variable lots, no minimum fallback used | -$86.02 | -8.60% | 0.924 | 36.11% |
| US500_x100 | 0.01 lot on every filled trade, 1% target overridden by minimum | -$240.53 | -24.05% | 0.832 | 46.18% |

Different contract exposure and feed/cost paths mean the monetary difference
cannot be attributed solely to symbol naming. The old US500 Python result was
January 2024-August 2026, with a January 2022 normalization history and modeled
M1 fills. This native study begins its model in June 2025 and evaluates only
eight months of 2026. Do not splice their returns together or call either a
new independent validation.

## Engineering validation and evidence

- One January smoke and all six full runs completed. Native reports state
  **100% real ticks** on their tested coverage; 28,855,528 ticks occurred in
  each full run. The EA was tester-only throughout; no demo or real order path
  was enabled.
- The reporter reconciled each native deal ledger to final balance, inspected
  actual commission/swap, and independently audited every entry direction,
  initial ATR stop, lot floor and trail (`path_audit=PASS`). Time exits and
  holding durations were recorded separately.
  All six final runs have `failed=0`.
- Final compiled EX5 SHA-256:
  `FD5EAF35202B665CA3D6F212FE318B97F364244D97CF5812E9C879E09B72D135`.
  Source SHA-256 before this report:
  `9126BFD0534C2E23E1EDA3DE207E3EF61C1BA1B303184D2D0FF05EE651064562`.
- The first $500 strict full attempt is retained under
  `evidence/native_us500_1atr24h_2026/` as **invalid**. Native USD
  `OrderCalcProfit` rounded a $4.6359 theoretical loss to $4.64 against a
  $4.6368 budget, tripping an overly strict post-fill cent check. The EA
  closed that entry and flagged failure. Only the post-fill half-cent
  conversion tolerance changed; the theoretical pre-order risk budget and
  strategy rules did not. All final runs used new tags and were rerun from
  scratch after the correction.
- Before testing and after restoring a read-only MT5 session, the connected
  demo account had Algo Trading disabled, zero positions and zero pending
  orders. No account orders were sent by this research.

Full native exports, configs and the checked summaries are in
[`evidence/native_us500_1atr24h_2026_v2/`](../evidence/native_us500_1atr24h_2026_v2/).
The original historical x100 and Python results remain unchanged. This test
does not support choosing US500 or x100 for an automated demo forward EA based
on this eight-month slice alone.
