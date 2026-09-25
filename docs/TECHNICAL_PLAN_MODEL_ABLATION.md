# Same-feature, same-target model ablation

Frozen before new results on `research/xauusd-loss-diagnostics`. This is a
retrospective diagnostic, not a fresh holdout and not authority to deploy.

## Question and scope

Can regularized logistic regression extract more useful information from the
existing five features than eight-neighbor Lorentzian classification, and more
than a feature-free historical class prior? Gold M30 is primary; US500 M30 is
secondary context. No M15/H1, parameter sweep, new indicators or exit tuning.

The previous audit demonstrated poor gold-short direction forecasts, but did
not identify whether the learner, the features or the endpoint target caused
the weakness. Changing only the learner is a bounded diagnostic, not a complete
causal identification of that mechanism.

## Frozen implementation contract

See `config/contract_model_ablation.json`. At decision i all three models use
eligible j in [max(0,i-2000),i-4], excluding j divisible by four and nonfinite
features, exactly as the original KNN. Labels are sign(close[j+4]-close[j]);
genuine unchanged prices remain class zero. No unmatured target enters training.

Original Lorentzian prediction is reproduced unchanged, including its tie
handling. For probability scoring reconstruct its eight neighbors with the
same batched argpartition implementation (not a differently tie-broken KNN).
Their class fractions are uncalibrated empirical probabilities. Logistic uses
L2 C=1, lbfgs, tol=1e-6, max_iter=500, intercept, no class weights, original
normalized features without additional scaling. Refit every bar from scratch;
minimum 200 candidates. A one-class fit falls back to the prior. Nonconvergence
is an explicit failure, not silently accepted. The prior uses the identical
pool, not the wider rolling-prior pool from the previous study.

Forecast sign(p_up-p_down) preserves the mean-label interpretation of KNN.
Ties abstain; existing filtered signal state persists. Do not add a confidence
threshold to manufacture short precision. Preserve filters, kernel and
start-on-state-change behavior. Each model has its own opposite signals, so
the same exit *rule* does not imply identical exit timestamps or exposure.

## Data and evaluation

Source hashes and original M30 trade ledgers must match frozen v3 evidence.
2022-2023 provides context; evaluation is January 2024-August 2026, 32 months.
Score on the common eligible universe with mature four-observed-bar targets;
these can span more than two clock hours. Censor unknown final labels. Training
continues online through the evaluation history but only after labels mature.

Primary prediction endpoint: multiclass Brier loss, sum over -1,0,+1 classes,
including flats and ties, on identical timestamps. Paired improvements versus
prior and Lorentzian; higher improvement means better logistic predictions.
Report coverage, confusion, class recall, short/long precision, abstention-aware
balanced accuracy, annual results, reliability bins, and matched fixed original
Lorentzian short-vote / executed-short cohorts. These are descriptive; do not
select thresholds or a favorable year from them.

Replay all three models through unchanged M1 ATR runner under base/stress costs.
Report total/per-trade R, PF, drawdown, frequency, sides, years, and label/PnL
quadrants. Illustrative $3,000/1% account retains floor-lot/skip rules and known
margin/swap/floating-drawdown limitations; no new capital grid.

Four gold primary comparisons form one family: two Brier improvements and two
monthly net-R differences, logistic versus each comparator. Bootstrap 10,000
paired circular three-calendar-month blocks, seed 20260929; Bonferroni 98.75%
intervals. Brier uses monthly sufficient sums/counts; PnL includes zero months.
No independence assumption for overlapping four-bar labels. This does not
correct multiplicity across the entire project history.

## Engineering and review gates

1. Commit plan and contract before measuring outcomes.
2. Unit tests: future perturbation and prefix invariance, maturity bounds,
   identical pools, missing/flat/one-class cases, probability sums, tie behavior,
   KNN prediction parity, metric/abstention calculations.
3. Full replay with immutable source and baseline ledger parity, sequential
   positions, next-bar entry, finite R and account reconciliation.
4. Separate saved-artifact validator recomputes metrics, comparisons and ledger
   joins; manifest binds inputs and outputs. Run existing tests and lint.
5. Report all results, including negative outcomes. Update README and MacBook
   handoff; commit/push only this branch. No merge or live/demo orders.

## Interpretation, frozen before results

All four adjusted primary lower bounds must exceed zero for preliminary
incremental support; even that would not authorize promotion. Better Brier
alone may reflect less overconfident forecasts without useful short timing.
Better trading without better forecasts may reflect state-change/exposure and
runner interaction. If neither learner improves over the prior, the tested
feature-target setup remains unproven, not mathematically devoid of information.
Only a later separately contracted experiment could change features or labels.

## Method references

- [Official logistic regression API](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html): regularized classifier and coefficient/probability interfaces.
- [Official leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html): keep fitting and preprocessing away from future evaluation information.

These references justify implementation practices, not a claim of financial edge.
