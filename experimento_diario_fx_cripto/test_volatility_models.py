"""Pruebas minimas de las propiedades metodologicas exigidas por el Articulo 4."""
import unittest

import numpy as np

from volatility_models import (
    causal_train_slice,
    fit_nnls_nonnegative,
    fit_ridge_temporal,
    fit_standardizer,
    garch_forecast,
    make_ssrc,
    predict_nnls,
    predict_ridge,
    run_ssrc_sequence,
)


class VolatilityModelsTest(unittest.TestCase):
    def setUp(self):
        rng = np.random.RandomState(23)
        self.features = rng.normal(size=(200, 4))
        self.target = np.exp(0.2 * self.features[:, 0] + rng.normal(scale=0.1, size=200)) * 1e-4

    def test_w_res_cambia_los_estados(self):
        w_in, w_res = make_ssrc(4, 20, rho=0.95, density=0.2, seed=9)
        recurrent, _ = run_ssrc_sequence(self.features[:30], w_in, w_res, leak=0.5)
        feed_forward, _ = run_ssrc_sequence(
            self.features[:30], w_in, np.zeros_like(w_res), leak=0.5
        )
        self.assertGreater(np.max(np.abs(recurrent[1:] - feed_forward[1:])), 1e-8)

    def test_prefijo_causal_excluye_t0(self):
        values = np.arange(30)
        train = causal_train_slice(values, t0=20, window=10)
        np.testing.assert_array_equal(train, np.arange(10, 20))
        self.assertNotIn(20, train)

    def test_escalador_no_ve_futuro(self):
        prefix = self.features[:120]
        scaler_before = fit_standardizer(prefix)
        future_with_outlier = np.vstack([self.features, np.full((1, 4), 1e9)])
        scaler_after = fit_standardizer(future_with_outlier[:120])
        np.testing.assert_allclose(scaler_before.mean, scaler_after.mean)
        np.testing.assert_allclose(scaler_before.scale, scaler_after.scale)

    def test_enlaces_y_nnls_son_positivos(self):
        nonnegative = np.abs(self.features)
        nnls_model = fit_nnls_nonnegative(nonnegative[:160], self.target[:160])
        self.assertTrue(np.all(predict_nnls(nnls_model, nonnegative[160:]) >= 0))
        for link in ("log", "softplus"):
            model = fit_ridge_temporal(self.features[:160], self.target[:160], link=link)
            pred = predict_ridge(model, self.features[160:])
            self.assertTrue(np.all(pred > 0), msg=link)

    def test_lambda_ridge_pertenece_a_grilla(self):
        model = fit_ridge_temporal(self.features[:160], self.target[:160], link="log")
        self.assertIn(model["lambda_multiplier"], (1e-6, 1e-4, 1e-2, 1.0, 1e2))
        self.assertGreater(model["lambda_value"], 0)

    def test_garch_y_gjr_producen_varianza_positiva(self):
        returns = np.random.RandomState(4).normal(scale=0.01, size=250)
        for gjr in (False, True):
            forecast, status = garch_forecast(returns, gjr=gjr)
            self.assertGreater(forecast, 0, msg=status)
            self.assertTrue(np.isfinite(forecast), msg=status)


if __name__ == "__main__":
    unittest.main()
