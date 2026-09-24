# Same-runner entry comparison

Frozen before opening the new runner-control results, 2026-09-25. This is a
retrospective diagnostic, not a new unseen test. Prior Lorentzian runner and
four-bar control results are already known.

## Question and scope

Does causal Lorentzian add value beyond Euclidean KNN, prior-four-bar momentum,
or kernel-slope signals when all use the existing ATR runner? Primary SP500 M30;
secondary XAUUSD M30. Preserve v3 source data, evaluation January 2024 through
August 2026, warmup from 2022, filters, costs, execution and exit engine.

Use the existing four signal implementations without tuning. Euclidean changes
only the distance metric; momentum and kernel replace the classifier but keep
the common filters. An entry occurs on the next bar open after a completed
qualified signal. SL 1 ATR(14), no fixed TP, trailing activates at +1 net R and
trails by 1 net R using completed M30 closes, maximum hold 24h. A qualifying
opposite signal closes/reverses the position. Thus this compares whole signal
policies under a common exit algorithm, not entry alone with identical exits.

## Outputs and evaluation

- Replay all eight asset/variant cells at base and existing v2 stress costs.
- Verify source hashes and exact baseline-ledger parity with v3.
- Report trades, activity, exposure, net R, R/trade, PF, win rate, drawdown,
  tails above 3R, long/short and annual contributions, all 32 monthly observations.
- Compare same-calendar exit-month R using paired circular three-month block
  bootstrap, 10,000 replicates, fixed seed. Primary three comparisons have
  Bonferroni-adjusted 98.333% intervals in addition to nominal 95% intervals.
- Historical incremental support requires Lorentzian total R and PF to beat
  all three controls and all adjusted primary lower bounds to exceed zero.
  Otherwise report incremental value unconfirmed, including any weaker or
  negative comparisons. Secondary and stress results cannot rescue the primary.
- Context only: USD 3,000, 1% current-equity risk, broker lot flooring and skip
  below minimum, unchanged v3 account simulation. This reduces small-account
  granularity but does not remove it. Margin and swap remain unmodeled.

## Engineering and review

Freeze JSON contract, implement thin orchestration over unchanged signal/runner
modules, unit-test paired-block statistics, run full tests and lint, regenerate
evidence and validate invariants. Reconcile calendars, trade accounting, source
hashes, label maturity and Lorentzian reproduction. Publish all controls, not
just the winner. Update README and portable handoff; no deployment or MT5 orders.
Do not silently replace the demo candidate with a retrospective winning control.
