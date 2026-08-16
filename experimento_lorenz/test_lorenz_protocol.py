"""Pruebas minimas del protocolo causal Lorenz63."""
import unittest

import numpy as np

from lorenz_common import (
    fit_ridge_fixed_ratio,
    make_ssrc,
    select_ridge_lambda_temporal,
    ssrc_states,
)


class LorenzProtocolTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.RandomState(123)
        self.X = rng.normal(size=(160, 9))
        self.y = 0.7 * self.X[:, 0] - 0.2 * self.X[:, 3] + rng.normal(0, 0.05, 160)
        self.w_in, self.w_res = make_ssrc(9, 20, rho=0.9, density=0.2, seed=11)

    def test_w_res_afecta_estados_despues_del_primer_paso(self):
        recurrent, _ = ssrc_states(self.X[:12], self.w_in, self.w_res)
        feedforward, _ = ssrc_states(self.X[:12], self.w_in, np.zeros_like(self.w_res))
        self.assertTrue(np.allclose(recurrent[0], feedforward[0]))
        self.assertGreater(float(np.max(np.abs(recurrent[1:] - feedforward[1:]))), 1e-6)

    def test_perturbacion_futura_no_cambia_estados_pasados(self):
        original, _ = ssrc_states(self.X, self.w_in, self.w_res)
        perturbed_X = self.X.copy()
        perturbed_X[100:] += 1e6
        perturbed, _ = ssrc_states(perturbed_X, self.w_in, self.w_res)
        self.assertTrue(np.array_equal(original[:100], perturbed[:100]))

    def test_lambda_seleccionada_no_usa_futuro_exterior(self):
        _, first = select_ridge_lambda_temporal(self.X[:100], self.y[:100])
        X_with_changed_future = self.X.copy()
        y_with_changed_future = self.y.copy()
        X_with_changed_future[100:] *= 1e5
        y_with_changed_future[100:] *= -1e5
        _, second = select_ridge_lambda_temporal(
            X_with_changed_future[:100], y_with_changed_future[:100]
        )
        self.assertEqual(first, second)

    def test_lambda_absoluta_responde_a_escala(self):
        _, lam_1 = fit_ridge_fixed_ratio(self.X, self.y, 0.1)
        _, lam_2 = fit_ridge_fixed_ratio(10.0 * self.X, self.y, 0.1)
        self.assertGreater(lam_2, 90.0 * lam_1)


if __name__ == "__main__":
    unittest.main()
