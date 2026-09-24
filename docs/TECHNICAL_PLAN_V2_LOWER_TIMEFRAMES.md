# Technical plan - lower-timeframe Lorentzian audit v2

## Reason for the new study

The H4 v1 contract produced less than one trade per week. TradingView screenshots
of XAUUSD showed materially higher signal counts at M15, M30 and H1. That is a
new timeframe hypothesis, not a repair of v1: four bars mean one hour at M15,
two hours at M30, four hours at H1, and sixteen trading hours at H4.

M30 is frozen as the primary because it is closest to the desired one-to-two
trades per day while carrying less microstructure friction than M15. M15 and H1
are complete sensitivity studies and cannot replace a failed M30 result.

## Two different evidence windows

The pinned indicator's `max_bars_back=2000` makes its TradingView trade panel a
short recent-window diagnostic. The exact original is therefore run on 2,500
ending bars per asset/timeframe: 500 context bars followed by approximately
2,000 scored bars. It is reported with its own observed duration and cannot pass
the multi-year gate.

The main test is January 2024 through August 2026 with data back to January 2022
for warm-up. Causal KNN uses a rolling maximum of 2,000 historical bars at every
decision. A feature at bar `j` is labelled by `close[j+4]-close[j]` and becomes
eligible only at `j+4`.

## Comparisons

For each asset and M15/M30/H1:

1. exact-original recent-window diagnostic;
2. causal Lorentzian exact 8-NN;
3. causal Euclidean exact 8-NN;
4. known four-bar momentum;
5. classifier-free kernel slope.

All full-history variants use identical features, default volatility/regime
filters, kernel confirmation, candidate spacing, execution, and costs. The
Lorentzian-versus-Euclidean comparison changes only the distance metric.

## Execution

Signals use completed candles. Entry is the next available Bid open. Exit is the
next open after four signal bars or an earlier qualified opposite start. Only
one position may be open. Base and stress costs reuse the frozen Exness models
from v1. Gross results are diagnostic.

## Evaluation

Report for every cell: trades, trades per active day and calendar week, net and
mean bps, win rate, PF, maximum drawdown, long/short contribution, annual and
monthly results, result without the ten best trades, monthly bootstrap,
same-window direction controls, and stress costs.

Only causal Lorentzian M30 is eligible for the declared promotion verdict. The
gate requires cross-asset profitability, PF at least 1.10, at least 500 trades,
positive 2024/2025/2026 blocks, positive result without the top ten, positive
bootstrap lower bounds and stress results, significant random-direction tests,
and superiority to every simpler comparator on both assets.

## Engineering audit

- Hash each consumed source file once and reuse the same normalized M1 frame.
- Verify resampling alignment and exact timeframe widths.
- Cross-check batched KNN against the transparent reference implementation.
- Assert every selected label matured no later than its decision.
- Assert next-bar fills, non-overlap, PnL/cost reconciliation and summary totals.
- Replay the full run and require identical evidence hashes.

