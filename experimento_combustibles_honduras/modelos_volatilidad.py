"""Utilidades causales para los experimentos semanales de volatilidad.

Todas las transformaciones se ajustan con observaciones anteriores al instante
pronosticado.  El modulo distingue el Ridge del lector de cualquier
regularizacion espectral y ofrece enlaces que producen varianzas positivas.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize, nnls


EPS = 1e-12


def softplus(z):
    return np.logaddexp(0.0, np.asarray(z, dtype=float))


def sigmoid(z):
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


def qlike(y_true, y_pred, floor):
    yt = np.maximum(np.asarray(y_true, dtype=float), floor)
    yp = np.maximum(np.asarray(y_pred, dtype=float), floor)
    ratio = yt / yp
    return ratio - np.log(ratio) - 1.0


def lag_features(z_lags, nonnegative=False):
    """Constante, rezagos y bloque cuadratico para una fila.

    La base no negativa usa magnitudes y productos absolutos. Por tanto, NNLS
    sobre esa base si garantiza una prediccion no negativa.
    """
    z = np.asarray(z_lags, dtype=float)
    lin = np.abs(z) if nonnegative else z
    quad = np.array([
        abs(z[i] * z[j]) if nonnegative else z[i] * z[j]
        for i in range(len(z)) for j in range(i, len(z))
    ])
    return np.concatenate(([1.0], lin, quad))


def causal_window(log_returns, target_index, train_size, k):
    """Construye entrenamiento y prueba sin usar el retorno objetivo al escalar.

    ``target_index`` identifica el retorno cuyo cuadrado se pronostica. El
    escalador usa solamente los rezagos necesarios hasta ``target_index - 1``.
    """
    r = np.asarray(log_returns, dtype=float)
    first_target = target_index - train_size
    if first_target < k or target_index >= len(r):
        raise ValueError("ventana causal fuera de rango")
    scaler_sample = r[first_target - k:target_index]
    mu = float(np.mean(scaler_sample))
    sigma = float(np.std(scaler_sample))
    sigma = sigma if sigma > EPS else 1.0
    z = (r - mu) / sigma
    train_targets = np.arange(first_target, target_index)
    f_signed = np.vstack([lag_features(z[t - k:t], False) for t in train_targets])
    f_nonneg = np.vstack([lag_features(z[t - k:t], True) for t in train_targets])
    f_test_signed = lag_features(z[target_index - k:target_index], False)
    f_test_nonneg = lag_features(z[target_index - k:target_index], True)
    y_train = r[train_targets] ** 2
    y_test = float(r[target_index] ** 2)
    return f_signed, f_nonneg, f_test_signed, f_test_nonneg, y_train, y_test


@dataclass
class DesignScaler:
    mean_: np.ndarray
    scale_: np.ndarray

    @classmethod
    def fit(cls, x):
        x = np.asarray(x, dtype=float)
        mean = x.mean(axis=0)
        scale = x.std(axis=0)
        # La primera columna es la constante y no se centra.
        mean[0] = 0.0
        scale[0] = 1.0
        scale[scale < EPS] = 1.0
        return cls(mean, scale)

    def transform(self, x):
        return (np.asarray(x, dtype=float) - self.mean_) / self.scale_


def _ridge(x, y, lam):
    penalty = np.eye(x.shape[1])
    penalty[0, 0] = 0.0
    return np.linalg.solve(x.T @ x + lam * penalty, x.T @ y)


def _validation_split(n):
    n_val = max(15, int(round(0.2 * n)))
    n_val = min(n_val, max(1, n - 20))
    return n - n_val


def fit_ridge_temporal(x, y, link="direct", multipliers=None):
    """Selecciona lambda mediante una particion temporal interna.

    La grilla se expresa respecto del numero de observaciones despues de escalar
    las columnas con el tramo de ajuste interno; no depende de la traza, que es
    precisamente el mecanismo fragil investigado en el articulo.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    multipliers = np.logspace(-6, 2, 9) if multipliers is None else np.asarray(multipliers)
    split = _validation_split(len(y))
    xi, xv = x[:split], x[split:]
    yi, yv = y[:split], y[split:]
    scaler_i = DesignScaler.fit(xi)
    xis, xvs = scaler_i.transform(xi), scaler_i.transform(xv)
    floor_i = max(EPS, float(np.median(yi)) * 1e-4)
    target_i = np.log(yi + floor_i) if link == "log" else yi
    scored = []
    for mult in multipliers:
        lam = float(len(yi) * mult)
        try:
            w = _ridge(xis, target_i, lam)
            raw = xvs @ w
            pred = np.exp(np.clip(raw, -50, 50)) - floor_i if link == "log" else raw
            score = float(np.mean(qlike(yv, pred, floor_i)))
        except (np.linalg.LinAlgError, FloatingPointError):
            score = np.inf
        scored.append((score, float(mult)))
    _, best_mult = min(scored, key=lambda item: item[0])
    scaler = DesignScaler.fit(x)
    xs = scaler.transform(x)
    floor = max(EPS, float(np.median(y)) * 1e-4)
    target = np.log(y + floor) if link == "log" else y
    lam = float(len(y) * best_mult)
    w = _ridge(xs, target, lam)
    return {"w": w, "scaler": scaler, "lambda": lam, "link": link, "floor": floor}


def predict_ridge(model, x):
    raw = np.asarray(model["scaler"].transform(np.atleast_2d(x)) @ model["w"]).ravel()
    if model["link"] == "log":
        raw = np.exp(np.clip(raw, -50, 50)) - model["floor"]
    return float(raw[0])


def _fit_softplus_fixed(x, y, alpha, scale, start=None):
    yn = y / scale
    if start is None:
        start = np.zeros(x.shape[1])
        mean_target = max(float(np.mean(yn)), EPS)
        start[0] = np.log(np.expm1(mean_target)) if mean_target < 30 else mean_target

    def objective(w):
        z = x @ w
        pred = softplus(z)
        err = pred - yn
        penalty = np.dot(w[1:], w[1:])
        loss = float(np.mean(err ** 2) + alpha * penalty)
        grad = 2.0 * (x.T @ (err * sigmoid(z))) / len(y)
        grad[1:] += 2.0 * alpha * w[1:]
        return loss, grad

    result = minimize(objective, start, jac=True, method="L-BFGS-B", options={"maxiter": 500})
    if not result.success and not np.all(np.isfinite(result.x)):
        raise RuntimeError(f"softplus no convergio: {result.message}")
    return result.x


def fit_softplus_temporal(x, y, alphas=None):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    alphas = np.logspace(-7, 1, 7) if alphas is None else np.asarray(alphas)
    split = _validation_split(len(y))
    xi, xv = x[:split], x[split:]
    yi, yv = y[:split], y[split:]
    scaler_i = DesignScaler.fit(xi)
    xis, xvs = scaler_i.transform(xi), scaler_i.transform(xv)
    scale_i = max(float(np.median(yi)), EPS)
    floor_i = max(EPS, scale_i * 1e-4)
    scored = []
    for alpha in alphas:
        try:
            w = _fit_softplus_fixed(xis, yi, float(alpha), scale_i)
            pred = scale_i * softplus(xvs @ w)
            score = float(np.mean(qlike(yv, pred, floor_i)))
        except Exception:
            score = np.inf
        scored.append((score, float(alpha)))
    _, best_alpha = min(scored, key=lambda item: item[0])
    scaler = DesignScaler.fit(x)
    xs = scaler.transform(x)
    scale = max(float(np.median(y)), EPS)
    w = _fit_softplus_fixed(xs, y, best_alpha, scale)
    return {"w": w, "scaler": scaler, "alpha": best_alpha, "scale": scale}


def predict_softplus(model, x):
    xs = model["scaler"].transform(np.atleast_2d(x))
    return float(model["scale"] * softplus(xs @ model["w"])[0])


def fit_nnls_nonnegative(x, y):
    if np.min(x) < -EPS:
        raise AssertionError("la base de NNLS debe ser no negativa")
    w, _ = nnls(np.asarray(x, dtype=float), np.asarray(y, dtype=float))
    return w


def make_reservoir(d_in, d_res, rho=0.9, density=0.1, leak=0.7, seed=7):
    rng = np.random.RandomState(seed)
    w_in = rng.uniform(-1.0, 1.0, size=(d_res, d_in)) / np.sqrt(max(d_in, 1))
    w_res = rng.uniform(-1.0, 1.0, size=(d_res, d_res))
    w_res *= rng.uniform(size=w_res.shape) < density
    radius = float(np.max(np.abs(np.linalg.eigvals(w_res))))
    if radius > 0:
        w_res *= rho / radius
    return {"w_in": w_in, "w_res": w_res, "leak": float(leak)}


def reservoir_states(x, reservoir, h0=None):
    x = np.atleast_2d(np.asarray(x, dtype=float))
    w_in, w_res, leak = reservoir["w_in"], reservoir["w_res"], reservoir["leak"]
    h = np.zeros(w_res.shape[0]) if h0 is None else np.asarray(h0, dtype=float).copy()
    states = np.empty((len(x), len(h)))
    for i, row in enumerate(x):
        candidate = np.tanh(w_in @ row + w_res @ h)
        h = (1.0 - leak) * h + leak * candidate
        states[i] = h
    return states


def fit_ssrc_log_temporal(x, y, reservoir):
    states = reservoir_states(x, reservoir)
    design = np.column_stack([np.ones(len(states)), states])
    readout = fit_ridge_temporal(design, y, link="log")
    return {"readout": readout, "last_state": states[-1], "reservoir": reservoir}


def predict_ssrc_log(model, x):
    state = reservoir_states(np.atleast_2d(x), model["reservoir"], model["last_state"])[-1]
    design = np.concatenate(([1.0], state))
    return predict_ridge(model["readout"], design)


def ewma_forecast(returns, decay=0.94):
    r = np.asarray(returns, dtype=float)
    var = max(float(np.var(r)), EPS)
    for value in r:
        var = decay * var + (1.0 - decay) * value ** 2
    return max(float(var), EPS)


def _volatility_params(theta, gjr):
    expv = np.exp(np.clip(theta[1:], -20, 20))
    denom = 1.0 + np.sum(expv)
    weights = 0.999 * expv / denom
    omega = np.exp(np.clip(theta[0], -30, 20))
    if gjr:
        alpha, half_gamma, beta = weights
        return omega, alpha, 2.0 * half_gamma, beta
    alpha, beta = weights
    return omega, alpha, 0.0, beta


def fit_garch_forecast(returns, gjr=False):
    """Pronostico GARCH/GJR por maxima verosimilitud gaussiana restringida."""
    r = np.asarray(returns, dtype=float)
    r = r - np.mean(r)
    variance = max(float(np.var(r)), EPS)
    starts = [
        np.array([np.log(max(0.05 * variance, EPS)), -2.0, 2.0] if not gjr else
                 [np.log(max(0.05 * variance, EPS)), -2.5, -3.0, 2.0]),
        np.array([np.log(max(0.01 * variance, EPS)), -1.5, 2.5] if not gjr else
                 [np.log(max(0.01 * variance, EPS)), -2.0, -2.5, 2.5]),
    ]

    def objective(theta):
        omega, alpha, gamma, beta = _volatility_params(theta, gjr)
        h = variance
        loss = 0.0
        for i in range(1, len(r)):
            asym = gamma * (r[i - 1] < 0) * r[i - 1] ** 2
            h = max(omega + alpha * r[i - 1] ** 2 + asym + beta * h, EPS)
            loss += np.log(h) + r[i] ** 2 / h
        return 0.5 * loss

    results = [minimize(objective, start, method="L-BFGS-B", options={"maxiter": 500})
               for start in starts]
    result = min(results, key=lambda res: float(res.fun))
    if not np.isfinite(result.fun):
        raise RuntimeError("GARCH no convergio")
    omega, alpha, gamma, beta = _volatility_params(result.x, gjr)
    h = variance
    for i in range(1, len(r)):
        asym = gamma * (r[i - 1] < 0) * r[i - 1] ** 2
        h = max(omega + alpha * r[i - 1] ** 2 + asym + beta * h, EPS)
    asym_last = gamma * (r[-1] < 0) * r[-1] ** 2
    forecast = omega + alpha * r[-1] ** 2 + asym_last + beta * h
    return max(float(forecast), EPS)
