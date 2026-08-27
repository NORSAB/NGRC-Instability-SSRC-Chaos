"""Escalamiento de la traza para mapas polinomiales de grado general.

Autor: Norman Sabillon (2026)

El experimento conserva la normalizacion causal de la coordenada de Lorenz63, pero no
reestandariza las columnas monomiales despues de introducir el shock. Para cada grado
maximo d se construyen todos los monomios de orden 1 hasta d y se mide
trace(F.T @ F) / D en una ventana que contiene el shock en su interior.
"""
from __future__ import annotations

import argparse
from itertools import combinations_with_replacement
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from lorenz_common import standardize_from_prefix


DEFAULT_DEGREES = (2, 3, 4)
DEFAULT_MAGNITUDES = (5.0, 10.0, 20.0, 40.0, 80.0)
DEFAULT_LOCATIONS = (4000, 9000, 14000)
DEFAULT_SIGNS = (-1, 1)
DEFAULT_LAGS = 3
DEFAULT_WINDOW = 500
DEFAULT_N_FIT = 3
DEFAULT_POINTS = 18000
DEFAULT_CALIBRATION = 500
DEFAULT_SEED = 7
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def polynomial_feature_matrix(
    series: np.ndarray,
    lags: int,
    degree: int,
) -> np.ndarray:
    """Construye monomios completos de orden 1 hasta ``degree`` sobre ``lags``."""
    values = np.asarray(series, dtype=float)
    if values.ndim != 1:
        raise ValueError("series debe ser un vector unidimensional")
    if lags < 1 or degree < 1:
        raise ValueError("lags y degree deben ser enteros positivos")
    if len(values) <= lags:
        raise ValueError("La serie es demasiado corta para los rezagos solicitados")

    lagged = np.lib.stride_tricks.sliding_window_view(values, lags)[:-1]
    columns: list[np.ndarray] = []
    for order in range(1, degree + 1):
        for indices in combinations_with_replacement(range(lags), order):
            columns.append(np.prod(lagged[:, indices], axis=1))
    return np.column_stack(columns)


def trace_per_feature(features: np.ndarray) -> float:
    """Calcula ``trace(F.T @ F) / D`` sin formar la matriz de Gram."""
    matrix = np.asarray(features, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] == 0:
        raise ValueError("features debe ser una matriz no vacia")
    return float(np.square(matrix).sum() / matrix.shape[1])


def shock_window_trace(
    series: np.ndarray,
    location: int,
    magnitude: float,
    sign: int,
    lags: int,
    degree: int,
    window: int,
) -> float:
    """Mide la traza en una ventana fija con el shock estrictamente interior."""
    values = np.asarray(series, dtype=float)
    if sign not in (-1, 1):
        raise ValueError("sign debe ser -1 o 1")
    if magnitude <= 0 or not np.isfinite(magnitude):
        raise ValueError("magnitude debe ser positiva y finita")
    if window <= lags or window > len(values) - lags:
        raise ValueError("window no es compatible con la longitud de la serie")
    if location < lags or location >= len(values) - lags:
        raise ValueError("location debe dejar el shock lejos de ambos bordes")

    shocked = values.copy()
    shocked[location] += sign * magnitude
    features = polynomial_feature_matrix(shocked, lags=lags, degree=degree)

    center_row = location - (lags - 1) // 2
    start = center_row - window // 2
    stop = start + window
    if start < 0 or stop > len(features):
        raise ValueError("La ventana solicitada no mantiene el shock en el interior")
    affected_first = location - lags + 1
    affected_last = location
    if not (start < affected_first and affected_last < stop):
        raise AssertionError("La ventana no contiene todos los rezagos afectados por el shock")
    return trace_per_feature(features[start:stop])


def log_log_slope(
    magnitudes: Iterable[float],
    traces: Iterable[float],
    n_fit: int = DEFAULT_N_FIT,
) -> tuple[float, float]:
    """Ajusta la pendiente asintotica sobre las ``n_fit`` magnitudes mayores."""
    x = np.asarray(list(magnitudes), dtype=float)
    y = np.asarray(list(traces), dtype=float)
    if len(x) != len(y) or len(x) < n_fit or n_fit < 2:
        raise ValueError("Se requieren pares suficientes para el ajuste log-log")
    if np.any(~np.isfinite(x)) or np.any(~np.isfinite(y)):
        raise ValueError("Magnitudes y trazas deben ser finitas")
    if np.any(x <= 0) or np.any(y <= 0):
        raise ValueError("El ajuste log-log requiere valores positivos")
    order = np.argsort(x)[-n_fit:]
    slope, intercept = np.polyfit(np.log(x[order]), np.log(y[order]), 1)
    return float(slope), float(intercept)


def run_degree_scaling(
    series: np.ndarray,
    locations: Iterable[int] = DEFAULT_LOCATIONS,
    magnitudes: Iterable[float] = DEFAULT_MAGNITUDES,
    signs: Iterable[int] = DEFAULT_SIGNS,
    degrees: Iterable[int] = DEFAULT_DEGREES,
    lags: int = DEFAULT_LAGS,
    window: int = DEFAULT_WINDOW,
    n_fit: int = DEFAULT_N_FIT,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejecuta la grilla y devuelve observaciones crudas y pendientes por condicion."""
    locations = tuple(int(value) for value in locations)
    magnitudes = tuple(float(value) for value in magnitudes)
    signs = tuple(int(value) for value in signs)
    degrees = tuple(int(value) for value in degrees)
    if not locations or not magnitudes or not signs or not degrees:
        raise ValueError("La grilla no puede contener conjuntos vacios")

    raw_rows: list[dict[str, float | int]] = []
    slope_rows: list[dict[str, float | int]] = []
    for degree in degrees:
        if degree < 1:
            raise ValueError("Todos los grados deben ser positivos")
        for location in locations:
            for sign in signs:
                condition_traces: list[float] = []
                for magnitude in magnitudes:
                    trace = shock_window_trace(
                        series,
                        location=location,
                        magnitude=magnitude,
                        sign=sign,
                        lags=lags,
                        degree=degree,
                        window=window,
                    )
                    condition_traces.append(trace)
                    raw_rows.append(
                        {
                            "degree": degree,
                            "expected_exponent": 2 * degree,
                            "location": location,
                            "sign": sign,
                            "magnitude": magnitude,
                            "trace_per_feature": trace,
                        }
                    )
                slope, intercept = log_log_slope(magnitudes, condition_traces, n_fit=n_fit)
                slope_rows.append(
                    {
                        "degree": degree,
                        "expected_exponent": 2 * degree,
                        "location": location,
                        "sign": sign,
                        "slope": slope,
                        "intercept": intercept,
                        "absolute_error": abs(slope - 2 * degree),
                        "n_fit": n_fit,
                    }
                )
    return pd.DataFrame(raw_rows), pd.DataFrame(slope_rows)


def summarize_slopes(slopes: pd.DataFrame) -> pd.DataFrame:
    """Resume la estabilidad del exponente entre ubicaciones y signos."""
    required = {"degree", "expected_exponent", "slope", "absolute_error"}
    missing = required.difference(slopes.columns)
    if missing:
        raise ValueError(f"Faltan columnas de pendientes: {sorted(missing)}")
    return (
        slopes.groupby(["degree", "expected_exponent"], as_index=False)
        .agg(
            slope_median=("slope", "median"),
            slope_min=("slope", "min"),
            slope_max=("slope", "max"),
            max_absolute_error=("absolute_error", "max"),
            n_conditions=("slope", "size"),
        )
        .sort_values("degree")
        .reset_index(drop=True)
    )


def simulate_lorenz_x(
    n_feature_points: int = DEFAULT_POINTS,
    dt: float = 0.01,
    skip: int = 5,
    burnin_steps: int = 5000,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Simula la coordenada x de Lorenz63 con RK4 y submuestreo determinista."""
    if n_feature_points < 1000 or dt <= 0 or skip < 1 or burnin_steps < 0:
        raise ValueError("Parametros de simulacion no validos")
    rng = np.random.RandomState(seed)
    state = np.array([1.0, 1.0, 1.0]) + rng.normal(0.0, 0.1, 3)
    sampled = np.empty(n_feature_points, dtype=float)
    total_steps = burnin_steps + n_feature_points * skip
    write_index = 0

    def rhs(point: np.ndarray) -> np.ndarray:
        x, y, z = point
        return np.array([10.0 * (y - x), x * (28.0 - z) - y, x * y - (8.0 / 3.0) * z])

    for step in range(total_steps):
        k1 = rhs(state)
        k2 = rhs(state + 0.5 * dt * k1)
        k3 = rhs(state + 0.5 * dt * k2)
        k4 = rhs(state + dt * k3)
        state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        if step >= burnin_steps and (step - burnin_steps) % skip == 0:
            sampled[write_index] = state[0]
            write_index += 1
    if write_index != n_feature_points:
        raise AssertionError("La simulacion no genero el numero solicitado de puntos")
    return sampled


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--degrees", nargs="+", type=int, default=list(DEFAULT_DEGREES))
    parser.add_argument("--magnitudes", nargs="+", type=float, default=list(DEFAULT_MAGNITUDES))
    parser.add_argument("--locations", nargs="+", type=int, default=list(DEFAULT_LOCATIONS))
    parser.add_argument("--signs", nargs="+", type=int, default=list(DEFAULT_SIGNS))
    parser.add_argument("--n-points", type=int, default=DEFAULT_POINTS)
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    parser.add_argument("--n-fit", type=int, default=DEFAULT_N_FIT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--no-save", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw_x = simulate_lorenz_x(n_feature_points=args.n_points)
    x = standardize_from_prefix(raw_x, DEFAULT_CALIBRATION)
    raw, slopes = run_degree_scaling(
        x,
        locations=args.locations,
        magnitudes=args.magnitudes,
        signs=args.signs,
        degrees=args.degrees,
        window=args.window,
        n_fit=args.n_fit,
    )
    summary = summarize_slopes(slopes)
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    if not args.no_save:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        raw.to_csv(args.output_dir / "general_degree_scaling.csv", index=False)
        slopes.to_csv(args.output_dir / "general_degree_scaling_by_condition.csv", index=False)
        summary.to_csv(args.output_dir / "general_degree_scaling_summary.csv", index=False)
        print(f"Resultados guardados en {args.output_dir}")


if __name__ == "__main__":
    main()
