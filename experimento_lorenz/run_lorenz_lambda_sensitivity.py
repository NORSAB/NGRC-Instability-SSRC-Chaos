"""Sensibilidad explicita de Ridge a lambda en Lorenz63.

Este control falsifica la lectura fuerte de M^4. No pregunta si "Ridge sirve" en
abstracto, sino si la antigua regla fija lambda=0.1*traza(F'F)/D es fragil frente a
una seleccion temporal interna. El punto OOS queda fuera de la seleccion.

Salida:
  output/sensibilidad_lambda_lorenz.csv
  output/resumen_sensibilidad_lambda_lorenz.md
"""
from pathlib import Path

import numpy as np
import pandas as pd

from lorenz_common import (
    DEFAULT_LAMBDA_RATIOS,
    fit_ridge_fixed_ratio,
    ridge_validation_path,
    select_ridge_lambda_temporal,
    standardize_from_prefix,
)


SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
DT = 0.01
SKIP = 5
BURNIN = 5000
N_POINTS = 12000
K = 3
T_TRAIN = 500
SEED = 7
T0_VALUES = [500, 1500, 3000, 5000, 7000, 9000, 11000]


def lorenz_rhs(state):
    x, y, z = state
    return np.array([SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z])


def simulate_and_subsample():
    rng = np.random.RandomState(SEED)
    state = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
    trajectory = np.empty((BURNIN + N_POINTS * SKIP, 3))
    for i in range(len(trajectory)):
        k1 = lorenz_rhs(state)
        k2 = lorenz_rhs(state + DT * k1 / 2)
        k3 = lorenz_rhs(state + DT * k2 / 2)
        k4 = lorenz_rhs(state + DT * k3)
        state = state + DT * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        trajectory[i] = state
    return trajectory[BURNIN:][::SKIP, 0]


def ngrc_features(x):
    linear = np.array([x[t:t + K] for t in range(len(x) - K)])
    quadratic = np.array(
        [linear[:, i] * linear[:, j] for i in range(K) for j in range(i, K)]
    ).T
    return np.hstack([linear, quadratic]), x[K:]


Path("output").mkdir(exist_ok=True)
x_clean = standardize_from_prefix(simulate_and_subsample(), T_TRAIN)
scenarios = {"limpio": x_clean}
x_shock = x_clean.copy()
x_shock[7000] += 15.0
scenarios["shock_15sigma"] = x_shock

rows = []
for scenario, series in scenarios.items():
    F_all, y_all = ngrc_features(series)
    for t0 in T0_VALUES:
        if t0 >= len(F_all):
            continue
        F_train = F_all[t0 - T_TRAIN:t0]
        y_train = y_all[t0 - T_TRAIN:t0]
        F_test = F_all[t0]
        y_test = float(y_all[t0])
        _, selected = select_ridge_lambda_temporal(F_train, y_train)
        path = ridge_validation_path(F_train, y_train)
        by_ratio = {float(item["lambda_relativa"]): item for item in path}
        for ratio in DEFAULT_LAMBDA_RATIOS:
            weights, lam = fit_ridge_fixed_ratio(F_train, y_train, float(ratio))
            rows.append(
                {
                    "escenario": scenario,
                    "t0": t0,
                    "lambda_relativa": float(ratio),
                    "lambda_ajuste_completo": lam,
                    "mae_validacion": by_ratio[float(ratio)]["mae_validacion"],
                    "error_absoluto_oos": abs(y_test - float(F_test @ weights)),
                    "seleccionada_nested": bool(np.isclose(ratio, selected.lambda_ratio)),
                    "heuristica_traza_legacy": bool(np.isclose(ratio, 0.1)),
                }
            )

detail = pd.DataFrame(rows)
detail.to_csv("output/sensibilidad_lambda_lorenz.csv", index=False)

aggregate = (
    detail.groupby("lambda_relativa")
    .agg(
        mae_validacion_mediana=("mae_validacion", "median"),
        error_oos_mediana=("error_absoluto_oos", "median"),
        veces_seleccionada=("seleccionada_nested", "sum"),
        n=("t0", "count"),
    )
    .reset_index()
)
paired = detail.pivot_table(
    index=["escenario", "t0"], columns="lambda_relativa", values="error_absoluto_oos"
)
legacy_error = float(paired[0.1].median()) if 0.1 in paired else np.nan
nested_rows = detail[detail["seleccionada_nested"]]
nested_error = float(nested_rows["error_absoluto_oos"].median())
n_distinct = int(nested_rows["lambda_relativa"].nunique())

with open("output/resumen_sensibilidad_lambda_lorenz.md", "w", encoding="utf-8") as handle:
    handle.write("# Sensibilidad de Ridge a lambda en Lorenz63\n\n")
    handle.write(
        "La validacion es temporal: el 80% inicial de cada ventana ajusta cada candidato, "
        "el 20% final selecciona y el punto OOS permanece fuera. Por ello este control "
        "evalua la fragilidad de la heuristica proporcional a la traza, no una supuesta "
        "inutilidad universal de Ridge.\n\n"
    )
    handle.write(aggregate.to_markdown(index=False, floatfmt=".6g"))
    handle.write(
        f"\n\nLambda relativa seleccionada: {n_distinct} valores distintos en "
        f"{len(nested_rows)} ventanas. Mediana del error OOS de la seleccion nested: "
        f"{nested_error:.6g}. Mediana con la heuristica fija 0.1: {legacy_error:.6g}.\n"
    )

print(aggregate.to_string(index=False))
print(f"Valores de lambda relativa elegidos: {n_distinct}")
print(f"Error OOS mediano nested={nested_error:.6g}; legacy 0.1={legacy_error:.6g}")
