# Result - ATR runner and small-account sizing v3

## Verdict

`ATR_RUNNER_DOES_NOT_RESCUE_LORENTZIAN_ENTRIES`

The runner materially improves the SP500 M30 payoff distribution, but the
effect does not transfer to XAUUSD and is not robust to concentration tests.
Only the frozen no-account-ruin gate passed. This result does not promote the
Lorentzian strategy to forward test.

## Frozen exit

- Entry: unchanged causal Lorentzian start event, filled at the next timeframe
  open on the executable side of the spread.
- Initial stop: `1 x ATR(14)` from entry fill.
- Take-profit: none.
- Trail: after a completed timeframe close reaches +1 net R, lock
  `best completed-close R - 1R`; the new stop is active from the next M1 bar.
- Other exits: opposite signal or 24-hour safety limit.
- Stop fills: M1 Bid for long and modeled Ask for short, including gaps,
  slippage and commission.

## Strategy result before account sizing

Evaluation: January 2024 through August 2026.

| Asset | TF | Trades | / week | Total R | Mean R | Win rate | PF | DD R | Ex top 10 R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SP500 | M15 | 1,323 | 9.51 | +15.05 | +0.011 | 39.3% | 1.019 | 53.41 | -66.68 |
| SP500 | M30 | 688 | 4.94 | +72.77 | +0.106 | 38.5% | 1.172 | 27.22 | -14.64 |
| SP500 | H1 | 338 | 2.43 | +20.24 | +0.060 | 39.6% | 1.100 | 21.63 | -49.41 |
| XAUUSD | M15 | 1,511 | 10.86 | +48.61 | +0.032 | 40.7% | 1.054 | 48.25 | -28.48 |
| XAUUSD | M30 | 745 | 5.35 | -32.48 | -0.044 | 39.6% | 0.927 | 46.79 | -98.90 |
| XAUUSD | H1 | 363 | 2.61 | +30.95 | +0.085 | 43.8% | 1.159 | 25.45 | -24.80 |

The lower win rates are expected: the median outcome is approximately -1R
because the model deliberately accepts many full initial-stop losses while
waiting for uncapped winners.

SP500 M30 improves from the unchanged four-bar baseline's +18.04R and PF 1.038
to +72.77R and PF 1.172. All three annual blocks are positive. Nevertheless,
the monthly-bootstrap interval remains [-0.37R, +4.92R] and removing the ten
best trades changes the result to -14.64R. Long positions contribute +75.33R;
short positions contribute -2.56R. The apparent edge is therefore concentrated
and mostly a long-equity-index effect.

XAUUSD M30 becomes slightly worse than its already negative four-bar baseline:
-32.48R and PF 0.927. Its 2024, 2025 and 2026 blocks are all negative. The
cross-asset primary hypothesis fails.

## SP500 M30 account simulation

| Start | Risk | Executed / skipped | Final | Total return | Mean monthly | Max DD |
|---:|---:|---:|---:|---:|---:|---:|
| $500 | 1% | 681 / 7 | $922.85 | +84.57% | +2.23% | 23.64% |
| $500 | 2% | 685 / 3 | $1,348.72 | +169.74% | +4.33% | 43.94% |
| $500 | 3% | 688 / 0 | $1,637.11 | +227.42% | +6.40% | 59.09% |
| $500 | 4% | 688 / 0 | $1,645.96 | +229.19% | +8.37% | 71.93% |
| $500 | 5% | 688 / 0 | $1,377.85 | +175.57% | +10.23% | 81.59% |
| $1,000 | 1% | 685 / 3 | $1,830.37 | +83.04% | +2.21% | 24.36% |
| $1,000 | 2% | 688 / 0 | $2,716.58 | +171.66% | +4.36% | 43.99% |
| $1,000 | 3% | 688 / 0 | $3,281.39 | +228.14% | +6.41% | 59.16% |
| $1,000 | 4% | 688 / 0 | $3,293.63 | +229.36% | +8.38% | 72.00% |
| $1,000 | 5% | 688 / 0 | $2,762.83 | +176.28% | +10.25% | 81.62% |

These attractive totals are not sufficient evidence. At 2% risk, historical
drawdown is already about 44%; at 3%-5% it reaches 59%-82%. Five percent produces
less terminal wealth than four percent because volatility drag overwhelms the
larger nominal sizing. Eight SP500 M30 trades also lost more than their planned
risk because of M1 gaps; the worst was approximately 1.19 times its budget.

## XAUUSD M30 account simulation

| Start | Risk | Executed / skipped | Final | Total return | Mean monthly | Max DD |
|---:|---:|---:|---:|---:|---:|---:|
| $500 | 1% | 171 / 574 | $445.84 | -10.83% | -0.32% | 24.66% |
| $500 | 2% | 394 / 351 | $381.21 | -23.76% | -0.54% | 42.98% |
| $500 | 3% | 407 / 338 | $265.92 | -46.82% | -1.23% | 66.10% |
| $500 | 4% | 468 / 277 | $307.31 | -38.54% | +0.04% | 76.35% |
| $500 | 5% | 469 / 276 | $241.92 | -51.62% | +0.15% | 81.53% |
| $1,000 | 1% | 424 / 321 | $777.46 | -22.25% | -0.71% | 30.21% |
| $1,000 | 2% | 589 / 156 | $638.18 | -36.18% | -0.79% | 52.10% |
| $1,000 | 3% | 520 / 225 | $414.46 | -58.55% | -1.67% | 77.43% |
| $1,000 | 4% | 498 / 247 | $310.08 | -68.99% | -1.73% | 84.63% |
| $1,000 | 5% | 478 / 267 | $242.18 | -75.78% | -1.87% | 90.15% |

At USD 500 and one percent risk, only 22.95% of XAUUSD M30 candidates are
executable at 0.01 lot. The rest correctly remain skipped. A positive arithmetic
mean monthly return in two losing high-risk rows does not contradict the final
loss; compounding and large drawdowns create geometric drag.

## Exit behavior

SP500 M30 activates the trail on 37.8% of trades and has a median hold of 1.39
hours. There are 420 initial-stop exits, 252 trailing-stop exits, 14 time exits
and two opposite exits. XAUUSD M30 activates the trail on 39.1%, holds 1.78 hours
at the median, and records 445 initial-stop, 287 trailing-stop and 13 time exits.

The requested principle is therefore implemented: losses cluster near -1R and
winners are uncapped. It improves one slice, but exit engineering cannot create
a transferable directional edge when the underlying entries lack one.

## Limits and audit

- Historical margin availability and swap are not modeled. A position may cross
  rollover within the 24-hour limit.
- Sizing filters the frozen theoretical ledger. Skipping a trade does not create
  an alternate re-entry path.
- Ten unit tests and all 14 evidence checks pass.
- A complete replay reproduced identical hashes for the strategy ledger,
  account ledger, summary, monthly table, manifest and validation.

Evidence is stored in `evidence/v3_atr_runner_sizing/`.
