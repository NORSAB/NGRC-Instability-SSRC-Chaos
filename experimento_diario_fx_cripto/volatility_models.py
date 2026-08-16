"""Componentes causales y reproducibles para el experimento diario de volatilidad.

Este modulo separa tres objetos que antes aparecian mezclados:

* regularizacion de una covarianza, que no se usa en estos lectores directos;
* regularizacion Ridge del readout, cuyo lambda se selecciona temporalmente;
* dinamica SSRC/ESN, que requiere una recurrencia explicita mediante ``W_res``.

Todas las transformaciones que aprenden parametros se ajustan exclusivamente con el
bloque de entrenamiento disponible en la ventana exterior.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import requests
from scipy.optimize import minimize, nnls


FX_SYMBOLS = {
    "MXN": "MXN=X", "BRL": "BRL=X", "COP": "COP=X", "CLP": "CLP=X",
    "PEN": "PEN=X", "ARS": "ARS=X", "GTQ": "GTQ=X",
}
CRYPTO_SYMBOLS = {"BTC": "BTC-USD", "ETH": "ETH-USD"}
ALL_SYMBOLS = {**FX_SYMBOLS, **CRYPTO_SYMBOLS}
HEADERS = {"User-Agent": "Mozilla/5.0 (research; tesis-articulo4)"}

RIDGE_MULTIPLIERS = np.array([1e-6, 1e-4, 1e-2, 1.0, 1e2], dtype=float)
QLIKE_FLOORS = (1e-12, 1e-10, 1e-8, 1e-6)


def fetch_daily_closes(symbol: str, years_back: int = 15) -> pd.Series:
    """Descarga cierres diarios sin usar observaciones posteriores al momento de descarga."""
    import time

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    period2 = int(time.time())
    period1 = period2 - years_back * 365 * 24 * 3600
    response = requests.get(
        url,
        params={"period1": period1, "period2": period2, "interval": "1d"},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()["chart"]["result"][0]
    values = data["indicators"]["quote"][0]["close"]
    series = pd.Series(values, index=pd.to_datetime(data["timestamp"], unit="s", utc=True)).dropna()
    # El endpoint puede incluir la barra diaria todavia abierta. Se excluye el dia UTC en
    # curso para no tratar un precio parcial como cierre observado.
    utc_today = pd.Timestamp.now(tz="UTC").normalize()
    return series[series.index < utc_today].tz_convert(None)


def ngrc_features(returns: np.ndarray, k: int, variant: str = "signed"):
    """Construye estados NG-RC y el retorno objetivo alineado.

    ``nonnegative`` usa valor absoluto en lineales y en todos los productos; por tanto,
    junto con NNLS garantiza un pronostico no negativo sin recorte posterior.
    ``intermediate`` conserva el signo de los productos cruzados y se mantiene solo como
    diagnostico de la especificacion anterior.
    """
    returns = np.asarray(returns, dtype=float)
    n_rows = len(returns) - k
    if n_rows < 10:
        return None, None, None
    lagged = np.array([returns[t:t + k] for t in range(n_rows)])
    if variant == "signed":
        linear = lagged
        quad_source_left = lagged
        quad_source_right = lagged
    elif variant == "intermediate":
        linear = np.abs(lagged)
        quad_source_left = lagged
        quad_source_right = lagged
    elif variant == "nonnegative":
        linear = np.abs(lagged)
        quad_source_left = np.abs(lagged)
        quad_source_right = np.abs(lagged)
    else:
        raise ValueError(f"Variante NG-RC desconocida: {variant}")
    quadratic = np.array([
        quad_source_left[:, i] * quad_source_right[:, j]
        for i in range(k) for j in range(i, k)
    ]).T
    features = np.hstack([linear, quadratic])
    target_returns = returns[k:]
    return features, target_returns ** 2, target_returns


def causal_train_slice(values: np.ndarray, t0: int, window: int) -> np.ndarray:
    """Devuelve exactamente [t0-window, t0), sin incluir la observacion a pronosticar."""
    if t0 < window or t0 > len(values):
        raise ValueError("Ventana temporal fuera de rango")
    out = np.asarray(values)[t0 - window:t0]
    if len(out) != window:
        raise AssertionError("La ventana causal no tiene la longitud solicitada")
    return out


@dataclass(frozen=True)
class Standardizer:
    mean: np.ndarray
    scale: np.ndarray

    def transform(self, values: np.ndarray) -> np.ndarray:
        return (np.asarray(values, dtype=float) - self.mean) / self.scale


def fit_standardizer(train: np.ndarray) -> Standardizer:
    train = np.asarray(train, dtype=float)
    scale = train.std(axis=0)
    scale = np.where(scale > 1e-12, scale, 1.0)
    return Standardizer(train.mean(axis=0), scale)


def _with_intercept(features: np.ndarray) -> np.ndarray:
    features = np.asarray(features, dtype=float)
    return np.column_stack([np.ones(len(features)), features])


def _ridge_beta(design: np.ndarray, target: np.ndarray, multiplier: float) -> tuple[np.ndarray, float]:
    design = np.asarray(design, dtype=float)
    target = np.asarray(target, dtype=float)
    gram = design.T @ design
    # El intercepto no se penaliza. lambda queda expresado respecto de la energia media
    # de las columnas estandarizadas, no respecto de una covarianza desplazada.
    base = float(np.trace(gram[1:, 1:]) / max(design.shape[1] - 1, 1))
    lam = max(multiplier * base, 1e-14)
    penalty = np.eye(design.shape[1])
    penalty[0, 0] = 0.0
    beta = np.linalg.solve(gram + lam * penalty, design.T @ target)
    return beta, lam


def qlike(y_true, y_pred, floor: float = 1e-10) -> float:
    true = np.maximum(np.asarray(y_true, dtype=float), floor)
    pred = np.maximum(np.asarray(y_pred, dtype=float), floor)
    ratio = true / pred
    return float(np.mean(ratio - np.log(ratio) - 1.0))


def qlike_sensitivity(y_true: float, y_pred: float,
                      floors: Iterable[float] = QLIKE_FLOORS) -> dict[str, float]:
    return {f"qlike_floor_{floor:.0e}": qlike(y_true, y_pred, floor) for floor in floors}


def _inner_cut(n: int, validation_fraction: float = 0.2) -> int:
    validation = max(40, int(round(n * validation_fraction)))
    cut = n - validation
    if cut < 80:
        raise ValueError("Se requieren al menos 120 observaciones para validacion temporal")
    return cut


def _positive_floor(train_target: np.ndarray) -> float:
    positive = np.asarray(train_target)[np.asarray(train_target) > 0]
    reference = float(np.median(positive)) if len(positive) else 1.0
    return max(reference * 1e-6, 1e-14)


def _softplus(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    return np.maximum(values, 0.0) + np.log1p(np.exp(-np.abs(values)))


def _inverse_softplus(values: np.ndarray) -> np.ndarray:
    values = np.maximum(np.asarray(values, dtype=float), 1e-12)
    return values + np.log(-np.expm1(-values))


def _encode_target(y: np.ndarray, link: str, scale: float, floor: float) -> np.ndarray:
    if link == "identity":
        return np.asarray(y, dtype=float)
    if link == "log":
        return np.log(np.asarray(y, dtype=float) + floor)
    if link == "softplus":
        return _inverse_softplus(np.asarray(y, dtype=float) / scale + floor / scale)
    raise ValueError(link)


def _decode_target(score: np.ndarray, link: str, scale: float, floor: float) -> np.ndarray:
    if link == "identity":
        return np.asarray(score, dtype=float)
    if link == "log":
        return np.maximum(np.exp(np.clip(score, -50, 50)) - floor, floor)
    if link == "softplus":
        return np.maximum(scale * _softplus(score) - floor, floor)
    raise ValueError(link)


def fit_ridge_temporal(features: np.ndarray, target: np.ndarray, link: str = "identity",
                       multipliers: np.ndarray = RIDGE_MULTIPLIERS) -> dict:
    """Selecciona lambda en el ultimo 20 % del train y reajusta en todo el train.

    El escalador de la seleccion se ajusta solo en el subbloque interior. Tras elegir el
    multiplicador, el modelo final se reajusta con la ventana exterior completa.
    """
    features = np.asarray(features, dtype=float)
    target = np.asarray(target, dtype=float)
    cut = _inner_cut(len(target))
    inner_scaler = fit_standardizer(features[:cut])
    inner_design = _with_intercept(inner_scaler.transform(features[:cut]))
    val_design = _with_intercept(inner_scaler.transform(features[cut:]))
    floor = _positive_floor(target[:cut])
    scale = max(float(np.median(target[:cut])), floor)
    encoded = _encode_target(target[:cut], link, scale, floor)
    scores = []
    for multiplier in multipliers:
        beta, _ = _ridge_beta(inner_design, encoded, float(multiplier))
        pred = _decode_target(val_design @ beta, link, scale, floor)
        if link == "identity":
            pred = np.maximum(pred, floor)
        scores.append(qlike(target[cut:], pred, floor))
    best = int(np.nanargmin(scores))

    scaler = fit_standardizer(features)
    design = _with_intercept(scaler.transform(features))
    floor = _positive_floor(target)
    scale = max(float(np.median(target)), floor)
    encoded = _encode_target(target, link, scale, floor)
    beta, lam = _ridge_beta(design, encoded, float(multipliers[best]))
    return {
        "kind": "ridge", "link": link, "scaler": scaler, "beta": beta,
        "target_scale": scale, "floor": floor,
        "lambda_multiplier": float(multipliers[best]), "lambda_value": lam,
        "validation_qlike": float(scores[best]),
    }


def predict_ridge(model: dict, features: np.ndarray) -> np.ndarray:
    values = np.atleast_2d(np.asarray(features, dtype=float))
    design = _with_intercept(model["scaler"].transform(values))
    pred = _decode_target(
        design @ model["beta"], model["link"], model["target_scale"], model["floor"]
    )
    return pred


def fit_ols(features: np.ndarray, target: np.ndarray) -> dict:
    scaler = fit_standardizer(features)
    design = _with_intercept(scaler.transform(features))
    beta, *_ = np.linalg.lstsq(design, target, rcond=None)
    return {"scaler": scaler, "beta": beta}


def predict_ols(model: dict, features: np.ndarray) -> np.ndarray:
    values = np.atleast_2d(np.asarray(features, dtype=float))
    return _with_intercept(model["scaler"].transform(values)) @ model["beta"]


def fit_nnls_nonnegative(features: np.ndarray, target: np.ndarray) -> dict:
    if np.min(features) < -1e-13:
        raise ValueError("NNLS no negativo requiere una base F >= 0")
    design = _with_intercept(features)
    beta, _ = nnls(design, target)
    return {"beta": beta}


def predict_nnls(model: dict, features: np.ndarray) -> np.ndarray:
    values = np.atleast_2d(np.asarray(features, dtype=float))
    pred = _with_intercept(values) @ model["beta"]
    if np.min(pred) < -1e-12:
        raise AssertionError("NNLS con base no negativa produjo un valor negativo")
    return np.maximum(pred, 0.0)


def fit_nnls_signed_legacy(features: np.ndarray, target: np.ndarray) -> dict:
    beta, _ = nnls(_with_intercept(features), target)
    return {"beta": beta}


def make_ssrc(d_in: int, d_res: int, rho: float = 0.95, density: float = 0.05,
              seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    w_in = rng.uniform(-1.0, 1.0, size=(d_res, d_in)) / np.sqrt(max(d_in, 1))
    w_res = rng.uniform(-1.0, 1.0, size=(d_res, d_res))
    w_res *= rng.uniform(size=w_res.shape) < density
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(w_res))))
    if spectral_radius > 0:
        w_res *= rho / spectral_radius
    return w_in, w_res


def run_ssrc_sequence(features: np.ndarray, w_in: np.ndarray, w_res: np.ndarray,
                      leak: float = 0.5, initial_state: np.ndarray | None = None):
    """Calcula estados recurrentes en orden temporal; ninguna fila futura retroalimenta otra."""
    features = np.asarray(features, dtype=float)
    state = (np.zeros(w_res.shape[0], dtype=float) if initial_state is None
             else np.asarray(initial_state, dtype=float).copy())
    states = np.empty((len(features), len(state)), dtype=float)
    for index, row in enumerate(features):
        candidate = np.tanh(w_in @ row + w_res @ state)
        state = (1.0 - leak) * state + leak * candidate
        states[index] = state
    return states, state.copy()


def fit_ssrc_temporal(features: np.ndarray, target: np.ndarray, w_in: np.ndarray,
                      w_res: np.ndarray, leak: float = 0.5,
                      multipliers: np.ndarray = RIDGE_MULTIPLIERS) -> dict:
    """SSRC recurrente con readout log-Ridge y validacion temporal interior."""
    features = np.asarray(features, dtype=float)
    target = np.asarray(target, dtype=float)
    cut = _inner_cut(len(target))

    inner_scaler = fit_standardizer(features[:cut])
    inner_all = inner_scaler.transform(features)
    inner_states, _ = run_ssrc_sequence(inner_all, w_in, w_res, leak)
    floor = _positive_floor(target[:cut])
    encoded = np.log(target[:cut] + floor)
    design_train = _with_intercept(inner_states[:cut])
    design_val = _with_intercept(inner_states[cut:])
    scores = []
    for multiplier in multipliers:
        beta, _ = _ridge_beta(design_train, encoded, float(multiplier))
        pred = np.maximum(np.exp(np.clip(design_val @ beta, -50, 50)) - floor, floor)
        scores.append(qlike(target[cut:], pred, floor))
    best = int(np.nanargmin(scores))

    scaler = fit_standardizer(features)
    states, last_state = run_ssrc_sequence(scaler.transform(features), w_in, w_res, leak)
    floor = _positive_floor(target)
    beta, lam = _ridge_beta(
        _with_intercept(states), np.log(target + floor), float(multipliers[best])
    )
    return {
        "kind": "ssrc", "scaler": scaler, "beta": beta, "w_in": w_in,
        "w_res": w_res, "leak": leak, "last_state": last_state, "floor": floor,
        "lambda_multiplier": float(multipliers[best]), "lambda_value": lam,
        "validation_qlike": float(scores[best]),
    }


def predict_ssrc(model: dict, feature: np.ndarray) -> float:
    transformed = model["scaler"].transform(np.atleast_2d(feature))
    states, _ = run_ssrc_sequence(
        transformed, model["w_in"], model["w_res"], model["leak"], model["last_state"]
    )
    score = float(np.asarray(_with_intercept(states) @ model["beta"]).ravel()[0])
    return max(float(np.exp(np.clip(score, -50, 50)) - model["floor"]), model["floor"])


def ewma_forecast(target_variance: np.ndarray, decay: float = 0.94) -> float:
    values = np.asarray(target_variance, dtype=float)
    variance = max(float(np.mean(values[:min(50, len(values))])), 1e-14)
    for value in values:
        variance = decay * variance + (1.0 - decay) * float(value)
    return max(variance, 1e-14)


def _garch_path(params: np.ndarray, returns: np.ndarray, gjr: bool) -> np.ndarray:
    omega, alpha = params[0], params[1]
    if gjr:
        gamma, beta = params[2], params[3]
    else:
        gamma, beta = 0.0, params[2]
    variance = np.empty(len(returns), dtype=float)
    variance[0] = max(float(np.var(returns)), 1e-8)
    for index in range(1, len(returns)):
        shock = returns[index - 1] ** 2
        asymmetric = gamma * shock if returns[index - 1] < 0 else 0.0
        variance[index] = max(omega + alpha * shock + asymmetric + beta * variance[index - 1], 1e-12)
    return variance


def garch_forecast(train_returns: np.ndarray, gjr: bool = False) -> tuple[float, str]:
    """Ajusta GARCH/GJR-GARCH gaussiano restringido con SciPy.

    Los retornos se escalan a puntos porcentuales para mejorar la condicion numerica. La
    prediccion vuelve a la escala original antes de regresar.
    """
    returns = np.asarray(train_returns, dtype=float) * 100.0
    unconditional = max(float(np.var(returns)), 1e-6)
    if gjr:
        initials = [
            np.array([0.03 * unconditional, 0.05, 0.05, 0.87]),
            np.array([0.08 * unconditional, 0.08, 0.02, 0.80]),
            np.array([0.15 * unconditional, 0.03, 0.10, 0.70]),
        ]
        bounds = [(1e-10, 10 * unconditional), (0.0, 0.8), (0.0, 0.8), (0.0, 0.999)]
        constraints = ({"type": "ineq", "fun": lambda p: 0.999 - p[1] - 0.5*p[2] - p[3]},)
    else:
        initials = [
            np.array([0.05 * unconditional, 0.05, 0.90]),
            np.array([0.10 * unconditional, 0.10, 0.80]),
            np.array([0.20 * unconditional, 0.03, 0.70]),
        ]
        bounds = [(1e-10, 10 * unconditional), (0.0, 0.999), (0.0, 0.999)]
        constraints = ({"type": "ineq", "fun": lambda p: 0.999 - p[1] - p[2]},)

    def objective(params):
        variance = _garch_path(params, returns, gjr)
        return float(0.5 * np.sum(np.log(variance) + returns ** 2 / variance))

    attempts = []
    for initial in initials:
        result = minimize(
            objective, initial, method="SLSQP", bounds=bounds, constraints=constraints,
            options={"maxiter": 250, "ftol": 1e-8, "disp": False},
        )
        attempts.append(result)
        if result.success:
            break
    valid = [item for item in attempts if np.all(np.isfinite(item.x)) and np.isfinite(item.fun)]
    if not valid:
        raise RuntimeError("El ajuste GARCH no produjo parametros finitos")
    successful = [item for item in valid if item.success]
    if not successful:
        messages = "; ".join(str(item.message) for item in valid)
        raise RuntimeError(f"El ajuste GARCH no convergio: {messages}")
    result = min(successful, key=lambda item: item.fun)
    params = result.x
    path = _garch_path(params, returns, gjr)
    last_shock = returns[-1] ** 2
    if gjr:
        forecast = params[0] + params[1] * last_shock + params[3] * path[-1]
        if returns[-1] < 0:
            forecast += params[2] * last_shock
    else:
        forecast = params[0] + params[1] * last_shock + params[2] * path[-1]
    return max(float(forecast) / 10000.0, 1e-14), "ok"
