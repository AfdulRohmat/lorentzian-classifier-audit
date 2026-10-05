# Native US500 x100 backtest results

All fifteen account scenarios completed in MT5 Strategy Tester. These are native fills and account PnL, not a Python replay. The classifier anchor is 15 June 2025; evaluation is January through August 2026. All reports indicate 100% real ticks. All deal ledgers reconcile to native final balances.

**Conclusion: the native run is operationally reproducible, but these results do not establish a robust profitable strategy. Do not promote the highest-return risk setting after inspection.**

## Account matrix

Sizing compounds from closed balance; sub-minimum positions are skipped. DD below is native maximum relative equity drawdown, including floating PnL. Monthly return is the arithmetic mean of eight realized-balance monthly returns, not total return divided by eight.

| Deposit | Risk | Trades | Trades/week | Final balance | Return | PF | Equity DD | Mean month return | Mean month USD |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $500 | 1% | 0 | 0.00 | $500.00 | +0.00% | N/A | 0.00% | +0.00% | $+0.00 |
| $500 | 2% | 60 | 1.73 | $544.35 | +8.87% | 1.128 | 23.98% | +1.53% | $+5.54 |
| $500 | 3% | 116 | 3.34 | $413.19 | -17.36% | 0.907 | 52.10% | -1.24% | $-10.85 |
| $500 | 4% | 146 | 4.21 | $440.10 | -11.98% | 0.967 | 70.96% | +1.11% | $-7.49 |
| $500 | 5% | 151 | 4.35 | $329.28 | -34.14% | 0.929 | 81.85% | -0.11% | $-21.34 |
| $1,000 | 1% | 57 | 1.64 | $1,049.78 | +4.98% | 1.156 | 13.12% | +0.73% | $+6.22 |
| $1,000 | 2% | 157 | 4.52 | $1,097.35 | +9.73% | 1.053 | 47.31% | +2.40% | $+12.17 |
| $1,000 | 3% | 163 | 4.70 | $791.22 | -20.88% | 0.921 | 64.94% | -0.53% | $-26.10 |
| $1,000 | 4% | 167 | 4.81 | $635.88 | -36.41% | 0.910 | 78.66% | -1.47% | $-45.51 |
| $1,000 | 5% | 164 | 4.72 | $499.71 | -50.03% | 0.892 | 84.38% | -2.98% | $-62.54 |
| $3,000 | 1% | 167 | 4.81 | $2,830.94 | -5.64% | 0.938 | 29.51% | -0.43% | $-21.13 |
| $3,000 | 2% | 167 | 4.81 | $2,540.36 | -15.32% | 0.925 | 54.83% | -0.74% | $-57.46 |
| $3,000 | 3% | 167 | 4.81 | $2,109.62 | -29.68% | 0.906 | 70.89% | -1.62% | $-111.30 |
| $3,000 | 4% | 167 | 4.81 | $1,620.82 | -45.97% | 0.889 | 82.10% | -2.63% | $-172.40 |
| $3,000 | 5% | 167 | 4.81 | $1,183.09 | -60.56% | 0.882 | 88.57% | -4.37% | $-227.11 |

## Every monthly realized return

| Deposit | Risk | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $500 | 1% | +0.00% | +0.00% | +0.00% | +0.00% | +0.00% | +0.00% | +0.00% | +0.00% |
| $500 | 2% | -0.75% | +7.99% | +3.66% | -4.95% | -13.04% | -1.83% | -1.81% | +22.98% |
| $500 | 3% | -6.47% | +19.02% | -0.60% | +3.11% | -24.69% | -3.45% | -17.30% | +20.46% |
| $500 | 4% | +4.31% | +27.57% | +7.48% | +14.87% | -36.30% | -22.23% | -16.85% | +30.06% |
| $500 | 5% | +3.63% | +38.92% | -1.04% | +18.35% | -41.54% | -35.41% | -28.51% | +44.69% |
| $1,000 | 1% | -0.38% | +4.61% | +1.88% | -4.10% | -5.11% | -0.87% | -1.81% | +11.62% |
| $1,000 | 2% | +0.95% | +14.99% | +3.71% | +17.13% | -20.00% | -13.37% | -12.45% | +28.24% |
| $1,000 | 3% | -1.01% | +21.95% | -2.09% | +5.64% | -29.42% | -21.59% | -18.94% | +41.26% |
| $1,000 | 4% | +0.63% | +34.93% | -1.31% | +12.75% | -37.77% | -30.30% | -30.69% | +39.98% |
| $1,000 | 5% | -2.54% | +35.40% | -6.93% | +13.04% | -45.65% | -37.63% | -28.88% | +49.32% |
| $3,000 | 1% | -0.69% | +7.26% | -0.17% | +2.78% | -10.56% | -8.12% | -7.26% | +13.29% |
| $3,000 | 2% | -0.00% | +15.99% | -0.25% | +7.46% | -22.13% | -18.16% | -15.84% | +26.99% |
| $3,000 | 3% | +0.20% | +22.90% | -0.58% | +11.71% | -32.36% | -26.02% | -23.96% | +35.12% |
| $3,000 | 4% | -0.02% | +31.34% | -3.19% | +11.37% | -41.44% | -35.96% | -31.34% | +48.19% |
| $3,000 | 5% | -1.87% | +40.14% | -5.50% | +12.38% | -48.97% | -42.67% | -38.47% | +50.00% |

## Trading activity and costs

| Deposit | Risk | Trades/month | WR | Long net | Short net | Commission | Swap | Losses above budget | Min lot skips |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $500 | 1% | 0.00 | N/A | $+0.00 | $+0.00 | $0.00 | $0.00 | 0 | 172 |
| $500 | 2% | 7.50 | 35.0% | $+11.38 | $+32.97 | $-7.80 | $-9.89 | 4 | 111 |
| $500 | 3% | 14.50 | 33.6% | $-12.41 | $-74.40 | $-17.01 | $-14.84 | 4 | 54 |
| $500 | 4% | 18.25 | 34.2% | $+88.67 | $-148.57 | $-31.91 | $-36.26 | 3 | 23 |
| $500 | 5% | 18.88 | 33.1% | $+30.94 | $-201.66 | $-39.88 | $-51.09 | 3 | 17 |
| $1,000 | 1% | 7.12 | 35.1% | $+15.62 | $+34.16 | $-7.41 | $-4.95 | 3 | 114 |
| $1,000 | 2% | 19.62 | 34.4% | $+201.53 | $-104.18 | $-32.71 | $-32.97 | 2 | 11 |
| $1,000 | 3% | 20.38 | 34.4% | $+43.77 | $-252.55 | $-44.96 | $-47.80 | 2 | 4 |
| $1,000 | 4% | 20.88 | 34.1% | $+22.73 | $-386.85 | $-66.79 | $-84.05 | 6 | 0 |
| $1,000 | 5% | 20.50 | 34.1% | $+40.81 | $-541.10 | $-76.42 | $-98.88 | 7 | 3 |
| $3,000 | 1% | 20.88 | 34.1% | $+56.35 | $-225.41 | $-46.32 | $-47.79 | 6 | 0 |
| $3,000 | 2% | 20.88 | 34.1% | $+150.46 | $-610.10 | $-101.26 | $-113.72 | 6 | 0 |
| $3,000 | 3% | 20.88 | 34.1% | $+128.98 | $-1019.36 | $-155.69 | $-181.27 | 7 | 0 |
| $3,000 | 4% | 20.88 | 34.1% | $+80.49 | $-1459.67 | $-202.79 | $-250.51 | 7 | 0 |
| $3,000 | 5% | 20.88 | 34.1% | $+148.74 | $-1965.65 | $-248.08 | $-321.36 | 8 | 0 |

## Execution audit and limits

- Same classifier signal stream in every full-period scenario; all used 6,458 warm-up bars. No entry/exit parameters were optimized.
- Native minimum lot 0.01, contract size 100, step 0.01, maximum 20. The old conditional 0.03 assumption was not used.
- Zero added execution delay; native tick prices, broker-side stops, commission and swap determine returns. Risk/trail calculations retain conservative legacy reserves of 0.02 points for exit slippage and 0.25 for round-trip commission; these reserves are not additional cash charges.
- Native maximum loss can exceed the nominal budget because stop fills and costs are not guaranteed. The risk-percent input is not a guaranteed loss ceiling.
- The initial smoke attempt was INVALID because an ordinary market-closed entry rejection halted the EA. The corrected implementation skips that entry; required exits are deferred while continuing classifier updates. The repeated smoke and all final scenarios passed without EA failure flags.
- All eight months are previously inspected history, not an unseen holdout. Current tester symbol settings may not reproduce every historical change in broker fees, sessions or margin.
- This new anchor, native price feed and tick execution differ from the earlier 2022-anchored Python study. The difference in performance has not been causally decomposed; do not attribute it to one factor without a matched audit.
- No demo/real broker orders, Telegram, optimization or forward trading were activated. The EA refuses non-tester execution.

## Reproduction

See [the frozen plan](TECH_PLAN_NATIVE_X100_2026.md). Native exports, fixed INI/SET inputs, EX5 hash and launch metadata are archived under [evidence/native_x100_2026](../evidence/native_x100_2026/). The raw HTML reports remain in the local MT5 reports directory; their hashes and quality checks are retained without publishing account metadata.

Run `scripts/report_native_matrix.py` to revalidate native exports. It does not simulate orders or recalculate fills. The report keeps verified outcomes separate from assumptions, following the document-writing review guidance.
