"""Pruebas de no fuga para las transformaciones BCIE del Articulo 4."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PIPELINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE))

from temporal_transforms import (  # noqa: E402
    compress_ngrc_temporal,
    reservoir_embedding_temporal,
    temporal_standardize,
)
from analysis_common import dm_test_by_year, paired_error_panel  # noqa: E402


class TemporalNoLeakageTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(1701)
        self.n = 48
        self.cut = 34
        self.mask = np.arange(self.n) < self.cut

    def test_standard_scaler_ignores_future_perturbations(self):
        X = self.rng.normal(size=(self.n, 3))
        X_changed = X.copy()
        X_changed[~self.mask] += 1e6
        z1, sc1 = temporal_standardize(X, self.mask, return_scaler=True)
        z2, sc2 = temporal_standardize(X_changed, self.mask, return_scaler=True)
        np.testing.assert_allclose(sc1.mean_, sc2.mean_, atol=0, rtol=0)
        np.testing.assert_allclose(sc1.scale_, sc2.scale_, atol=0, rtol=0)
        np.testing.assert_allclose(z1[self.mask], z2[self.mask], atol=1e-12)

    def test_all_ngrc_readers_ignore_future_perturbations(self):
        raw = self.rng.normal(size=(4, self.n))
        F = np.vstack([np.ones(self.n), raw])
        target = 2.0 + 0.4 * raw[0] + self.rng.normal(scale=0.02, size=self.n)
        F_changed, target_changed = F.copy(), target.copy()
        F_changed[1:, ~self.mask] += 1e5
        target_changed[~self.mask] -= 1e5

        for mode in ("baseline", "ledoitwolf", "tikhonov_covariance", "nnls_directo"):
            kwargs = dict(target=target) if mode == "nnls_directo" else {}
            kwargs_changed = dict(target=target_changed) if mode == "nnls_directo" else {}
            z1, a1 = compress_ngrc_temporal(
                F, mode=mode, fit_mask=self.mask, return_artifacts=True, **kwargs,
            )
            z2, a2 = compress_ngrc_temporal(
                F_changed, mode=mode, fit_mask=self.mask, return_artifacts=True,
                **kwargs_changed,
            )
            np.testing.assert_allclose(z1[self.mask], z2[self.mask], atol=1e-10)
            np.testing.assert_allclose(a1["scaler_mean"], a2["scaler_mean"], atol=0, rtol=0)
            np.testing.assert_allclose(a1["covariance_train"], a2["covariance_train"], atol=0, rtol=0)
            if mode == "nnls_directo":
                np.testing.assert_allclose(a1["weights"], a2["weights"], atol=1e-12)
            else:
                np.testing.assert_allclose(a1["component"], a2["component"], atol=1e-12)

    def test_reservoir_scaler_and_pca_ignore_future_perturbations(self):
        years = np.arange(1980, 1980 + self.n)
        train_end = years[self.cut - 1]
        alpha = self.rng.normal(size=(2, self.n))
        changed = alpha.copy()
        changed[:, self.cut:] += 1e4
        w_in = self.rng.normal(size=(5, 2))
        w_res = np.eye(5) * 0.4

        def causal_reservoir(a, win, wres):
            states = np.zeros((wres.shape[0], a.shape[1]))
            for t in range(a.shape[1]):
                previous = states[:, t - 1] if t else np.zeros(wres.shape[0])
                states[:, t] = np.tanh(win @ a[:, t] + wres @ previous)
            return states

        z1 = reservoir_embedding_temporal(
            alpha, years, run_reservoir=causal_reservoir, w_in=w_in, w_res=w_res,
            train_end_year=train_end,
        )
        z2 = reservoir_embedding_temporal(
            changed, years, run_reservoir=causal_reservoir, w_in=w_in, w_res=w_res,
            train_end_year=train_end,
        )
        np.testing.assert_allclose(z1[:self.cut], z2[:self.cut], atol=1e-10)

    def test_covariance_shrinkage_preserves_oriented_principal_direction(self):
        n = 80
        mask = np.arange(n) < 60
        latent = self.rng.normal(size=n)
        features = np.column_stack([
            4.0 * latent + self.rng.normal(scale=0.05, size=n),
            1.5 * latent + self.rng.normal(scale=0.10, size=n),
            self.rng.normal(scale=0.30, size=n),
        ])
        F = np.vstack([np.ones(n), features.T])
        outputs = {}
        artifacts = {}
        for mode in ("baseline", "ledoitwolf", "tikhonov_covariance"):
            outputs[mode], artifacts[mode] = compress_ngrc_temporal(
                F, mode=mode, fit_mask=mask, return_artifacts=True,
            )
        for mode in ("ledoitwolf", "tikhonov_covariance"):
            np.testing.assert_allclose(
                artifacts["baseline"]["component"], artifacts[mode]["component"],
                atol=1e-10, rtol=1e-10,
            )
            np.testing.assert_allclose(
                outputs["baseline"], outputs[mode], atol=1e-10, rtol=1e-10,
            )

    def test_inference_counts_years_not_stacked_entity_rows(self):
        panel = pd.DataFrame({
            "entity": [f"e{i}" for i in range(20)] * 5,
            "year": np.repeat(np.arange(2020, 2025), 20),
            "error_a": np.tile(np.linspace(-0.4, 0.4, 20), 5),
            "error_b": np.tile(np.linspace(-0.5, 0.5, 20), 5),
        })
        stat, pvalue, n_years, n_pairs = dm_test_by_year(panel, loss="absolute")
        self.assertEqual(n_years, 5)
        self.assertEqual(n_pairs, 100)
        self.assertTrue(np.isfinite(stat))
        self.assertGreaterEqual(pvalue, 0.0)
        self.assertLessEqual(pvalue, 1.0)

    def test_paired_losses_are_normalized_to_each_embedding_mase_scale(self):
        model_a = {"x": {"years": [2020], "y_true": [4.0], "y_pred": [2.0],
                         "MAE": 2.0, "MASE": 1.0}}
        model_b = {"x": {"years": [2020], "y_true": [2.0], "y_pred": [1.0],
                         "MAE": 1.0, "MASE": 1.0}}
        panel = paired_error_panel(model_a, model_b, ["x"])
        self.assertAlmostEqual(panel.loc[0, "error_a"], 1.0)
        self.assertAlmostEqual(panel.loc[0, "error_b"], 1.0)


if __name__ == "__main__":
    unittest.main()
