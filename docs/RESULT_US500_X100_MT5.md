# US500 x100 MT5 audit result

> Historical stage report: the connection blockage below was subsequently resolved. Native account simulations are now documented in [the 2026 results](RESULT_NATIVE_X100_2026.md). Preserve this report as the original parity/blocker record, not the current terminal status.

The classifier port passes identical-data verification, but the native broker backtest is blocked. This is an engineering result, not a new profitability result. No demo or real broker orders, Telegram notifications, observation mode or forward test were started.

Verdict: `CLASSIFIER_PARITY_PASS_NATIVE_EXECUTION_BLOCKED`.

## Status of the four stages

| Stage | Result | Evidence and limitation |
|---|---|---|
| 1. Symbol and account audit | Partial, connection blocked | Python initialization twice returned `-6 Terminal: Authorization failed`. An MQL script read cached metadata with `terminal_connected=0`; it is not verification of an active account. |
| 2. Native EA implementation | Implemented and compiled | Tester-only MQL5 EA; final compiler result has zero errors and warnings. Execution behavior still requires the native tests below. |
| 3. Signal parity and MT5 backtest | Signal parity passes; backtest incomplete | 53,774 archived M30 bars match. Native real-tick smoke test could not finish because the terminal was not synchronized with the trade server. No native report or trade ledger was produced. |
| 4. Reconciliation | Classifier reconciled; fills and PnL pending | Features, filters, predictions and starts match. Broker fills, commissions, swaps, risk sizing in orders and PnL cannot be reconciled without a completed native run. |

## What was actually verified

The read-only MQL parity script independently recalculated the classifier from OHLC. It did not read Python predictions as inputs. The reference covers **53,774 M30 bars from 2 January 2022 through 31 August 2026**, including warm-up history. The original trading evaluation remains January 2024 through August 2026.

- Zero mismatches in prediction, filter, direction and entry-start flags.
- All five features, ATR and kernel pass the checker's declared numerical comparison tolerance: absolute `1e-10` plus relative `1e-11`.
- Largest observed feature error: approximately `2.14e-13`; kernel error: `1.82e-12`.
- 600 long starts and 693 short starts across the **entire source history**, including warm-up. These are signal transitions, not 1,293 executed trades and not a replacement for the old 688-trade evaluation.
- Zero ambiguous nearest-neighbor boundary ties on this fixture. The EA stops for review if one appears on a different feed; Numpy's unstable tie behavior is not silently assumed reproducible.
- 17 native MQL self-checks pass: minimum-lot skipping, flooring, maximum lot, invalid steps, outward stop-grid rounding, net-R trailing formulas, Wilder warm-up, flat prices, ring wrap and full-history state reset.
- 50 Python tests pass, including parity mismatch/missing-row failure tests and tester-configuration safety checks. These tests do **not** prove broker order execution or restart recovery with an open position.

Full compressed outputs and hashes are in [the evidence directory](../evidence/us500_x100_mt5/). The old strategy contract and original trade ledger hashes are unchanged.

## Cached symbol findings

The following are cached terminal values, **not current connected-account specifications**:

| Field | Cached value | Previous sizing assumption |
|---|---:|---:|
| Contract size | 100 | 100 |
| Minimum lot | 0.01 | 0.03 |
| Lot step | 0.01 | 0.01 |
| Maximum lot | 20 | 20 |
| Tick size | 0.01 | Not verified natively |
| Tick value | 0 | Not usable for execution verification |

The lot-minimum discrepancy matters: the old small-account skip counts cannot be treated as final for the active account. We have not replaced 0.03 with 0.01 in the old study or claimed improved returns from this cache.

The cache yielded **14,319 native US500_x100 M30 bars**, starting **15 June 2025 at 22:00** and ending **31 August 2026 at 23:30**, in terminal timestamps. It does not supply the frozen January 2022 normalization anchor or the full 2024–2026 evaluation. Server-clock alignment is also not yet reconciled. Cached swap and session fields were saved for later comparison, not promoted to verified historical costs. The cache script's original error fields can include stale API errors; its `terminal_connected=0` and actual returned rows are the relevant evidence.

## Native smoke test attempt

The attempted test requested exact `US500_x100`, M30, **USD 3,000 at 1% risk**, January 2024, real-tick mode, no optimization and local agents only. This account configuration is an audit example, not a selected forward-test allocation.

The terminal logged that it was not synchronized with the trade server. The local tester agent initialized and accepted the EA, but did not produce trades or a report. The launcher stopped its own terminal after 90 seconds; the agent recorded an unexpected end of testing. This is an **incomplete infrastructure attempt**, not a zero-trade strategy result or a negative strategy verdict. Real-tick mode was requested but no claim of tick-data coverage is made.

During the audit, MT5 performed its own automatic update to build 6230 and restarted under the audit configuration. No platform update was explicitly requested by our code. Only audit-owned processes were restarted; credentials were never read or saved.

## EA rules and safety

The port retains the causal eight-neighbor Lorentzian variant, five features, volatility/regime filters and kernel-slope start confirmation. It uses closed M30 bars and reconstructs normalization from the full historical anchor. It is not a port of the original author's stateful ANN.

The native order adapter implements one position, next-bar entry, one-ATR initial stop, no fixed TP, a completed-bar trailing stop activated at net +1R with a 1R distance, opposite-signal reversal, and a 24-hour exit deadline at the next available quote. Stops are rounded outward to the symbol grid; lot size is floored from closed balance, capped at maximum and skipped below minimum. Margin, stop/freeze constraints and order checks are explicit. Missing anchor history, unexpected bar gaps, unresolved neighbor ties and execution failures are fail-closed conditions.

The EA refuses initialization and order submission outside `MQL_TESTER`. It has no network/Telegram calls. This version is **not a forward-trading EA**. A failure can leave a simulated position protected by its existing SL until the test ends; no claim of production recovery, reconnection or crash safety is made.

## Remaining execution reconciliation

These differences must be measured, not assumed away:

1. **Feed and clock:** native x100 bars versus archived regular-US500 bars; full warm-up and server time alignment.
2. **Fills and stop ordering:** native Bid/Ask ticks and server stop triggering versus the old M1 approximation. A stop may execute before the EA receives the opening tick and modifies its trail.
3. **Trail marks:** the EA uses the previous completed bar's last observed Bid/Ask quote. Python used M30 close plus a modeled spread. Missing quotes are logged and not filled using future ticks.
4. **Costs:** native deal commission/swap versus legacy reserves of 0.02 index points exit slippage and 0.25 round-trip commission. These reserves support sizing/stop math; they do not force the tester to charge those amounts.
5. **Risk and volume:** tick-grid rounding, actual minimum lot, margin and post-fill risk overshoots. Nominal 1% is not a hard gap-loss guarantee.
6. **Skipped entries:** the native state machine can encounter later signals while flat after a skipped candidate. The old conditional account simulation only sized its frozen ledger. Exact agreement with the old 548 executed / 140 skipped result is therefore not an automatic acceptance criterion.
7. **Open positions at boundaries:** native tester final liquidation, time exits across closures, partial fills, rejections and broker SL handling still need runtime evidence.

## Reproduction and next gate

See [the technical plan](TECH_PLAN_US500_X100_MT5.md) and [the MQL runbook](MT5_AUDIT_RUNBOOK.md). Python and native MQL are both required for the complete check. The original source parquet files are local research inputs and are not embedded in this repo; the compressed comparison outputs are retained.

To unblock stages three and four: sign into an MT5 account exposing the exact symbol, repeat the read-only audit, obtain the missing native history and prove anchored feature parity. If the broker cannot supply that history, agree on a new anchored research contract or clearly separate a replay-fixture execution test; do not silently shorten warm-up. Then run the bounded smoke test and full native evaluation and reconcile deal-level evidence before considering demo forward testing.

The writing review kept verified classifier results separate from cached specifications and unperformed native tests. No trading rule was tuned to improve a result during this audit.
