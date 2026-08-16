"""Transformaciones causales para los experimentos BCIE del Articulo 4.

Toda estimacion de parametros (media, escala, covarianza, componente principal o pesos
NNLS) usa exclusivamente las filas marcadas por ``fit_mask``. Las transformaciones ya
ajustadas se aplican luego a la serie completa, incluido el tramo OOS.

La regularizacion ``tikhonov_covariance`` de este modulo actua sobre la matriz de
covarianza antes de extraer su autovector principal. No es Ridge y no regulariza un
readout de regresion. PCA, Ledoit-Wolf y Tikhonov comparten una convencion determinista
de signo para que una ambiguedad algebraica no altere el operador NNLS posterior.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import nnls
from sklearn.covariance import LedoitWolf
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def validate_fit_mask(fit_mask, n_samples: int, min_train: int = 2) -> np.ndarray:
    """Valida y devuelve una mascara booleana de entrenamiento temporal."""
    mask = np.asarray(fit_mask, dtype=bool)
    if mask.ndim != 1 or mask.size != n_samples:
        raise ValueError(f"fit_mask debe tener {n_samples} elementos; recibido {mask.shape}")
    if int(mask.sum()) < min_train:
        raise ValueError(f"se requieren al menos {min_train} observaciones de entrenamiento")
    return mask


def temporal_standardize(X, fit_mask, return_scaler: bool = False):
    """Estandariza ``X`` (muestras x variables) con parametros del train solamente."""
    X = np.asarray(X, dtype=float)
    if X.ndim != 2:
        raise ValueError("X debe ser bidimensional (muestras x variables)")
    mask = validate_fit_mask(fit_mask, X.shape[0])
    scaler = StandardScaler().fit(X[mask])
    transformed = scaler.transform(X)
    return (transformed, scaler) if return_scaler else transformed


def _condition_number(matrix: np.ndarray) -> float:
    try:
        return float(np.linalg.cond(matrix))
    except np.linalg.LinAlgError:
        return float("inf")


def orient_component(component: np.ndarray) -> np.ndarray:
    """Fija el signo haciendo positiva la carga de mayor magnitud (desempate por indice).

    El signo de un autovector es indeterminado. Sin esta convencion, SVD y ``eigh`` pueden
    devolver la misma direccion con signos opuestos y alterar artificialmente el NNLS del
    operador posterior. Esta regla no usa el tramo OOS ni el target.
    """
    oriented = np.asarray(component, dtype=float).copy()
    anchor = int(np.argmax(np.abs(oriented)))
    if oriented[anchor] < 0:
        oriented *= -1.0
    return oriented


def compress_ngrc_temporal(
    F,
    *,
    mode: str,
    fit_mask,
    target=None,
    tikhonov_covariance_fraction: float = 0.25,
    return_artifacts: bool = False,
):
    """Comprime estados NG-RC sin usar informacion posterior al corte de entrenamiento.

    ``F`` tiene forma (variables, tiempo) y su primera fila es la constante. Esa fila se
    excluye del escalado y de la covarianza. En ``nnls_directo`` se reincorpora despues
    como un intercepto literal de unos. NNLS restringe los pesos, pero ``X`` es signada;
    por eso la salida ``z`` no queda restringida a valores positivos.

    Se acepta ``tikhonov`` como alias historico, pero el artefacto registra el nombre
    inequívoco ``tikhonov_covariance``.
    """
    F = np.asarray(F, dtype=float)
    if F.ndim != 2 or F.shape[0] < 2:
        raise ValueError("F debe tener forma (D,T), incluida una fila constante")
    mask = validate_fit_mask(fit_mask, F.shape[1])
    X_raw = F.T[:, 1:]
    X, scaler = temporal_standardize(X_raw, mask, return_scaler=True)
    X_train = X[mask]
    train_location = X_train.mean(axis=0)
    cov_raw = np.atleast_2d(np.cov(X_train, rowvar=False))
    kappa_raw = _condition_number(cov_raw)
    artifacts = {
        "mode": "tikhonov_covariance" if mode == "tikhonov" else mode,
        "scaler_mean": scaler.mean_.copy(),
        "scaler_scale": scaler.scale_.copy(),
        "covariance_train": cov_raw.copy(),
        "feature_location_train": train_location.copy(),
        "kappa_raw": kappa_raw,
        "n_train": int(mask.sum()),
        "d_features": int(X.shape[1]),
        "motivo_singularidad": "",
    }

    if mode == "baseline":
        reducer = PCA(n_components=1).fit(X_train)
        component = orient_component(reducer.components_[0])
        z = (X - reducer.mean_) @ component
        kappa_used = kappa_raw
        artifacts["component"] = component.copy()
    elif mode == "ledoitwolf":
        estimator = LedoitWolf().fit(X_train)
        cov_used = estimator.covariance_
        _, eigvecs = np.linalg.eigh(cov_used)
        component = orient_component(eigvecs[:, -1])
        z = (X - estimator.location_) @ component
        kappa_used = _condition_number(cov_used)
        artifacts.update(component=component.copy(), covariance_used=cov_used.copy())
    elif mode in {"tikhonov", "tikhonov_covariance"}:
        D = cov_raw.shape[0]
        lam_cov = float(tikhonov_covariance_fraction * np.trace(cov_raw) / max(D, 1))
        cov_used = cov_raw + lam_cov * np.eye(D)
        _, eigvecs = np.linalg.eigh(cov_used)
        component = orient_component(eigvecs[:, -1])
        z = (X - train_location) @ component
        kappa_used = _condition_number(cov_used)
        artifacts.update(
            component=component.copy(), covariance_used=cov_used.copy(),
            lambda_covariance=lam_cov,
        )
    elif mode == "nnls_directo":
        if target is None:
            raise ValueError("nnls_directo requiere target")
        y = np.asarray(target, dtype=float)
        if y.shape != (F.shape[1],):
            raise ValueError("target debe tener una observacion por columna temporal de F")
        A = np.column_stack([np.ones(X.shape[0]), X])
        A_train, y_train = A[mask], y[mask]
        if A_train.shape[0] <= A_train.shape[1]:
            weights = np.zeros(A.shape[1])
            kappa_used = float("inf")
            artifacts["motivo_singularidad"] = "insuficiente_muestra (n_train<=D_features)"
        else:
            weights, _ = nnls(A_train, y_train)
            kappa_used = _condition_number(A_train)
        z = A @ weights
        artifacts.update(weights=weights.copy(), design_train=A_train.copy())
    else:
        raise ValueError(f"modo desconocido: {mode}")

    artifacts["kappa_used"] = kappa_used
    if not np.isfinite(kappa_used) and not artifacts["motivo_singularidad"]:
        artifacts["motivo_singularidad"] = "singular_real_en_entrenamiento"
    return (z, artifacts) if return_artifacts else z


def reservoir_embedding_temporal(alpha, years, *, run_reservoir, w_in, w_res, train_end_year):
    """Calcula el embedding del reservorio con escalado y PCA ajustados solo en train."""
    alpha = np.asarray(alpha, dtype=float)
    years = np.asarray(years)
    if alpha.ndim != 2 or alpha.shape[1] != years.size:
        raise ValueError("alpha y years no estan alineados")
    mask = years <= train_end_year
    alpha_std = temporal_standardize(alpha.T, mask).T
    states = np.asarray(run_reservoir(alpha_std, w_in, w_res), dtype=float).T
    reducer = PCA(n_components=1).fit(states[mask])
    return reducer.transform(states).ravel()
