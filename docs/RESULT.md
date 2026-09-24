# Result - Lorentzian classifier cross-asset audit v1

## Verdict

`NO_ROBUST_CROSS_ASSET_LORENTZIAN_EDGE`

The test does not support the video's implied claim that Lorentzian
classification supplies a robust cross-asset trading edge. The causally aligned
Lorentzian model was positive after modeled costs on both assets, but the gains
were statistically and economically fragile. The exact original indicator was
profitable only on XAUUSD and lost on SP500.

This verdict rejects the frozen cross-asset Lorentzian hypothesis. It does not
say that every component is useless. A preregistered classifier-free XAUUSD
control produced a materially stronger internal result and is a candidate for
a separate external-validation study.

## Data and execution

- Exness US500 and XAUUSD M1 archives were aggregated into UTC-aligned H4 bars.
- Source span: January 2022 through August 2026.
- Evaluation: January 2024 through August 2026; earlier bars provide history.
- Completed-bar signals enter at the next available H4 Bid open.
- Exit is at the next open after four signal bars, or after an earlier qualified
  opposite signal.
- Base and stress spread, slippage, and commission assumptions were frozen
  before outcomes were inspected.
- There is no stop loss, sizing, leverage, swap, or account-equity simulation.

All bps below are summed price returns relative to each trade's entry price.
For example, `+100 bps` is approximately `+1%` at one-times price notional; it
is not automatically a one-percent account return.

## Headline results after base costs

| Asset | Variant | Trades | Trades/week | Net bps | Mean bps/trade | PF | Win rate | Max DD bps | Net ex top 5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SP500 | Official original | 67 | 0.48 | -399.37 | -5.96 | 0.793 | 46.3% | 933.57 | -1,061.56 |
| SP500 | Causal Lorentzian | 89 | 0.64 | +275.17 | +3.09 | 1.128 | 47.2% | 561.41 | -733.66 |
| SP500 | Causal Euclidean | 83 | 0.60 | -29.72 | -0.36 | 0.985 | 44.6% | 537.15 | -713.40 |
| SP500 | Simple four-bar momentum | 147 | 1.06 | +47.13 | +0.32 | 1.012 | 49.7% | 864.82 | -933.66 |
| SP500 | Filter-only kernel | 145 | 1.04 | +94.17 | +0.65 | 1.025 | 50.3% | 954.28 | -918.03 |
| XAUUSD | Official original | 59 | 0.42 | +1,307.60 | +22.16 | 1.790 | 52.5% | 226.68 | +135.17 |
| XAUUSD | Causal Lorentzian | 108 | 0.78 | +317.80 | +2.94 | 1.089 | 52.8% | 1,085.20 | -633.91 |
| XAUUSD | Causal Euclidean | 105 | 0.76 | +70.55 | +0.67 | 1.019 | 48.6% | 1,118.04 | -855.07 |
| XAUUSD | Simple four-bar momentum | 126 | 0.91 | +1,769.29 | +14.04 | 1.530 | 51.6% | 466.04 | +491.41 |
| XAUUSD | Filter-only kernel | 127 | 0.91 | +2,521.07 | +19.85 | 1.767 | 51.2% | 402.69 | +735.35 |

The official default's 2,000-bar chart limit means its first executable trades
occurred only in June 2025. It therefore has 59-67 trades and is not a full
January-2024-to-August-2026 test despite sharing the declared evaluation bounds.

## Why causal Lorentzian did not pass

The nominal positive totals are not sufficient:

- SP500 had only 89 trades, below the frozen 100-trade minimum.
- Removing the five best trades changed SP500 from `+275.17` to `-733.66 bps`
  and XAUUSD from `+317.80` to `-633.91 bps`.
- The mean-calendar-month bootstrap intervals crossed zero: SP500
  `[-32.45, +46.60] bps`; XAUUSD `[-37.85, +57.80] bps`.
- Both assets lost in the frozen 2026 block: SP500 `-53.18 bps`; XAUUSD
  `-435.62 bps`.
- On identical trade windows, causal Lorentzian reached only the 69.2nd
  percentile of random directions on SP500 and the 65.6th on XAUUSD. One-sided
  random-direction p-values were approximately 0.308 and 0.344.
- Although Lorentzian beat Euclidean on both assets, it failed the incremental
  gate because simple momentum earned `+1,769.29 bps` on XAUUSD versus only
  `+317.80 bps` for Lorentzian.

Stress costs did not turn the causal totals negative (`+202.89 bps` on SP500
and `+264.06 bps` on XAUUSD), but that single passed gate cannot repair the
stability and concentration failures.

## Exact original indicator

The exact pinned implementation did not generalize across assets:

- SP500: `-399.37 bps`, PF `0.793`; the opposite direction made
  `+317.25 bps` over the same windows.
- XAUUSD: `+1,307.60 bps`, PF `1.790`; it beat the random-direction median and
  reached the 95.8th percentile, but contained only 59 trades over an effective
  June-2025-to-August-2026 sample.

This divergence is not enough to accept the original label alignment. The
source still pairs current features with the previous four-bar movement while
describing the target as the next four bars. A profitable one-asset slice does
not resolve that contract ambiguity.

## Unexpected but important XAUUSD control

The strongest result did not come from machine learning. `filter_only_kernel`
uses the slope of the causal rational-quadratic kernel estimate, gated by the
same default volatility and regime filters, then holds for four H4 bars. It
does not use Lorentzian distance, KNN, RSI, CCI, WaveTrend voting, or the
ambiguous training labels.

Its XAUUSD result was:

- 127 trades, approximately 0.91 trade/week;
- `+2,521.07 bps` after base costs and `+2,456.32 bps` under stress costs;
- PF `1.767`, win rate `51.2%`, maximum cumulative drawdown `402.69 bps`;
- `+735.35 bps` after removing the best five trades;
- positive frozen blocks: `+1,476.11 bps` in 2024-2025 and `+1,044.96 bps`
  in January-August 2026;
- mean calendar month `+78.78 bps`, bootstrap 95% interval
  `[+18.10, +152.91] bps`;
- 97.85th percentile versus 2,000 random directions on the same windows,
  one-sided p approximately `0.022`.

The four-bar momentum control was very similar: 121 of the 127 kernel-control
trades had exactly the same entry, exit, and direction. This indicates that the
interesting component is ordinary filtered H4 trend continuation, not
Lorentzian classification.

It is still not ready for forward trading. The control was declared before the
run, but selecting it because it became the strongest result creates a new
research hypothesis. It also failed to transfer to SP500, and its current
XAUUSD sample comes from one broker/feed and one UTC bar alignment.

## Annual stability

| Asset / variant | 2024 | 2025 | Jan-Aug 2026 |
|---|---:|---:|---:|
| SP500 causal Lorentzian | -55.97 | +384.32 | -53.18 |
| SP500 filter-only kernel | +565.09 | -325.76 | -145.16 |
| XAUUSD causal Lorentzian | +370.67 | +382.75 | -435.62 |
| XAUUSD simple momentum | +176.77 | +1,148.54 | +443.97 |
| XAUUSD filter-only kernel | +208.86 | +1,267.25 | +1,044.96 |

Values are after-cost bps. The concentration in XAUUSD 2025-2026 makes truly
untouched older data especially important.

## Limitations

- US500 is the broker CFD, not cash SPX or exchange-traded futures.
- UTC H4 boundaries are frozen but materially affect bar-based signals.
- The historical spread field is imperfect; cost floors and slippage are
  modeled assumptions, not synchronized executable quotes.
- Four trading bars sometimes span a weekend: maximum elapsed holding time was
  84 hours for causal XAUUSD and 60 hours for the strongest XAUUSD control.
  Swap/financing is not deducted.
- Without a stop loss, leverage and account-level ruin risk are undefined.
- No untouched external period has yet tested the newly noticed XAUUSD
  filter-only candidate.

## Engineering verification

- Unit tests: 4 passed.
- Static lint: clean.
- Independent artifact validation: 10/10 checks passed.
- Source hashes, causal-label maturity, next-bar timing, cost reconciliation,
  trade totals, non-overlap, and verdict reconciliation all passed.
- A complete second replay produced identical hashes for all six evidence
  artifacts.

The appropriate next experiment, if pursued, is not Lorentzian parameter
tuning. It is a separately frozen external validation of the simple XAUUSD H4
kernel/momentum control on untouched 2017-2021 data, with predefined bar
alignment sensitivity and explicit overnight/weekend financing treatment.

