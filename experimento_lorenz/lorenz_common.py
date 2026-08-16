"""Utilidades causales para los experimentos Lorenz63 del Articulo 4.

Este modulo separa dos regularizaciones que antes aparecian mezcladas:

* Ridge del *readout*: lambda cambia la solucion y se selecciona con una
  validacion temporal interna, usando solo la ventana de entrenamiento.
* SSRC/ESN: el estado usa de forma explicita ``W_res`` y evoluciona en orden
  temporal. No es una proyeccion aleatoria fila a fila.

Las funciones no leen archivos ni ejecutan experimentos al importarse.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


DEFAULT_LAMBDA_RATIOS = np.array(
    [1e-8, 1e-6, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0], dtype=float
)


def standardize_from_prefix(x: np.ndarray, n_calibration: int) -> np.ndarray:
    """Estandariza toda la serie con estadisticos de un prefijo pasado."""
    x = np.asarray(x, dtype=float)
    if n_calibration < 2 or n_calibration > len(x):
        raise ValueError("n_calibration debe estar entre 2 y la longitud de x")
    calibration = x[:n_calibration]
    scale = float(calibration.std())
    if scale <= np.finfo(float).eps:
        raise ValueError("El prefijo de calibracion tiene varianza nula")
    return (x - float(calibration.mean())) / scale


@dataclass(frozen=True)
class RidgeSelection:
    """Resultado auditable de la validacion temporal interna."""

    lambda_value: float
    lambda_ratio: float
    validation_mae: float
    legacy_lambda: float
    n_inner_train: int
    n_validation: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "lambda_elegida": self.lambda_value,
            "lambda_relativa": self.lambda_ratio,
            "mae_validacion": self.validation_mae,
            "lambda_traza_legacy": self.legacy_lambda,
            "n_inner_train": self.n_inner_train,
            "n_validacion": self.n_validation,
        }


def make_ssrc(
    d_in: int,
    d_res: int,
    rho: float = 0.9,
    density: float = 0.1,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    """Construye pesos fijos de un SSRC/ESN con radio espectral controlado."""
    rng = np.random.RandomState(seed)
    w_in = rng.uniform(-1.0, 1.0, size=(d_res, d_in))
    w_res = rng.uniform(-1.0, 1.0, size=(d_res, d_res))
    w_res *= rng.uniform(size=(d_res, d_res)) < density
    radius = float(np.max(np.abs(np.linalg.eigvals(w_res))))
    if radius > 0.0:
        w_res *= rho / radius
    return w_in, w_res


def ssrc_step(
    x_row: np.ndarray,
    previous_state: np.ndarray,
    w_in: np.ndarray,
    w_res: np.ndarray,
    leak_rate: float = 1.0,
) -> np.ndarray:
    """Actualiza un estado recurrente usando solo el presente y el pasado."""
    x_row = np.asarray(x_row, dtype=float).reshape(-1)
    previous_state = np.asarray(previous_state, dtype=float).reshape(-1)
    proposal = np.tanh(w_in @ x_row + w_res @ previous_state)
    return (1.0 - leak_rate) * previous_state + leak_rate * proposal


def ssrc_states(
    X: np.ndarray,
    w_in: np.ndarray,
    w_res: np.ndarray,
    initial_state: np.ndarray | None = None,
    leak_rate: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Recorre ``X`` en orden y devuelve un estado por fila y el estado final."""
    X = np.asarray(X, dtype=float)
    if X.ndim != 2:
        raise ValueError("X debe ser una matriz bidimensional")
    state = (
        np.zeros(w_res.shape[0], dtype=float)
        if initial_state is None
        else np.asarray(initial_state, dtype=float).copy()
    )
    states = np.empty((len(X), w_res.shape[0]), dtype=float)
    for i, row in enumerate(X):
        state = ssrc_step(row, state, w_in, w_res, leak_rate=leak_rate)
        states[i] = state
    return states, state.copy()


def _ridge_solution(X: np.ndarray, y: np.ndarray, lam: float) -> np.ndarray:
    gram = X.T @ X
    rhs = X.T @ y
    system = gram + float(lam) * np.eye(X.shape[1])
    try:
        return np.linalg.solve(system, rhs)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(system, rhs, rcond=None)[0]


def ridge_lambda_scale(X: np.ndarray) -> float:
    """Escala de la heuristica historica ``traza(X'X)/D``."""
    X = np.asarray(X, dtype=float)
    scale = float(np.trace(X.T @ X) / max(1, X.shape[1]))
    return max(scale, np.finfo(float).eps)


def fit_ridge_fixed_ratio(
    X: np.ndarray, y: np.ndarray, lambda_ratio: float
) -> tuple[np.ndarray, float]:
    """Ajusta Ridge con una razon fija respecto a ``traza(X'X)/D``."""
    if lambda_ratio <= 0:
        raise ValueError("lambda_ratio debe ser positivo")
    lam = float(lambda_ratio * ridge_lambda_scale(X))
    return _ridge_solution(np.asarray(X, dtype=float), np.asarray(y, dtype=float), lam), lam


def select_ridge_lambda_temporal(
    X: np.ndarray,
    y: np.ndarray,
    lambda_ratios: Iterable[float] = DEFAULT_LAMBDA_RATIOS,
    validation_fraction: float = 0.2,
) -> tuple[np.ndarray, RidgeSelection]:
    """Selecciona lambda con holdout temporal interno y reajusta en toda la ventana.

    El primer bloque se usa para ajustar candidatos y el ultimo bloque, sin barajar,
    para seleccionarlos. El punto OOS exterior no entra en esta funcion.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1)
    if X.ndim != 2 or len(X) != len(y):
        raise ValueError("X e y deben estar alineados")
    if len(X) < 12:
        raise ValueError("Se requieren al menos 12 observaciones para validacion temporal")

    n_validation = max(5, int(round(len(X) * validation_fraction)))
    n_validation = min(n_validation, len(X) - 6)
    split = len(X) - n_validation
    X_inner, y_inner = X[:split], y[:split]
    X_validation, y_validation = X[split:], y[split:]
    inner_scale = ridge_lambda_scale(X_inner)

    candidates = np.asarray(list(lambda_ratios), dtype=float)
    if candidates.ndim != 1 or len(candidates) == 0 or np.any(candidates <= 0):
        raise ValueError("lambda_ratios debe contener valores positivos")

    scores: list[tuple[float, float]] = []
    for ratio in candidates:
        weights = _ridge_solution(X_inner, y_inner, ratio * inner_scale)
        score = float(np.mean(np.abs(y_validation - X_validation @ weights)))
        scores.append((score, float(ratio)))
    validation_mae, selected_ratio = min(scores, key=lambda item: (item[0], item[1]))

    full_scale = ridge_lambda_scale(X)
    selected_lambda = selected_ratio * full_scale
    weights = _ridge_solution(X, y, selected_lambda)
    selection = RidgeSelection(
        lambda_value=float(selected_lambda),
        lambda_ratio=float(selected_ratio),
        validation_mae=float(validation_mae),
        legacy_lambda=float(0.1 * full_scale),
        n_inner_train=int(split),
        n_validation=int(n_validation),
    )
    return weights, selection


def ridge_validation_path(
    X: np.ndarray,
    y: np.ndarray,
    lambda_ratios: Iterable[float] = DEFAULT_LAMBDA_RATIOS,
    validation_fraction: float = 0.2,
) -> list[dict[str, float | int]]:
    """Devuelve el barrido interno completo para auditar la sensibilidad a lambda."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1)
    n_validation = max(5, int(round(len(X) * validation_fraction)))
    n_validation = min(n_validation, len(X) - 6)
    split = len(X) - n_validation
    X_inner, y_inner = X[:split], y[:split]
    X_validation, y_validation = X[split:], y[split:]
    scale = ridge_lambda_scale(X_inner)
    rows: list[dict[str, float | int]] = []
    for ratio in np.asarray(list(lambda_ratios), dtype=float):
        lam = float(ratio * scale)
        weights = _ridge_solution(X_inner, y_inner, lam)
        rows.append(
            {
                "lambda_relativa": float(ratio),
                "lambda_interna": lam,
                "mae_validacion": float(
                    np.mean(np.abs(y_validation - X_validation @ weights))
                ),
                "n_inner_train": int(split),
                "n_validacion": int(n_validation),
            }
        )
    return rows


def fit_readout(
    X_train: np.ndarray,
    y_train: np.ndarray,
    mode: str,
    H_train: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float | int]]:
    """Ajusta un lector sin usar la observacion OOS exterior."""
    X_train = np.asarray(X_train, dtype=float)
    y_train = np.asarray(y_train, dtype=float)
    if mode == "ols":
        weights, *_ = np.linalg.lstsq(X_train, y_train, rcond=None)
        return weights, {}
    if mode == "ridge":
        weights, selection = select_ridge_lambda_temporal(X_train, y_train)
        return weights, selection.as_dict()
    if mode == "nnls":
        from scipy.optimize import nnls

        weights, _ = nnls(X_train, y_train)
        return weights, {}
    if mode == "ssrc":
        if H_train is None:
            raise ValueError("SSRC requiere estados recurrentes H_train precomputados")
        weights, selection = select_ridge_lambda_temporal(H_train, y_train)
        return weights, selection.as_dict()
    raise ValueError(f"Modo desconocido: {mode}")


def predict_readout(
    X_row: np.ndarray,
    weights: np.ndarray,
    mode: str,
    H_row: np.ndarray | None = None,
) -> float:
    """Predice una fila; SSRC usa el estado recurrente ya actualizado."""
    design_row = H_row if mode == "ssrc" else X_row
    if design_row is None:
        raise ValueError("SSRC requiere H_row")
    return float(np.asarray(design_row @ weights).ravel()[0])


def empty_selection_metadata() -> dict[str, float]:
    """Columnas homogeneas para lectores sin lambda."""
    return {
        "lambda_elegida": np.nan,
        "lambda_relativa": np.nan,
        "mae_validacion": np.nan,
        "lambda_traza_legacy": np.nan,
    }
