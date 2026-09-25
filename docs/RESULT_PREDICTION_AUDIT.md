# Direct-label audit: is gold short prediction actually weak?

## Answer

Yes, the current implementation shows weak SHORT directional classification on
gold, not merely an exit problem. Its raw down forecasts are correct 47.42%;
qualified short starts and executed shorts are correct about 43.7%. A causal
historical-majority baseline achieves 53.34% on the comparable raw-short rows.
At the same time, correct endpoint forecasts can still lose under the runner.
Both weak direction selection and target/payoff mismatch are present.

This evaluates the exact existing target and frozen v3 trades. No model, feature,
label, filter, stop, target, sizing, or live execution rule is changed.
Verdict: `DIRECT_PREDICTION_DIAGNOSTIC_NO_MODEL_CHANGE`.

## Target and scoring boundaries

Target = sign(close[i+4] - close[i]), where i indexes observed M30 bars. Four
bars are normally 120 minutes but can span session gaps or weekends. This is
not automatically a fixed two-clock-hour forecast and not a stop/target outcome.
Labels become known at target-bar end. Unmatured labels are missing, not zero.

Evaluation decisions: January 2024-August 2026, using 2022 onward context.
Gold has 31,509 decision rows, 31,506 scoreable labels and three censored tail
rows. SP500 has 31,315 decisions, 31,312 scoreable labels and three censored rows.
All 1,433 executed baseline trades have a scoreable, nonflat target. Zero raw
votes abstain: 7,514 gold and 7,204 SP500 scoreable rows. A vote is not a calibrated
probability. Zero price changes are real flat targets, separate from missing labels.

Raw gold-short targets exceed 120 minutes in 845/9,888 cases (8.55%); executed
gold shorts do so in only 5/355 (1.41%). SP500 equivalents are 817/9,495 and
27/380. Those targets remain included to audit the algorithm actually used.

## Prediction, filtered start, executed trade are different populations

Precision here means the fraction of forecasts whose target direction matches
the forecast; true flat targets count as not correct. Intervals are descriptive
95% circular three-month-block bootstrap intervals, not iid binomial intervals.

| Asset | Direction | Stage | Correct / forecasts | Precision | 95% interval |
|---|---|---|---:|---:|---|
| Gold | Short | Raw negative vote | 4,689 / 9,888 | **47.42%** | [45.38%, 49.62%] |
| Gold | Short | Qualified start | 163 / 373 | **43.70%** | [37.85%, 49.73%] |
| Gold | Short | Executed trade | 155 / 355 | **43.66%** | [37.37%, 50.13%] |
| Gold | Long | Raw positive vote | 7,618 / 14,104 | 54.01% | [52.27%, 55.63%] |
| Gold | Long | Qualified start | 221 / 417 | 53.00% | [48.61%, 57.77%] |
| Gold | Long | Executed trade | 208 / 390 | 53.33% | [48.61%, 58.58%] |
| SP500 | Short | Raw negative vote | 4,387 / 9,495 | 46.20% | [44.92%, 47.55%] |
| SP500 | Short | Qualified start | 192 / 403 | 47.64% | [44.06%, 51.30%] |
| SP500 | Short | Executed trade | 182 / 380 | 47.89% | [43.73%, 52.29%] |
| SP500 | Long | Raw positive vote | 7,873 / 14,613 | 53.88% | [52.45%, 55.36%] |
| SP500 | Long | Qualified start | 186 / 320 | 58.13% | [54.80%, 61.59%] |
| SP500 | Long | Executed trade | 181 / 308 | 58.77% | [55.26%, 62.34%] |

Gold's selected short starts have lower observed precision than raw negative
votes. This is not a randomized filter ablation: it does not prove removing a
particular filter will fix the problem. Start transitions, kernel conditions and
position availability all change which observations are selected.

SP500's raw short predictions are NOT more accurate than gold's. Its better
strategy PnL cannot be explained as universally better raw ML predictions.
Selected long precision and the previously audited winner-payoff distribution
are materially different. Classification correctness alone is not trading edge.

## Comparison with causal simple forecasts on the SAME raw-short rows

Compare the classifier's down prediction with always-up, prior-four-bar momentum,
and the majority of the latest 2,000 already-matured labels. The last baseline
uses truth.shift(4), with 200 minimum labels, not the future test-set majority.
Exclude flat targets and that baseline's abstentions for each paired comparison.

Primary gold results (different baselines abstain on slightly different rows):

| Baseline | Paired rows | Classifier accuracy | Baseline accuracy | Model-minus-baseline | Adjusted interval, percentage points |
|---|---:|---:|---:|---:|---|
| Always up | 9,888 | 47.42% | 52.58% | -5.16 pp | [-9.94, +0.23] |
| Momentum4 | 9,887 | 47.43% | 50.27% | -2.84 pp | [-5.71, -0.04] |
| Matured historical majority | 9,872 | 47.41% | **53.34%** | **-5.94 pp** | **[-9.81, -2.32]** |

Ten thousand paired circular three-month blocks preserve paired accuracy
differences and cluster overlapping labels. Three comparisons receive Bonferroni
98.333% individual intervals. The majority comparison is negative throughout;
the momentum interval is marginal near zero. These are conditional retrospective
results, not research-history-wide multiplicity correction or new unseen evidence.

Always-down is identical to the classifier inside this short-only forecast
cohort, so it is not independent evidence. Whole-universe gold down prevalence
is 46.74% versus raw-short precision 47.42%; that slight difference uses unmatched
populations and is not proof of predictive skill. Below 50% alone would not be
enough to reject a profitable asymmetric-payoff strategy; the actual short PnL
and paired simple-baseline results matter too.

Secondary SP500 raw-short comparisons are also unfavorable to the classifier:
approximately 46.24%-46.28% on paired nonflat rows versus 50.00% momentum and
53.44% historical majority. Complete paired intervals are saved in summary.json.

## Connect the learned label to gold short PnL

| Endpoint direction | Actual runner result | Trades | Total net R | Mean R |
|---|---|---:|---:|---:|
| Correct | Profitable | 110 | +147.49 | +1.341 |
| Correct | Nonprofitable | 45 | -44.62 | -0.992 |
| Wrong | Profitable | 12 | +9.21 | +0.768 |
| Wrong | Nonprofitable | 188 | -187.18 | -0.996 |
| **All** | | **355** | **-75.10** | **-0.212** |

155 correct-direction shorts contribute +102.87R; 200 wrong-direction shorts
contribute -177.97R. Direction errors are a real part of the loss. This split
uses future labels and is NOT an executable selection rule.

Of the 45 correct-but-losing shorts, 44 hit initial stops; 21 had already hit
initial SL BEFORE the four-bar target became known. The other correct-direction
losses demonstrate that later path behavior can also differ from the endpoint.
Conversely, 12 wrong-endpoint predictions still win because the runner can exit
profitably before the later direction reverses.

Hypothetical liquidation at the target close is nonpositive in only 3/155 of
the correct-direction shorts. This mark includes actual entry price and modeled
friction, but ignores the earlier real exit and is not a realizable strategy
backtest. Most right labels therefore correspond to a favorable endpoint mark,
yet the path can still stop the real trade. Neither a pure fees explanation nor
a pure exit explanation is sufficient.

For comparison, SP500 short correct-label trades contribute +170.91R across 182
trades, versus -173.47R across 198 wrong-label trades: approximately breakeven
overall. Gold has fewer correct selected short forecasts proportionally and
smaller realized winners, consistent with the preceding path audit.

## Regime/year and vote strength

| Gold short stage | 2024 precision | 2025 precision | 2026 Jan-Aug precision |
|---|---:|---:|---:|
| Raw | 45.70% | 46.04% | 51.24% |
| Qualified start | 44.03% | 39.29% | 49.49% |
| Executed | 42.97% | 39.69% | 50.00% |

Executed shorts during daily bull: 136/325 correct (41.85%). Bear: 12/21
(57.14%); mixed: 7/9 (77.78%). Bear/mixed are small 2026-only cells, so their
attractive percentages must not become a newly optimized exception rule.

Larger negative votes do not show monotonically better accuracy in gold:

| Raw vote | Forecasts | Correct direction |
|---:|---:|---:|
| -2 | 5,615 | 47.18% |
| -4 | 3,018 | 47.45% |
| -6 | 1,048 | 48.47% |
| -8 | 197 | 46.70% |

Ten additional rare odd-vote rows are retained in the full evidence; their tiny
sample rates are not threshold candidates. Even -8 means eight historical
neighbor labels vote down, not an 80%/100% calibrated chance of a correct forecast.

## Interpretation and boundary

We can now say more than "short trades lose": the current short forecasting
implementation underperforms simple causal forecasts on its own learned target
in this gold sample. Filtering/state selection does not visibly rescue its
selected shorts, and a close-direction label is not the same as profitable
path-dependent execution. Weak directional performance and target/payoff mismatch
coexist. The particular defect in features, neighborhood similarity or regime
adaptation has NOT been identified by this audit.

Do not automatically invert signals, raise a vote threshold or widen a stop
using these inspected results. Those would be different hypotheses. If model
research continues, any regime-aware features or cost/path-aware target must
beat simple baselines under a frozen chronological evaluation with correct
label maturity and a genuine unseen/forward stage. No such retraining is part
of this audit. The SP500 candidate remains unchanged; its PnL is not proof of
superior raw classifier accuracy.

## Verification and reproduction

34 tests and repository lint pass. Source hashes and parent contract match;
labels used by KNN are mature. All original 1,433 trade fields and PnL are
preserved, and every executed entry matches the regenerated start flag and
raw vote sign. The portable validator checks target-price signs, censoring,
elapsed horizons, rolling prior on full internal windows, confusion/cohort
counts, block intervals and original PnL quadrants. No new strategy replay or
broker order is claimed.

```bash
python -m lorentzian_audit.audit_predictions
python -m lorentzian_audit.validate_predictions
python -m pytest -q
python -m ruff check src tests scripts
```

Full audit regeneration requires the original raw archives; saved-artifact
validation does not. Evidence is in `evidence/prediction_audit/`: all decision
observations and votes, joined trade labels, confusion, cohorts, year/regime
splits, vote strengths, quadrants, hashes and validation.
