"""Audita el artefacto de NNLS signado frente a la base no negativa corregida.

El NNLS legado se conserva solo como control negativo: pesos no negativos sobre
rezagos con signo no garantizan una varianza positiva. Ambas variantes usan la
misma ventana causal y ninguna transformación ve el retorno pronosticado.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import nnls

from eventos import categoria, tipo_categoria
from modelos_volatilidad import causal_window, fit_nnls_nonnegative
from data_paths import resolve_fuel_repository


BASE = Path(__file__).resolve().parent
REPO = resolve_fuel_repository()
OUT = BASE / "output"
FIG = BASE.parent / "paper" / "figuras"
FUELS = ["Súper", "Regular", "Diesel", "Kerosene"]
K, T_TRAIN, STEP = 3, 150, 4


def main():
    df = pd.read_csv(REPO, encoding="utf-8-sig").sort_values("Índice")
    dates_all = pd.to_datetime(df["FechaInicioISO"], errors="coerce").to_numpy()
    rows = []
    for fuel in FUELS:
        prices = df[fuel].to_numpy(dtype=float)
        raw = np.log(prices[1:] / prices[:-1])
        valid = np.isfinite(raw)
        returns, dates = raw[valid], dates_all[1:][valid]
        for target in range(K + T_TRAIN, len(returns), STEP):
            fs, fn, fts, ftn, y_train, y_test = causal_window(
                returns, target, T_TRAIN, K
            )
            w_legacy, _ = nnls(fs, y_train)
            w_nonneg = fit_nnls_nonnegative(fn, y_train)
            legacy = float(fts @ w_legacy)
            corrected = float(ftn @ w_nonneg)
            date = pd.Timestamp(dates[target])
            rows.append({
                "fuel": fuel,
                "fecha": date.date().isoformat(),
                "categoria": categoria(date),
                "definicion_ventana": tipo_categoria(date),
                "y_true": y_test,
                "nnls_signado_legacy": legacy,
                "nnls_base_no_negativa": corrected,
                "legacy_negativa": legacy < 0,
                "corregida_negativa": corrected < 0,
            })

    detail = pd.DataFrame(rows)
    rate = (detail.groupby("fuel")
            .agg(n_ventanas=("fecha", "size"),
                 n_negativas_legacy=("legacy_negativa", "sum"),
                 n_negativas_corregida=("corregida_negativa", "sum"))
            .reset_index())
    rate["pct_negativas_legacy"] = 100 * rate["n_negativas_legacy"] / rate["n_ventanas"]
    rate["pct_negativas_corregida"] = 100 * rate["n_negativas_corregida"] / rate["n_ventanas"]
    OUT.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    detail.to_csv(OUT / "investigacion_negativas_por_semana.csv", index=False)
    rate.to_csv(OUT / "tasa_negativas_por_combustible.csv", index=False)

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    x = np.arange(len(rate))
    width = 0.36
    ax.bar(x - width / 2, rate["pct_negativas_legacy"], width,
           label="NNLS con base signada (legado)", color="#C44E52")
    ax.bar(x + width / 2, rate["pct_negativas_corregida"], width,
           label="NNLS con base no negativa", color="#55A868")
    ax.set_xticks(x, rate["fuel"])
    ax.set_ylabel("predicciones crudas negativas (%)")
    ax.set_title("La base no negativa elimina el artefacto de positividad")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "fig10_tasa_negativas_combustibles.pdf", bbox_inches="tight")
    plt.close(fig)
    print(rate.to_string(index=False))


if __name__ == "__main__":
    main()
