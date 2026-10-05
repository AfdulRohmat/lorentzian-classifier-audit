# Native MT5 Lorentzian and VWAP comparison

This contract tests the user's price-location hypothesis with actual MT5 Strategy Tester fills, not Python-simulated orders. It compares the existing modified causal KNN with the official author's unmodified MQL5 indicator, and filtered entries against the corresponding unfiltered model. This is exploratory research on a previously inspected period, not an unseen validation or authorization to trade an account.

## Frozen scope

- Symbols: exact Exness demo `US500` and `US500_x100`, evaluated separately.
- Timeframe: M30, retaining the established native runner timeframe. The supplied chart is M15 on Pepperstone; this experiment is not an exact replication of its chart, feed, or unidentified VWAP settings.
- Evaluation: January through August 2026 inclusive. Native real ticks, local agents only, no cloud, optimization, DLLs, or account orders. Tester USD leverage 1:400 and no added execution delay.
- Capital: USD 500, 1000, 3000. Six sizing policies: fixed broker minimum volume, or strict 1%, 2%, 3%, 4%, 5% of current closed balance. Strict policies floor to lot step and skip below minimum; never silently upgrade risk. Fixed-minimum volume is NOT a percentage risk cap.
- Matrix: 2 symbols x 2 models x 2 entry filters x 2 holding styles x 3 balances x 6 sizing policies = 288 scenarios, plus engineering controls. No further parameter search after results.

## Model comparison

The modified model retains `LorentzianCore.mqh` unchanged: mature four-bar forward labels and exact eight-neighbor selection. The author model uses the untouched indicator source from official release `mql5-v1.00`, commit `a23a2301bbad66a6136ffa4b838eceb46ae2db1f`, via `iCustom` buffers on the most recently CLOSED bar. Default predictive inputs remain unchanged; display-only controls may be disabled for tester performance. No use of the author's native exits because both models receive the same requested trailing wrapper.

The Market page advertises version 1.0 and links the official source. A locally compiled published-source version is not proven byte-identical to the downloaded Market binary or to the user's TradingView chart. Keep provenance and licensing with the source. Do not substitute a rewritten ANN and call it the original.

On the first tester quote, capture the oldest preloaded M30 bar and initialize the modified model on precisely that available history. The author indicator uses this same native chart history. Record first history timestamp and count; require them to match between paired runs. Do not calculate signals retrospectively from a chart containing the future end of the test. The author's history-window and persistent ANN behavior can make cold restarts differ from continuous operation; test this and report it rather than fixing the model silently.

## VWAP hypothesis

Session anchor is 00:00 UTC each calendar day, including all available broker M30 bars; this is an explicit research convention, not a claim about institutional value or exchange volume. Use HLC3 and broker tick volume, with weighted population standard deviation of HLC3. The live broker clock is checked against UTC before testing. Record OHLC, tick and real volumes, VWAP, sigma, and z for independent reconstruction.

At completed signal bar t:

`VWAP = sum(tick_volume * HLC3) / sum(tick_volume)`

`sigma = sqrt(sum(tick_volume * (HLC3 - VWAP)^2) / sum(tick_volume))`

`z = (close - VWAP) / sigma`

- Center: -1 < z < 1, allow either model direction.
- Lower band: -3 <= z <= -1, allow only model buys.
- Upper band: 1 <= z <= 3, allow only model sells.
- Beyond 3 sigma, missing volume, or undefined sigma: skip filtered entries.
- No filter: the identical model start without the VWAP gate.

Use only complete bars. Entry is on the next available quote; the latest bar's high/low is never used before close. The filter cannot create a new signal, delay a rejected signal for later, or reverse its direction. Raw model opposite starts still close an existing position, even if their reverse entry is VWAP-rejected. This isolates entry filtering from exit redesign. Same-side starts never pyramid or reset the stop. Resetting daily VWAP does not reset a swing position.

## Risk and exits

Common initial SL: 3 x ATR14(M30), outward rounded to the native tick grid. This is a fixed research choice giving more room than 1 ATR, not a newly optimized or proven width. The previous 1-to-10 ATR study remains separate. The existing 0.27 price-point combined sizing/trailing reserve is retained as a modeling assumption; actual native commission, swap, spread and stop execution remain in net PnL. Reserve is not double-charged as a synthetic fee.

R is the initial stop distance plus that reserve. Activate trailing at +1R, trail by 1R, tighten only using completed-M30 executable-side quotes. The native protective stop can execute on any real tick. No fixed TP. Opposite raw model start closes first; reversal requires current entry eligibility and executable sizing. Retry closed-market exits without entering stale signals.

- Swing: model entries throughout the available broker trading day, no fixed time limit; hold through sessions/weekends until stop, opposite start, or test end.
- Intraday: entries only 09:30 <= New York time < 15:30, with the signal bar itself starting no earlier than 09:30. Flatten at the first available quote at/after 15:55 New York. Use US DST rules for 2026, monitor rare missing-close/session-delay exposure. No reentry outside that window. This differs from the former 24-hour deadline and changes both entry exposure and maximum holding time.

## Engineering and evaluation

1. Pin source, check demo flat and Algo Trading disabled, freeze this plan and matrix.
2. Compile safely; smoke-test both models and symbols. Confirm real-tick coverage, buffers, settings, immutable provenance, no TP, native ledger reconciliation, volume risk, and causal signal timestamps.
3. Check filtered/unfiltered and sizing scenarios preserve identical underlying signal/VWAP streams. Independently recompute VWAP, bands, session eligibility and risk/stop/trail paths in Python from exports. Treat terminal exit alone as no proof of a valid backtest.
4. Test continuous author buffers for stability, and compare a short endpoint replay with the same prefix of the full run. A separate cold restart audit distinguishes historical redrawing from online signal availability. Do not promote author results if a material execution/reproducibility defect is unresolved.
5. Execute all 288 scenarios, retaining failures and no-trade outcomes. Record full or verified insolvency-stopped coverage; do not call a truncated profitable run complete. Native costs and equity drawdown must be reconciled.
6. Report trades, trades/week/month, net PnL, total return, arithmetic and geometric monthly returns, monthly cash PnL, PF, equity drawdown, win rate, actual initial risk, stop-outs, holding time and long/short breakdown. Monthly closed-balance returns are not month-end marked-to-market returns.
7. Compare VWAP-on versus off within each otherwise-identical configuration, and author versus modified within each symbol/style. Diagnose center/reversion/skipped directional bands, including removed profitable runners. Parameter/capital rows share history and are not independent statistical trials. Use matched daily PnL differences with day-block bootstrap as a descriptive uncertainty check, not an OOS p-value.
8. Update README and report limitations, preserve previous native work, run tests, scan staged artifacts for credentials/oversized files, commit and push this research branch. Restore the terminal with Algo Trading disabled and confirm no account positions/orders were created.

## Sources

- [Official MQL5 Market listing](https://www.mql5.com/en/market/product/185048).
- [Pinned official MQL5 release source](https://github.com/artificial-intelligence-edge/lorentzian-classification/tree/a23a2301bbad66a6136ffa4b838eceb46ae2db1f/ports/mql5).
- [TradingView VWAP documentation](https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/). The precise tick-volume weighted variance above is our frozen implementation; exact chart equivalence is not assumed.
