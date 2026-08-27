"""Pruebas del escalamiento de grado general y del benchmark de Jensen.

Autor: Norman Sabillon (2026)
"""
from __future__ import annotations

from math import comb
from pathlib import Path
import sys

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
FX_DIR = HERE.parent / "experimento_diario_fx_cripto"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(FX_DIR) not in sys.path:
    sys.path.insert(0, str(FX_DIR))

from run_general_degree_scaling import (
    polynomial_feature_matrix,
    run_degree_scaling,
)
from run_jensen_smearing_benchmark import (
    apply_causal_smearing,
    normal_smearing_factor,
    summarize_smearing,
)


def _synthetic_oos_frame(n: int, sigma: float = 0.6, seed: int = 123) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    residuals = rng.normal(0.0, sigma, n)
    return pd.DataFrame(
        {
            "entity": "SYNTHETIC",
            "t0": np.arange(n),
            "mode": "ssrc_log",
            "y_test": np.exp(residuals),
            "yhat": np.ones(n),
        }
    )


def test_polynomial_feature_count_includes_all_orders_through_degree_four():
    series = np.linspace(-1.0, 1.0, 40)
    lags = 3
    degree = 4
    features = polynomial_feature_matrix(series, lags=lags, degree=degree)
    expected_columns = sum(comb(lags + order - 1, order) for order in range(1, degree + 1))
    assert features.shape == (len(series) - lags, expected_columns)
    assert np.all(np.isfinite(features))


def test_general_degree_slopes_match_two_times_degree_asymptotically():
    series = np.zeros(1200, dtype=float)
    _, slopes = run_degree_scaling(
        series,
        locations=(600,),
        magnitudes=(100.0, 200.0, 400.0, 800.0),
        signs=(-1, 1),
        degrees=(2, 3, 4),
        lags=3,
        window=300,
        n_fit=3,
    )
    for degree, group in slopes.groupby("degree"):
        assert np.allclose(group["slope"], 2 * degree, atol=2e-4)


def test_normal_smearing_factor_uses_sample_variance():
    variance, factor = normal_smearing_factor(np.array([-1.0, 0.0, 1.0]))
    assert np.isclose(variance, 1.0)
    assert np.isclose(factor, np.exp(0.5))


def test_causal_smearing_does_not_use_future_residuals():
    original = _synthetic_oos_frame(80)
    perturbed = original.copy()
    perturbed.loc[perturbed["t0"] >= 60, "y_test"] *= 1e8

    first = apply_causal_smearing(original, min_history=10)
    second = apply_causal_smearing(perturbed, min_history=10)
    columns = ["residual_variance", "smearing_factor", "yhat_smearing"]
    pd.testing.assert_frame_equal(
        first.loc[first["t0"] < 60, columns].reset_index(drop=True),
        second.loc[second["t0"] < 60, columns].reset_index(drop=True),
    )


def test_smearing_reduces_mean_qlike_for_lognormal_underprediction():
    detail = apply_causal_smearing(_synthetic_oos_frame(3000), min_history=100)
    summary = summarize_smearing(detail)
    global_row = summary.loc[summary["entity"].eq("__all__")].iloc[0]
    assert global_row["qlike_mean_smearing"] < global_row["qlike_mean_original"]
    assert global_row["mean_absolute_reduction"] > 0


def test_canonical_ssrc_benchmark_measures_qlike_reduction():
    source_path = FX_DIR / "output" / "oos_univariado.csv"
    source = pd.read_csv(source_path)
    detail = apply_causal_smearing(source, min_history=20)
    summary = summarize_smearing(detail)
    global_row = summary.loc[summary["entity"].eq("__all__")].iloc[0]
    median_series = summary.loc[summary["entity"].eq("__median_series__")].iloc[0]
    assert int(global_row["n"]) > 1000
    assert global_row["qlike_mean_smearing"] < global_row["qlike_mean_original"]
    assert int(median_series["n"]) == source.loc[source["mode"].eq("ssrc_log"), "entity"].nunique()
    assert median_series["qlike_mean_smearing"] < median_series["qlike_mean_original"]
