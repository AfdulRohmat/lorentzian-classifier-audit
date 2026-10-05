# Native US500 x100 minimum lot variation

The requested minimum-lot fallback was tested directly in MT5. It removes minimum-volume skips but does not improve this eight-month result. All three fallback scenarios lose money. This is not a strict 1% risk strategy when the minimum lot requires more risk.

## Configuration

US500_x100, M30. Feature history begins 15 June 2025, with 6,458 warm-up bars through December 2025. Trading evaluation is January through August 2026. The original causal classifier and ATR runner are unchanged. Entry sizing targets 1% of closed balance; if below broker minimum, it uses 0.01 lot, subject to margin checks. No extra risk cap was added because the user explicitly requested the minimum executable lot. The option is off by default and remains tester-only.

## Minimum lot results

| Deposit | Final balance | Net PnL | Return | PF | Maximum equity DD | Fallback entries |
|---:|---:|---:|---:|---:|---:|---:|
| $500 | $259.47 | -$240.53 | -48.11% | 0.832 | 76.45% | 166 |
| $1,000 | $759.47 | -$240.53 | -24.05% | 0.832 | 46.18% | 111 |
| $3,000 | $2,830.94 | -$169.06 | -5.64% | 0.938 | 29.51% | 0 |

Each scenario has **167 trades**, **4.81 trades per calendar week**, **20.88 per month**, and **34.13% win rate**. There were no stop-out deals. Lack of stop-out is not evidence of acceptable risk.

The $500 and $1,000 accounts both executed every filled trade at 0.01 lot, so they have identical dollar PnL but different percentage returns and drawdowns. The $3,000 account used 0.01–0.05 lots and never needed the fallback; its result is exactly equal to the strict 1% control.

## Risk actually taken

These figures are planned stop-loss exposure divided by balance at entry, including the retained friction reserve. They are not guaranteed maximum realized losses.

| Deposit | Mean planned risk | Maximum planned risk | Mean monthly PnL | Mean monthly return | Compound monthly equivalent |
|---:|---:|---:|---:|---:|---:|
| $500 | 2.96% | 8.74% | -$30.07 | -3.89% | -7.87% |
| $1,000 | 1.32% | 3.18% | -$30.07 | -2.71% | -3.38% |
| $3,000 | 0.81% | 1.00% rounded | -$21.13 | -0.43% | -0.72% |

The unrounded maximum for $3,000 is 0.99737%. Average monthly return is the arithmetic average of eight realized monthly returns; compound monthly equivalent is `(final/deposit)^(1/8)-1`. Neither is a promise of steady monthly income. Monthly compounding explains why the arithmetic average differs from total growth and can be misleading when volatility is large.

## Monthly realized returns

| Deposit | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $500 | +7.43% | +14.64% | -6.14% | +14.25% | -21.59% | -39.15% | -41.64% | +41.12% |
| $1,000 | +3.72% | +7.58% | -3.39% | +7.64% | -12.29% | -19.92% | -16.09% | +11.06% |
| $3,000 | -0.69% | +7.26% | -0.17% | +2.78% | -10.56% | -8.12% | -7.26% | +13.29% |

## Full requested return grid

The 1% row uses the new minimum-lot fallback. Rows 2%–5% retain the original strict risk-sizing and skip policy. This explicitly mixed policy matches the user's follow-up request; the complete original strict matrix remains separately archived.

| Risk target | $500 return | $1,000 return | $3,000 return |
|---:|---:|---:|---:|
| 1% plus minimum lot | -48.11% | -24.05% | -5.64% |
| 2% strict | +8.87% | +9.73% | -15.32% |
| 3% strict | -17.36% | -20.88% | -29.68% |
| 4% strict | -11.98% | -36.41% | -45.97% |
| 5% strict | -34.14% | -50.03% | -60.56% |

The positive $500/2% and $1,000/2% runs have equity drawdowns of **23.98% and 47.31%**, respectively, and PF of **1.128 and 1.053**. They do not establish that 2% risk creates a superior signal. Lot rounding, skips, compounding and which opportunities can be filled produce different trade samples. Do not select the positive pockets after inspection as proof of an edge.

## Costs and interpretation

On $500 and $1,000, price PnL before commission and swap is -$195.74; recorded commission is -$21.71 and swap -$23.08. On $3,000, price PnL is -$74.95, commission -$46.32 and swap -$47.79. Thus costs worsen the result, but are not the sole cause of losses.

Long trades contributed +$34.11 on each smaller account and +$56.35 on $3,000; shorts contributed -$274.64 and -$225.41. This is a diagnostic observation, not a tested permission to remove shorts. No long-only variant was selected or run.

All reports indicate **100% real ticks**, with 28,855,530 ticks in each full test. Native first tick is 1 January 2026 at 23:00:01 and last tick 31 August 2026 at 23:59:58 in the exported terminal time representation. No added execution delay was simulated. Native fills, stops, commission and swap determine PnL; the legacy cost reserves only affect risk/trail calculations.

## Verification and handoff

- All 18 full scenarios (15 strict plus three minimum-lot variations) reconcile their MT5 deal ledgers to final balances.
- Every full run has an identical classifier signal stream. The no-fallback $3,000/1% control is unchanged across builds, including trades, profit and equity drawdown.
- Final builds compile without errors or warnings. No classifier thresholds or exit parameters were tuned to improve results.
- All 55 Python tests pass, including native ledger reconciliation and explicit reporting of minimum-lot risk above the nominal target. Python was used for checks/reporting, not to simulate the reported fills.
- The first smoke attempt is invalidated and retained: a market-closed entry rejection incorrectly halted the run. Corrected runs skip that entry and defer necessary exits while continuing feature updates. No real/demo-account orders were sent.
- The eight months were previously inspected and use a shorter anchor than the old Python study. This does not isolate why older results differ, establish robustness, or justify real-money deployment.

See [the full strict matrix](RESULT_NATIVE_X100_2026.md), [the frozen plan and user amendment](TECH_PLAN_NATIVE_X100_2026.md), and [native minimum-lot evidence](../evidence/native_x100_2026_minimum/validated_summary.json). `scripts/validate_native_minimum.py` rechecks the native exports without simulating prices or fills.

The engineering objective of running the strategy natively has been met. The performance result remains **not supported for promotion** on this sample; production forward automation has not been enabled.
