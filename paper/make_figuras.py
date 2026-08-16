"""Regenera las figuras del registro corregido desde resultados auditables.

El guion no contiene cifras manuales. Resuelve rutas desde su propio archivo y
falla si un resultado requerido no existe o usa el esquema anterior.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OUT = HERE / "figuras"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 600,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
W = 6.8


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)


def require_columns(frame, columns, source):
    missing = set(columns) - set(frame.columns)
    if missing:
        raise RuntimeError(f"{source} conserva un esquema obsoleto; faltan {sorted(missing)}")


# 1. Condicionamiento FX por T.
kappa = pd.read_csv(BASE / "experimento_diario_fx_cripto/output/kappa_vs_T.csv")
require_columns(kappa, {"entity", "k", "T", "kappa_raw"}, "kappa_vs_T.csv")
fig, ax = plt.subplots(figsize=(W, 4.1))
for entity, group in kappa[kappa["k"] == 3].groupby("entity"):
    group = group.sort_values("T")
    ax.plot(group["T"], group["kappa_raw"], marker="o", ms=3, lw=1.2, label=entity)
ax.set_yscale("log")
ax.set_xlabel("T (días)")
ax.set_ylabel(r"$\kappa(\mathrm{cov}(F))$")
ax.set_title("FX y cripto: condicionamiento del bloque NG-RC")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=5, frameon=False)
save(fig, "fig1_kappa_vs_T.pdf")


# 2. Lorenz: MASE en la trayectoria limpia, con SSRC recurrente real.
lorenz = pd.read_csv(BASE / "experimento_lorenz/output/oos_lorenz.csv")
require_columns(lorenz, {"escenario", "mode", "mase", "ventana_incluye_shock"}, "oos_lorenz.csv")
clean = lorenz[(lorenz["escenario"] == "limpio") & (~lorenz["ventana_incluye_shock"])]
order_l = ["ssrc", "ridge", "ols", "naive", "nnls"]
med_l = clean.groupby("mode")["mase"].median().reindex(order_l)
fig, ax = plt.subplots(figsize=(W, 3.9))
bars = ax.bar(order_l, med_l, color=["#4C72B0", "#C44E52", "#DD8452", "#8C8C8C", "#55A868"])
ax.axhline(1.0, color="gray", ls="--", lw=1)
ax.set_ylabel("MASE mediana")
ax.set_title("Lorenz63: comparación causal de lectores")
for bar, value in zip(bars, med_l):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.025, f"{value:.3f}", ha="center")
save(fig, "fig4_mase_lorenz.pdf")


# 3. Sensibilidad de Ridge: la razón fija 0.1 no representa al método completo.
lam = pd.read_csv(BASE / "experimento_lorenz/output/sensibilidad_lambda_lorenz.csv")
require_columns(lam, {"lambda_relativa", "error_absoluto_oos", "seleccionada_nested"},
                "sensibilidad_lambda_lorenz.csv")
path = lam.groupby("lambda_relativa")["error_absoluto_oos"].median().sort_index()
selected = lam[lam["seleccionada_nested"]].groupby("lambda_relativa").size()
fig, ax = plt.subplots(figsize=(W, 4.1))
ax.plot(path.index, path.values, marker="o", color="#C44E52", label="error OOS mediano")
ax.axvline(0.1, color="#8C8C8C", ls="--", label="heurística fija 0.1")
for value, count in selected.items():
    ax.scatter(value, path.loc[value], s=35 + 12 * count, color="#4C72B0", zorder=4)
ax.set_xscale("log")
ax.set_xlabel(r"razón de $\lambda$ respecto del tamaño de muestra")
ax.set_ylabel("error absoluto OOS mediano")
ax.set_title("Lorenz63: la validación temporal selecciona distintos niveles de regularización")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False)
save(fig, "fig5_ridge_fragilidad.pdf")


# 4. FX/cripto: modelos positivos y referencias financieras.
fx = pd.read_csv(BASE / "experimento_diario_fx_cripto/output/oos_univariado.csv")
require_columns(fx, {"mode", "qlike", "mase", "fit_status", "pred_negativa_cruda"},
                "oos_univariado.csv")
fair_modes = ["ewma_0.94", "gjr_garch_11", "garch_11", "nnls_nonneg",
              "softplus_ridge", "ssrc_log", "log_ridge", "naive"]
fair_labels = ["EWMA", "GJR", "GARCH", "NNLS+", "softplus", "SSRC", "log-Ridge", "naive"]
valid_fx = fx[(fx["fit_status"] == "ok") & fx["mode"].isin(fair_modes)]
med_fx = valid_fx.groupby("mode")["qlike"].median().reindex(fair_modes)
fig, ax = plt.subplots(figsize=(W, 4.0))
bars = ax.bar(fair_labels, med_fx, color="#4C72B0")
ax.set_ylabel("QLIKE mediana")
ax.set_title("FX y cripto: modelos positivos y referencias de volatilidad")
ax.tick_params(axis="x", rotation=24)
for bar, value in zip(bars, med_fx):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.03, f"{value:.2f}", ha="center", fontsize=8)
save(fig, "fig3_qlike_barras.pdf")


# 5. Sensibilidad del QLIKE al piso, incluidas variantes de legado.
floor_cols = ["qlike_floor_1e-12", "qlike_floor_1e-10", "qlike_floor_1e-08", "qlike_floor_1e-06"]
require_columns(fx, set(floor_cols), "oos_univariado.csv")
floor_modes = ["ols_clip_legacy", "ridge_clip", "nnls_signed_clip_legacy",
               "nnls_nonneg", "softplus_ridge", "ssrc_log"]
matrix = []
for mode in floor_modes:
    sub = fx[(fx["mode"] == mode) & (fx["fit_status"] == "ok")]
    matrix.append([sub[col].median() for col in floor_cols])
fig, ax = plt.subplots(figsize=(W, 4.1))
for mode, values in zip(floor_modes, matrix):
    ax.plot([1e-12, 1e-10, 1e-8, 1e-6], values, marker="o", label=mode)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("piso de varianza usado por QLIKE")
ax.set_ylabel("QLIKE mediana")
ax.set_title("FX y cripto: sensibilidad explícita al piso de evaluación")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=3, fontsize=8, frameon=False)
save(fig, "fig13_qlike_piso_fx.pdf")


# 6. El control NNLS muestra por qué w>=0 no basta con una base signada.
nnls_fx = pd.read_csv(BASE / "experimento_diario_fx_cripto/output/oos_nnls_features_noneg.csv")
require_columns(nnls_fx, {"variant", "pred_negativa", "qlike", "mase"},
                "oos_nnls_features_noneg.csv")
summary_nnls = nnls_fx.groupby("variant").agg(
    negativas=("pred_negativa", "mean"), qlike=("qlike", "median"), mase=("mase", "median")
)
variants = ["nnls_original_legacy", "nnls_nonneg"]
values = np.array([[100 * summary_nnls.loc[v, "negativas"], summary_nnls.loc[v, "qlike"],
                    summary_nnls.loc[v, "mase"]] for v in variants])
fig, axes = plt.subplots(1, 3, figsize=(W, 3.4))
titles = ["predicciones negativas (%)", "QLIKE mediana", "MASE mediana"]
for index, ax in enumerate(axes):
    ax.bar([0, 1], values[:, index], color=["#C44E52", "#55A868"])
    ax.set_xticks([0, 1], ["legado", "base no negativa"], rotation=20)
    ax.set_title(titles[index], fontsize=9)
save(fig, "fig6_nnls_tradeoff.pdf")


# 7. BCIE causal, cobertura pareja. Es figura suplementaria.
bcie = pd.read_csv(BASE / "experimento/codigo_pipeline/output/comparacion_cobertura_pareja.csv")
require_columns(bcie, {"label", "mase", "ents", "dm_p_block_exact_abs"},
                "comparacion_cobertura_pareja.csv")
bcie = bcie.sort_values("mase")
fig, ax = plt.subplots(figsize=(W, 4.4))
ax.barh(np.arange(len(bcie)), bcie["mase"], color="#8172B2")
ax.set_yticks(np.arange(len(bcie)), bcie["label"], fontsize=8)
ax.invert_yaxis()
ax.axvline(1.0, color="gray", ls="--", lw=1)
ax.set_xlabel("MASE, ocho entidades comunes")
ax.set_title("Suplemento BCIE: ventaja numérica sin significancia por bloques")
save(fig, "fig12_bcie_causal.pdf")

print(f"Figuras corregidas guardadas en {OUT}")
