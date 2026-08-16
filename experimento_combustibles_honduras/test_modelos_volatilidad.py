"""Pruebas rapidas de causalidad, recurrencia y positividad."""
import numpy as np

from modelos_volatilidad import (
    causal_window,
    fit_nnls_nonnegative,
    fit_softplus_temporal,
    lag_features,
    make_reservoir,
    predict_softplus,
    reservoir_states,
)


def test_reservorio_es_recurrente():
    rng = np.random.RandomState(3)
    x = rng.normal(size=(12, 5))
    reservoir = make_reservoir(5, 20, seed=11)
    states = reservoir_states(x, reservoir)
    no_rec = dict(reservoir)
    no_rec["w_res"] = np.zeros_like(reservoir["w_res"])
    states_no_rec = reservoir_states(x, no_rec)
    assert np.allclose(states[0], states_no_rec[0])
    assert not np.allclose(states[1:], states_no_rec[1:])


def test_el_futuro_no_cambia_estados_pasados():
    rng = np.random.RandomState(5)
    x = rng.normal(size=(10, 4))
    reservoir = make_reservoir(4, 15, seed=2)
    before = reservoir_states(x, reservoir)
    changed = x.copy()
    changed[-1] += 1000.0
    after = reservoir_states(changed, reservoir)
    assert np.allclose(before[:-1], after[:-1])


def test_ventana_y_enlaces_son_positivos():
    rng = np.random.RandomState(13)
    returns = rng.normal(scale=0.02, size=240)
    fs, fn, fts, ftn, y, _ = causal_window(returns, 220, 150, 3)
    assert np.min(fn) >= 0
    w = fit_nnls_nonnegative(fn, y)
    assert float(ftn @ w) >= 0
    model = fit_softplus_temporal(fs, y)
    assert predict_softplus(model, fts) > 0
    assert np.min(lag_features(np.array([-2.0, 1.0, -0.5]), True)) >= 0


if __name__ == "__main__":
    test_reservorio_es_recurrente()
    test_el_futuro_no_cambia_estados_pasados()
    test_ventana_y_enlaces_son_positivos()
    print("OK: causalidad, recurrencia y positividad verificadas")
