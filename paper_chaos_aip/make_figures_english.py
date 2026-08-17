"""
Genera todas las figuras en ingles para el manuscrito Chaos (AIP).
Lee directamente los CSVs de salida auditados.
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)

sys.path.insert(0, str(BASE / "experimento_lorenz"))
# lorenz_rhs y las constantes de integracion vienen del script de la ablacion de 30
# Reutilización de constantes físicas e integrador canónico RK4.
from run_lorenz_30_seeds_ablation import (
    DT_INTEGRATE as LORENZ_DT,
    N_BURNIN_INTEGRATE as LORENZ_N_BURNIN,
    SKIP as LORENZ_SKIP,
    TRAJ_SEED as LORENZ_SEED,
    lorenz_rhs,
)

plt.rcParams.update({
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 600,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.family": "serif",
})
W_SINGLE = 3.4  # ancho columna AIP
W_DOUBLE = 7.0  # ancho doble columna AIP


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)


# 1. Figure 1 (main.tex): Quartic trace inflation under localized outlier shocks.
#    M (shock magnitude, sigma units) on x vs. the trace-proportional heuristic
#    lambda = gamma * tr(F^T F) / D on y, both log-scale, with a power-law fit in the
# 1. Figure 1: Quartic trace inflation under localized outlier shocks.
grid_file = BASE / "experimento_lorenz/output/oos_grid_shocks.csv"
if not grid_file.exists():
    raise FileNotFoundError(
        f"Missing required source file for Figure 1 (M^4 trace inflation): {grid_file}"
    )
grid = pd.read_csv(grid_file)
# Filtrar ventanas que contienen el shock para evaluar la traza empírica
grid_shock = grid.dropna(subset=["lambda_traza_legacy"])
grid_shock = grid_shock[grid_shock["ventana_incluye_shock"]]
med_by_mag = grid_shock.groupby("magnitud_sigma")["lambda_traza_legacy"].median().sort_index()
M_vals = med_by_mag.index.values.astype(float)
lam_vals = med_by_mag.values.astype(float)

n_fit = min(3, len(M_vals))  # Régimen asintótico para ajuste de ley de potencia
fit_idx = np.argsort(M_vals)[-n_fit:]
slope, intercept = np.polyfit(np.log(M_vals[fit_idx]), np.log(lam_vals[fit_idx]), 1)
print(f"[fig5_ridge_fragilidad] Fitted log-log slope over top {n_fit} magnitudes: {slope:.4f}")

fig, ax = plt.subplots(figsize=(W_SINGLE * 1.55, 2.9))
ax.plot(M_vals, lam_vals, marker="o", ms=5, lw=1.5, color="#4C72B0",
        label=r"Median $\lambda$ (shock window)")
fit_M = np.array([M_vals[fit_idx].min(), M_vals[fit_idx].max()])
fit_line = np.exp(intercept) * fit_M ** slope
ax.plot(fit_M, fit_line, ls="--", color="#C44E52", lw=1.5,
        label=fr"Power-law fit, slope $\approx {slope:.2f}$")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"Shock magnitude $M$ ($\sigma$)")
ax.set_ylabel(r"Trace-proportional $\lambda = \gamma\,\mathrm{tr}(F^\top F)/D$ (median)", fontsize=8.5)
ax.set_title("Quartic trace inflation under localized outlier shocks", fontsize=10, pad=10)
ax.legend(loc="upper left", frameon=False, fontsize=8)
save(fig, "fig5_ridge_fragilidad.pdf")


# 1b. Supplementary: Sensibilidad a la selección temporal anidada de lambda
lam_file = BASE / "experimento_lorenz/output/sensibilidad_lambda_lorenz.csv"
if not lam_file.exists():
    raise FileNotFoundError(
        f"Missing required source file for the supplementary lambda-selection figure: {lam_file}"
    )
lam = pd.read_csv(lam_file)
path = lam.groupby("lambda_relativa")["error_absoluto_oos"].median().sort_index()
selected = lam[lam["seleccionada_nested"]].groupby("lambda_relativa").size()
fig, ax = plt.subplots(figsize=(W_SINGLE, 2.8))
ax.plot(path.index, path.values, marker="o", ms=4, color="#C44E52", lw=1.5, label="Median OOS absolute error")
ax.axvline(0.1, color="#8C8C8C", ls="--", lw=1.2, label=r"Heuristic $\lambda = 0.1 \operatorname{tr}(F^\top F)/D$")
for value, count in selected.items():
    ax.scatter(value, path.loc[value], s=25 + 10 * count, color="#4C72B0", zorder=4)
ax.set_xscale("log")
ax.set_xlabel(r"Regularization ratio $\lambda / \lambda_{\mathrm{scale}}$")
ax.set_ylabel("Median OOS absolute error")
ax.set_title(r"Lorenz63: Nested temporal $\lambda$ selection")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False, fontsize=8)
save(fig, "fig_supp_lambda_selection.pdf")


# 2. Atractor de Lorenz y shock sintético (integrador RK4).
n_feature_points = 3000
rng = np.random.RandomState(LORENZ_SEED)
state = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
n_total = LORENZ_N_BURNIN + n_feature_points * LORENZ_SKIP
dt = LORENZ_DT
traj = np.zeros((n_total, 3))
for i in range(n_total):
    k1 = lorenz_rhs(state)
    k2 = lorenz_rhs(state + dt / 2 * k1)
    k3 = lorenz_rhs(state + dt / 2 * k2)
    k4 = lorenz_rhs(state + dt * k3)
    state = state + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    traj[i] = state
sub_traj = traj[LORENZ_N_BURNIN:][::LORENZ_SKIP]

fig, ax = plt.subplots(figsize=(W_SINGLE, 2.8))
ax.scatter(sub_traj[:, 0], sub_traj[:, 2], s=0.3, alpha=0.4, color="#4C72B0", rasterized=True)
# Outlier puntual
shock_pt = np.array([sub_traj[500, 0] + 15.0 * sub_traj[:, 0].std(), sub_traj[500, 2]])
ax.scatter(shock_pt[0], shock_pt[1], s=45, color="#C44E52", marker="x", lw=2, label=r"Synthetic outlier ($+15\sigma$)")
ax.set_xlabel("$x(t)$ (Observable)")
ax.set_ylabel("$z(t)$")
ax.set_title("Lorenz63: Attractor & Off-manifold Shock")
ax.legend(loc="upper right", frameon=False, fontsize=8)
save(fig, "fig2b_lorenz_atractor.pdf")


# 3. Sensibilidad del QLIKE al piso positivo (FX/cripto).
#    sensibilidad_piso_qlike.csv nunca existio; los datos ya estan en oos_univariado.csv
#    con columnas qlike_floor_1e-12..1e-06 (una por piso) y una fila por ventana/modo.
piso_file = BASE / "experimento_diario_fx_cripto/output/oos_univariado.csv"
if not piso_file.exists():
    raise FileNotFoundError(
        f"Missing required source file for Figure 3 (QLIKE floor sensitivity): {piso_file}. "
        "This block must fail loudly instead of silently skipping -- a stale/wrong figure "
        "left in place is worse than a crashed build."
    )
df_uni = pd.read_csv(piso_file)
floor_cols = {
    "qlike_floor_1e-12": 1e-12,
    "qlike_floor_1e-10": 1e-10,
    "qlike_floor_1e-08": 1e-8,
    "qlike_floor_1e-06": 1e-6,
}
missing_cols = [c for c in floor_cols if c not in df_uni.columns]
if missing_cols:
    raise KeyError(f"oos_univariado.csv is missing expected floor columns: {missing_cols}")

med_by_mode = df_uni.groupby("mode")[list(floor_cols.keys())].median()
floors = list(floor_cols.values())

fig, ax = plt.subplots(figsize=(W_SINGLE * 1.7, 3.4))
for m, row in med_by_mode.iterrows():
    label = "Ridge NG-RC" if "ridge" in m else ("Non-negative NNLS" if "nonneg" in m else ("Sparse ESN (log)" if "ssrc" in m else m))
    color = "#C44E52" if "ridge" in m else ("#55A868" if "nonneg" in m else ("#4C72B0" if "ssrc" in m else "#8C8C8C"))
    lw = 1.8 if "nonneg" in m or "ridge" in m else 1.2
    ax.plot(floors, row.values, marker="s" if "nonneg" in m else "o", ms=4, lw=lw, color=color, label=label)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"Positivity floor $\epsilon$ used by QLIKE")
ax.set_ylabel("Median QLIKE")
ax.set_title("Sensitivity of QLIKE to the evaluation floor (FX/crypto)", fontsize=10)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=False, fontsize=7)
save(fig, "fig13_qlike_piso_fx.pdf")

print("Figures successfully generated in English in paper_chaos_aip/figures/")
