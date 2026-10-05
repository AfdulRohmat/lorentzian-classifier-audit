# Native US500 x100 account matrix

Run the existing causal Lorentzian M30 ATR runner directly in MT5 Strategy Tester. This is a new, explicitly authorized history anchor, not a replication of the old 2022-anchored results and not an unseen holdout. Python may orchestrate runs and summarize MT5 exports; it will not generate the PnL or simulate fills.

## Frozen configuration

- Exact broker symbol: US500_x100, M30.
- Feature and label history begins 15 June 2025; warm-up ends 31 December 2025. The connected terminal returned 6,458 warm-up bars.
- Evaluation: 1 January 2026 inclusive to 1 September 2026 exclusive. Record actual first/last ticks and any date shift.
- Deposits: USD 500, 1000 and 3000; risk per entry: 1%, 2%, 3%, 4%, 5% of current closed balance. Fifteen scenarios, not an optimizer.
- Native current symbol rules: contract 100, lot minimum/step 0.01, maximum 20; confirm within tester. Minimum-risk violation skips, never round upward. Use test leverage 1:400 as in the earlier execution audit, with actual symbol margin calculation; it is not a claim that all index margin follows account leverage.
- Freeze original classifier/entry parameters. One ATR initial SL, no fixed TP, net +1R activation and 1R completed-bar trailing distance, opposite reversal, maximum 24-hour deadline subject to available quotes.
- Retain 0.02-point exit-slippage and 0.25-point round-trip fee reserves for risk/trail math. Native tester charges and recorded fills determine PnL; these reserves do not themselves charge fees. Audit actual deal commission, fee, swap and native report costs.
- Request real ticks (model 4), zero added execution delay, local agents only, no optimization. Report real tick coverage/fallback rather than assuming 100% real ticks.
- EA hard-blocks non-tester execution. No demo/real account orders, Telegram or forward operation.

## Engineering gates

Compile and run unit tests, then a short January smoke run before all 15 full-period scenarios. Bug fixes can repair execution/reporting without tuning entry or exit rules to outcomes. Preserve failed attempts with distinct run tags. Any missing history, initialization failure, strategy failure flag, missing report or unreconciled balance invalidates that run; do not treat an incomplete run as a strategy loss.

Export native statistics, complete deal ledger, signals, entry risk and diagnostic events. Independently reconcile deposit plus deal PnL/commission/fees/swap to final tester balance, count entries/exits, inspect time range, risk breaches, margin skips, stop-outs and terminal errors. Report equity drawdown (not only closed balance drawdown), total trades, win rate, PF, frequency and all eight monthly realized returns. Do not choose the highest-return risk as a promoted allocation.

## Evidence boundaries

Eight months cannot establish cross-regime robustness. Current broker symbol costs may be applied historically by the tester. Retrospectively inspected 2026 is not pristine out of sample. Native tick trailing can differ from the Python M1 approximation. The prior classifier parity test still documents the port; this experiment prioritizes native execution rather than replacing the requested result with a Python backtest.

## User requested minimum lot variation

After the strict matrix was launched and minimum-lot skips were reported, the user explicitly requested using broker minimum volume when a 1% target cannot be met. Add three separately labeled scenarios (USD 500, 1000, 3000; 1% target plus minimum-lot fallback). Use the calculated risk-sized volume when feasible, otherwise the broker's 0.01 minimum, subject to margin/order constraints. No additional percentage ceiling was requested. Report planned actual risk distribution and how often it exceeds 1%; never label this as a strict 1% risk strategy. Preserve all original skip scenarios. This is an execution sensitivity, not a new unseen test or profit-based promotion.
