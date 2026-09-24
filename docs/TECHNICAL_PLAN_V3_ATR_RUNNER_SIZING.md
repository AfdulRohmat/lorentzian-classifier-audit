# Technical plan - ATR runner and small-account sizing v3

## Objective

Keep every causal Lorentzian entry from v2 unchanged and test whether a
mechanical `cut losses short, let profits run` exit alters the expectancy. Then
translate the resulting trade path into executable Exness lot sizes for USD 500
and USD 1,000 starting balances at one through five percent risk.

## Exit state machine

At the next timeframe open after a start event, enter using the executable side
of the spread plus adverse slippage. ATR(14) is known at the completed signal
bar. The initial liquidation stop is one ATR from the entry fill. There is no
take-profit.

Stops are checked on M1. A gap beyond the stop exits at the adverse M1 open;
otherwise the trigger price is used with adverse slippage. For short positions,
the M1 Bid feed is converted to an effective Ask using the frozen spread model.

At each completed signal-timeframe close, calculate the best net mark in R. Once
it reaches +1R, tighten the stop to lock `best R - 1R`, inclusive of modeled
exit slippage and commission. A new stop becomes active only from the following
M1 bar and can never loosen. An opposite signal exits and reverses at its next
timeframe open. Any remaining trade exits after 24 hours as a safety time stop.

## Position sizing

Risk budget is a percentage of current realized equity. Planned initial-stop
loss per lot includes the ATR distance, adverse exit slippage and round-trip
commission. Raw volume is floored to the broker lot step. A result below the
minimum lot is skipped; it is never rounded upward.

Report final balance, return, maximum balance drawdown, executed and skipped
trades, realized maximum loss relative to planned risk, and monthly return for
every balance/risk combination. Margin and swap are not modeled, so this is a
risk-sizing simulation rather than a promise that every historical order would
have passed the broker's margin check.

## Audit

- Unit-test long/short stop fills, gap handling, completed-bar trail timing,
  non-loosening stops and minimum-lot flooring.
- Verify ATR and every entry use only information available before execution.
- Reconcile price PnL, commission, lot PnL and account balance.
- Require no overlapping theoretical positions.
- Replay and compare evidence hashes.
