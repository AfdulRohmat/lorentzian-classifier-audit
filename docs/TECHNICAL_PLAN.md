# Technical plan - Lorentzian classifier audit v1

## Objective

Test the claim behind the reviewed video without optimizing its many settings:
does the pinned open-source Lorentzian classifier contain causal directional
information that survives executable timing and modeled Exness Raw costs on
both SP500 and XAUUSD?

The study separates three questions that the video's built-in win rate mixes:

1. Does the exact original indicator make money under conservative fills?
2. Does a correctly matured future-four-bar target make money?
3. Does Lorentzian distance add value over Euclidean distance and simple price
   filters when everything else is held constant?

## Frozen scope

- Instruments: Exness US500 CFD and Exness XAUUSD CFD.
- Source: existing local M1 Parquet archives; no raw data is copied.
- Bars: H4 aligned to UTC. This is the primary timeframe because the indicator
  documentation says its defaults target higher intraday timeframes.
- Data: January 2022 through August 2026. January 2024 through August 2026 is
  the evaluation interval; earlier bars provide feature and neighbor history.
- Parameters: the official defaults. There is no grid search, threshold search,
  asset-specific tuning, or post-result rescue variant.

## Signal variants

`official_original` uses the pinned Python port exactly for feature calculation,
greedy ANN state, filters, kernel confirmation, and start signals. Its embedded
trade statistics are ignored.

`causal_lorentzian` and `causal_euclidean` use exact KNN. A historical feature
at bar `j` receives the sign of `close[j+4] - close[j]`, and cannot enter the
candidate set until bar `j+4`. Both variants use eight neighbours, the most
recent 2,000 bars, identical candidate spacing, features, filters, and trade
logic. Only the distance metric changes.

`simple_momentum4` asks whether the sign of the already-known prior four-bar
return performs as well as the classifiers. `filter_only_kernel` removes the
classifier and trades qualified kernel-slope changes.

## Execution and costs

Signals are formed only after the H4 candle closes. Entry occurs at the next
available H4 Bid open. A position exits at the next open after four signal bars,
or at the next open following an earlier qualified opposite start. Positions do
not overlap; a direct flip closes one trade and opens the other at the same open.

Bid/Ask is reconstructed from the M1 spread at the execution open. Long trades
pay entry spread; short trades pay exit spread. Both sides pay adverse slippage
and a round-trip commission expressed in price units. Base and stress settings
reuse the frozen assumptions from the earlier Exness research. Gross results
are diagnostic only.

## Required comparisons

For every strategy, run opposite, always-long, always-short and deterministic
random directions over the exact same entry/exit windows. Report trade count,
trades/week, win rate, PF, total/mean bps, maximum drawdown, yearly and monthly
stability, long/short contribution, result without the five best trades,
monthly-block bootstrap intervals, and stress costs.

The primary scientific contrast is `causal_lorentzian` versus
`causal_euclidean`. If Lorentzian does not win that controlled comparison on
both assets, its name is not evidence of an incremental trading edge.

## Audit requirements

- hash every consumed monthly source file and record source coverage;
- reject duplicate timestamps and malformed OHLC rows after deterministic
  deduplication/validation;
- verify every causal neighbor label was mature at decision time;
- verify every fill occurs strictly after the signal timestamp;
- independently reconcile cost and PnL arithmetic;
- replay the run and compare deterministic artifact hashes;
- freeze the final verdict from the declared gates, not narrative judgment.

