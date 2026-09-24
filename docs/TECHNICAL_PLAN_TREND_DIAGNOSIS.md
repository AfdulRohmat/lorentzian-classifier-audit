# Gold loss diagnosis: daily trend and directional asymmetry

All gold-loss diagnosis work lives on `research/xauusd-loss-diagnostics`, including
the previous same-runner control and path audits. Main remains unchanged. Commit
and push this branch after evaluation; no merge or deployment.

## Frozen questions

Is negative gold short performance concentrated in a known-before-entry bull
trend? Is any positive long-only result more than exposure to rising gold?
Primary XAUUSD M30, secondary SP500 M30. Frozen v3 data, January 2024-August 2026
evaluation; 2022-2023 warmup. Previously inspected history, not pristine holdout.

## Regime and replay

Use UTC daily bars from the original M1 data, excluding empty days. EMA200 uses
adjust=False with 200 observed-day warmup; compare its slope to 20 observed days
earlier. Last completed daily close above EMA and positive slope = bull; inverse
= bear; otherwise mixed. Missing warmup = unavailable. Assign at M30 signal close
using only daily bars that have already ended. No use of the full day's future
close or the next session's information. No parameter grid.

Replay baseline, long-only, short-only and trend-aligned (bull longs, bear shorts,
skip mixed/unavailable). Keep ALL original opposite starts as exits; rejecting a
reverse entry must not accidentally remove the exit. No entry on regime change
without a fresh start signal; no exit just because the regime changes. Add only
an optional entry-eligibility mask to the existing runner, default unrestricted.
Verify baseline full-ledger parity on both assets.

Report base/stress PnL, trades, frequency, PF, R/trade, R drawdown, annual results,
monthly paired circular three-month bootstrap differences to baseline (10,000;
three-comparison adjustment within each asset, gold primary), long/short/regime
cell counts and time/regime coverage. Cells below 30 trades are explicitly weak
evidence. Account context: USD3,000 at 1%, existing lot flooring/skip/compounding;
no margin or swap model. This is not another capital/risk search.

## Matched gold-long diagnostic

Generate 20 seeded schedules, matching one alternate entry for each matchable
base long-only trade. Same calendar month, New York hour, causal daily regime;
ATR14/close within 25% of the original. Candidates exclude all original starts
and must have a valid executable next bar. No relaxed fallback for unmatched
anchors; record every match and exclusion. Sampling must not inspect PnL.

Keep original classifier short exits and the same runner. Controls have no
short entries; original long starts are replaced with sampled entries. A full
one-position replay resolves overlap, so executed counts need not match anchors.
Report actual count, exposure, R/trade and total R distributions. The matched
anchor subset's original R is descriptive, not a separately replayed portfolio.
Do not infer significance from a small rank among 20 schedules. The controls are
conditional diagnostics, NOT an independently deployable regime-only strategy:
anchor matching uses the observed future sample's month/hour distribution and
retains classifier-based short exits. They ask about incremental LONG ENTRY
timing under that shared exit rule.

## Engineering gates and scientific limits

Freeze contract before new results; preserve past audits. Test daily availability,
prefix invariance, directional masks, rejected-reverse exit preservation and
control matching. Reconstruct both baselines, check source hashes and causal
label maturity. Reconcile account/trade/calendar arithmetic, all variant cells
and control draw properties. Review all results including adverse outcomes.

The chosen regime proxy is not ground truth. Annual gold appreciation does not
assign individual entries. If most data are bull and few shorts enter bear,
state lack of support instead of claiming bear-short behavior identified.
Stress and SP500 contextual comparisons cannot rescue failed gold inference.
Any gold-specific strategy remains a new hypothesis requiring untouched data or
demo forward observation. No model-label retraining in this experiment.
