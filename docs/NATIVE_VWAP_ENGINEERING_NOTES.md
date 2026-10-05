# Native VWAP engineering audit

The full strategy matrix is separate from the failed smoke attempts. No native account orders are authorized or submitted; all order paths are guarded by `MQL_TESTER`.

`PASS` in the native coordinator means that the archived tester run passed its engineering/accounting checks. It does not mean that the strategy made money or passed an edge gate. A correctly recorded losing or insolvent account is still valid negative evidence; final coverage checks distinguish an insolvency stop from an incomplete test.

## Invalid engineering runs

- `evidence/native_vwap_2026/lcv26_smoke_u_m0`: post-fill risk guard rejected a half-cent monetary conversion. US500 minimum 0.14 lot gives fractional cents, while native `OrderCalcProfit` at that volume rounds to USD cents. The corrected guard allows at most 0.005001 USD rounding. The lot budget remains floored, and this run is not a strategy result.
- `evidence/native_vwap_2026_v2/lcv27_smoke_u_m0`: the proposed 15:55 New York flatten coincided with a closed native Friday session on 16 January. The tester returned `MARKET_CLOSED` repeatedly and closed on Sunday. The intraday audit correctly rejected this result, even though its PnL was positive. The completed matrix moves the flatten to 15:45 and skips prepublished NYSE full-day holidays. Original failed exports and the prior contract are preserved.
- An initial restricted terminal launch could not use the normal MT5 profile. Only the process created by that attempt was terminated; it submitted no account orders. Subsequent tests use the original terminal profile with explicit tester configuration and local-only execution.

## Scope of the author comparison

Official release source v1.00 is preserved unchanged, with provenance and MIT license. The Market webpage version matches this source release number, but exact Market binary parity has not been established. Display-only options are disabled in the iCustom call; predictive defaults, ANN state, labels and filters are not rewritten. The unsafe-for-this-task upstream example EA is not deployed.

The [Market listing](https://www.mql5.com/en/market/product/185048) dates publication to July 2026 and describes the default features as tuned for higher, roughly 4-to-12-hour charts. Our frozen M30 comparison holds the execution timeframe constant with the existing research; it does not claim to evaluate the indicator's best timeframe or to recreate a system genuinely published before January 2026. Both facts reinforce the exploratory, retrospective verdict.

The wrapper reads closed-bar buffers online. It checks the previously observed closed bar on each next bar for start/prediction stability. The full-versus-January endpoint replay tests whether knowing the tester's future stop date changes the actually observed prefix. A separate cold-start diagnostic checks a different problem: whether restarting the stateful model in February reconstructs its previously running signals. Passing one test does not imply passing the other.

The February cold-start diagnostic subsequently passed on both symbols: 6,903 overlapping observed bars each, zero prediction/direction/start differences, and unchanged native history origin. This is positive reproducibility evidence for the tested restart, not a guarantee under every history truncation, terminal update or live calculation schedule. See [the recorded comparison](RESULT_NATIVE_VWAP_RESTART.md).

Calculation cadence is another, separate forward-test gate. In the nonvisual tester, the unchanged custom indicator is evaluated when buffers are requested; our wrapper requests them at each M30 boundary. A live indicator normally calculates on ticks, and forming-bar feature normalization is stateful in this source. Consequently, closed-bar stability and endpoint checks alone do not establish live-versus-tester parity. This study does not silently add `tester_everytick_calculate` to the author's source or claim to have certified its live cadence. The [MetaQuotes tester documentation](https://www.mql5.com/en/docs/runtime/testing) also explains that the indicator drawn after a test is calculated afresh; those final-chart arrows are not the evidence used here.

Both model paths use the same available chart prehistory within each symbol. US500 starts on 1 January 2025 at 23:00 UTC; US500_x100 starts on 15 June 2025 at 22:00 UTC. Consequently, comparing symbols is not a pure contract-multiplier experiment. For US500_x100, the modified path retains the earlier June anchor. The official indicator's historical arrows outside its processing window are not treated as observed live signals.

In the shared signal-export schema, `prediction`, `direction`, and `start` are the selected model's actual outputs; for author runs these come directly from official buffers 7, 6 and 0/1. `f1` through `f5`, `kernel`, `filter`, `atr` and boundary-tie diagnostics remain the common auxiliary causal-core calculation. They are NOT presented as an export or parity proof of the author's internal features. The common ATR supplies the identical risk/exit wrapper for both models. `online=1` identifies observed decision bars; the author output columns on historical warm-up rows are zero placeholders, not a reconstructed original-model track record.

## Exit and accounting audit

Native stops, executable bid/ask marks, commissions and swap are retained. The 0.27-point modeling reserve affects sizing/trailing and is not subtracted twice as PnL. The independent validator checks entry signal availability, tick-volume VWAP/variance, entry bands, session times, ATR stop distance, lot floor, planned risk conversion, never-loosening stops, trailing activation/width, opposite exits, and end balance against every deal.

Native tester PF and the independently calculated after-cost position PF are both retained; the readable comparison uses after-cost PF. Month tables use closed-deal cash accounting rather than month-end liquidation values. The calendar window, prior strategy selection, broker feed and current historical tester session/swap assumptions preclude an OOS or production-ready verdict.
