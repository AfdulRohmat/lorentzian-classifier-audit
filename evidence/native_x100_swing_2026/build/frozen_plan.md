# Native US500 x100 swing exit experiment

Test whether removing the 24 hour deadline and widening the initial stop and
trailing distance improves the existing Lorentzian runner. This is exploratory
research on an already inspected period, not an unseen holdout or authorization
for demo or real account execution. Freeze this contract before inspecting PnL.

## Rules agreed with the user

Keep the causal exact KNN classifier, features, filters, signal timing, symbol
US500_x100, M30 timeframe and one position maximum unchanged. A completed-bar
start enters at the next available bar quote. A valid opposite start closes the
position and may reverse, subject to sizing and execution checks. Same-direction
starts do not close, add to or reset an existing position. This is not a change
to the classifier or the original author's ANN implementation.

Initial stop distance is k times ATR14 M30 known at entry, k = 1 through 10.
Round the stop outward to the price tick grid. Freeze that initial distance;
never widen an existing stop. R is the initial stop distance plus the existing
0.27 point cost reserve, not an instruction to multiply monetary risk by k.
Trail activation remains +1R net of the same reserve; trailing width is 1R.
The trail uses completed M30 quotes, not intrabar high/low excursions, and can
only tighten. Native stop execution still uses real ticks. Actual commissions
and swaps are charged by MT5; the reserve is not an extra PnL debit. Breakeven
protection is approximate and does not guarantee recovery of accumulated swap.

Remove the 24 hour deadline in every swing variant. No fixed TP, Friday exit,
floating-loss exit, session filter or profitable-position-only holding rule.
Positions close via initial/trailing SL, opposite setup, or final tester
liquidation. Broker stop-out remains possible and is counted, not hidden.
Margin or market-closed rejections retain existing handling. A pending close
must not interrupt classifier updates. A failed immediate reversal during a
market closure is not retried as a stale entry.

## Frozen test matrix

Warm-up June 15 through December 2025; native evaluation January 1 through
August 31 2026. Real ticks, no added execution delay, USD and 1:400 test leverage,
same as the previous native matrix. Historical swap schedule fidelity is not
independently established; report actual tester swap charges without claiming
that today's symbol swap schedule reconstructs all historical rates.

Run 150 full scenarios: 10 stop widths x deposits $500/$1000/$3000 x nominal
risk targets 1/2/3/4/5 percent of current balance. The 1 percent row retains the
user-authorized minimum 0.01 lot fallback, which can substantially exceed the
nominal budget. Rows 2 through 5 remain strict floor sizing with skips below
minimum. No minimum fallback is silently extended to these rows. Report planned
risk percentages, actual losses beyond budget, skips, margin and stop-out events.

Three legacy controls (one per balance, 1 percent plus minimum fallback,
k=1 and 24 hour deadline) must reproduce the archived minimum-lot runs on the new
build. A January smoke test at k=10 precedes the full matrix. Archive source,
configuration, native ledgers, stats, signal hashes and report hashes. Do not
overwrite old results. Default EA settings keep the old 24 hour behavior.

## Acceptance and reporting

Compile without errors or warnings; run Python unit tests and native checks.
Fail results with EA failures, unreconciled deals, incorrect settings, unexpected
signal streams, missing native reports or unresolved positions. Validate that
initial stop distances and sizing obey the requested multiplier, that there are
no time exits in swing runs and that trails never loosen. Audit opposite exits
against completed-bar starts, holding durations, overnight/weekend exposure and
realized R using entry risk. Zero-trade and stop-out cases remain in the matrix.

Report all 150 results, not only the best variant: net return, equity drawdown,
PF, win rate, trades/week/month, monthly cash returns, costs, duration and risk.
Compare k=1 swing with the legacy deadline to isolate the deadline change, then
compare k=2..10 with k=1 swing. Strict lot floors can change the sample of trades;
minimum fallback can change monetary exposure. Neither comparison alone proves
an improved predictive edge. A selected best width is post-selection and would
need a frozen new-data test before any promotion. No automatic production or
forward trading, remote push, optimization or new strategy selection is in scope.
