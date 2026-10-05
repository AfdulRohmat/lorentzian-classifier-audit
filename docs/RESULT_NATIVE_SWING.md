# Native US500 x100 swing results

The complete 150-variant swing experiment ran in the MT5 Strategy Tester, not a Python price simulator. It uses the previously inspected January through August 2026 period, with June through December 2025 classifier warm-up. It is not unseen validation, production readiness or authorization to trade.

Of 150 scenarios, **22 are positive, 82 negative and 46 have no trades**. These overlapping scenarios are not independent replications. A best result selected from this grid is exploratory.

## Verified execution

Three legacy controls reproduce the old deal exports byte for byte and match native balance, trades, drawdown and costs. Runs that reach the end use the identical classifier signal stream; insolvent early stops must match its exact prefix. Every run uses one EA build. Native reports indicate 100 percent real ticks; all deal ledgers reconcile to final balances. The path audit verifies entry direction, initial ATR stop, scaled trail, opposite-only setup exits and absence of time exits in swing variants. All positions are liquidated by test end. Zero added execution delay is a modeling limitation.

EA compilation completed with zero errors and zero warnings. The Python suite has 87 passing tests, including stop/trail width, sizing, causal setup checks and insolvency reporting. This is engineering verification, not a profitability pass. The one January smoke run is excluded from performance comparisons and full-period scenario counts.

**4 scenarios stopped early after native insolvency.** They remain failed economic outcomes in the matrix, not missing data or completed eight-month histories. Activity averages use the full intended eight-month calendar. Compounded and arithmetic monthly returns are undefined once balance is nonpositive.

The first insolvency exposed a reporting error when adding undefined monthly returns. The reporter was corrected and immutable native exports reprocessed; no EA trading rule or parameters changed. Early termination is accepted only with native stop-out reason, nonpositive balance, reconciled closed deals and exact classifier prefix. No insolvent scenario is silently dropped.

## Rules and interpretation

Entry remains the existing causal exact KNN Lorentzian M30 start, not the original author's ANN. Initial stop is k times entry ATR14; that distance plus the existing 0.27 point reserve defines R. Trail activates at +1R net of reserve and follows at 1R, using completed M30 quotes. No fixed TP or 24 hour deadline. Opposite starts close and may reverse; same-side starts do not add or reset.

The 1 percent row uses minimum 0.01 lot fallback when necessary: **it is not a strict 1 percent loss limit**. Risk rows 2 to 5 floor position size and skip below minimum. Widening stops can change both actual monetary risk and the trade sample. Stop gaps can exceed planned risk. Swaps are native tester charges; historical fidelity of the swap schedule is not independently proved.

## Isolating removal of the deadline

These matched 1 percent plus minimum-lot rows compare old 24 hour exits with swing at the same one ATR stop. They do not isolate the effect of wider stops.

| Capital | Old return % | Swing 1 ATR return % | Old equity DD % | Swing equity DD % | Old trades | Swing trades |
|---|---:|---:|---:|---:|---:|---:|
| $500 | -48.11 | -63.97 | 76.45 | 86.50 | 167 | 167 |
| $1000 | -24.05 | -31.98 | 46.18 | 51.73 | 167 | 167 |
| $3000 | -5.64 | -10.24 | 29.51 | 31.73 | 167 | 167 |

The $1000 minimum-lot comparison has 167 matched entry timestamps and identical lots. Only 5 trade outcomes change, totaling $-79.31. This separates the deadline effect from position sizing in this one comparison. The old deadline can execute later than 24 hours when the market is closed.

| Entry timestamp as exported | Old net USD | Swing net USD | Old holding h | Swing holding h |
|---|---:|---:|---:|---:|
| 2026-02-06 15:30:00+00:00 | 57.25 | 51.88 | 55.50 | 62.52 |
| 2026-04-10 17:00:01+00:00 | 74.20 | 71.91 | 53.00 | 54.93 |
| 2026-04-13 16:30:00+00:00 | 120.30 | 108.78 | 24.00 | 25.86 |
| 2026-06-26 20:30:00+00:00 | 9.95 | -25.92 | 49.50 | 50.56 |
| 2026-07-17 19:30:00+00:00 | 6.68 | -17.58 | 50.50 | 52.62 |

## Highest historical returns in the grid

Descriptive ranking only, selected after inspecting all 150 variations. These are not independent confirmations or approved settings. Positive sizing rows may trade different subsets of the identical signal stream.

| Capital | ATR | Target risk % | Trades | Return % | Equity DD % | PF | Trades per week | Geometric month % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| $1000 | 3 | 4 | 87 | 36.77 | 22.56 | 1.223 | 2.51 | 3.99 |
| $3000 | 10 | 4 | 64 | 24.85 | 9.90 | 1.618 | 1.84 | 2.81 |
| $1000 | 2 | 3 | 103 | 19.93 | 34.23 | 1.154 | 2.97 | 2.30 |
| $500 | 2 | 5 | 79 | 16.41 | 53.15 | 1.091 | 2.28 | 1.92 |
| $3000 | 8 | 3 | 61 | 15.45 | 8.76 | 1.420 | 1.76 | 1.81 |

## All capital and risk combinations

Cells contain total return percent followed by maximum equity drawdown percent. The full trade, monthly, risk and holding metrics for every cell are in [validated evidence](../evidence/native_x100_swing_2026/validated_summary.json). N/A marks scenarios with no executed trades, not a profitable strategy.

### Capital 500 USD

| SL and trail ATR | 1% plus min lot | Strict 2% | Strict 3% | Strict 4% | Strict 5% |
|---|---:|---:|---:|---:|---:|
| 1 | -63.97 / 86.50 | 8.87 / 23.98 | -15.60 / 49.87 | -10.53 / 69.36 | -32.68 / 78.77 |
| 2 | -99.93 / 99.94 | N/A | 4.31 / 11.55 | -8.75 / 29.65 | 16.41 / 53.15 |
| 3 | -100.00 / 100.00 | N/A | N/A | -5.43 / 11.91 | -7.92 / 25.20 |
| 4 | -100.20 / 100.12 | N/A | N/A | N/A | -0.55 / 7.37 |
| 5 | -100.56 / 100.42 | N/A | N/A | N/A | N/A |
| 6 | -99.01 / 99.42 | N/A | N/A | N/A | N/A |
| 7 | -100.23 / 100.12 | N/A | N/A | N/A | N/A |
| 8 | -27.96 / 76.13 | N/A | N/A | N/A | N/A |
| 9 | -46.71 / 83.15 | N/A | N/A | N/A | N/A |
| 10 | -45.13 / 82.67 | N/A | N/A | N/A | N/A |

### Capital 1000 USD

| SL and trail ATR | 1% plus min lot | Strict 2% | Strict 3% | Strict 4% | Strict 5% |
|---|---:|---:|---:|---:|---:|
| 1 | -31.98 / 51.73 | 0.28 / 47.83 | -21.24 / 64.82 | -38.32 / 79.26 | -51.04 / 84.93 |
| 2 | -54.40 / 81.14 | 3.34 / 11.21 | 19.93 / 34.23 | 1.64 / 35.79 | -10.38 / 50.28 |
| 3 | -41.13 / 68.97 | 0.34 / 6.59 | 13.61 / 19.75 | 36.77 / 22.56 | 9.49 / 32.12 |
| 4 | -54.63 / 73.59 | N/A | -4.33 / 11.64 | -8.02 / 25.00 | -3.36 / 29.64 |
| 5 | -54.11 / 68.76 | N/A | 0.02 / 3.82 | -11.42 / 17.58 | -15.42 / 25.75 |
| 6 | -55.36 / 71.04 | N/A | N/A | -6.99 / 8.68 | -17.82 / 21.89 |
| 7 | -50.44 / 70.08 | N/A | N/A | 0.68 / 3.61 | -12.78 / 13.95 |
| 8 | -13.98 / 52.71 | N/A | N/A | N/A | -4.98 / 5.00 |
| 9 | -23.35 / 56.76 | N/A | N/A | N/A | -0.27 / 4.89 |
| 10 | -22.57 / 55.89 | N/A | N/A | N/A | N/A |

### Capital 3000 USD

| SL and trail ATR | 1% plus min lot | Strict 2% | Strict 3% | Strict 4% | Strict 5% |
|---|---:|---:|---:|---:|---:|
| 1 | -10.24 / 31.73 | -21.48 / 57.19 | -39.42 / 73.39 | -52.81 / 83.92 | -66.24 / 89.36 |
| 2 | -18.79 / 29.19 | -18.38 / 36.23 | -30.21 / 48.56 | -45.01 / 60.95 | -52.84 / 70.72 |
| 3 | -13.71 / 27.66 | -4.89 / 23.03 | -10.07 / 32.70 | -24.97 / 47.02 | -31.76 / 56.10 |
| 4 | -18.21 / 29.33 | 2.62 / 8.99 | -18.35 / 28.02 | -18.64 / 35.15 | -31.17 / 50.01 |
| 5 | -18.04 / 25.45 | 4.33 / 10.06 | -9.32 / 18.53 | -17.31 / 28.20 | -24.53 / 31.54 |
| 6 | -18.45 / 28.64 | -5.07 / 10.39 | -1.43 / 15.53 | -19.70 / 28.89 | -17.88 / 34.26 |
| 7 | -16.81 / 29.69 | -1.89 / 8.45 | 3.11 / 10.46 | -7.90 / 24.44 | -14.84 / 32.23 |
| 8 | -4.66 / 23.64 | -1.92 / 6.79 | 15.45 / 8.76 | 7.97 / 12.50 | -10.03 / 25.89 |
| 9 | -7.78 / 25.01 | -4.13 / 5.53 | 4.26 / 11.68 | 12.22 / 11.11 | -2.03 / 20.45 |
| 10 | -7.52 / 24.35 | -0.65 / 1.69 | -0.52 / 8.15 | 24.85 / 9.90 | 6.63 / 13.05 |

## One percent target with minimum lot fallback

Monthly dollar average is total net PnL divided by eight. Geometric monthly return is the constant compounded rate matching the start and end balance; it is not a prediction of regular monthly income. Realized trade R divides net PnL by each entry planned dollar risk, including the sizing reserve.

### Minimum lot results for 500 USD

| ATR | Trades | Per week | Per month | PF | WR % | Mean month $ | Geom month % | Mean holding h | Max planned risk % | Mean net R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 167 | 4.81 | 20.88 | 0.784 | 32.93 | -39.98 | -11.98 | 4.24 | 14.41 | -0.059 |
| 2 | 102 | 2.94 | 12.75 | 0.673 | 41.18 | -62.46 | -59.96 | 10.72 | 99.51 | -0.141 |
| 3 | 108 | 3.11 | 13.50 | 0.781 | 38.89 | -62.50 | N/A | 26.47 | 173.56 | -0.061 |
| 4 | 101 | 2.91 | 12.62 | 0.791 | 40.59 | -62.63 | N/A | 33.59 | 111.21 | -0.050 |
| 5 | 93 | 2.68 | 11.62 | 0.799 | 34.41 | -62.85 | N/A | 42.29 | 180.89 | -0.053 |
| 6 | 91 | 2.62 | 11.38 | 0.809 | 34.07 | -61.88 | -43.84 | 45.33 | 94.93 | -0.050 |
| 7 | 92 | 2.65 | 11.50 | 0.807 | 34.78 | -62.64 | N/A | 47.83 | 165.43 | -0.035 |
| 8 | 100 | 2.88 | 12.50 | 0.948 | 35.00 | -17.47 | -4.02 | 52.83 | 49.02 | 0.014 |
| 9 | 100 | 2.88 | 12.50 | 0.914 | 35.00 | -29.19 | -7.57 | 53.30 | 79.79 | 0.001 |
| 10 | 98 | 2.82 | 12.25 | 0.917 | 34.69 | -28.21 | -7.23 | 55.11 | 88.80 | 0.004 |

Monthly realized cash returns percent. Open-position floating PnL is **not** marked to market at month end in this table; swing holding can shift realized profits between months. Native maximum equity drawdown does include floating losses.

| ATR | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7.43 | 13.64 | -6.20 | 11.97 | -22.24 | -47.85 | -59.79 | 72.32 |
| 2 | -26.27 | 12.56 | -27.21 | 13.35 | -34.55 | -99.85 | 0.00 | 0.00 |
| 3 | -12.84 | -1.84 | -13.82 | 50.66 | 16.42 | -77.08 | -100.01 | N/A |
| 4 | -10.08 | -27.85 | 8.61 | 38.79 | 16.78 | -66.51 | -100.53 | N/A |
| 5 | -27.72 | -67.97 | 124.25 | 49.87 | 54.96 | -76.50 | -101.99 | N/A |
| 6 | -37.40 | -55.95 | 223.44 | 24.53 | 24.95 | -68.49 | -97.74 | 0.00 |
| 7 | -35.92 | 5.78 | 73.31 | 11.16 | 15.65 | -69.55 | -100.50 | N/A |
| 8 | -40.75 | 57.19 | 64.71 | 12.53 | 22.12 | -46.61 | -49.67 | 27.17 |
| 9 | -43.81 | 54.44 | 68.29 | 11.41 | 23.37 | -52.65 | -58.82 | 36.16 |
| 10 | -46.96 | 73.01 | 57.36 | 9.33 | 23.12 | -51.14 | -58.86 | 40.45 |

### Minimum lot results for 1000 USD

| ATR | Trades | Per week | Per month | PF | WR % | Mean month $ | Geom month % | Mean holding h | Max planned risk % | Mean net R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 167 | 4.81 | 20.88 | 0.784 | 32.93 | -39.98 | -4.70 | 4.24 | 3.25 | -0.059 |
| 2 | 145 | 4.18 | 18.12 | 0.749 | 41.38 | -68.00 | -9.35 | 11.74 | 16.04 | -0.092 |
| 3 | 124 | 3.57 | 15.50 | 0.839 | 38.71 | -51.41 | -6.41 | 26.75 | 12.15 | -0.041 |
| 4 | 118 | 3.40 | 14.75 | 0.803 | 38.98 | -68.28 | -9.41 | 33.83 | 19.09 | -0.058 |
| 5 | 108 | 3.11 | 13.50 | 0.811 | 33.33 | -67.64 | -9.28 | 42.34 | 22.76 | -0.058 |
| 6 | 106 | 3.05 | 13.25 | 0.813 | 33.02 | -69.20 | -9.59 | 44.92 | 25.69 | -0.060 |
| 7 | 105 | 3.02 | 13.12 | 0.826 | 34.29 | -63.05 | -8.40 | 48.09 | 26.76 | -0.042 |
| 8 | 100 | 2.88 | 12.50 | 0.948 | 35.00 | -17.47 | -1.86 | 52.83 | 18.56 | 0.014 |
| 9 | 100 | 2.88 | 12.50 | 0.914 | 35.00 | -29.19 | -3.27 | 53.30 | 22.66 | 0.001 |
| 10 | 98 | 2.82 | 12.25 | 0.917 | 34.69 | -28.21 | -3.15 | 55.11 | 25.18 | 0.004 |

Monthly realized cash returns percent. Open-position floating PnL is **not** marked to market at month end in this table; swing holding can shift realized profits between months. Native maximum equity drawdown does include floating losses.

| ATR | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3.72 | 7.06 | -3.41 | 6.39 | -12.50 | -23.89 | -20.45 | 12.51 |
| 2 | -13.13 | 5.33 | -12.34 | 5.03 | -14.04 | -47.31 | -42.97 | 109.59 |
| 3 | -6.42 | -0.85 | -6.37 | 21.50 | 8.64 | -43.47 | -33.66 | 36.90 |
| 4 | -5.04 | -13.18 | 3.39 | 16.03 | 8.30 | -35.46 | -47.27 | 24.49 |
| 5 | -13.86 | -28.52 | 23.36 | 17.04 | 24.05 | -41.82 | -40.51 | 20.21 |
| 6 | -18.70 | -21.54 | 48.30 | 11.57 | 13.13 | -39.81 | -43.55 | 10.04 |
| 7 | -17.96 | 2.26 | 29.62 | 6.03 | 8.87 | -41.85 | -37.77 | 9.11 |
| 8 | -20.37 | 21.28 | 31.20 | 7.59 | 14.01 | -31.61 | -26.30 | 9.83 |
| 9 | -21.91 | 19.59 | 31.73 | 6.78 | 14.47 | -35.14 | -28.66 | 10.17 |
| 10 | -23.48 | 25.31 | 27.45 | 5.51 | 14.16 | -33.77 | -28.67 | 11.36 |

### Minimum lot results for 3000 USD

| ATR | Trades | Per week | Per month | PF | WR % | Mean month $ | Geom month % | Mean holding h | Max planned risk % | Mean net R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 167 | 4.81 | 20.88 | 0.888 | 32.93 | -38.41 | -1.34 | 4.24 | 1.00 | -0.059 |
| 2 | 145 | 4.18 | 18.12 | 0.746 | 41.38 | -70.48 | -2.57 | 11.74 | 2.15 | -0.092 |
| 3 | 124 | 3.57 | 15.50 | 0.839 | 38.71 | -51.41 | -1.83 | 26.75 | 2.83 | -0.041 |
| 4 | 118 | 3.40 | 14.75 | 0.803 | 38.98 | -68.28 | -2.48 | 33.83 | 3.77 | -0.058 |
| 5 | 108 | 3.11 | 13.50 | 0.811 | 33.33 | -67.64 | -2.46 | 42.34 | 4.80 | -0.058 |
| 6 | 106 | 3.05 | 13.25 | 0.813 | 33.02 | -69.20 | -2.52 | 44.92 | 5.59 | -0.060 |
| 7 | 105 | 3.02 | 13.12 | 0.826 | 34.29 | -63.05 | -2.27 | 48.09 | 6.50 | -0.042 |
| 8 | 100 | 2.88 | 12.50 | 0.948 | 35.00 | -17.47 | -0.59 | 52.83 | 6.63 | 0.014 |
| 9 | 100 | 2.88 | 12.50 | 0.914 | 35.00 | -29.19 | -1.01 | 53.30 | 7.67 | 0.001 |
| 10 | 98 | 2.82 | 12.25 | 0.917 | 34.69 | -28.21 | -0.97 | 55.11 | 8.53 | 0.004 |

Monthly realized cash returns percent. Open-position floating PnL is **not** marked to market at month end in this table; swing holding can shift realized profits between months. Native maximum equity drawdown does include floating losses.

| ATR | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -0.69 | 7.08 | -0.17 | 1.92 | -10.91 | -9.48 | -8.40 | 12.30 |
| 2 | -5.69 | 1.64 | -3.93 | 0.99 | -4.24 | -12.82 | -7.04 | 12.52 |
| 3 | -2.14 | -0.27 | -2.02 | 6.51 | 2.98 | -15.84 | -8.24 | 6.53 |
| 4 | -1.68 | -4.24 | 0.99 | 4.79 | 2.75 | -12.37 | -12.14 | 3.78 |
| 5 | -4.62 | -8.58 | 5.50 | 4.69 | 7.40 | -14.86 | -9.84 | 3.24 |
| 6 | -6.23 | -6.23 | 11.68 | 3.71 | 4.53 | -14.88 | -11.51 | 1.69 |
| 7 | -5.99 | 0.66 | 8.75 | 2.12 | 3.24 | -16.14 | -10.10 | 1.69 |
| 8 | -6.79 | 6.06 | 10.16 | 2.94 | 5.68 | -13.82 | -9.13 | 2.77 |
| 9 | -7.30 | 5.50 | 10.10 | 2.58 | 5.74 | -15.08 | -9.39 | 2.63 |
| 10 | -7.83 | 7.00 | 8.90 | 2.09 | 5.55 | -14.32 | -9.40 | 2.93 |

## Holding costs and exit paths on 3000 USD

These are the 1 percent target plus minimum-lot rows. Wider stops also change risk and the entry sample, so the table is not a constant-risk experiment.

| ATR | Price PnL USD | Commission USD | Swap USD | Mean hold h | Maximum hold h | Initial SL exits | Trailed SL exits | Opposite exits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -214.07 | -45.45 | -47.79 | 4.24 | 62.52 | 112 | 54 | 0 |
| 2 | -489.86 | -19.57 | -54.41 | 11.74 | 115.39 | 80 | 59 | 6 |
| 3 | -268.24 | -16.12 | -126.92 | 26.75 | 149.50 | 54 | 44 | 25 |
| 4 | -375.97 | -15.34 | -154.95 | 33.83 | 149.50 | 37 | 34 | 46 |
| 5 | -355.63 | -14.04 | -171.44 | 42.34 | 149.50 | 22 | 22 | 63 |
| 6 | -366.72 | -13.78 | -173.09 | 44.92 | 149.50 | 18 | 17 | 70 |
| 7 | -307.77 | -13.65 | -182.98 | 48.09 | 149.51 | 10 | 16 | 78 |
| 8 | 67.73 | -13.00 | -194.52 | 52.83 | 150.00 | 3 | 12 | 84 |
| 9 | -24.37 | -13.00 | -196.17 | 53.30 | 150.00 | 3 | 10 | 86 |
| 10 | -16.74 | -12.74 | -196.17 | 55.11 | 163.00 | 3 | 8 | 86 |

## Limitations and reproduction

This broad grid tests exit sensitivity, not a new predictive classifier. Do not promote whichever width earns most on these same eight months. Performance may depend on changed trade eligibility, short sample, market path, costs and minimum-lot exposure. Session-open gaps, liquidity and live execution delay are not independently stress-tested here. The EA remains tester-only and lacks production restart/recovery handling.

Holding times use exported terminal timestamps. Overnight/weekend counts are calendar exposure diagnostics, not proof of exact swap billing. Giveback diagnostics use completed-bar marks, not true tick-level MFE, and compare a reserved-cost price mark with realized net including swap.

Run with `PYTHONPATH=src;vendor`: `scripts/prepare_native_swing.py`, deploy compiled tester-only EA and set files, then `scripts/run_native_matrix.py` with `local_mt5/matrix_swing_2026`, `evidence/native_x100_swing_2026` and `local_mt5/runs_swing_2026`. `scripts/report_native_swing.py` independently rechecks exports. Existing artifacts are preserved; choose new tags for a rerun. Source snapshot and artifact hashes accompany the evidence.

See [frozen technical contract](TECH_PLAN_NATIVE_SWING.md) and [previous native account results](RESULT_NATIVE_X100_MINIMUM_LOT.md).
