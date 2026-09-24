# Technical plan - SP500 M30 runner tail robustness v4

## Purpose

The top-ten deletion used in v3 is intentionally hostile to a convex runner.
This audit replaces that single diagnostic with tests that preserve the reason
the strategy exists: a small number of large trends must pay for many -1R
losses. No entry or exit rule changes are allowed.

This is partially posthoc. The 3R/5R cap totals were inspected during the v3
discussion. They remain descriptive, not newly preregistered evidence. The
Monte Carlo contract and September Exness extension are frozen before their
outcomes are inspected.

## Historical tail tests

1. Cap each winner at +3R and +5R rather than deleting it.
2. Measure the contribution of the best 1, 3, 5 and 10 trades.
3. Count and sum winners above 3R by year.
4. Report development 2024-2025 separately from the retrospective January to
   August 2026 partition.

## Tail-miss Monte Carlo

For every trade above +3R, independently simulate failure to capture it at 5%,
10%, 20% and 30% probabilities. All ordinary winners and losses remain. Across
20,000 deterministic-seed replications report total R, probability of remaining
profitable, tails missed, and a continuous 1%-risk equity path. This directly
answers operational fragility without pretending the largest winners never
exist.

## New holdout

After the contract commit, request read-only Exness US500 M1 bars from 1 through
24 September 2026. Append them to the existing warm-up history locally, rebuild
the unchanged causal signal, and score only September entries. Raw bars remain
gitignored; their hash and quality diagnostics enter the evidence manifest.

The short extension is forward-like evidence, not a sufficient standalone
sample. Fewer than 30 trades receives an explicit `INSUFFICIENT_SAMPLE` label.
