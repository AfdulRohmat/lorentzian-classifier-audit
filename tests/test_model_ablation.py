import json

import numpy as np
import pandas as pd

from lorentzian_audit.model_ablation import (
    brier,
    classification_metrics,
    eligible,
    forecast,
    neighbor_probabilities,
    rolling_learners,
)
from lorentzian_audit.run_v3 import ROOT
from lorentzian_audit.signals import (
    causal_knn_prediction_pair_batched,
    default_filter_mask,
    feature_kernel_outputs,
    start_events_from_predictions,
)


def settings():
    result = json.loads((ROOT / "config/contract_model_ablation.json").read_text())["training"]
    return result | {"window": 60, "minimum": 12}


def fixture():
    rng = np.random.default_rng(73)
    return rng.normal(size=(110, 5)), 100 + rng.normal(size=110).cumsum()


def test_same_pool_excludes_unmatured_and_modulo_rows():
    x, _ = fixture()
    x[19] = np.nan
    selected = eligible(x, 60, window=45)
    assert selected.min() >= 15
    assert selected.max() + 4 <= 60
    assert (selected % 4 != 0).all()
    assert 19 not in selected


def test_future_perturbation_and_prefix_invariance():
    x, close = fixture()
    before, diag, _ = rolling_learners(x, close, settings())
    altered_x, altered_close = x.copy(), close.copy()
    altered_x[71:] *= 40
    altered_close[71:] += 200
    after, _, _ = rolling_learners(altered_x, altered_close, settings())
    prefix, _, _ = rolling_learners(x[:71], close[:71], settings())
    for name in before:
        np.testing.assert_allclose(before[name][:71], after[name][:71], equal_nan=True)
        np.testing.assert_allclose(before[name][:71], prefix[name], equal_nan=True)
        p = before[name][diag[:, 0] >= settings()["minimum"]]
        np.testing.assert_allclose(p.sum(axis=1), 1)
    assert (diag[diag[:, 0] >= 12, 1] <= 0).all()


def test_prior_uses_exact_candidate_labels():
    x, close = fixture()
    result, _, _ = rolling_learners(x, close, settings())
    indices = eligible(x, 75, window=60)
    y = np.sign(close[indices + 4] - close[indices])
    np.testing.assert_allclose(result["prior"][75], [(y == side).mean() for side in (-1, 0, 1)])


def test_flat_and_single_class_fallback_not_unknown():
    x, close = fixture()
    result, diag, _ = rolling_learners(x, close * 0 + 100, settings())
    known = diag[:, 0] >= 12
    for name in result:
        assert np.isnan(result[name][~known]).all()
        np.testing.assert_array_equal(result[name][known, 1], 1)
        assert (forecast(result[name]) == 0).all()


def test_neighbor_probabilities_reproduce_batched_votes_including_ties():
    x, close = fixture()
    x[30:40] = x[25]  # Exercise distance ties using the original partition order.
    p = neighbor_probabilities(x, close, window=60)
    expected, _ = causal_knn_prediction_pair_batched(x, close, max_bars_back=60)
    votes = np.nan_to_num((p[:, 2] - p[:, 0]) * 8).astype(int)
    np.testing.assert_array_equal(votes, expected["lorentzian"])


def test_metrics_count_abstention_as_missed_class():
    p = np.array([[0.8, 0, 0.2], [0.5, 0, 0.5], [0.1, 0, 0.9]])
    truth = np.array([-1, -1, 1])
    rows = pd.DataFrame(
        {"truth": truth, "logistic_forecast": forecast(p), "logistic_brier": brier(p, truth)}
    )
    result = classification_metrics(rows, "logistic")
    assert result["short_precision"] == 1
    assert result["short_recall"] == 0.5
    assert result["balanced_accuracy_abstention_miss"] == 0.75
    assert result["coverage"] == 2 / 3
    np.testing.assert_allclose(brier(p, truth), [0.08, 0.5, 0.02])


def test_feature_filter_and_start_pipeline_prefix_invariance():
    rng = np.random.default_rng(22)
    close = 100 + rng.normal(size=320).cumsum()
    bars = pd.DataFrame(
        {"open": close + 0.1, "high": close + 1, "low": close - 1, "close": close}
    )
    full = feature_kernel_outputs(bars, 1)
    prefix = feature_kernel_outputs(bars.iloc[:220], 1)
    pd.testing.assert_frame_equal(full.iloc[:220], prefix)
    full_filter, prefix_filter = default_filter_mask(bars), default_filter_mask(bars.iloc[:220])
    np.testing.assert_array_equal(full_filter[:220], prefix_filter)
    predictions = rng.choice([-1, 0, 1], size=320)
    full_start = start_events_from_predictions(predictions, full_filter, full.kernel.to_numpy())
    prefix_start = start_events_from_predictions(
        predictions[:220], prefix_filter, prefix.kernel.to_numpy()
    )
    pd.testing.assert_frame_equal(full_start.iloc[:220], prefix_start)


def test_nan_feature_is_not_imputed_from_future_and_one_class_up():
    x, _ = fixture()
    x[60] = np.nan
    probabilities, diagnostics, _ = rolling_learners(x, np.arange(len(x)), settings())
    assert diagnostics[60, 0] == -1
    for p in probabilities.values():
        assert np.isnan(p[60]).all()
        np.testing.assert_array_equal(p[diagnostics[:, 0] >= 12, 2], 1)
