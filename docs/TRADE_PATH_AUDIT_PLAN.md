# Frozen-ledger SP500 versus XAUUSD path audit

Diagnostic registered 2026-09-25, before opening path statistics. No signal,
stop, target, timeframe or position-sizing changes. Existing v3 M30 base-cost
Lorentzian ledger only: January 2024-August 2026, both directions. Previously
known payoff, win rates and long/short contributions are not new discoveries.

## Questions

1. Is lower gold payoff associated with smaller favorable excursions or more
   profit surrendered before exit?
2. Do M1 intrabar extremes differ from the completed-M30 observations used by
   the trailing stop? Does gold more often touch +1R but fail to activate trailing?
3. Is the difference concentrated in shorts, and is it persistent by year?
4. Do fixed windows after the original entries show smaller opportunities even
   when the strategy's actual exit is ignored? Is stop-out then recovery common?
5. Is there descriptive evidence of directional extension before entry?

## Definitions and limits

- Use original fills, costs and planned risk. Long liquidation uses Bid; short
  uses Bid plus historical M1 spread, matching the existing bar-level model.
- In-position positive MFE and adverse MAE use completed M1 bars strictly BEFORE
  the exit minute, plus actual exit R and zero. Do not include exit-minute high,
  low or close: the stop may precede these prices. Thus MFE is a conservative
  bound, not an exact tick-path maximum; include a separate full-exit-bar upper
  sensitivity bound for intraminute stops only. Gap/time/opposite exits do not
  permit exit-minute extremes. M1 spread is not true intraminute Ask history.
- Net mark deducts hypothetical exit slippage and round-trip commission.
  Giveback = positive MFE minus realized R; report all trades, activated trails,
  and winners separately. MFE is hindsight, not achievable target profit.
- Reconstruct best completed-M30 net R and reconcile with the old ledger.
  MFE timing is the earliest pre-exit M1 extreme; if the exit creates the peak,
  use exit time. Zero-excursion trades have no peak time. This is minute resolution.
- For fixed 30/120/240-minute windows, disregard real exits and measure net mark
  at the EXACT horizon open, MFE/MAE before the horizon and minute coverage.
  Require exact entry/horizon quotes and >=90% M1 coverage. Otherwise flag missing,
  never forward-fill a closed session or cross a large gap silently. Such shadow
  windows can overlap; they are NOT executable strategy returns.
- At 120 minutes classify which net +/-1R barrier is touched first; report
  SAME_MINUTE_AMBIGUOUS explicitly, never infer OHLC ordering.
- For original initial-stop trades closed before 120 minutes, report recovery
  to +1R AFTER the exit minute but before the fixed 120-minute deadline.
  This is conditional hindsight evidence, not permission to widen a stop.
- Pre-entry extension: side-adjusted movement from entry-minus-120-minute open
  to the last completed M1 close, in entry ATR; require >=90% coverage and exact
  start. It is descriptive and known at entry, not an already-validated filter.

## Outputs and review

Per-trade audit, fixed-window observations, aggregate and annual metrics split
by asset and side, source manifest and validation. Decompose mean net R as mean
positive MFE minus mean giveback, including exit-bar sensitivity bounds. Report
raw sample sizes/coverage and avoid p-values from overlapping shadow trades.
The different entry selections are a confound: do not generalize these paths
into universal gold/index characteristics or an identified economic cause.

Verify original/source hashes, completed-close parity, excursion bounds,
calendar and accounting identities; unit-test short Ask, exit-bar exclusion,
missing horizons and simultaneous barrier hits. Keep all earlier experiments.
No new backtest grid, broker orders, external publishing or strategy promotion.
