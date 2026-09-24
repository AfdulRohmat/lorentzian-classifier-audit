# Trade-path audit: XAUUSD versus SP500

## Answer

On the frozen Lorentzian M30 trades, XAUUSD's lower realized payoff is primarily
associated with smaller favorable excursions, especially on shorts, rather than
a substantially larger absolute giveback before exit. The evidence does not
justify blaming unusually frequent stop-outs, uniquely slow M30 trailing, or
obviously more extended gold entries. It does not yet establish an economic
cause or a profitable gold-specific modification.

This is a retrospective diagnostic of 688 SP500 and 745 XAUUSD trades, January
2024-August 2026. Original trades, entries, exits, settings and costs are unchanged.
Gold/index paths are normalized by each trade's planned initial-stop risk, R.
They are different selected entry populations, not a matched causal experiment.

## What was measured

MFE means maximum favorable excursion: the largest positive marked net R
observed while the trade is open. MAE is the adverse equivalent. Net marks use
the original entry fill, modeled spread, hypothetical exit slippage and commission.
Giveback is MFE minus realized net R. This includes losers that surrender a
small favorable move and then lose 1R; it is NOT just trailing-stop inefficiency.

M1 bars strictly before the exit minute are used, together with actual exit R
and zero. Exit-minute highs/lows are excluded because a stop may execute before
them. A separate upper bound includes that minute for intraminute stops only.
The base peak is therefore conservative and not exactly observable tick MFE.
No hindsight peak is claimed to be executable profit. Short Ask highs/lows are
approximated with the broker's one-spread-per-M1 convention, as in the runner.

## 1. The performance gap is mostly in favorable opportunity

All trades, not just winners:

| Metric | SP500 | XAUUSD |
|---|---:|---:|
| Trades | 688 | 745 |
| Mean favorable peak, conservative | 1.580R | 1.448R |
| Mean giveback from that peak | 1.474R | 1.492R |
| Mean realized result | +0.106R | -0.044R |
| Mean peak, exit-minute upper sensitivity | 1.584R | 1.451R |
| Median favorable peak | 0.912R | 0.899R |
| 90th-percentile favorable peak | 4.091R | 3.465R |
| 95th-percentile favorable peak | 5.422R | 4.431R |
| Mean peak among eventual winners | 3.302R | 2.896R |
| Mean giveback among eventual winners | 1.433R | 1.489R |
| Mean realized winner | 1.869R | 1.408R |

The identity mean(result) = mean(MFE) - mean(giveback) splits the 0.149R/trade
SP500 advantage into approximately 0.132R of larger peaks and 0.018R of lower
giveback. About 88% of this **arithmetic decomposition** is in the peak term.
This is not an estimate that 88% of the economic cause has been identified.
MFE depends on the existing stops and holding periods as well as the market.

The nearly equal median peak and more different upper quantiles are consistent
with a tail-opportunity distinction on these entries. Changing the exit-minute
assumption barely changes the result: only seven SP500 and three gold trades
have a higher favorable bound when that ambiguous minute is included.

## 2. Shorts explain the sharpest contrast

| Side | Asset | Mean peak | Mean giveback | Mean realized R |
|---|---|---:|---:|---:|
| Long | SP500 | 1.657 | 1.412 | +0.245 |
| Long | XAUUSD | 1.570 | 1.461 | +0.109 |
| Short | SP500 | 1.518 | 1.525 | -0.007 |
| Short | XAUUSD | 1.314 | 1.525 | -0.212 |

For shorts, giveback is almost identical in absolute R. Gold has substantially
less favorable movement available before its existing exit. Among activated
trails, mean realized R is 1.908 for SP500 shorts versus 1.287 for gold shorts;
mean giveback is again similar, 1.577 versus 1.584R.

Annual attribution here uses entry year; 2026 ends in August:

| Asset / side | 2024 mean R | 2025 mean R | 2026 mean R |
|---|---:|---:|---:|
| SP500 long | +0.356 | +0.223 | +0.086 |
| SP500 short | -0.140 | +0.039 | +0.133 |
| XAUUSD long | +0.081 | +0.164 | +0.063 |
| XAUUSD short | -0.224 | -0.244 | -0.151 |

This is not just one negative gold-short year. It still does not establish
long-only profitability: removing shorts changes position availability and can
change exit/reversal logic. These are contributions within the two-sided ledger.

## 3. No evidence of a uniquely bad M30 trailing observation problem in gold

| Metric | SP500 | XAUUSD |
|---|---:|---:|
| Trades reaching at least +1R before exit | 48.5% | 47.7% |
| Trailing activation | 37.8% | 39.1% |
| Touched +1R but trailing never activated | 10.8% | 8.6% |
| Mean M1 peak above completed-M30/exit peak | 0.400R | 0.408R |
| Median time to positive pre-exit peak | 40 min | 41 min |
| Median holding duration | 83.5 min | 107 min |

An intrabar +1R touch does not activate the runner unless a qualifying completed
M30 close is observed. That distinction affects both instruments and is not
worse for gold by the touch-without-activation measure. It could still matter
in an absolute sense, but these comparisons do not support it as the main
cross-asset explanation. A faster trail could also cut off future winners;
this audit does not simulate or recommend that alteration.

## 4. Fixed windows after entry: the difference survives ignoring actual exits

For separate diagnostic windows we ignore the original exits and mark the
same entry at 30, 120 and 240 clock minutes. Exact horizon quotes and >=90% M1
coverage are required. Closed-session/gap windows are flagged rather than
forward-filled. These hypothetical positions can overlap and are NOT strategy
returns or a viable hold-without-stop account simulation.

| Asset | Minutes | Valid / candidates | Mean favorable peak | Mean endpoint net R |
|---|---:|---:|---:|---:|
| SP500 | 30 | 676 / 688 | 0.641R | -0.049R |
| XAUUSD | 30 | 743 / 745 | 0.630R | -0.046R |
| SP500 | 120 | 608 / 688 | 1.405R | +0.033R |
| XAUUSD | 120 | 730 / 745 | 1.205R | -0.033R |
| SP500 | 240 | 534 / 688 | 2.043R | +0.037R |
| XAUUSD | 240 | 684 / 745 | 1.624R | -0.000R |

Thirty-minute peaks are similar; longer-window peaks are smaller for gold in
the eligible samples. Coverage differs materially, especially at four hours;
the valid cohorts also change with horizon. Therefore this is corroborating
descriptive evidence, not a clean estimate of universal follow-through speed.
It also does not imply SP500 shorts are good directional forecasts: their mean
120-minute endpoint is -0.116R despite a mean favorable peak of 1.433R.

At 120 minutes, gold shorts have a mean peak of 1.177R and endpoint -0.102R.
Across all eligible entries, +1R is touched before -1R in 254/608 SP500 windows
and 283/730 gold windows. The reverse ordering occurs in 273 and 290 windows;
81 and 156 hit neither barrier. One gold window hits both in the same minute
and is explicitly ambiguous. No within-candle ordering is invented.

Among initial-stop trades closed before the valid two-hour deadline, recovery
to +1R AFTER the exit minute occurs in:

- SP500: 57/304, or 18.8%;
- XAUUSD: 38/313, or 12.1%.

That does not support the claim that gold especially needs a wider stop because
it frequently stops out just before a strong recovery. Recovery after two hours
is outside this particular diagnostic, and losses from holding longer are not
replaced by the favorable recovery outcome.

## 5. Obvious entry lateness is not established

Median direction-aligned movement during the 120 minutes BEFORE entry is
1.892 entry-ATR for SP500 and 1.853 for gold (663/688 and 695/745 valid windows).
For shorts the medians are 1.962 and 1.851 ATR respectively. This simple measure
does not show gold entries being uniquely more extended. It cannot rule out
late entries relative to a local swing, news event or session-specific move.

## What to change next, if a new experiment is authorized

Do not change parameters from this audit alone. The more defensible next
questions concern **signal/payoff alignment and directional asymmetry**, not
immediately widening SL or speeding up the trailing clock:

1. Check whether short opportunities can be distinguished using information
   available before entry, controlling for session/volatility and sample coverage.
2. Evaluate whether predicting cost-aware trade outcomes, with an explicit
   no-trade option, is more useful than the current four-bar close-direction label.
   Labels must mature only when their actual outcomes become known.
3. Only test an exit alteration if the new hypothesis specifies how it should
   improve the joint winner/loser distribution, not just retain hindsight peaks.

Keep SP500 frozen. Any gold-specific adaptation needs a bounded contract and
chronological evaluation; this already-inspected sample cannot be rebranded as
pristine out-of-sample evidence. Session selection, broker feed differences,
normalization, regime and entry composition remain possible explanations not
identified by the present audit. No claim about macroeconomic causation is made.

## Engineering, evidence and reproduction

All original source hashes and the frozen trade ledger match. Best completed-M30
marks were reconstructed from raw data and match all original ledger values.
Both runs reproduce 1,433 paths and 4,299 fixed-window rows. All 26 tests and
repository lint pass. Unit tests cover exit-bar exclusion, Ask-side accounting,
ambiguous same-minute barriers and missing horizon/entry/coverage rejection.
The portable validator checks unchanged ledger fields, excursion bounds,
decomposition, coverage, and aggregate reconciliation.

Evidence: `evidence/trade_path_audit/` contains `paths.csv.gz`,
`shadow_windows.csv.gz`, `metrics.csv`, `annual.csv`, `shadow_metrics.csv`,
`summary.json`, source hashes and both validation artifacts.

```bash
python -m lorentzian_audit.audit_trade_paths
python -m lorentzian_audit.validate_trade_paths
python -m pytest -q
python -m ruff check src tests scripts
```

Full reconstruction needs the original M1 archives. Saved-artifact validation
does not. No strategy implementation was changed, no orders were placed, and
no external repository was published by this audit.
