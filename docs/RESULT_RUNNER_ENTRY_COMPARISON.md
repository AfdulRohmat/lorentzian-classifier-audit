# Same ATR runner: does Lorentzian add value?

## Conclusion

SP500 M30 remains historically positive, but the result is not unique to
Lorentzian distance. Euclidean KNN produces almost the same base-cost outcome.
The two non-classifier controls are slightly negative. All four XAUUSD policies
are negative. The frozen incremental-value verdict is:

`LORENTZIAN_INCREMENTAL_VALUE_UNCONFIRMED`

This does **not** erase the positive SP500 ledger or prove that all strategies
are equivalent. It means these data do not establish Lorentzian's superiority.
There is no automatic strategy replacement or new live approval.

## What was held constant

Evaluation January 2024-August 2026 (32 months); raw context from January 2022;
Exness M1 replay aggregated into M30; unchanged v3 filters, one-position limit,
next-bar entries, initial SL 1 ATR(14), no fixed TP, completed-close trailing
activated at +1 net R and trailing by 1 net R, opposite-signal exit and 24h cap.
Both long and short remain enabled. No parameter search.

The signal policies are:

- Lorentzian: causal eight-neighbor classifier using the existing features.
- Euclidean: identical classifier and labels, different distance metric.
- Momentum4: direction of the known previous four-bar return, common filters.
- Kernel-only: smoothed-price kernel-slope direction, common filters, no KNN.

**Same exit algorithm is not identical exit timestamps:** different signals can
close/reverse positions at different times. This is a comparison of signal
policies under a common runner, not a fully isolated entry-only causal effect.
Native trade frequencies and market exposure are allowed to differ.

## Base-cost results

R is each trade's planned initial-stop risk including modeled exit friction;
net R includes the full modeled round-trip costs. DD is closed-trade cumulative
R drawdown, not floating-equity drawdown.

| Asset | Signal | Trades | /week | Net R | R/trade | PF | WR | DD R |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| SP500 | Lorentzian | 688 | 4.94 | +72.77 | +0.106 | 1.172 | 38.5% | 27.22 |
| SP500 | Euclidean | 703 | 5.05 | +72.55 | +0.103 | 1.165 | 37.4% | 32.04 |
| SP500 | Momentum4 | 968 | 6.96 | -2.74 | -0.003 | 0.996 | 37.0% | 57.64 |
| SP500 | Kernel-only | 974 | 7.00 | -7.13 | -0.007 | 0.988 | 37.0% | 57.19 |
| XAUUSD | Lorentzian | 745 | 5.35 | -32.48 | -0.044 | 0.927 | 39.6% | 46.79 |
| XAUUSD | Euclidean | 758 | 5.45 | -18.07 | -0.024 | 0.960 | 40.6% | 43.10 |
| XAUUSD | Momentum4 | 1,029 | 7.40 | -23.56 | -0.023 | 0.963 | 37.3% | 50.05 |
| XAUUSD | Kernel-only | 1,024 | 7.36 | -26.82 | -0.026 | 0.958 | 37.3% | 54.60 |

Lorentzian beats Euclidean by only **0.22R across 32 months** at base costs.
Its advantage over momentum/kernel is larger in the observed totals, but the
uncertainty intervals below still include zero.

## Calendar and exposure

Year attribution uses exit time; 2026 is January-August only. Prior v3 annual
tables used entry time, so attribution at calendar boundaries may differ.

| Asset | Signal | 2024 R | 2025 R | 2026 R | Total holding hours | Winners >3R |
|---|---|---:|---:|---:|---:|---:|
| SP500 | Lorentzian | +23.45 | +31.64 | +17.68 | 2,714 | 53 |
| SP500 | Euclidean | +24.36 | +28.30 | +19.88 | 2,804 | 58 |
| SP500 | Momentum4 | -1.66 | +14.68 | -15.77 | 3,546 | 56 |
| SP500 | Kernel-only | -7.80 | +24.29 | -23.62 | 3,605 | 56 |
| XAUUSD | Lorentzian | -15.56 | -6.53 | -10.39 | 2,904 | 33 |
| XAUUSD | Euclidean | -14.07 | +7.73 | -11.73 | 3,044 | 34 |
| XAUUSD | Momentum4 | -22.47 | -6.84 | +5.74 | 3,981 | 57 |
| XAUUSD | Kernel-only | -36.17 | -1.21 | +10.55 | 3,923 | 56 |

On SP500 the classifiers make fewer trades and retain a similar number of
large winners. This is consistent with useful selection in this sample, but
does not identify the distance metric as the cause or prove predictive edge.
The filters, signal-state transitions, opposite exits, costs and market history
are all part of the observed system.

Direction contributions also matter:

| Asset | Signal | Long R | Short R |
|---|---|---:|---:|
| SP500 | Lorentzian | +75.33 | -2.56 |
| SP500 | Euclidean | +74.38 | -1.83 |
| SP500 | Momentum4 | +10.55 | -13.30 |
| SP500 | Kernel-only | +7.46 | -14.59 |
| XAUUSD | Lorentzian | +42.62 | -75.10 |
| XAUUSD | Euclidean | +17.27 | -35.34 |
| XAUUSD | Momentum4 | +74.90 | -98.47 |
| XAUUSD | Kernel-only | +79.94 | -106.77 |

These are contributions from the existing two-sided ledgers, **not** backtests
of standalone long-only strategies. Removing shorts would change position
availability and possibly exits. Do not promote those slices post hoc.

## Paired monthly uncertainty

We compare Lorentzian minus each control in realized R over the same 32 calendar
months, including zero-trade months. Ten thousand paired circular three-month
block bootstraps preserve common calendar shocks and short-run dependence.
The primary SP500 family has three comparisons: Bonferroni intervals have
98.333% nominal individual coverage. Bootstrap assumptions and the small number
of months limit interpretation; historical research-wide selection is not corrected.

| Asset | Control | Difference R/month | Nominal 95% interval | Family-adjusted interval |
|---|---|---:|---|---|
| SP500 | Euclidean | +0.007 | [-0.947, +0.969] | [-1.158, +1.181] |
| SP500 | Momentum4 | +2.360 | [-0.479, +5.272] | [-1.124, +6.090] |
| SP500 | Kernel-only | +2.497 | [-0.438, +5.488] | [-0.958, +6.191] |
| XAUUSD | Euclidean | -0.450 | [-2.948, +2.044] | [-3.481, +2.620] |
| XAUUSD | Momentum4 | -0.279 | [-2.805, +2.348] | [-3.301, +2.906] |
| XAUUSD | Kernel-only | -0.177 | [-2.706, +2.577] | [-3.233, +3.164] |

Secondary XAUUSD intervals are exploratory; the adjusted column uses the same
three-control calculation but is not a six-comparison global claim. Even the
unadjusted SP500 intervals cross zero. Absence of a significant difference is
not proof of equivalence.

## Cost stress

The existing v2 stress profile widens effective spreads and adverse slippage;
XAU commission also increases. R denominators and stop paths are recalculated,
so this is not merely subtracting a fixed amount from an unchanged ledger.

| Asset | Signal | Stress net R | Stress PF |
|---|---|---:|---:|
| SP500 | Lorentzian | +31.81 | 1.073 |
| SP500 | Euclidean | +5.35 | 1.012 |
| SP500 | Momentum4 | -50.61 | 0.919 |
| SP500 | Kernel-only | -55.22 | 0.913 |
| XAUUSD | Lorentzian | -61.61 | 0.865 |
| XAUUSD | Euclidean | -50.51 | 0.891 |
| XAUUSD | Momentum4 | -48.52 | 0.925 |
| XAUUSD | Kernel-only | -52.08 | 0.919 |

Lorentzian is descriptively better than Euclidean in this stress scenario, but
stress was designated contextual, not a replacement primary significance test.

## USD 3,000, 1% compounded risk, base costs

Reuse v3 sizing with lot-step flooring and skip below the broker minimum. US500
here is the **regular contract, not US500_x100**. Means are arithmetic over all
32 months and are not guaranteed monthly income. Drawdown is closed balance;
margin, swap, floating drawdown and stop-outs are not modeled. Account skips
filter the frozen trade ledger and do not create new entry opportunities.

| Asset | Signal | Final USD | Total return | Mean month | Balance DD |
|---|---|---:|---:|---:|---:|
| SP500 | Lorentzian | 5,525.57 | +84.19% | +2.23% | 24.49% |
| SP500 | Euclidean | 5,488.06 | +82.94% | +2.29% | 28.56% |
| SP500 | Momentum4 | 2,541.32 | -15.29% | -0.22% | 46.45% |
| SP500 | Kernel-only | 2,431.34 | -18.96% | -0.34% | 46.12% |
| XAUUSD | Lorentzian | 2,190.02 | -27.00% | -0.78% | 35.37% |
| XAUUSD | Euclidean | 2,479.39 | -17.35% | -0.42% | 32.40% |
| XAUUSD | Momentum4 | 2,236.20 | -25.46% | -0.70% | 36.42% |
| XAUUSD | Kernel-only | 2,023.57 | -32.55% | -1.01% | 45.29% |

Arithmetic monthly averages can rank differently from terminal compounded
wealth. Positive aggregate R also does not guarantee compounded profit: stress
Euclidean SP500 finishes at USD 2,837.09 despite +5.35R.

## Verification and decision

All 16 asset/variant/cost cells completed. Source hashes match the prior v3
manifest. Both base Lorentzian ledgers reproduce v3 within 1e-10 numerical
tolerance, including timestamps and all saved fields. Label maturity is causal;
a prefix-invariance test confirms that future bars do not change past features
or any of the four signal policies. All 22 tests and repository lint pass.

An independent saved-artifact validator reconciles PnL, risk, lot sizes,
calendar totals, reported metrics and all six bootstrap comparisons. This is
an independent calculation path, not an independent market data source or
second execution engine.

Keep the frozen SP500 candidate as a demo research candidate, not a proven
Lorentzian-specific edge. Do not switch to Euclidean or remove shorts based on
these same inspected data. XAUUSD remains unsupported by all four policies.
This experiment does not determine the economic cause of the cross-asset gap.

## Reproduction

```bash
python -m lorentzian_audit.run_entry_comparison
python -m lorentzian_audit.validate_entry_comparison
python -m pytest -q
python -m ruff check src tests scripts
```

Full replay needs the original raw archives at the frozen paths. The validator
only needs repository artifacts. Evidence is in `evidence/runner_entry_comparison/`:
complete trades/accounts, metrics, all months/years, manifests, signal diagnostics,
summary, replay validation and independent validation. No MT5 orders were placed.
