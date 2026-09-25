# Direct prediction versus learned label, then PnL

Frozen before direct label audit outcomes. Continue `research/xauusd-loss-diagnostics`;
commit and push here, never merge main. Keep prior evidence immutable.

The model forecasts sign(close[i+4] - close[i]). Four observed M30 bars are
usually two hours but can span session gaps/weekends. Audit the EXACT existing
target; report elapsed-time distribution rather than silently replacing it with
a clock-time target. Label maturity is the target bar end. Data after the
evaluation end cannot label an evaluation observation. Flat prices are explicit
zero labels; unavailable future labels remain missing, never false zeros.

## Separate three stages

1. Every raw negative classifier vote: direct prediction ability.
2. Qualified short start after existing filters, kernel and state transition.
3. Executed original baseline short: join to the frozen v3 runner PnL.

Repeat long cohorts and SP500 as context. Record censoring, abstentions, raw
confusion, label prevalence, precision, year/regime and vote-strength tables.
The original 8-neighbor vote is not a calibrated probability. Regime mapping
reuses the completed-D1 definition from the preceding diagnosis.

## Baselines and uncertainty

Always-up, prior-four-bar momentum, and rolling past-label majority. The prior
uses truth.shift(4), a 2000-observation window and 200-label minimum, so labels
are already mature at decision time. Never fit a majority from the entire future
test period. On raw-short rows compare classifier correctness with each baseline
on the SAME nonflat rows where that baseline has a directional prediction.
Record abstentions and sample counts; these pairwise universes may differ.

Use paired circular three-calendar-month blocks (32 months, 10,000 replicates)
to obtain accuracy differences from resampled hit/count totals, not iid binomial
tests on overlapping four-bar labels. Three gold raw-short comparisons receive
Bonferroni 98.333% intervals; SP500 is context. Cohort precision 95% intervals
are descriptive. Selection across the prior research history is not corrected.
Whole-period down prevalence is descriptive, not a matched tradable benchmark;
always-down is tautologically identical within a short-only forecast cohort.

## Link label success to actual PnL

Join actual original entries by exact signal timestamp, preserving all original
trade fields and totals. Separate correct-and-win, correct-and-nonwin,
wrong-and-win, wrong-and-nonwin, flat-target and unavailable-target categories.
Report count, total/mean R, exit reasons and exit before target-maturity time.
Within correct shorts identify initial SL before maturity. A right endpoint
does not establish a favorable path before SL.

Also mark the original entry at the target bar close using side-correct Bid/Ask,
original costs and R denominator, ignoring prior exit solely for this diagnostic.
This is hypothetical liquidation, not a new four-bar backtest or achievable fill.
Report how often a directionally right label still fails to cover entry/exit
friction. Preserve target close, spread, timestamps and raw votes for verification.

## Engineering and limits

Hash-check parent/data, regenerate causal signals and reconcile every original
entry against the correct start flag/vote sign. Test missing-label handling,
gapped-bar horizons, prior-label maturity and bootstrap pairing. Validate saved
confusion/cohort counts and PnL-quadrant sums against original ledgers. Do not
modify the model or select a confidence threshold from observed results.

The audit can distinguish observed direction errors from target/payoff mismatch.
It cannot identify the economic cause, prove training convergence, or establish
that another feature/label will fix the model. Classification failures and exit
misalignment can coexist. Report them separately without a live-promotion verdict.
