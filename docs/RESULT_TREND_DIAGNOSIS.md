# Gold loss diagnosis: directional trend and matched long entries

## Outcome

The negative gold baseline is strongly associated, in this inspected sample,
with shorts entered during a causal daily bull regime. Removing shorts makes
the frozen runner historically profitable; the trend-aligned policy is also
positive but does not beat the simpler long-only policy. Long-entry timing's
incremental advantage remains unconfirmed: 14/20 matched random-long schedules
are positive and several beat Lorentzian.

Verdict: `RETROSPECTIVE_TREND_DIAGNOSIS_NO_PROMOTION`.
This is a more specific diagnosis, not proof that gold cannot be traded or that
Lorentzian long-only is now a validated edge. No economic cause is identified.

All related work is on `research/xauusd-loss-diagnostics`: earlier same-runner
controls, the path audit, this plan/contract, code, tests and results. Main remains
at its original baseline; no merge, broker order or live deployment is included.

## Frozen method

- Primary XAUUSD M30, secondary regular US500 M30; January 2024-August 2026
  evaluation, January 2022 onward warmup; unchanged raw source hashes.
- Completed UTC daily close versus EMA200 (`adjust=False`, 200 observed-day
  minimum), plus EMA direction over 20 observed days. Bull requires close above
  EMA and rising EMA, bear the inverse, otherwise mixed. Empty days excluded.
  Only daily bars completed by the M30 signal close are available.
- Four policies: baseline, long-only, short-only and trend-aligned (bull long,
  bear short, skip mixed). Original entries remain start events, next-bar fills.
- ALL original opposite start signals remain exits, even when their reverse
  entry is rejected. Regime flips alone never open or close a position. Thus
  the experiment changes entry eligibility, not the meaning of an opposite exit.
- Unchanged SL 1 ATR14, no TP, +1 net R activation, completed-M30 one-R trailing,
  24h cap, M1 stop/gap execution, base and existing v2 stress costs. No tuning.

The regime is a slow proxy, not ground truth or a fundamental macro model.
This is already-inspected history: neither annual splits nor bootstrap make it
pristine out-of-sample. Twenty bearish trades in one historical episode are not
twenty independent market regimes.

## Regime coverage and the reason for gold's loss

Of available M30 decision bars in the evaluation period, gold is classified as
bull 91.44%, bear 6.22%, mixed 2.35%. All 2024 and 2025 decision bars are bull;
bear/mixed occur only in 2026. There are no unavailable-regime evaluation bars.

Original baseline gold contributions:

| Direction | Regime known at decision | Trades | Total net R | Mean R |
|---|---|---:|---:|---:|
| Long | Bull | 355 | +32.74 | +0.092 |
| Long | Bear | 23 | +10.49 | +0.456 |
| Long | Mixed | 12 | -0.62 | -0.052 |
| Short | Bull | 325 | **-82.82** | **-0.255** |
| Short | Bear | 21 | +4.81 | +0.229 |
| Short | Mixed | 9 | +2.91 | +0.324 |

Short-bull losses exceed the entire baseline loss (-32.48R), because other
components offset some of them. This supports the directional-conflict diagnosis
on this sample. It does NOT prove bullish regime caused every losing short.
Every gold bear/mixed direction cell has fewer than 30 trades and comes from
2026 only: evidence for bear-short profitability is weak. Bull gold-long returns
could also reflect favorable underlying drift rather than special entry skill.

Interestingly, the small bear-long cell is positive too. A slow bearish label
does not mean every intraday long must lose. Do not tune the regime definition
to preserve this now-visible positive slice.

## Full replay, after costs

DD is cumulative closed-trade R drawdown, not floating-equity drawdown.

| Asset | Cost | Policy | Trades | /week | Net R | PF | Mean R | DD R |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Gold | Base | Baseline | 745 | 5.35 | -32.48 | 0.927 | -0.044 | 46.79 |
| Gold | Base | Long-only | 390 | 2.80 | **+42.62** | **1.197** | +0.109 | **13.89** |
| Gold | Base | Short-only | 355 | 2.55 | -75.10 | 0.676 | -0.212 | 82.47 |
| Gold | Base | Trend-aligned | 377 | 2.71 | +39.16 | 1.187 | +0.104 | 13.89 |
| Gold | Stress | Baseline | 743 | 5.34 | -61.61 | 0.865 | -0.083 | 74.29 |
| Gold | Stress | Long-only | 388 | 2.79 | **+30.42** | **1.139** | +0.078 | 15.35 |
| Gold | Stress | Short-only | 355 | 2.55 | -92.03 | 0.610 | -0.259 | 98.59 |
| Gold | Stress | Trend-aligned | 375 | 2.70 | +27.23 | 1.128 | +0.073 | 15.35 |
| SP500 | Base | Baseline | 688 | 4.94 | +72.77 | 1.172 | +0.106 | 27.22 |
| SP500 | Base | Long-only | 308 | 2.21 | +75.33 | 1.435 | +0.245 | 16.61 |
| SP500 | Base | Short-only | 380 | 2.73 | -2.56 | 0.990 | -0.007 | 37.90 |
| SP500 | Base | Trend-aligned | 296 | 2.13 | +67.07 | 1.401 | +0.227 | 16.13 |
| SP500 | Stress | Baseline | 689 | 4.95 | +31.81 | 1.073 | +0.046 | 32.89 |
| SP500 | Stress | Long-only | 308 | 2.21 | +66.02 | 1.377 | +0.214 | 17.48 |
| SP500 | Stress | Short-only | 381 | 2.74 | -34.21 | 0.868 | -0.090 | 53.84 |
| SP500 | Stress | Trend-aligned | 296 | 2.13 | +60.10 | 1.357 | +0.203 | 17.21 |

Gold long-only and short-only happen to reproduce the corresponding baseline
subsets under the frozen opposite-exit convention. This was verified by full
replay, not assumed by filtering the old ledger. Trend-aligned has 355 bull longs
and 22 bear shorts (+6.42R); one bear-short entry becomes available after a
previous position is skipped. Hence its result is not identical to slicing
the baseline's 21 bear shorts.

Annual base net R, attributed by ENTRY year; 2026 ends in August:

| Asset | Policy | 2024 | 2025 | 2026 |
|---|---|---:|---:|---:|
| Gold | Baseline | -15.81 | -7.29 | -9.39 |
| Gold | Long-only | +12.80 | +24.68 | +5.14 |
| Gold | Short-only | -28.61 | -31.96 | -14.53 |
| Gold | Trend-aligned | +12.80 | +24.68 | +1.68 |
| SP500 | Baseline | +23.45 | +31.64 | +17.68 |
| SP500 | Long-only | +43.43 | +25.90 | +6.00 |
| SP500 | Short-only | -19.98 | +5.74 | +11.68 |
| SP500 | Trend-aligned | +43.43 | +23.33 | +0.31 |

The trend filter adds no historical improvement over long-only here. It is not
therefore a proven better design. SP500 changes are context only; its main/demo
baseline is not replaced by a post-inspection long-only selection.

## Matched gold-long control: not all profit belongs to Lorentzian

Twenty seeded random schedules each match all 390 long-only anchor trades to
alternate M30 signal bars, without replacement within a schedule. Matches share
UTC month, New York hour, causal daily regime, and ATR14/price within 25% of the
anchor. All original long/short start bars are excluded from candidate entries.
No fallback matching or outcome-based selection. All 7,800 draws are saved and
independently regenerated from the seed by the validator.

Same runner and original classifier short exits remain. One-position overlap
suppresses some scheduled entries: actual control trades range 359-374, versus
390 Lorentzian longs. There are no unmatched anchors; this activity difference
comes from replay, not failed matching.

| Metric | Lorentzian long-only | Median control | Control min-max |
|---|---:|---:|---:|
| Executed candidate trades | 390 | 362 | 359-374 |
| Total net R | +42.62 | +21.85 | -36.32 to +85.49 |
| Mean R/trade | +0.109 | +0.060 | -0.097 to +0.231 |
| PF | 1.197 | 1.102 | 0.848-1.435 |
| Total holding hours | 1,585.88 | 1,489.17 | 1,223.00-1,772.82 |

- 14/20 controls are positive.
- 5/20 beat Lorentzian total R; 7/20 beat R/trade.
- Lorentzian is above the median, but not exceptional enough in this small
  diagnostic to establish incremental entry edge. These counts are NOT p-values.

Matching is conditional on the observed anchor sample, including its future
month/hour distribution. Controls retain classifier short exits and do not
replicate all classifier entry filters. Therefore they diagnose the combined
LONG ENTRY policy under a shared exit rule, not Lorentzian distance alone and
not a separately deployable random-long or macro-bias strategy. They suggest
background long exposure plus the runner may explain part of the result; they
do not identify the exact fraction attributable to a bull market.

## Paired monthly uncertainty versus the two-sided baseline

32 exit-attributed calendar months, zeros retained, paired circular three-month
block bootstrap, 10,000 replicates. Bonferroni adjusts three comparisons within
the primary gold family (98.333% individual intervals). SP500 is a separate
exploratory family, not a pooled six-test claim.

| Asset | Policy minus baseline | Mean R/month difference | Adjusted interval |
|---|---|---:|---|
| Gold | Long-only | +2.347 | [+0.157, +4.455] |
| Gold | Short-only | -1.332 | [-3.017, +0.245] |
| Gold | Trend-aligned | +2.239 | [+0.129, +4.270] |
| SP500 | Long-only | +0.080 | [-2.157, +1.900] |
| SP500 | Short-only | -2.354 | [-5.068, +0.425] |
| SP500 | Trend-aligned | -0.178 | [-2.442, +1.770] |

The gold intervals support improvement over the bad two-sided baseline
conditional on this sample and bootstrap specification. They do not test
profitability against zero or superiority over matched controls, and do not
correct the long history of prior research/selection. Do not translate them
into a live-edge or untouched-holdout claim.

## USD 3,000 account context, 1% compounded risk

Original lot-step flooring and minimum-lot skips; closed-balance compounding.
No margin/swap/stop-out model. Monthly values are arithmetic means over all 32
months; DD is closed balance, not floating equity. Skips filter the frozen trade
ledger rather than creating new opportunities. Regular US500, not US500_x100.

| Asset | Policy | Base final USD | Base return | Mean month | Balance DD |
|---|---|---:|---:|---:|---:|
| Gold | Baseline | 2,190.02 | -27.00% | -0.78% | 35.37% |
| Gold | Long-only | **4,356.89** | **+45.23%** | **+1.26%** | **10.53%** |
| Gold | Short-only | 1,419.41 | -52.69% | -2.22% | 53.93% |
| Gold | Trend-aligned | 4,129.43 | +37.65% | +1.09% | 10.53% |
| SP500 | Baseline | 5,525.57 | +84.19% | +2.23% | 24.49% |
| SP500 | Long-only | 5,976.64 | +99.22% | +2.41% | 15.47% |
| SP500 | Short-only | 2,771.68 | -7.61% | -0.16% | 33.42% |
| SP500 | Trend-aligned | 5,528.84 | +84.29% | +2.11% | 15.06% |

Gold long-only executes 389/390 trades and skips one. Stress final balance is
USD3,780.61 (mean month +0.80%, DD10.89%); aligned stress is USD3,692.72.
Neither long-only gold nor aligned gold exceeds its nominal budget in these
replays, but that is not a guarantee against gaps. Other policies do show such
breaches, including the original gold baseline. Full stress accounts are saved.

## Engineering review and next boundary

Both baseline full ledgers reproduce v3 within 1e-10 tolerance. Source hashes
match. All 31 tests and lint pass, including causal daily availability, prefix
invariance, unavailable/bull/bear/mixed distinctions, preserved opposite exits
under rejected reverse entries, and match criteria. Independent saved-artifact
checks reconcile 16 cells, calendars, risk budgets, all 20 random draw schedules,
nonoverlap and bootstrap results. Prior path and entry-comparison validators
also remain green. LF attributes preserve contract/plan hashes across platforms.

Keep gold long-only as a clearly marked research hypothesis, not a live strategy.
Do not optimize EMA length, stops or short exclusions to rescue inspected cells.
If continuing, freeze the simple long-only candidate and control protocol and
test genuinely uninspected data or demo forward observations. A bear-cycle
extension is particularly useful for assessing directional dependence. Neither
retraining the classifier nor automatically deleting all future shorts is
authorized or established by this diagnostic.

## Reproduce

```bash
git switch research/xauusd-loss-diagnostics
python -m lorentzian_audit.trend_diagnosis
python -m lorentzian_audit.validate_trend_diagnosis
python -m pytest -q
python -m ruff check src tests scripts
```

Full replay needs the original raw archives; validation needs only saved
repository evidence. `evidence/trend_diagnosis/` includes daily regimes, per-signal
availability, all policy and control ledgers, match pools/draws, regime cells and
coverage, accounts, annual/monthly results, source manifest and validation.
