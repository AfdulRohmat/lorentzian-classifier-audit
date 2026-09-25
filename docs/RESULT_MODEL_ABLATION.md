# Same-feature model ablation: what changed, what did not

Verdict: **`MODEL_REPLACEMENT_NOT_SUPPORTED`**. No promotion, no merge into main,
and no broker orders. All experiments stay on `research/xauusd-loss-diagnostics`.

Logistic regression is a better probability forecast than the uncalibrated
eight-neighbor class fractions, but it does not beat a historical class prior.
Gold's runner moves from negative to approximately flat at base costs, fails
stress costs, and loses money in the executable account simulation. This is
not a successful repair of gold shorts.

## Frozen experiment

Plan/contract were committed in `6973129`, before the new outcomes. Implementation
and initial checks were committed in `6f76211`. See
[technical plan](TECHNICAL_PLAN_MODEL_ABLATION.md) and
[contract](../config/contract_model_ablation.json).

- Same five features, same four-observed-M30-bar target, same eligible rolling
  training pool (up to 2,000 bars back, mature labels only, j modulo 4 nonzero).
- Every-bar logistic refit: L2 C=1, no class weights, no hyperparameter search.
- Three policies: original Lorentzian; logistic regression; empirical class
  prior from that exact training pool. The prior differs from the previous
  audit's wider rolling-prior pool, so its numbers need not match that audit.
- Same filters, kernel confirmation, state-change entry, next-bar fill and
  ATR runner: 1 ATR initial stop, 1R trailing activation/distance, no fixed TP.
- Same source archives and base/stress costs. No label, feature or exit tuning.
- Evaluation January 2024-August 2026, 32 months; 2022-2023 is causal context.
  Gold has 31,506 scoreable decisions and SP500 31,312. Three final targets per
  asset are censored. This history was already inspected, not a fresh holdout.

## 1. Prediction quality

Brier loss is the sum of squared class-probability errors over down/flat/up;
lower is better. It includes ties and genuine flat outcomes on the same rows.
These values are not accuracy percentages. Neighbor fractions and logistic
probabilities are not assumed calibrated.

| Asset | Model | Brier loss | Directional coverage | Covered accuracy | Short forecasts | Short precision |
|---|---|---:|---:|---:|---:|---:|
| XAUUSD | Lorentzian | 0.571729 | 76.15% | 51.30% | 9,888 | 47.42% |
| XAUUSD | Logistic | 0.499353 | 100.00% | 53.07% | 7,085 | 49.61% |
| XAUUSD | Prior | 0.498037 | 99.75% | 53.51% | 4,246 | 50.94% |
| SP500 | Lorentzian | 0.578511 | 76.99% | 50.85% | 9,495 | 46.20% |
| SP500 | Logistic | 0.501290 | 100.00% | 52.82% | 3,599 | 44.98% |
| SP500 | Prior | 0.498986 | 99.93% | 53.65% | 1,488 | 46.64% |

Covered accuracies and each model's short precision have different coverage
and selected timestamps; they are descriptive, not the primary paired test.
This table retains genuine flat outcomes; the earlier audit's nonflat-only
covered accuracy is therefore slightly different, without changing predictions.
Gold's abstention-as-missed-class balanced accuracy is 38.62% Lorentzian,
51.29% logistic, 51.02% prior. Logistic's short recall is 23.87%, versus 14.69%
prior and 31.84% Lorentzian. The large abstention rate penalizes Lorentzian in
this recall metric; it is not a claim that its covered forecasts are 38% correct.

Gold primary comparisons use 10,000 paired circular three-month bootstrap
samples and 98.75% intervals adjusted for the four predeclared comparisons.
Positive values favor logistic:

| Comparison | Estimate | Adjusted interval |
|---|---:|---:|
| Prior Brier minus logistic Brier | -0.001316 | [-0.002278, -0.000287] |
| Lorentzian Brier minus logistic Brier | +0.072377 | [+0.067281, +0.077543] |
| Logistic minus prior net R/month | +0.0961R | [-1.4310, +1.7755]R |
| Logistic minus Lorentzian net R/month | +1.1586R | [-2.3806, +4.7465]R |

Thus logistic reduces the large probability error of eight-neighbor voting,
but is slightly worse than the feature-free prior on the primary prediction
metric. The PnL differences remain uncertain. Neither claim establishes an
unseen advantage, and the correction does not cover the entire research history.

## 2. Did it repair short gold specifically?

| Native short stage | Lorentzian correct / count | Logistic correct / count |
|---|---:|---:|
| Raw negative forecast | 4,689 / 9,888 (47.42%) | 3,515 / 7,085 (49.61%) |
| Qualified short start | 163 / 373 (43.70%) | 36 / 85 (42.35%) |
| Executed short | 155 / 355 (43.66%) | 33 / 82 (40.24%) |

On the **same 355 original short decision timestamps**, logistic correctly
classifies 202 (56.90%) versus the prior's 198 (55.77%) and original classifier's
155 (43.66%). But logistic predicts **long on 289 of those rows**, and short
on only 66 (34 correct). This is not 56.90% short precision or a new trade win
rate; much of the change is disagreement with the old bearish prediction.
The small selected-cohort difference versus prior is descriptive, not a new gate.

The actual new strategy enters at different timestamps. Its 82 shorts contribute
**-10.89R**, while 125 longs contribute **+15.49R**. The 33 correct-label shorts
contribute +30.64R, but 49 wrong-label shorts contribute -41.53R. Eight correct
shorts still lose. Short direction and endpoint-label/runner-path mismatch remain
separate problems. The stage deterioration is an association, not proof that
removing a particular filter would improve results.

## 3. Identical runner rules, different signal streams

Opposite-start exits are generated by each model's own signal stream. Holding
times, exposure and trade counts therefore differ even though the exit rule
is frozen. Prior PnL is a sparse policy comparator, not an exposure-matched
gold-long strategy or an independently validated trading system.

| Asset | Model | Trades | Trades/week | Base net R | Base PF | Stress net R | Stress PF |
|---|---|---:|---:|---:|---:|---:|---:|
| XAUUSD | Lorentzian | 745 | 5.35 | -32.48 | 0.927 | -61.61 | 0.865 |
| XAUUSD | Logistic | 207 | 1.49 | +4.59 | 1.038 | -5.85 | 0.953 |
| XAUUSD | Prior | 19 | 0.14 | +1.52 | 1.152 | +0.89 | 1.089 |
| SP500 | Lorentzian | 688 | 4.94 | +72.77 | 1.172 | +31.81 | 1.073 |
| SP500 | Logistic | 299 | 2.15 | -6.52 | 0.966 | -14.06 | 0.927 |
| SP500 | Prior | 6 | 0.04 | +5.16 | 3.579 | +5.00 | 3.499 |

Counts/frequency above are base cost; original Lorentzian has 743 gold and 689
SP500 trades at stress costs. The prior's 19/6 trades are too few to promote
its PF. Gold logistic averages 6.47 trades/month, +0.0222R/trade and 40.58% trade
win rate at base costs; its drawdown is 17.26R (24.92R stress). It is close to
flat, not a strong new strategy.

Annual base R (2026 January-August only):

| Asset | Model | 2024 | 2025 | 2026 partial |
|---|---|---:|---:|---:|
| XAUUSD | Lorentzian | -15.56 | -6.53 | -10.39 |
| XAUUSD | Logistic | -10.33 | +4.23 | +10.70 |
| XAUUSD | Prior | -2.36 | +1.30 | +2.58 |
| SP500 | Lorentzian | +23.45 | +31.64 | +17.68 |
| SP500 | Logistic | +7.96 | -16.82 | +2.34 |
| SP500 | Prior | 0.00 (no trades) | +1.27 | +3.88 |

On SP500, a better probability score versus Lorentzian accompanies worse runner
PnL. This is direct evidence that improved probability scoring and improved
trading performance are different objectives. It does not prove the source
of the original SP500 profit or validate its classifier.

## 4. Executable account illustration: $3,000, nominal 1% per trade

Closed-balance compounding, broker lot floor/step and minimum-lot skip rules:

| Asset | Model | Base final balance | Base mean monthly return | Base balance DD | Stress final balance |
|---|---|---:|---:|---:|---:|
| XAUUSD | Lorentzian | $2,190.02 | -0.784% | 35.37% | $1,736.98 |
| XAUUSD | Logistic | $2,945.42 | +0.011% | 16.00% | $2,737.56 |
| XAUUSD | Prior | $3,022.53 | +0.025% | 5.16% | $3,005.54 |
| SP500 | Lorentzian | $5,525.57 | +2.228% | 24.49% | $3,692.50 |
| SP500 | Logistic | $2,695.60 | -0.249% | 23.78% | $2,508.09 |
| SP500 | Prior | $3,153.85 | +0.161% | 1.00% | $3,148.93 |

Monthly means are arithmetic, not compounded growth rates. Gold logistic's
slightly positive monthly arithmetic average is consistent with a -1.82%
terminal return; it does not mean the account grew. Stress terminal return is
-8.75%, monthly mean -0.221% and balance DD 20.08%.

Gold logistic executes 205/207 candidates. Two minimum-lot skips, March 23 and
24 UTC 2026, remove +2.967R and +1.534R hypothetical winners. Together these
account for almost all of the +4.595R candidate sum. Fractional-lot ideal
compounding without skips would finish about $3,066.58; that is not the executable
account. Lot rounding, skipped opportunities and compounding must be retained.

Safety finding in the SP500 logistic comparator: one short entered May 9, 2025
at 15:00 UTC survives until the Sunday reopening May 11 at 22:00 UTC (55 hours),
then stops through a gap at -5.394R. Its account loss is $159.08 against a $29.50
budget, or 5.39 times nominal risk. The four-bar prediction was actually correct.
The inherited 24h rule exits at an available quote after the deadline, not through
a closed market, and stops cannot guarantee fill prices. We did not silently
change weekend/holding rules to remove this event. The original baseline remains
unchanged. Any future deployment contract must explicitly address closed-market
exposure and gap risk; no strategy here guarantees a hard 1% realized loss cap.

These account illustrations exclude margin constraints, swaps and floating-equity
drawdown. No new $500/$1,000 or 1%-5% search was run in this diagnostic.

## Interpretation and next decision boundary

1. Replacing the learner improves probability scoring versus raw eight-neighbor
   fractions but does not establish useful predictive information beyond prior.
2. The short trading problem is not repaired. Trading outcomes still depend on
   signal selection, path-dependent stops and rare winners, not only endpoint
   direction accuracy.
3. This does **not** prove the five features contain no information, that every
   ML model fails, or that gold cannot be traded profitably. Only two learners
   and one frozen representation/target were tested here.
4. Do not replace the SP500 baseline, promote gold logistic, tune confidence
   thresholds, or select 2026 because it looks better. A future label/payoff or
   signal-selection study needs a separate contract and eventually untouched
   data/forward observation. No additional experiment has been launched.

## Engineering review and reproduction

43 unit tests and full repository lint pass. Validation independently
reconciles saved probabilities/targets, confusion counts, calendars, monthly
paired statistics, all 12 policy/cost ledgers and accounts. Source hashes and
all 1,433 original M30 trade records match. No convergence failures occurred;
maximum solver iterations were 80 gold / 86 SP500, below the frozen limit 500.

Review fixed annual frequency denominators and Windows/macOS LF/path hashing;
the finalizer verified that forecast, trade and account ledger bytes were not
changed. Those were reporting/portability corrections, not strategy changes.
Runtime: Python 3.14.5, numpy 2.5.3, pandas 3.0.5, sklearn 1.9.1, scipy 1.18.1.

```bash
python -m pip install -e '.[dev,research]'
python -m lorentzian_audit.model_ablation
python -m lorentzian_audit.validate_model_ablation
python -m pytest -q
python -m ruff check src tests scripts
```

`model_ablation` needs the original raw archives and finalizes reporting
automatically. `validate_model_ablation` works from GitHub evidence without
MT5 or raw archives. The idempotent finalizer can also run separately as
`python -m lorentzian_audit.finalize_model_ablation`.

Evidence: `evidence/model_ablation/` contains observations, classification and
matched cohorts, reliability bins, monthly coefficient snapshots (not causal
feature-importance claims), trades, PnL quadrants, account ledgers, annual/monthly
metrics, paired intervals, manifests and validation. Approximately 4.6 MB, with
no raw market archive or account credentials included.
