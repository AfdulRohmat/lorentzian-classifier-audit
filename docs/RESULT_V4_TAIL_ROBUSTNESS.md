# Result - SP500 M30 runner tail robustness v4

## Assessment

`TAIL_STRUCTURE_SUPPORTED_EDGE_UNCONFIRMED`

The SP500 M30 runner is not dependent on one singular lucky trade. Its large
winners recur across years, the result remains positive when every winner is
capped at +5R, and a deliberately adverse Monte Carlo that misses 10% of all
greater-than-3R winners remains positive in 99.91% of simulations.

This does not prove a live edge. The 3R/5R cap totals were inspected before the
v4 contract and are explicitly posthoc. The pristine September extension is
negative but contains only nine completed trades.

## Winner caps

| Result | Total R | PF | 2024 | 2025 | 2026 Jan-Aug |
|---|---:|---:|---:|---:|---:|
| Uncapped | +72.77 | 1.172 | +23.45 | +31.64 | +17.68 |
| Every winner capped at +5R | +30.24 | 1.072 | +10.07 | +22.81 | -2.64 |
| Every winner capped at +3R | -34.10 | 0.919 | -18.89 | +1.57 | -16.77 |

The strategy therefore needs to capture moves above +3R. It does not require
the full +16R best trade to remain profitable, because a +5R cap still leaves
+30.24R. However, the negative 2026 result under a +5R cap shows that recent
profit depended on some winners exceeding +5R.

## Concentration ladder

| Removed | Winner contribution | Share of total net | Remaining result |
|---|---:|---:|---:|
| Best 1 | +15.96R | 21.9% | +56.80R |
| Best 3 | +35.75R | 49.1% | +37.01R |
| Best 5 | +53.61R | 73.7% | +19.16R |
| Best 10 | +87.41R | 120.1% | -14.64R |

Removing the top ten is a useful hostile stress test, but it obscures the more
important result: the strategy remains positive without its best one, three or
five trades. Dependence emerges only after removing a broader set of tail
events.

There are 53 trades above +3R, or 7.7% of all 688 trades. Together they produce
+265.86R while all other trades sum to approximately -193.10R. At the observed
frequency this is roughly one greater-than-3R trade per 13 trades, or once every
2.6 calendar weeks.

| Year | Trades above +3R | Tail contribution |
|---:|---:|---:|
| 2024 | 21 | +105.35R |
| 2025 | 21 | +93.06R |
| 2026 Jan-Aug | 11 | +67.45R |

The tail is present in every year rather than being one isolated market event.

## Tail-miss Monte Carlo

Each greater-than-3R trade is independently missed with the stated probability;
all losses and ordinary winners remain. This is deliberately adverse. Results
use 20,000 deterministic-seed simulations. The equity diagnostic continuously
risks 1% per trade and does not reproduce broker minimum-lot constraints.

| Tail miss | Median tails missed | Median total R | 95% total-R interval | P(total R > 0) | Median equity | Median DD |
|---:|---:|---:|---:|---:|---:|---:|
| 5% | 2 | +60.75R | [+39.35, +72.77] | 100.00% | 1.638x | 25.1% |
| 10% | 5 | +47.27R | [+19.98, +66.10] | 99.91% | 1.437x | 27.4% |
| 20% | 10 | +20.31R | [-14.42, +48.60] | 88.26% | 1.107x | 32.1% |
| 30% | 16 | -6.28R | [-44.34, +27.58] | 36.26% | 0.855x | 38.9% |

The operational boundary is meaningful. Missing around 10% of tail winners is
tolerable historically. At 20%, the lower interval becomes negative. At 30%,
the median strategy loses money. Early discretionary profit-taking would have
the same destructive effect as missing the tail.

## Temporal partition

| Partition | Trades | Total R | Mean R | PF | Win rate | DD R |
|---|---:|---:|---:|---:|---:|---:|
| Development 2024-2025 | 530 | +55.09 | +0.104 | 1.172 | 39.2% | 27.22 |
| Retrospective Jan-Aug 2026 | 158 | +17.68 | +0.112 | 1.175 | 36.1% | 24.83 |

The mean expectancy and PF are unusually consistent across this split. It is
still a retrospective partition, not pristine evidence: v2 had already exposed
aggregate outcomes through August 2026 before this v4 contract.

## New September extension

The MT5 read-only request for 1-24 September failed with `IPC timeout`. A prior
untouched Exness cache provided complete UTC coverage through 9 September and
was scored without changing the model:

- 9 trades, approximately 7 per week;
- -3.92R total and -0.435R mean;
- 22.2% win rate and PF 0.440;
- 4.82R drawdown.

Status: `INSUFFICIENT_SAMPLE`. This is a negative warning, not a rejection.
Historically, 16.8% of same-length nine-trade windows were at least this bad,
and only 52.1% of nine-trade windows were positive. The observed extension is
therefore inside the normal short-run noise of the strategy.

## Practical interpretation

The prior statement that every positive variant fails after deleting ten
winners was mathematically correct but too blunt for a convex runner. For
SP500 M30, the stronger conclusion is:

- the tail mechanism is real in the historical sample and distributed across
  years;
- the strategy requires reliably holding winners beyond +3R;
- it tolerates modest tail-execution misses but not systematic early exits;
- the clean new-data sample remains far too short and currently negative;
- the edge is suitable for continued demo observation, not live-money
  promotion.

Eleven unit tests and all 13 evidence checks pass. A full replay reproduced
identical summary, source, trade and validation hashes.

Evidence is stored in `evidence/v4_tail_robustness/`.
