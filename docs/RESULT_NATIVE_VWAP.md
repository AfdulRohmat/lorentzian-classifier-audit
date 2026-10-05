# Native MT5 Lorentzian and VWAP results

Actual MT5 Strategy Tester runs on Exness US500 and US500_x100, January through August 2026. This is an exploratory comparison on previously inspected history, not an unseen holdout or an approval to forward/live trade.

Completed and independently re-audited: **288 scenarios plus four smoke tests**. 133 positive, 115 negative, 40 without trades. All completed native reports state 100% real ticks. Full versus January-only signal prefixes match for both models and symbols.

## What was tested

M30. Modified causal exact KNN versus the untouched official MQL5 v1.00 indicator source. Same 3 ATR14 initial stop, +1R activation and 1R trailing distance, no fixed TP, raw opposite-start exits. VWAP filters only entries: both directions within one sigma, long only from the lower 1-3 sigma region, short only from the upper 1-3 sigma region, and skip beyond three sigma. HLC3 is weighted by broker tick volume, reset at midnight UTC. No positive real-volume bars were present in this feed.

Intraday entries require a closed in-session bar and a next quote before 15:30 New York; holidays are skipped and positions flatten at 15:45. Swing entries run across broker sessions and can hold overnight/weekends. The two styles differ in both trading hours and exit horizon; only VWAP-on versus off within the SAME style isolates the filter.

Sizing 0 means fixed broker minimum volume (US500 0.14, x100 0.01), NOT a fixed percentage risk. Sizing 1-5 means a strict percentage of current closed balance with lot flooring and minimum-lot skips. Actual stop gaps, swap and commission can exceed planned risk. Current contract/session/swap settings in historical tester runs are not independent proof of historical broker execution conditions. Intraday is checked for no exposure past the daily cutoff.

## Aggregate paired filter comparison

Each row pools 18 capital/sizing pairs on the SAME history. These are correlated implementation sensitivities, not 18 independent confirmations. Positive delta means the filtered strategy beat its unfiltered counterpart, not necessarily that either is profitable.

Pairs with no executable trades can be ties; they are not evidence that a filter lacks predictive value. Consult the complete trade counts and the fixed-volume comparison rather than interpreting improved/18 as a probability of success.

| Symbol | Model | Style | VWAP improved / 18 | Median return delta pp | Median trade delta | Median DD delta pp |
|---|---|---|---:|---:|---:|---:|
| US500 | Modified | Swing | 17 | 5.57 | -97 | -23.39 |
| US500 | Modified | Intraday | 17 | 6.90 | -51 | -18.81 |
| US500 | Author | Swing | 18 | 31.01 | -191 | -29.40 |
| US500 | Author | Intraday | 0 | -10.66 | -68 | -6.86 |
| US500_x100 | Modified | Swing | 9 | 2.71 | -60 | -11.99 |
| US500_x100 | Modified | Intraday | 8 | 0.00 | -27 | -4.42 |
| US500_x100 | Author | Swing | 12 | 25.49 | -104 | -19.13 |
| US500_x100 | Author | Intraday | 3 | -1.16 | -38 | -5.92 |

## Author versus modified model

Author minus modified within the same symbol, entry filter, holding style, capital and sizing policy. These are correlated historical comparisons, not model prediction-accuracy scores.

| Symbol | VWAP | Style | Author better / 18 | Median return delta pp | Median trade delta |
|---|---|---|---:|---:|---:|
| US500 | 0 | Swing | 0 | -29.91 | 118 |
| US500 | 0 | Intraday | 18 | 6.49 | 28 |
| US500 | 1 | Swing | 1 | -5.19 | 24 |
| US500 | 1 | Intraday | 0 | -11.78 | 11 |
| US500_x100 | 0 | Swing | 5 | -2.64 | 54 |
| US500_x100 | 0 | Intraday | 3 | -3.58 | 10 |
| US500_x100 | 1 | Swing | 8 | 0.00 | 13 |
| US500_x100 | 1 | Intraday | 1 | -4.48 | 0 |

## Fixed minimum lot comparisons

The USD 3000 fixed-minimum rows keep position volume constant. They are the cleanest diagnostic here for separating the entry-location rule from percentage-compounding and minimum-size eligibility effects; the two SYMBOLS still have different exposures.

| Symbol | Model | Style | VWAP | Trades | Net USD | Return % | Net PF | Equity DD % | Trades/week | Mean USD/month | Geometric %/month |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| US500 | Modified | Swing | Off | 119 | -12.16 | -0.41 | 0.963 | 4.45 | 3.43 | -1.52 | -0.05 |
| US500 | Modified | Intraday | Off | 61 | -17.56 | -0.59 | 0.829 | 2.29 | 1.76 | -2.20 | -0.07 |
| US500 | Modified | Swing | On | 22 | 7.63 | 0.25 | 1.132 | 1.34 | 0.63 | 0.95 | 0.03 |
| US500 | Modified | Intraday | On | 10 | 10.65 | 0.35 | 1.688 | 0.55 | 0.29 | 1.33 | 0.04 |
| US500 | Author | Swing | Off | 237 | -90.43 | -3.01 | 0.855 | 5.93 | 6.83 | -11.30 | -0.38 |
| US500 | Author | Intraday | Off | 89 | -14.93 | -0.50 | 0.896 | 2.02 | 2.56 | -1.87 | -0.06 |
| US500 | Author | Swing | On | 46 | -9.40 | -0.31 | 0.932 | 1.94 | 1.33 | -1.18 | -0.04 |
| US500 | Author | Intraday | On | 21 | -18.75 | -0.62 | 0.535 | 1.14 | 0.60 | -2.34 | -0.08 |
| US500_x100 | Modified | Swing | Off | 124 | -411.28 | -13.71 | 0.839 | 27.66 | 3.57 | -51.41 | -1.83 |
| US500_x100 | Modified | Intraday | Off | 66 | -49.52 | -1.65 | 0.931 | 12.90 | 1.90 | -6.19 | -0.21 |
| US500_x100 | Modified | Swing | On | 27 | 44.02 | 1.47 | 1.091 | 8.44 | 0.78 | 5.50 | 0.18 |
| US500_x100 | Modified | Intraday | On | 16 | 143.16 | 4.77 | 2.285 | 2.88 | 0.46 | 17.89 | 0.58 |
| US500_x100 | Author | Swing | Off | 232 | -853.14 | -28.44 | 0.813 | 41.16 | 6.68 | -106.64 | -4.10 |
| US500_x100 | Author | Intraday | Off | 90 | -210.51 | -7.02 | 0.814 | 15.70 | 2.59 | -26.31 | -0.91 |
| US500_x100 | Author | Swing | On | 43 | -65.79 | -2.19 | 0.926 | 11.31 | 1.24 | -8.22 | -0.28 |
| US500_x100 | Author | Intraday | On | 20 | -131.95 | -4.40 | 0.539 | 7.89 | 0.58 | -16.49 | -0.56 |

## Uncertainty of fixed minimum lot differences

Descriptive 95% intervals from 2000 paired seven-calendar-day moving-block resamples of daily CLOSED-deal cash PnL, seed 1006. These are not independent OOS significance tests, and cash booking of multi-day positions limits interpretation. No inference that an interval excluding zero survives the wider strategy search.

| Symbol | Model | Style | Filter delta pp | Lower pp | Upper pp |
|---|---|---|---:|---:|---:|
| US500 | Modified | Swing | 0.66 | -4.13 | 4.83 |
| US500 | Modified | Intraday | 0.94 | -1.01 | 2.77 |
| US500 | Author | Swing | 2.70 | -4.00 | 8.73 |
| US500 | Author | Intraday | -0.13 | -1.88 | 1.81 |
| US500_x100 | Modified | Swing | 15.18 | -17.44 | 44.96 |
| US500_x100 | Modified | Intraday | 6.42 | -8.09 | 19.85 |
| US500_x100 | Author | Swing | 26.24 | -25.14 | 73.48 |
| US500_x100 | Author | Intraday | 2.62 | -10.81 | 16.48 |

## Baseline trades rejected by the VWAP rule

This diagnoses executed unfiltered trades at USD 3000 minimum lot. It is NOT the filtered portfolio PnL: skipping a trade can free the account for a different later signal. Positive rejected net PnL means the gate would have excluded a profitable baseline cohort.

| Symbol | Model | Style | Rejected trades | Rejected winners | Rejected net USD | Rejected winners above 3R |
|---|---|---|---:|---:|---:|---:|
| US500 | Modified | Swing | 101 | 40 | -11.27 | 4 |
| US500 | Modified | Intraday | 51 | 21 | -28.21 | 0 |
| US500 | Author | Swing | 191 | 70 | -81.03 | 5 |
| US500 | Author | Intraday | 68 | 40 | 3.82 | 0 |
| US500_x100 | Modified | Swing | 103 | 39 | -393.91 | 4 |
| US500_x100 | Modified | Intraday | 50 | 20 | -192.68 | 0 |
| US500_x100 | Author | Swing | 189 | 67 | -787.35 | 5 |
| US500_x100 | Author | Intraday | 70 | 40 | -78.56 | 0 |

## Executed filtered trade locations

USD 3000 fixed-minimum runs. This separates central entries from the hypothesized band-to-VWAP reversion entries; total strategy PnL alone cannot establish that both mechanisms work.

Distinct entry-time/direction band events across these reference runs: **1**. The same underlying event appearing on US500 and US500_x100 is not two independent confirmations. See the exact timestamps in `band_reversion_events.json`.

| Symbol | Model | Style | Location | Trades | Net USD | Mean R |
|---|---|---|---|---:|---:|---:|
| US500 | Modified | Swing | center | 22 | 7.63 | 0.174 |
| US500 | Modified | Swing | toward_vwap | 0 | 0.00 | n/a |
| US500 | Modified | Intraday | center | 10 | 10.65 | 0.157 |
| US500 | Modified | Intraday | toward_vwap | 0 | 0.00 | n/a |
| US500 | Author | Swing | center | 45 | -34.67 | -0.059 |
| US500 | Author | Swing | toward_vwap | 1 | 25.27 | 5.791 |
| US500 | Author | Intraday | center | 21 | -18.75 | -0.154 |
| US500 | Author | Intraday | toward_vwap | 0 | 0.00 | n/a |
| US500_x100 | Modified | Swing | center | 27 | 44.02 | 0.093 |
| US500_x100 | Modified | Swing | toward_vwap | 0 | 0.00 | n/a |
| US500_x100 | Modified | Intraday | center | 16 | 143.16 | 0.177 |
| US500_x100 | Modified | Intraday | toward_vwap | 0 | 0.00 | n/a |
| US500_x100 | Author | Swing | center | 42 | -246.32 | -0.061 |
| US500_x100 | Author | Swing | toward_vwap | 1 | 180.53 | 5.792 |
| US500_x100 | Author | Intraday | center | 20 | -131.95 | -0.160 |
| US500_x100 | Author | Intraday | toward_vwap | 0 | 0.00 | n/a |

## Minimum lot risk exposure

Maximum planned initial loss as percent of balance, across the eight fixed-minimum model/filter/style combinations per symbol and capital. These volumes have NO percentage ceiling. The CSV distinguishes strict-budget loss breaches from losses exceeding a 1% reference in the uncapped minimum-lot policy.

| Symbol | Starting capital | Highest planned risk % | Insolvency-stopped cases |
|---|---:|---:|---:|
| US500 | 500 | 3.25 | 0 |
| US500 | 1000 | 1.46 | 0 |
| US500 | 3000 | 0.49 | 0 |
| US500_x100 | 500 | 173.56 | 2 |
| US500_x100 | 1000 | 124.41 | 0 |
| US500_x100 | 3000 | 4.55 | 0 |

## Cross-symbol price and signal differences

Matched observed bar timestamps from USD 3000 unfiltered minimum-lot swing runs. Price feeds are similar, but the histories available before January differ, and model signals are NOT interchangeable between symbols. Counts below are descriptive; this is not a causal decomposition of history versus feed effects.

| Model | Matched bars | Open differences | High differences | Low differences | Close differences | Tick-volume differences | Prediction differences | Start differences |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Modified | 7861 | 6 | 0 | 0 | 6 | 16 | 2444 | 53 |
| Author | 7861 | 6 | 0 | 0 | 6 | 16 | 2903 | 18 |

## Complete capital and risk matrix

All 288 cases follow; do not select the best row and call it a validated setting. Net PF and win rate are recomputed from closed-position PnL AFTER commission, fees and swap, which may differ from native tester summary PF. Monthly arithmetic/geometric returns and all 2304 monthly cash records are also in the CSV evidence. They are not month-end marked-to-market returns or promised income.

A net PF of n/a means no measurable losing-position denominator (including no-trade cases), not a risk-free system. A high PF from one or a few closed trades is not robust evidence.

| Symbol | Model | Style | VWAP | Capital | Sizing | Trades | Return % | Net PF | Net WR % | Equity DD % | Trades/week | Mean USD/month | Geometric %/month |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| US500 | M | S | 0 | 500 | min | 119 | -2.43 | 0.963 | 39.50 | 23.12 | 3.43 | -1.52 | -0.31 |
| US500 | M | S | 0 | 500 | 1% | 77 | 21.91 | 1.567 | 49.35 | 7.25 | 2.22 | 13.69 | 2.51 |
| US500 | M | S | 0 | 500 | 2% | 118 | 4.44 | 1.032 | 39.83 | 31.82 | 3.40 | 2.77 | 0.54 |
| US500 | M | S | 0 | 500 | 3% | 119 | 3.19 | 1.014 | 39.50 | 44.45 | 3.43 | 1.99 | 0.39 |
| US500 | M | S | 0 | 500 | 4% | 119 | 0.36 | 1.001 | 39.50 | 54.80 | 3.43 | 0.22 | 0.04 |
| US500 | M | S | 0 | 500 | 5% | 119 | -4.50 | 0.989 | 39.50 | 63.53 | 3.43 | -2.82 | -0.57 |
| US500 | M | S | 0 | 1000 | min | 119 | -1.22 | 0.963 | 39.50 | 12.57 | 3.43 | -1.52 | -0.15 |
| US500 | M | S | 0 | 1000 | 1% | 117 | 3.98 | 1.062 | 40.17 | 16.59 | 3.37 | 4.97 | 0.49 |
| US500 | M | S | 0 | 1000 | 2% | 119 | 4.17 | 1.030 | 39.50 | 32.17 | 3.43 | 5.21 | 0.51 |
| US500 | M | S | 0 | 1000 | 3% | 119 | 2.87 | 1.013 | 39.50 | 44.72 | 3.43 | 3.59 | 0.35 |
| US500 | M | S | 0 | 1000 | 4% | 119 | 0.13 | 1.000 | 39.50 | 55.04 | 3.43 | 0.16 | 0.02 |
| US500 | M | S | 0 | 1000 | 5% | 119 | -4.95 | 0.988 | 39.50 | 63.70 | 3.43 | -6.19 | -0.63 |
| US500 | M | S | 0 | 3000 | min | 119 | -0.41 | 0.963 | 39.50 | 4.45 | 3.43 | -1.52 | -0.05 |
| US500 | M | S | 0 | 3000 | 1% | 119 | 3.11 | 1.047 | 39.50 | 17.50 | 3.43 | 11.68 | 0.38 |
| US500 | M | S | 0 | 3000 | 2% | 119 | 4.13 | 1.029 | 39.50 | 32.36 | 3.43 | 15.49 | 0.51 |
| US500 | M | S | 0 | 3000 | 3% | 119 | 2.97 | 1.013 | 39.50 | 44.81 | 3.43 | 11.14 | 0.37 |
| US500 | M | S | 0 | 3000 | 4% | 119 | -0.12 | 1.000 | 39.50 | 55.17 | 3.43 | -0.45 | -0.01 |
| US500 | M | S | 0 | 3000 | 5% | 119 | -4.96 | 0.988 | 39.50 | 63.81 | 3.43 | -18.60 | -0.63 |
| US500 | M | I | 0 | 500 | min | 61 | -3.51 | 0.829 | 42.62 | 12.74 | 1.76 | -2.20 | -0.45 |
| US500 | M | I | 0 | 500 | 1% | 29 | 1.96 | 1.302 | 44.83 | 3.96 | 0.84 | 1.23 | 0.24 |
| US500 | M | I | 0 | 500 | 2% | 61 | -2.23 | 0.940 | 42.62 | 19.97 | 1.76 | -1.39 | -0.28 |
| US500 | M | I | 0 | 500 | 3% | 61 | -3.77 | 0.934 | 42.62 | 28.67 | 1.76 | -2.36 | -0.48 |
| US500 | M | I | 0 | 500 | 4% | 61 | -5.90 | 0.925 | 42.62 | 36.60 | 1.76 | -3.69 | -0.76 |
| US500 | M | I | 0 | 500 | 5% | 61 | -7.80 | 0.923 | 42.62 | 43.53 | 1.76 | -4.88 | -1.01 |
| US500 | M | I | 0 | 1000 | min | 61 | -1.76 | 0.829 | 42.62 | 6.66 | 1.76 | -2.20 | -0.22 |
| US500 | M | I | 0 | 1000 | 1% | 61 | -0.93 | 0.948 | 42.62 | 10.43 | 1.76 | -1.16 | -0.12 |
| US500 | M | I | 0 | 1000 | 2% | 61 | -2.28 | 0.939 | 42.62 | 20.13 | 1.76 | -2.85 | -0.29 |
| US500 | M | I | 0 | 1000 | 3% | 61 | -3.96 | 0.932 | 42.62 | 28.89 | 1.76 | -4.95 | -0.50 |
| US500 | M | I | 0 | 1000 | 4% | 61 | -5.81 | 0.927 | 42.62 | 36.67 | 1.76 | -7.27 | -0.75 |
| US500 | M | I | 0 | 1000 | 5% | 61 | -8.02 | 0.921 | 42.62 | 43.73 | 1.76 | -10.03 | -1.04 |
| US500 | M | I | 0 | 3000 | min | 61 | -0.59 | 0.829 | 42.62 | 2.29 | 1.76 | -2.20 | -0.07 |
| US500 | M | I | 0 | 3000 | 1% | 61 | -0.98 | 0.946 | 42.62 | 10.60 | 1.76 | -3.68 | -0.12 |
| US500 | M | I | 0 | 3000 | 2% | 61 | -2.33 | 0.938 | 42.62 | 20.27 | 1.76 | -8.74 | -0.29 |
| US500 | M | I | 0 | 3000 | 3% | 61 | -3.91 | 0.933 | 42.62 | 28.95 | 1.76 | -14.66 | -0.50 |
| US500 | M | I | 0 | 3000 | 4% | 61 | -5.82 | 0.927 | 42.62 | 36.77 | 1.76 | -21.84 | -0.75 |
| US500 | M | I | 0 | 3000 | 5% | 61 | -7.96 | 0.922 | 42.62 | 43.80 | 1.76 | -29.87 | -1.03 |
| US500 | M | S | 1 | 500 | min | 22 | 1.53 | 1.132 | 40.91 | 7.54 | 0.63 | 0.95 | 0.19 |
| US500 | M | S | 1 | 500 | 1% | 10 | 2.46 | 1.544 | 50.00 | 3.56 | 0.29 | 1.54 | 0.30 |
| US500 | M | S | 1 | 500 | 2% | 21 | 8.41 | 1.440 | 42.86 | 11.33 | 0.60 | 5.25 | 1.01 |
| US500 | M | S | 1 | 500 | 3% | 22 | 10.35 | 1.324 | 40.91 | 18.15 | 0.63 | 6.47 | 1.24 |
| US500 | M | S | 1 | 500 | 4% | 22 | 13.12 | 1.298 | 40.91 | 23.52 | 0.63 | 8.20 | 1.55 |
| US500 | M | S | 1 | 500 | 5% | 22 | 15.44 | 1.273 | 40.91 | 28.59 | 0.63 | 9.65 | 1.81 |
| US500 | M | S | 1 | 1000 | min | 22 | 0.76 | 1.132 | 40.91 | 3.91 | 0.63 | 0.95 | 0.10 |
| US500 | M | S | 1 | 1000 | 1% | 21 | 4.26 | 1.460 | 42.86 | 5.82 | 0.60 | 5.33 | 0.52 |
| US500 | M | S | 1 | 1000 | 2% | 22 | 7.13 | 1.345 | 40.91 | 12.54 | 0.63 | 8.91 | 0.86 |
| US500 | M | S | 1 | 1000 | 3% | 22 | 10.32 | 1.322 | 40.91 | 18.23 | 0.63 | 12.90 | 1.24 |
| US500 | M | S | 1 | 1000 | 4% | 22 | 13.00 | 1.294 | 40.91 | 23.60 | 0.63 | 16.25 | 1.54 |
| US500 | M | S | 1 | 1000 | 5% | 22 | 15.43 | 1.271 | 40.91 | 28.70 | 0.63 | 19.28 | 1.81 |
| US500 | M | S | 1 | 3000 | min | 22 | 0.25 | 1.132 | 40.91 | 1.34 | 0.63 | 0.95 | 0.03 |
| US500 | M | S | 1 | 3000 | 1% | 22 | 3.69 | 1.369 | 40.91 | 6.50 | 0.63 | 13.84 | 0.45 |
| US500 | M | S | 1 | 3000 | 2% | 22 | 7.06 | 1.340 | 40.91 | 12.60 | 0.63 | 26.49 | 0.86 |
| US500 | M | S | 1 | 3000 | 3% | 22 | 10.20 | 1.317 | 40.91 | 18.32 | 0.63 | 38.25 | 1.22 |
| US500 | M | S | 1 | 3000 | 4% | 22 | 13.02 | 1.294 | 40.91 | 23.68 | 0.63 | 48.81 | 1.54 |
| US500 | M | S | 1 | 3000 | 5% | 22 | 15.51 | 1.272 | 40.91 | 28.73 | 0.63 | 58.18 | 1.82 |
| US500 | M | I | 1 | 500 | min | 10 | 2.13 | 1.688 | 50.00 | 3.15 | 0.29 | 1.33 | 0.26 |
| US500 | M | I | 1 | 500 | 1% | 3 | -0.73 | 0.228 | 33.33 | 2.27 | 0.09 | -0.46 | -0.09 |
| US500 | M | I | 1 | 500 | 2% | 10 | 2.90 | 1.543 | 50.00 | 4.54 | 0.29 | 1.81 | 0.36 |
| US500 | M | I | 1 | 500 | 3% | 10 | 4.39 | 1.543 | 50.00 | 6.74 | 0.29 | 2.74 | 0.54 |
| US500 | M | I | 1 | 500 | 4% | 10 | 5.86 | 1.532 | 50.00 | 8.88 | 0.29 | 3.67 | 0.71 |
| US500 | M | I | 1 | 500 | 5% | 10 | 7.20 | 1.513 | 50.00 | 11.09 | 0.29 | 4.50 | 0.87 |
| US500 | M | I | 1 | 1000 | min | 10 | 1.06 | 1.688 | 50.00 | 1.62 | 0.29 | 1.33 | 0.13 |
| US500 | M | I | 1 | 1000 | 1% | 10 | 1.50 | 1.579 | 50.00 | 2.29 | 0.29 | 1.88 | 0.19 |
| US500 | M | I | 1 | 1000 | 2% | 10 | 2.98 | 1.556 | 50.00 | 4.54 | 0.29 | 3.73 | 0.37 |
| US500 | M | I | 1 | 1000 | 3% | 10 | 4.46 | 1.547 | 50.00 | 6.78 | 0.29 | 5.58 | 0.55 |
| US500 | M | I | 1 | 1000 | 4% | 10 | 5.93 | 1.536 | 50.00 | 8.93 | 0.29 | 7.41 | 0.72 |
| US500 | M | I | 1 | 1000 | 5% | 10 | 7.17 | 1.510 | 50.00 | 11.10 | 0.29 | 8.96 | 0.87 |
| US500 | M | I | 1 | 3000 | min | 10 | 0.35 | 1.688 | 50.00 | 0.55 | 0.29 | 1.33 | 0.04 |
| US500 | M | I | 1 | 3000 | 1% | 10 | 1.54 | 1.586 | 50.00 | 2.31 | 0.29 | 5.79 | 0.19 |
| US500 | M | I | 1 | 3000 | 2% | 10 | 3.02 | 1.561 | 50.00 | 4.57 | 0.29 | 11.32 | 0.37 |
| US500 | M | I | 1 | 3000 | 3% | 10 | 4.48 | 1.546 | 50.00 | 6.79 | 0.29 | 16.81 | 0.55 |
| US500 | M | I | 1 | 3000 | 4% | 10 | 5.89 | 1.531 | 50.00 | 8.97 | 0.29 | 22.10 | 0.72 |
| US500 | M | I | 1 | 3000 | 5% | 10 | 7.23 | 1.513 | 50.00 | 11.09 | 0.29 | 27.10 | 0.88 |
| US500 | A | S | 0 | 500 | min | 237 | -18.09 | 0.855 | 36.29 | 32.33 | 6.83 | -11.30 | -2.46 |
| US500 | A | S | 0 | 500 | 1% | 138 | 6.88 | 1.101 | 40.58 | 14.76 | 3.98 | 4.30 | 0.83 |
| US500 | A | S | 0 | 500 | 2% | 231 | -18.65 | 0.917 | 36.36 | 43.20 | 6.65 | -11.66 | -2.55 |
| US500 | A | S | 0 | 500 | 3% | 236 | -31.89 | 0.905 | 36.44 | 57.72 | 6.80 | -19.93 | -4.69 |
| US500 | A | S | 0 | 500 | 4% | 236 | -43.80 | 0.899 | 36.44 | 68.29 | 6.80 | -27.38 | -6.95 |
| US500 | A | S | 0 | 500 | 5% | 236 | -55.28 | 0.894 | 36.44 | 76.59 | 6.80 | -34.55 | -9.57 |
| US500 | A | S | 0 | 1000 | min | 237 | -9.04 | 0.855 | 36.29 | 17.11 | 6.83 | -11.30 | -1.18 |
| US500 | A | S | 0 | 1000 | 1% | 229 | -9.13 | 0.918 | 35.81 | 25.48 | 6.60 | -11.41 | -1.19 |
| US500 | A | S | 0 | 1000 | 2% | 237 | -20.58 | 0.910 | 36.29 | 43.41 | 6.83 | -25.73 | -2.84 |
| US500 | A | S | 0 | 1000 | 3% | 237 | -32.57 | 0.903 | 36.29 | 57.78 | 6.83 | -40.72 | -4.81 |
| US500 | A | S | 0 | 1000 | 4% | 237 | -45.06 | 0.897 | 36.29 | 68.60 | 6.83 | -56.32 | -7.21 |
| US500 | A | S | 0 | 1000 | 5% | 237 | -56.73 | 0.892 | 36.29 | 76.84 | 6.83 | -70.91 | -9.94 |
| US500 | A | S | 0 | 3000 | min | 237 | -3.01 | 0.855 | 36.29 | 5.93 | 6.83 | -11.30 | -0.38 |
| US500 | A | S | 0 | 3000 | 1% | 237 | -9.10 | 0.920 | 36.29 | 24.65 | 6.83 | -34.14 | -1.19 |
| US500 | A | S | 0 | 3000 | 2% | 237 | -20.49 | 0.911 | 36.29 | 43.60 | 6.83 | -76.82 | -2.82 |
| US500 | A | S | 0 | 3000 | 3% | 237 | -33.01 | 0.902 | 36.29 | 57.97 | 6.83 | -123.77 | -4.88 |
| US500 | A | S | 0 | 3000 | 4% | 237 | -45.33 | 0.896 | 36.29 | 68.80 | 6.83 | -170.00 | -7.27 |
| US500 | A | S | 0 | 3000 | 5% | 237 | -56.92 | 0.891 | 36.29 | 76.97 | 6.83 | -213.45 | -9.99 |
| US500 | A | I | 0 | 500 | min | 89 | -2.99 | 0.896 | 55.06 | 11.29 | 2.56 | -1.87 | -0.38 |
| US500 | A | I | 0 | 500 | 1% | 41 | 8.50 | 2.097 | 58.54 | 2.52 | 1.18 | 5.31 | 1.02 |
| US500 | A | I | 0 | 500 | 2% | 87 | 0.95 | 1.020 | 54.02 | 16.60 | 2.51 | 0.59 | 0.12 |
| US500 | A | I | 0 | 500 | 3% | 89 | 2.68 | 1.034 | 55.06 | 22.32 | 2.56 | 1.68 | 0.33 |
| US500 | A | I | 0 | 500 | 4% | 89 | 3.02 | 1.028 | 55.06 | 28.74 | 2.56 | 1.89 | 0.37 |
| US500 | A | I | 0 | 500 | 5% | 89 | 3.08 | 1.021 | 55.06 | 34.65 | 2.56 | 1.92 | 0.38 |
| US500 | A | I | 0 | 1000 | min | 89 | -1.49 | 0.896 | 55.06 | 5.89 | 2.56 | -1.87 | -0.19 |
| US500 | A | I | 0 | 1000 | 1% | 86 | 0.87 | 1.038 | 54.65 | 8.30 | 2.48 | 1.09 | 0.11 |
| US500 | A | I | 0 | 1000 | 2% | 89 | 2.41 | 1.049 | 55.06 | 15.38 | 2.56 | 3.01 | 0.30 |
| US500 | A | I | 0 | 1000 | 3% | 89 | 2.97 | 1.038 | 55.06 | 22.32 | 2.56 | 3.71 | 0.37 |
| US500 | A | I | 0 | 1000 | 4% | 89 | 2.97 | 1.027 | 55.06 | 28.88 | 2.56 | 3.71 | 0.37 |
| US500 | A | I | 0 | 1000 | 5% | 89 | 2.85 | 1.020 | 55.06 | 34.79 | 2.56 | 3.56 | 0.35 |
| US500 | A | I | 0 | 3000 | min | 89 | -0.50 | 0.896 | 55.06 | 2.02 | 2.56 | -1.87 | -0.06 |
| US500 | A | I | 0 | 3000 | 1% | 89 | 1.35 | 1.057 | 55.06 | 8.02 | 2.56 | 5.04 | 0.17 |
| US500 | A | I | 0 | 3000 | 2% | 89 | 2.37 | 1.048 | 55.06 | 15.50 | 2.56 | 8.90 | 0.29 |
| US500 | A | I | 0 | 3000 | 3% | 89 | 2.93 | 1.037 | 55.06 | 22.45 | 2.56 | 10.98 | 0.36 |
| US500 | A | I | 0 | 3000 | 4% | 89 | 3.04 | 1.027 | 55.06 | 28.92 | 2.56 | 11.39 | 0.37 |
| US500 | A | I | 0 | 3000 | 5% | 89 | 2.82 | 1.019 | 55.06 | 34.91 | 2.56 | 10.58 | 0.35 |
| US500 | A | S | 1 | 500 | min | 46 | -1.88 | 0.932 | 34.78 | 10.79 | 1.33 | -1.18 | -0.24 |
| US500 | A | S | 1 | 500 | 1% | 21 | 9.39 | 1.854 | 33.33 | 5.12 | 0.60 | 5.87 | 1.13 |
| US500 | A | S | 1 | 500 | 2% | 45 | 2.93 | 1.058 | 33.33 | 17.19 | 1.30 | 1.83 | 0.36 |
| US500 | A | S | 1 | 500 | 3% | 46 | 5.04 | 1.062 | 34.78 | 24.94 | 1.33 | 3.15 | 0.62 |
| US500 | A | S | 1 | 500 | 4% | 46 | 4.86 | 1.043 | 34.78 | 31.84 | 1.33 | 3.04 | 0.59 |
| US500 | A | S | 1 | 500 | 5% | 46 | 3.58 | 1.025 | 34.78 | 38.19 | 1.33 | 2.23 | 0.44 |
| US500 | A | S | 1 | 1000 | min | 46 | -0.94 | 0.932 | 34.78 | 5.65 | 1.33 | -1.18 | -0.12 |
| US500 | A | S | 1 | 1000 | 1% | 45 | 1.94 | 1.080 | 33.33 | 9.03 | 1.30 | 2.43 | 0.24 |
| US500 | A | S | 1 | 1000 | 2% | 46 | 4.51 | 1.087 | 34.78 | 17.49 | 1.33 | 5.64 | 0.55 |
| US500 | A | S | 1 | 1000 | 3% | 46 | 5.14 | 1.063 | 34.78 | 25.04 | 1.33 | 6.43 | 0.63 |
| US500 | A | S | 1 | 1000 | 4% | 46 | 4.60 | 1.041 | 34.78 | 32.02 | 1.33 | 5.75 | 0.56 |
| US500 | A | S | 1 | 1000 | 5% | 46 | 3.46 | 1.024 | 34.78 | 38.35 | 1.33 | 4.33 | 0.43 |
| US500 | A | S | 1 | 3000 | min | 46 | -0.31 | 0.932 | 34.78 | 1.94 | 1.33 | -1.18 | -0.04 |
| US500 | A | S | 1 | 3000 | 1% | 46 | 2.69 | 1.108 | 34.78 | 9.16 | 1.33 | 10.09 | 0.33 |
| US500 | A | S | 1 | 3000 | 2% | 46 | 4.31 | 1.083 | 34.78 | 17.55 | 1.33 | 16.18 | 0.53 |
| US500 | A | S | 1 | 3000 | 3% | 46 | 5.00 | 1.061 | 34.78 | 25.17 | 1.33 | 18.75 | 0.61 |
| US500 | A | S | 1 | 3000 | 4% | 46 | 4.66 | 1.041 | 34.78 | 32.08 | 1.33 | 17.47 | 0.57 |
| US500 | A | S | 1 | 3000 | 5% | 46 | 3.39 | 1.023 | 34.78 | 38.40 | 1.33 | 12.73 | 0.42 |
| US500 | A | I | 1 | 500 | min | 21 | -3.75 | 0.535 | 42.86 | 6.67 | 0.60 | -2.34 | -0.48 |
| US500 | A | I | 1 | 500 | 1% | 5 | -0.84 | 0.340 | 40.00 | 2.02 | 0.14 | -0.53 | -0.11 |
| US500 | A | I | 1 | 500 | 2% | 20 | -6.97 | 0.433 | 40.00 | 10.13 | 0.58 | -4.35 | -0.90 |
| US500 | A | I | 1 | 500 | 3% | 21 | -9.30 | 0.500 | 42.86 | 14.96 | 0.60 | -5.81 | -1.21 |
| US500 | A | I | 1 | 500 | 4% | 21 | -12.44 | 0.500 | 42.86 | 19.57 | 0.60 | -7.78 | -1.65 |
| US500 | A | I | 1 | 500 | 5% | 21 | -15.52 | 0.501 | 42.86 | 23.96 | 0.60 | -9.70 | -2.09 |
| US500 | A | I | 1 | 1000 | min | 21 | -1.87 | 0.535 | 42.86 | 3.39 | 0.60 | -2.34 | -0.24 |
| US500 | A | I | 1 | 1000 | 1% | 20 | -3.51 | 0.431 | 40.00 | 5.18 | 0.58 | -4.39 | -0.45 |
| US500 | A | I | 1 | 1000 | 2% | 21 | -6.33 | 0.494 | 42.86 | 10.23 | 0.60 | -7.91 | -0.81 |
| US500 | A | I | 1 | 1000 | 3% | 21 | -9.40 | 0.499 | 42.86 | 15.06 | 0.60 | -11.75 | -1.23 |
| US500 | A | I | 1 | 1000 | 4% | 21 | -12.55 | 0.499 | 42.86 | 19.70 | 0.60 | -15.69 | -1.66 |
| US500 | A | I | 1 | 1000 | 5% | 21 | -15.59 | 0.501 | 42.86 | 24.10 | 0.60 | -19.49 | -2.10 |
| US500 | A | I | 1 | 3000 | min | 21 | -0.62 | 0.535 | 42.86 | 1.14 | 0.60 | -2.34 | -0.08 |
| US500 | A | I | 1 | 3000 | 1% | 21 | -3.17 | 0.495 | 42.86 | 5.25 | 0.60 | -11.90 | -0.40 |
| US500 | A | I | 1 | 3000 | 2% | 21 | -6.37 | 0.495 | 42.86 | 10.32 | 0.60 | -23.87 | -0.82 |
| US500 | A | I | 1 | 3000 | 3% | 21 | -9.47 | 0.498 | 42.86 | 15.15 | 0.60 | -35.53 | -1.24 |
| US500 | A | I | 1 | 3000 | 4% | 21 | -12.59 | 0.499 | 42.86 | 19.77 | 0.60 | -47.21 | -1.67 |
| US500 | A | I | 1 | 3000 | 5% | 21 | -15.62 | 0.502 | 42.86 | 24.16 | 0.60 | -58.57 | -2.10 |
| US500_x100 | M | S | 0 | 500 | min | 108 | -100.00 | 0.780 | 38.89 | 100.00 | 3.11 | -62.50 | n/a |
| US500_x100 | M | S | 0 | 500 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 0 | 500 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 0 | 500 | 3% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 0 | 500 | 4% | 4 | -5.43 | 0.503 | 25.00 | 11.91 | 0.12 | -3.39 | -0.70 |
| US500_x100 | M | S | 0 | 500 | 5% | 12 | -7.92 | 0.757 | 33.33 | 25.20 | 0.35 | -4.95 | -1.03 |
| US500_x100 | M | S | 0 | 1000 | min | 124 | -41.13 | 0.839 | 38.71 | 68.97 | 3.57 | -51.41 | -6.41 |
| US500_x100 | M | S | 0 | 1000 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 0 | 1000 | 2% | 7 | 0.34 | 1.034 | 28.57 | 6.59 | 0.20 | 0.42 | 0.04 |
| US500_x100 | M | S | 0 | 1000 | 3% | 57 | 13.61 | 1.164 | 40.35 | 19.75 | 1.64 | 17.01 | 1.61 |
| US500_x100 | M | S | 0 | 1000 | 4% | 87 | 36.77 | 1.224 | 42.53 | 22.56 | 2.51 | 45.97 | 3.99 |
| US500_x100 | M | S | 0 | 1000 | 5% | 95 | 9.49 | 1.047 | 41.05 | 32.12 | 2.74 | 11.87 | 1.14 |
| US500_x100 | M | S | 0 | 3000 | min | 124 | -13.71 | 0.839 | 38.71 | 27.66 | 3.57 | -51.41 | -1.83 |
| US500_x100 | M | S | 0 | 3000 | 1% | 52 | 9.22 | 1.397 | 42.31 | 6.46 | 1.50 | 34.59 | 1.11 |
| US500_x100 | M | S | 0 | 3000 | 2% | 116 | -4.89 | 0.950 | 38.79 | 23.03 | 3.34 | -18.33 | -0.62 |
| US500_x100 | M | S | 0 | 3000 | 3% | 124 | -10.07 | 0.936 | 38.71 | 32.70 | 3.57 | -37.76 | -1.32 |
| US500_x100 | M | S | 0 | 3000 | 4% | 124 | -24.97 | 0.884 | 38.71 | 47.02 | 3.57 | -93.64 | -3.53 |
| US500_x100 | M | S | 0 | 3000 | 5% | 124 | -31.76 | 0.886 | 38.71 | 56.10 | 3.57 | -119.10 | -4.66 |
| US500_x100 | M | I | 0 | 500 | min | 66 | -9.90 | 0.931 | 45.45 | 50.88 | 1.90 | -6.19 | -1.30 |
| US500_x100 | M | I | 0 | 500 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 0 | 500 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 0 | 500 | 3% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 0 | 500 | 4% | 1 | 4.94 | n/a | 100.00 | 1.68 | 0.03 | 3.09 | 0.61 |
| US500_x100 | M | I | 0 | 500 | 5% | 5 | 7.94 | 2.928 | 80.00 | 9.67 | 0.14 | 4.96 | 0.96 |
| US500_x100 | M | I | 0 | 1000 | min | 66 | -4.95 | 0.931 | 45.45 | 32.02 | 1.90 | -6.19 | -0.63 |
| US500_x100 | M | I | 0 | 1000 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 0 | 1000 | 2% | 1 | 2.47 | n/a | 100.00 | 0.85 | 0.03 | 3.09 | 0.31 |
| US500_x100 | M | I | 0 | 1000 | 3% | 25 | 11.37 | 1.954 | 48.00 | 8.40 | 0.72 | 14.22 | 1.36 |
| US500_x100 | M | I | 0 | 1000 | 4% | 40 | 14.95 | 1.537 | 47.50 | 12.99 | 1.15 | 18.69 | 1.76 |
| US500_x100 | M | I | 0 | 1000 | 5% | 54 | 1.15 | 1.018 | 44.44 | 32.72 | 1.56 | 1.43 | 0.14 |
| US500_x100 | M | I | 0 | 3000 | min | 66 | -1.65 | 0.931 | 45.45 | 12.90 | 1.90 | -6.19 | -0.21 |
| US500_x100 | M | I | 0 | 3000 | 1% | 20 | 4.17 | 2.254 | 50.00 | 2.99 | 0.58 | 15.63 | 0.51 |
| US500_x100 | M | I | 0 | 3000 | 2% | 63 | 4.19 | 1.158 | 46.03 | 14.26 | 1.81 | 15.70 | 0.51 |
| US500_x100 | M | I | 0 | 3000 | 3% | 66 | 3.77 | 1.085 | 45.45 | 21.31 | 1.90 | 14.12 | 0.46 |
| US500_x100 | M | I | 0 | 3000 | 4% | 66 | 8.41 | 1.130 | 45.45 | 27.81 | 1.90 | 31.53 | 1.01 |
| US500_x100 | M | I | 0 | 3000 | 5% | 66 | 6.20 | 1.070 | 45.45 | 36.28 | 1.90 | 23.26 | 0.76 |
| US500_x100 | M | S | 1 | 500 | min | 27 | 8.80 | 1.091 | 44.44 | 37.86 | 0.78 | 5.50 | 1.06 |
| US500_x100 | M | S | 1 | 500 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 1 | 500 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 1 | 500 | 3% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 1 | 500 | 4% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 1 | 500 | 5% | 2 | -1.81 | 0.654 | 50.00 | 10.15 | 0.06 | -1.13 | -0.23 |
| US500_x100 | M | S | 1 | 1000 | min | 27 | 4.40 | 1.091 | 44.44 | 22.31 | 0.78 | 5.50 | 0.54 |
| US500_x100 | M | S | 1 | 1000 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 1 | 1000 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | S | 1 | 1000 | 3% | 7 | 1.78 | 1.162 | 42.86 | 9.66 | 0.20 | 2.22 | 0.22 |
| US500_x100 | M | S | 1 | 1000 | 4% | 16 | 14.39 | 1.658 | 43.75 | 10.51 | 0.46 | 17.98 | 1.69 |
| US500_x100 | M | S | 1 | 1000 | 5% | 22 | 2.24 | 1.050 | 40.91 | 20.19 | 0.63 | 2.80 | 0.28 |
| US500_x100 | M | S | 1 | 3000 | min | 27 | 1.47 | 1.091 | 44.44 | 8.44 | 0.78 | 5.50 | 0.18 |
| US500_x100 | M | S | 1 | 3000 | 1% | 7 | 0.59 | 1.162 | 42.86 | 3.32 | 0.20 | 2.22 | 0.07 |
| US500_x100 | M | S | 1 | 3000 | 2% | 24 | 3.30 | 1.181 | 41.67 | 7.65 | 0.69 | 12.38 | 0.41 |
| US500_x100 | M | S | 1 | 3000 | 3% | 27 | 4.60 | 1.154 | 44.44 | 12.99 | 0.78 | 17.26 | 0.56 |
| US500_x100 | M | S | 1 | 3000 | 4% | 27 | 7.70 | 1.173 | 44.44 | 19.13 | 0.78 | 28.88 | 0.93 |
| US500_x100 | M | S | 1 | 3000 | 5% | 27 | 7.28 | 1.121 | 44.44 | 24.95 | 0.78 | 27.28 | 0.88 |
| US500_x100 | M | I | 1 | 500 | min | 16 | 28.63 | 2.285 | 62.50 | 12.97 | 0.46 | 17.89 | 3.20 |
| US500_x100 | M | I | 1 | 500 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 1 | 500 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 1 | 500 | 3% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 1 | 500 | 4% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 1 | 500 | 5% | 1 | -4.12 | 0.000 | 0.00 | 7.81 | 0.03 | -2.57 | -0.52 |
| US500_x100 | M | I | 1 | 1000 | min | 16 | 14.32 | 2.285 | 62.50 | 7.63 | 0.46 | 17.89 | 1.69 |
| US500_x100 | M | I | 1 | 1000 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 1 | 1000 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | M | I | 1 | 1000 | 3% | 4 | -1.94 | 0.217 | 25.00 | 5.84 | 0.12 | -2.42 | -0.24 |
| US500_x100 | M | I | 1 | 1000 | 4% | 7 | 6.33 | 3.557 | 57.14 | 6.71 | 0.20 | 7.91 | 0.77 |
| US500_x100 | M | I | 1 | 1000 | 5% | 10 | 1.48 | 1.125 | 50.00 | 10.30 | 0.29 | 1.85 | 0.18 |
| US500_x100 | M | I | 1 | 3000 | min | 16 | 4.77 | 2.285 | 62.50 | 2.88 | 0.46 | 17.89 | 0.58 |
| US500_x100 | M | I | 1 | 3000 | 1% | 4 | -0.65 | 0.217 | 25.00 | 1.97 | 0.12 | -2.42 | -0.08 |
| US500_x100 | M | I | 1 | 3000 | 2% | 15 | 4.59 | 2.126 | 66.67 | 3.83 | 0.43 | 17.21 | 0.56 |
| US500_x100 | M | I | 1 | 3000 | 3% | 16 | 5.57 | 1.923 | 62.50 | 5.71 | 0.46 | 20.87 | 0.68 |
| US500_x100 | M | I | 1 | 3000 | 4% | 16 | 11.19 | 2.234 | 62.50 | 7.56 | 0.46 | 41.97 | 1.33 |
| US500_x100 | M | I | 1 | 3000 | 5% | 16 | 9.64 | 1.741 | 62.50 | 10.58 | 0.46 | 36.14 | 1.16 |
| US500_x100 | A | S | 0 | 500 | min | 164 | -100.54 | 0.857 | 37.20 | 100.35 | 4.72 | -62.84 | n/a |
| US500_x100 | A | S | 0 | 500 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 0 | 500 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 0 | 500 | 3% | 2 | -4.74 | 0.000 | 0.00 | 5.14 | 0.06 | -2.97 | -0.61 |
| US500_x100 | A | S | 0 | 500 | 4% | 11 | 3.72 | 1.217 | 36.36 | 16.66 | 0.32 | 2.32 | 0.46 |
| US500_x100 | A | S | 0 | 500 | 5% | 25 | -5.31 | 0.858 | 40.00 | 24.41 | 0.72 | -3.32 | -0.68 |
| US500_x100 | A | S | 0 | 1000 | min | 198 | -98.52 | 0.764 | 34.34 | 99.40 | 5.70 | -123.16 | -40.97 |
| US500_x100 | A | S | 0 | 1000 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 0 | 1000 | 2% | 10 | 3.54 | 1.471 | 40.00 | 7.50 | 0.29 | 4.42 | 0.44 |
| US500_x100 | A | S | 0 | 1000 | 3% | 106 | 18.13 | 1.130 | 40.57 | 25.04 | 3.05 | 22.66 | 2.10 |
| US500_x100 | A | S | 0 | 1000 | 4% | 146 | -13.36 | 0.943 | 38.36 | 41.90 | 4.21 | -16.70 | -1.78 |
| US500_x100 | A | S | 0 | 1000 | 5% | 156 | -26.41 | 0.900 | 37.82 | 45.44 | 4.49 | -33.02 | -3.76 |
| US500_x100 | A | S | 0 | 3000 | min | 232 | -28.44 | 0.813 | 35.34 | 41.16 | 6.68 | -106.64 | -4.10 |
| US500_x100 | A | S | 0 | 3000 | 1% | 104 | 14.19 | 1.326 | 41.35 | 8.83 | 3.00 | 53.23 | 1.67 |
| US500_x100 | A | S | 0 | 3000 | 2% | 206 | -18.40 | 0.885 | 34.95 | 36.10 | 5.93 | -69.01 | -2.51 |
| US500_x100 | A | S | 0 | 3000 | 3% | 230 | -20.23 | 0.923 | 35.65 | 44.61 | 6.63 | -75.87 | -2.79 |
| US500_x100 | A | S | 0 | 3000 | 4% | 231 | -40.08 | 0.887 | 35.50 | 61.20 | 6.65 | -150.31 | -6.20 |
| US500_x100 | A | S | 0 | 3000 | 5% | 231 | -54.09 | 0.861 | 35.50 | 69.20 | 6.65 | -202.82 | -9.27 |
| US500_x100 | A | I | 0 | 500 | min | 90 | -42.10 | 0.814 | 54.44 | 64.98 | 2.59 | -26.31 | -6.60 |
| US500_x100 | A | I | 0 | 500 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 0 | 500 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 0 | 500 | 3% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 0 | 500 | 4% | 1 | 1.16 | n/a | 100.00 | 2.00 | 0.03 | 0.72 | 0.14 |
| US500_x100 | A | I | 0 | 500 | 5% | 13 | 18.70 | 2.440 | 69.23 | 8.97 | 0.37 | 11.69 | 2.17 |
| US500_x100 | A | I | 0 | 1000 | min | 90 | -21.05 | 0.814 | 54.44 | 39.92 | 2.59 | -26.31 | -2.91 |
| US500_x100 | A | I | 0 | 1000 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 0 | 1000 | 2% | 1 | 0.58 | n/a | 100.00 | 1.01 | 0.03 | 0.72 | 0.07 |
| US500_x100 | A | I | 0 | 1000 | 3% | 34 | 28.90 | 3.071 | 61.76 | 5.43 | 0.98 | 36.12 | 3.22 |
| US500_x100 | A | I | 0 | 1000 | 4% | 52 | 8.37 | 1.183 | 55.77 | 12.54 | 1.50 | 10.47 | 1.01 |
| US500_x100 | A | I | 0 | 1000 | 5% | 71 | -8.04 | 0.907 | 52.11 | 25.57 | 2.05 | -10.05 | -1.04 |
| US500_x100 | A | I | 0 | 3000 | min | 90 | -7.02 | 0.814 | 54.44 | 15.70 | 2.59 | -26.31 | -0.91 |
| US500_x100 | A | I | 0 | 3000 | 1% | 23 | 5.17 | 2.272 | 56.52 | 2.08 | 0.66 | 19.40 | 0.63 |
| US500_x100 | A | I | 0 | 3000 | 2% | 85 | -0.78 | 0.979 | 54.12 | 14.57 | 2.45 | -2.94 | -0.10 |
| US500_x100 | A | I | 0 | 3000 | 3% | 90 | 0.38 | 1.006 | 54.44 | 20.64 | 2.59 | 1.43 | 0.05 |
| US500_x100 | A | I | 0 | 3000 | 4% | 90 | -2.89 | 0.969 | 54.44 | 27.71 | 2.59 | -10.85 | -0.37 |
| US500_x100 | A | I | 0 | 3000 | 5% | 90 | -3.29 | 0.974 | 54.44 | 34.62 | 2.59 | -12.32 | -0.42 |
| US500_x100 | A | S | 1 | 500 | min | 43 | -13.16 | 0.926 | 34.88 | 46.63 | 1.24 | -8.22 | -1.75 |
| US500_x100 | A | S | 1 | 500 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 1 | 500 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 1 | 500 | 3% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 1 | 500 | 4% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 1 | 500 | 5% | 16 | 53.13 | 2.376 | 37.50 | 16.82 | 0.46 | 33.21 | 5.47 |
| US500_x100 | A | S | 1 | 1000 | min | 43 | -6.58 | 0.926 | 34.88 | 28.70 | 1.24 | -8.22 | -0.85 |
| US500_x100 | A | S | 1 | 1000 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 1 | 1000 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | S | 1 | 1000 | 3% | 18 | 31.97 | 2.311 | 38.89 | 10.77 | 0.52 | 39.97 | 3.53 |
| US500_x100 | A | S | 1 | 1000 | 4% | 29 | 17.07 | 1.355 | 34.48 | 18.28 | 0.84 | 21.33 | 1.99 |
| US500_x100 | A | S | 1 | 1000 | 5% | 35 | -1.59 | 0.977 | 34.29 | 23.83 | 1.01 | -1.99 | -0.20 |
| US500_x100 | A | S | 1 | 3000 | min | 43 | -2.19 | 0.926 | 34.88 | 11.31 | 1.24 | -8.22 | -0.28 |
| US500_x100 | A | S | 1 | 3000 | 1% | 14 | 11.82 | 2.903 | 42.86 | 3.98 | 0.40 | 44.31 | 1.41 |
| US500_x100 | A | S | 1 | 3000 | 2% | 42 | 7.76 | 1.215 | 33.33 | 13.77 | 1.21 | 29.09 | 0.94 |
| US500_x100 | A | S | 1 | 3000 | 3% | 43 | 10.07 | 1.171 | 34.88 | 19.69 | 1.24 | 37.77 | 1.21 |
| US500_x100 | A | S | 1 | 3000 | 4% | 43 | 8.75 | 1.102 | 34.88 | 25.74 | 1.24 | 32.83 | 1.05 |
| US500_x100 | A | S | 1 | 3000 | 5% | 43 | 8.13 | 1.070 | 34.88 | 31.92 | 1.24 | 30.51 | 0.98 |
| US500_x100 | A | I | 1 | 500 | min | 20 | -26.39 | 0.539 | 45.00 | 40.34 | 0.58 | -16.49 | -3.76 |
| US500_x100 | A | I | 1 | 500 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 1 | 500 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 1 | 500 | 3% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 1 | 500 | 4% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 1 | 500 | 5% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 1 | 1000 | min | 20 | -13.19 | 0.539 | 45.00 | 22.13 | 0.58 | -16.49 | -1.75 |
| US500_x100 | A | I | 1 | 1000 | 1% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 1 | 1000 | 2% | 0 | 0.00 | n/a | n/a | 0.00 | 0.00 | 0.00 | 0.00 |
| US500_x100 | A | I | 1 | 1000 | 3% | 4 | -2.29 | 0.320 | 25.00 | 5.41 | 0.12 | -2.86 | -0.29 |
| US500_x100 | A | I | 1 | 1000 | 4% | 7 | -4.39 | 0.412 | 42.86 | 8.13 | 0.20 | -5.49 | -0.56 |
| US500_x100 | A | I | 1 | 1000 | 5% | 12 | -9.21 | 0.371 | 41.67 | 12.34 | 0.35 | -11.51 | -1.20 |
| US500_x100 | A | I | 1 | 3000 | min | 20 | -4.40 | 0.539 | 45.00 | 7.89 | 0.58 | -16.49 | -0.56 |
| US500_x100 | A | I | 1 | 3000 | 1% | 4 | -0.76 | 0.320 | 25.00 | 1.83 | 0.12 | -2.86 | -0.10 |
| US500_x100 | A | I | 1 | 3000 | 2% | 18 | -4.02 | 0.531 | 44.44 | 7.15 | 0.52 | -15.08 | -0.51 |
| US500_x100 | A | I | 1 | 3000 | 3% | 20 | -8.16 | 0.458 | 45.00 | 12.20 | 0.58 | -30.60 | -1.06 |
| US500_x100 | A | I | 1 | 3000 | 4% | 20 | -8.51 | 0.557 | 45.00 | 15.17 | 0.58 | -31.91 | -1.11 |
| US500_x100 | A | I | 1 | 3000 | 5% | 20 | -11.99 | 0.542 | 45.00 | 21.01 | 0.58 | -44.95 | -1.58 |

## Provenance and limitations

Author source: official release `mql5-v1.00`, commit `a23a2301bbad66a6136ffa4b838eceb46ae2db1f`, compiled unchanged. It is not proven binary-identical to Market or the supplied TradingView chart. See `vendor/official_mql5/UPSTREAM.md`. Existing causal core is unchanged. Both models within each symbol start from exactly the same available native history; US500 has longer prehistory than x100, so cross-symbol differences are not attributable only to contract size.

The official source uses its own backward-window labels and stateful ANN exactly as supplied. It is materially different from the modified forward-label exact KNN. All decisions consume recorded closed-bar buffers during the chronological tester run; no final-chart arrows are used retroactively. January endpoint prefix checks and next-bar buffer stability passed, but neither proves cold-restart invariance. See the [separate restart diagnostic](RESULT_NATIVE_VWAP_RESTART.md) for that test.

Live calculation cadence is not certified: this nonvisual tester requests the official buffers once per M30 boundary, whereas live indicators normally calculate on ticks. The author's forming-bar normalization state makes that a separate parity gate, not something proven by the closed-bar checks. The official source was not modified to force a different calculation cadence. See the [engineering notes](NATIVE_VWAP_ENGINEERING_NOTES.md) and [MetaQuotes documentation](https://www.mql5.com/en/docs/runtime/testing).

There is no new unseen holdout, external-feed validation, live execution, or Telegram deployment in this study. Broker tick volume is only a feed proxy. The 3 ATR width and UTC anchor are one explicit operationalization; M15 and NY-anchored VWAP were not tested. Historical commission/session/swap fidelity and added latency remain unverified. Risk 5% and minimum lot at small capital can be highly aggressive.

The [official listing](https://www.mql5.com/en/market/product/185048) was published in July 2026 and describes feature defaults aimed at higher timeframes. This common-M30 test is not a universal verdict on that indicator or a pre-January published trading system.

Lower drawdown can partly follow mechanically from fewer trades and less market exposure. No frequency-matched random entry-gate control was run; the paired comparison measures the complete filter's historical effect, not a certified informational edge independent of exposure reduction.

## Evidence and reproduction

[Frozen plan](TECH_PLAN_NATIVE_VWAP.md), [matrix CSV](../evidence/native_vwap_2026_v3/matrix_summary.csv), [monthly CSV](../evidence/native_vwap_2026_v3/monthly_results.csv), [paired comparisons](../evidence/native_vwap_2026_v3/paired_vwap_comparison.csv), and [validation](../evidence/native_vwap_2026_v3/validated_summary.json). Immutable native deals, signal/volume exports, settings, native statistics and sanitized launch records are under each scenario. Native HTML is kept local because it can include account metadata; only its hash and real-tick quality flag are published.

Run `python scripts/report_native_vwap.py --evidence evidence/native_vwap_2026_v3 --output docs/RESULT_NATIVE_VWAP.md` with `PYTHONPATH=src;vendor` to independently regenerate this report from saved evidence. Full native replay additionally needs the broker terminal and history. No order-capable upstream example EA is deployed.
