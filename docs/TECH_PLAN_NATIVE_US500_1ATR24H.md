# Native US500 one-ATR, 24-hour comparison

## Question and frozen contract

Replay the established causal Lorentzian M30 runner on Exness `US500` directly
in MT5, because its earlier positive US500 result used a Python M1 replay while
the subsequent native `US500_x100` result was negative. This is a symbol/feed and
execution comparison, not a fresh holdout or a claim that contract size causes a
return difference.

- Keep the archived classifier and trade logic unchanged. The only EA source
  amendment permits exact `US500` as well as `US500_x100` in Strategy Tester;
  the hard non-tester order guard remains in place.
- M30, history anchor 15 June 2025, evaluation 1 January through 31 August 2026.
  Record the first actually available warm-up bar and count. This differs from
  the old US500 Python normalization anchor in January 2022.
- Entry on the first available quote after a closed-bar Lorentzian start; one
  position at a time; opposite start closes and may reverse. No VWAP.
- Initial broker-side stop 1 x ATR14(M30), no fixed target. Activate trailing
  at +1 net R and trail completed-bar quotes by 1R. Exit at stop, opposite start,
  or the first tradable quote at or after 24 hours. Retain the existing 0.27
  price-point combined sizing/trailing reserve, without charging it as cash.
- USD 500, 1000, 3000 accounts. For each, compare strict 1% risk sizing that
  skips sub-minimum lots with the previously requested 1% target plus broker
  minimum-lot fallback. Report actual planned risk when fallback exceeds 1%.
- Local MT5 tester only, `Every tick based on real ticks`, no optimization,
  USD account, simulated leverage 1:400, zero additional execution delay.
  One January smoke and six full-period scenarios. No demo or real orders.

## Gates and reporting

Check compiled source and archived EX5 hashes, confirm the demo account is flat
and Algo Trading disabled before and after, use unique run tags, and retain failed
attempts. A test counts only after successful tester completion, real-tick
coverage inspection, no EA failure flag, full native deal export and balance
reconciliation. Independently audit initial stop, trailing, time exits, minimum
lot and signal stream against the archived x100 comparison where applicable.
Report trade count, trades/week and month, net PnL, return, PF, win rate, equity
drawdown, risk breaches, and monthly PnL. Show US500 and x100 next to each other
only with their different available histories and fills made explicit.

The first full $500 strict attempt revealed that native `OrderCalcProfit` rounds
USD to cents: a $4.6359 theoretical planned loss was reported as $4.64 against
a $4.6368 budget. The EA treated that approximately $0.0032 conversion difference
as an execution breach and invalidated the run. Retain that attempt as an
engineering failure. For the restart, allow at most $0.005001 of half-cent
conversion rounding in the post-fill check, matching the later audited native
wrapper; do not relax the pre-order theoretical budget or change trade rules.
