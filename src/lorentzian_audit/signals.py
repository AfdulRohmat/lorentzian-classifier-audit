from __future__ import annotations

import math

import numpy as np
import pandas as pd
from lorentzian_classification import Bar, Settings, calculate
from lorentzian_classification.core import calc_atr, calc_regime_filter

FEATURE_COLUMNS = ["f1", "f2", "f3", "f4", "f5"]


def official_outputs(bars: pd.DataFrame, price_scale: float) -> pd.DataFrame:
    source = [
        Bar(
            time=index.isoformat(),
            open=float(row.open),
            high=float(row.high),
            low=float(row.low),
            close=float(row.close),
        )
        for index, row in bars.iterrows()
    ]
    results = calculate(source, Settings(), price_scale=price_scale)
    return pd.DataFrame(
        {
            "prediction": [row.prediction for row in results],
            "direction": [row.direction for row in results],
            "start_long": [row.buy for row in results],
            "start_short": [row.sell for row in results],
            "exit_long": [row.exit_buy for row in results],
            "exit_short": [row.exit_sell for row in results],
            "kernel": [row.kernel for row in results],
            "f1": [row.f1 for row in results],
            "f2": [row.f2 for row in results],
            "f3": [row.f3 for row in results],
            "f4": [row.f4 for row in results],
            "f5": [row.f5 for row in results],
        },
        index=bars.index,
    )


def default_filter_mask(bars: pd.DataFrame) -> np.ndarray:
    high = bars["high"].astype(float).tolist()
    low = bars["low"].astype(float).tolist()
    close = bars["close"].astype(float).tolist()
    open_ = bars["open"].astype(float).tolist()
    ohlc4 = [(open_[i] + high[i] + low[i] + close[i]) / 4.0 for i in range(len(bars))]
    atr1 = calc_atr(high, low, close, 1)
    atr10 = calc_atr(high, low, close, 10)
    abs_slope, ema_abs_slope = calc_regime_filter(ohlc4, high, low)
    mask = np.ones(len(bars), dtype=bool)
    for i in range(len(bars)):
        volatility = True
        if not math.isnan(atr1[i]) and not math.isnan(atr10[i]):
            volatility = atr1[i] > atr10[i]
        regime = True
        if ema_abs_slope[i] != 0:
            normalized = (abs_slope[i] - ema_abs_slope[i]) / ema_abs_slope[i]
            regime = normalized >= -0.1
        mask[i] = volatility and regime
    return mask


def causal_knn_predictions(
    features: np.ndarray,
    close: np.ndarray,
    metric: str,
    neighbors: int = 8,
    max_bars_back: int = 2000,
) -> tuple[np.ndarray, dict[str, int]]:
    if metric not in {"lorentzian", "euclidean"}:
        raise ValueError(f"Unsupported metric: {metric}")
    count = len(close)
    predictions = np.zeros(count, dtype=int)
    labels = np.zeros(count, dtype=int)
    labels[:-4] = np.sign(close[4:] - close[:-4]).astype(int)
    max_maturity_lag = -(10**9)
    prediction_rows = 0
    for i in range(count):
        stop = i - 3
        start = max(0, i - max_bars_back)
        if stop <= start:
            continue
        indices = np.arange(start, stop, dtype=int)
        indices = indices[indices % 4 != 0]
        finite = np.isfinite(features[indices]).all(axis=1) & np.isfinite(features[i]).all()
        indices = indices[finite]
        if len(indices) < neighbors:
            continue
        delta = features[indices] - features[i]
        if metric == "lorentzian":
            distances = np.log1p(np.abs(delta)).sum(axis=1)
        else:
            distances = np.sqrt(np.square(delta).sum(axis=1))
        order = np.lexsort((indices, distances))[:neighbors]
        selected = indices[order]
        predictions[i] = int(labels[selected].sum())
        max_maturity_lag = max(max_maturity_lag, int((selected + 4 - i).max()))
        prediction_rows += 1
    return predictions, {
        "prediction_rows": prediction_rows,
        "maximum_selected_label_maturity_minus_decision": max_maturity_lag,
    }


def start_events_from_predictions(
    predictions: np.ndarray, filter_mask: np.ndarray, kernel: np.ndarray
) -> pd.DataFrame:
    signal = 0
    starts_long = np.zeros(len(predictions), dtype=bool)
    starts_short = np.zeros(len(predictions), dtype=bool)
    directions = np.zeros(len(predictions), dtype=int)
    for i, prediction in enumerate(predictions):
        previous = signal
        if prediction > 0 and filter_mask[i]:
            signal = 1
        elif prediction < 0 and filter_mask[i]:
            signal = -1
        directions[i] = signal
        changed = signal != previous
        bullish_kernel = i >= 1 and kernel[i] > kernel[i - 1]
        bearish_kernel = i >= 1 and kernel[i] < kernel[i - 1]
        starts_long[i] = changed and signal == 1 and bullish_kernel
        starts_short[i] = changed and signal == -1 and bearish_kernel
    return pd.DataFrame(
        {
            "prediction": predictions,
            "direction": directions,
            "start_long": starts_long,
            "start_short": starts_short,
        }
    )


def build_variants(
    bars: pd.DataFrame, official: pd.DataFrame
) -> tuple[dict[str, pd.DataFrame], dict[str, dict]]:
    features = official[FEATURE_COLUMNS].to_numpy(dtype=float)
    close = bars["close"].to_numpy(dtype=float)
    kernel = official["kernel"].to_numpy(dtype=float)
    filters = default_filter_mask(bars)
    variants: dict[str, pd.DataFrame] = {
        "official_original": official[
            ["prediction", "direction", "start_long", "start_short"]
        ].copy()
    }
    diagnostics: dict[str, dict] = {}
    for name, metric in (
        ("causal_lorentzian", "lorentzian"),
        ("causal_euclidean", "euclidean"),
    ):
        predictions, diag = causal_knn_predictions(features, close, metric)
        frame = start_events_from_predictions(predictions, filters, kernel)
        frame.index = bars.index
        variants[name] = frame
        diagnostics[name] = diag

    momentum = np.zeros(len(bars), dtype=int)
    momentum[4:] = np.sign(close[4:] - close[:-4]).astype(int)
    momentum_frame = start_events_from_predictions(momentum, filters, kernel)
    momentum_frame.index = bars.index
    variants["simple_momentum4"] = momentum_frame

    kernel_direction = np.zeros(len(bars), dtype=int)
    kernel_direction[1:] = np.sign(kernel[1:] - kernel[:-1]).astype(int)
    kernel_frame = start_events_from_predictions(kernel_direction, filters, kernel)
    kernel_frame.index = bars.index
    variants["filter_only_kernel"] = kernel_frame
    diagnostics["filter_mask"] = {
        "passing_bars": int(filters.sum()),
        "total_bars": len(filters),
    }
    return variants, diagnostics
