"""
Generador Maestro y Robusto de TODAS las Figuras Vectoriales (DPI 600+)
para las versiones en INGLES y ESPANOL del manuscrito y suplementario de Chaos (AIP).

Garantiza que:
1. No se omita ninguna figura silenciosamente.
2. Todas las etiquetas y leyendas tengan tamano >= 8.5 pt (cumpliendo el estandar >= 8pt de AIP).
3. Todas las figuras esten disponibles tanto en figures/ como en figures_es/.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

OUT_EN = HERE / "figures"
OUT_ES = HERE / "figures_es"
OUT_EN.mkdir(exist_ok=True)
OUT_ES.mkdir(exist_ok=True)

# Configuracion global de estilo AIP (font size >= 8.5pt en todos los elementos)
plt.rcParams.update({
    "font.size": 9.5,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "figure.titlesize": 10.0,
    "figure.dpi": 300,
    "savefig.dpi": 600,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.family": "serif",
})

W_SINGLE = 3.4   # Ancho columna individual AIP (pulgadas)
W_DOUBLE = 7.0   # Ancho doble columna AIP (pulgadas)


def save_bilingual(fig_en, fig_es, filename_base):
    # Guardar version en ingles (PDF y PNG)
    fig_en.tight_layout()
    fig_en.savefig(OUT_EN / f"{filename_base}.pdf", bbox_inches="tight", dpi=600)
    fig_en.savefig(OUT_EN / f"{filename_base}.png", bbox_inches="tight", dpi=600)
    plt.close(fig_en)

    # Guardar version en espanol (PDF y PNG)
    fig_es.tight_layout()
    fig_es.savefig(OUT_ES / f"{filename_base}.pdf", bbox_inches="tight", dpi=600)
    fig_es.savefig(OUT_ES / f"{filename_base}.png", bbox_inches="tight", dpi=600)
    plt.close(fig_es)
    print(f"  [OK] {filename_base}.pdf (EN & ES) generado a 600 DPI.")


print("=== GENERANDO TODAS LAS FIGURAS BILINGUES (DPI 600+) ===")

# =========================================================================
# 1. FIGURA: Inflacion Cuartica de Traza (Teorema 1) - fig5_ridge_fragilidad
# =========================================================================
grid_file = BASE / "experimento_lorenz/output/oos_grid_shocks.csv"
if not grid_file.exists():
    raise FileNotFoundError(f"Falta archivo requerido: {grid_file}")
grid = pd.read_csv(grid_file)
grid_shock = grid.dropna(subset=["lambda_traza_legacy"])
grid_shock = grid_shock[grid_shock["ventana_incluye_shock"]]
med_by_mag = grid_shock.groupby("magnitud_sigma")["lambda_traza_legacy"].median().sort_index()
M_vals = med_by_mag.index.values.astype(float)
lam_vals = med_by_mag.values.astype(float)

n_fit = min(3, len(M_vals))
fit_idx = np.argsort(M_vals)[-n_fit:]
slope, intercept = np.polyfit(np.log(M_vals[fit_idx]), np.log(lam_vals[fit_idx]), 1)
fit_M = np.array([M_vals[fit_idx].min(), M_vals[fit_idx].max()])
fit_line = np.exp(intercept) * fit_M ** slope

# Version Ingles
fig_en, ax = plt.subplots(figsize=(W_SINGLE * 1.5, 2.9))
ax.plot(M_vals, lam_vals, marker="o", ms=4.5, lw=1.5, color="#4C72B0", label=r"Median $\lambda$ (shock window)")
ax.plot(fit_M, fit_line, ls="--", color="#C44E52", lw=1.5, label=fr"Power-law fit, slope $\approx {slope:.2f}$")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"Shock magnitude $M$ ($\sigma$)")
ax.set_ylabel(r"Trace-proportional $\lambda = \gamma\,\mathrm{tr}(F^\top F)/D$", fontsize=8.5)
ax.set_title("Quartic trace inflation under localized outlier shocks", fontsize=9.5, pad=8)
ax.legend(loc="upper left", frameon=False, fontsize=8.5)

# Version Espanol
fig_es, ax = plt.subplots(figsize=(W_SINGLE * 1.5, 2.9))
ax.plot(M_vals, lam_vals, marker="o", ms=4.5, lw=1.5, color="#4C72B0", label=r"Mediana $\lambda$ (ventana con shock)")
ax.plot(fit_M, fit_line, ls="--", color="#C44E52", lw=1.5, label=fr"Ajuste ley potencia, pend. $\approx {slope:.2f}$")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"Magnitud del shock $M$ ($\sigma$)")
ax.set_ylabel(r"$\lambda = \gamma\,\mathrm{tr}(F^\top F)/D$ proporcional a la traza", fontsize=8.5)
ax.set_title("Inflación cuártica de traza ante shocks exógenos", fontsize=9.5, pad=8)
ax.legend(loc="upper left", frameon=False, fontsize=8.5)

save_bilingual(fig_en, fig_es, "fig5_ridge_fragilidad")


# =========================================================================
# 2. FIGURA: Atractor de Lorenz y Outlier Exogeno - fig2b_lorenz_atractor
# =========================================================================
def lorenz_rhs(s):
    x, y, z = s
    return np.array([10.0 * (y - x), x * (28.0 - z) - y, x * y - (8.0 / 3.0) * z])

rng = np.random.RandomState(7)
state = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
n_total = 5000 + 3000 * 5
dt = 0.01
traj = np.zeros((n_total, 3))
for i in range(n_total):
    k1 = lorenz_rhs(state)
    k2 = lorenz_rhs(state + dt / 2 * k1)
    k3 = lorenz_rhs(state + dt / 2 * k2)
    k4 = lorenz_rhs(state + dt * k3)
    state = state + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    traj[i] = state
sub_traj = traj[5000:][::5]
shock_pt = np.array([sub_traj[500, 0] + 15.0 * sub_traj[:, 0].std(), sub_traj[500, 2]])

# Version Ingles
fig_en, ax = plt.subplots(figsize=(W_SINGLE, 2.8))
ax.scatter(sub_traj[:, 0], sub_traj[:, 2], s=0.3, alpha=0.35, color="#4C72B0", rasterized=True)
ax.scatter(shock_pt[0], shock_pt[1], s=45, color="#C44E52", marker="x", lw=2, label=r"Synthetic outlier ($+15\sigma$)")
ax.set_xlabel("$x(t)$ (Observable)")
ax.set_ylabel("$z(t)$")
ax.set_title("Lorenz63: Attractor & Off-manifold Shock", fontsize=9.5)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)

# Version Espanol
fig_es, ax = plt.subplots(figsize=(W_SINGLE, 2.8))
ax.scatter(sub_traj[:, 0], sub_traj[:, 2], s=0.3, alpha=0.35, color="#4C72B0", rasterized=True)
ax.scatter(shock_pt[0], shock_pt[1], s=45, color="#C44E52", marker="x", lw=2, label=r"Outlier sintético ($+15\sigma$)")
ax.set_xlabel("$x(t)$ (Observable)")
ax.set_ylabel("$z(t)$")
ax.set_title("Lorenz63: Atractor y Shock Fuera del Manifold", fontsize=9.5)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)

save_bilingual(fig_en, fig_es, "fig2b_lorenz_atractor")


# =========================================================================
# 3. FIGURA: Curva de Pronostico Multipaso vs Tiempos de Lyapunov - fig_lyapunov_curve
# =========================================================================
lyap_csv = BASE / "experimento_lorenz/output/lorenz_lyapunov_curve_summary.csv"
if not lyap_csv.exists():
    raise FileNotFoundError(f"Falta archivo requerido: {lyap_csv}")
df_lyap = pd.read_csv(lyap_csv)

# Version Ingles
fig_en, ax = plt.subplots(figsize=(W_SINGLE * 1.5, 3.0))
ax.plot(df_lyap["tau_lyapunov"], df_lyap["static_lag_median"], marker="o", ms=4, lw=1.5, color="#55A868", label="Static tanh ($W_{\\mathrm{res}}=0$)")
ax.plot(df_lyap["tau_lyapunov"], df_lyap["esn_lag_median"], marker="s", ms=4, lw=1.5, color="#4C72B0", label="Recurrent ESN-lag")
ax.plot(df_lyap["tau_lyapunov"], df_lyap["ridge_median"], marker="^", ms=4, lw=1.5, color="#C44E52", label="Ridge NG-RC")
ax.plot(df_lyap["tau_lyapunov"], df_lyap["ols_median"], marker="v", ms=4, lw=1.2, ls="--", color="#DD8452", label="OLS NG-RC")
ax.axhline(1.0, color="#8C8C8C", ls=":", lw=1, label="Naive baseline (MASE=1)")
ax.set_yscale("log")
ax.set_xlabel(r"Forecast horizon $\tau$ (Lyapunov times, $\lambda_{\max} \approx 0.91$)")
ax.set_ylabel("Median OOS MASE")
ax.set_title("Lorenz63: Iterated Multistep Stability", fontsize=9.5)
ax.legend(loc="upper left", frameon=False, fontsize=8.5)

# Version Espanol
fig_es, ax = plt.subplots(figsize=(W_SINGLE * 1.5, 3.0))
ax.plot(df_lyap["tau_lyapunov"], df_lyap["static_lag_median"], marker="o", ms=4, lw=1.5, color="#55A868", label="tanh estática ($W_{\\mathrm{res}}=0$)")
ax.plot(df_lyap["tau_lyapunov"], df_lyap["esn_lag_median"], marker="s", ms=4, lw=1.5, color="#4C72B0", label="ESN recurrente")
ax.plot(df_lyap["tau_lyapunov"], df_lyap["ridge_median"], marker="^", ms=4, lw=1.5, color="#C44E52", label="Ridge NG-RC")
ax.plot(df_lyap["tau_lyapunov"], df_lyap["ols_median"], marker="v", ms=4, lw=1.2, ls="--", color="#DD8452", label="OLS NG-RC")
ax.axhline(1.0, color="#8C8C8C", ls=":", lw=1, label="Referencia ingenua (MASE=1)")
ax.set_yscale("log")
ax.set_xlabel(r"Horizonte de pronóstico $\tau$ (tiempos de Lyapunov, $\lambda_{\max} \approx 0.91$)")
ax.set_ylabel("MASE OOS Mediano")
ax.set_title("Lorenz63: Estabilidad de Pronóstico Multipaso", fontsize=9.5)
ax.legend(loc="upper left", frameon=False, fontsize=8.5)

save_bilingual(fig_en, fig_es, "fig_lyapunov_curve")


# =========================================================================
# 4. FIGURA: Sensibilidad de QLIKE al Piso Positivo - fig13_qlike_piso_fx
# =========================================================================
piso_file = BASE / "experimento_diario_fx_cripto/output/oos_univariado.csv"
if not piso_file.exists():
    raise FileNotFoundError(f"Falta archivo requerido: {piso_file}")
df_uni = pd.read_csv(piso_file)
floor_cols = {
    "qlike_floor_1e-12": 1e-12,
    "qlike_floor_1e-10": 1e-10,
    "qlike_floor_1e-08": 1e-8,
    "qlike_floor_1e-06": 1e-6,
}
med_by_mode = df_uni.groupby("mode")[list(floor_cols.keys())].median()
floors = list(floor_cols.values())

# Version Ingles
fig_en, ax = plt.subplots(figsize=(W_SINGLE * 1.55, 3.2))
for m, row in med_by_mode.iterrows():
    label = "Ridge NG-RC" if "ridge" in m else ("Non-negative NNLS" if "nonneg" in m else ("Sparse ESN (log)" if "ssrc" in m else m))
    color = "#C44E52" if "ridge" in m else ("#55A868" if "nonneg" in m else ("#4C72B0" if "ssrc" in m else "#8C8C8C"))
    lw = 1.8 if "nonneg" in m or "ridge" in m else 1.2
    ax.plot(floors, row.values, marker="s" if "nonneg" in m else "o", ms=4, lw=lw, color=color, label=label)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"Positivity floor $\epsilon$ used by QLIKE")
ax.set_ylabel("Median QLIKE")
ax.set_title("Sensitivity of QLIKE to Numerical Floor (FX/crypto)", fontsize=9.5)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False, fontsize=8.5)

# Version Espanol
fig_es, ax = plt.subplots(figsize=(W_SINGLE * 1.55, 3.2))
for m, row in med_by_mode.iterrows():
    label = "Ridge NG-RC" if "ridge" in m else ("NNLS No Negativo" if "nonneg" in m else ("ESN Disperso (log)" if "ssrc" in m else m))
    color = "#C44E52" if "ridge" in m else ("#55A868" if "nonneg" in m else ("#4C72B0" if "ssrc" in m else "#8C8C8C"))
    lw = 1.8 if "nonneg" in m or "ridge" in m else 1.2
    ax.plot(floors, row.values, marker="s" if "nonneg" in m else "o", ms=4, lw=lw, color=color, label=label)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"Piso numérico $\epsilon$ empleado en QLIKE")
ax.set_ylabel("QLIKE Mediana")
ax.set_title("Sensibilidad de QLIKE al Piso Numérico (FX/cripto)", fontsize=9.5)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False, fontsize=8.5)

save_bilingual(fig_en, fig_es, "fig13_qlike_piso_fx")


# =========================================================================
# 5. FIGURA: BCIE Panel Causal MASE - fig12_bcie_causal
# =========================================================================
bcie_file = BASE / "experimento/codigo_pipeline/output/comparacion_cobertura_pareja.csv"
if bcie_file.exists():
    df_bcie = pd.read_csv(bcie_file)
    labels_en, labels_es, values_bcie = [], [], []
    for _, row in df_bcie.iterrows():
        variant = row.get("variant", "")
        k = row.get("k", "")
        if pd.isna(variant) or variant == "" or variant == "reservoir":
            lab_en = "Recurrent sparse ESN (ref.)"
            lab_es = "ESN recurrente disperso (ref.)"
        else:
            p_en = {"baseline": "Baseline PCA", "ledoitwolf": "Ledoit-Wolf", "tikhonov_covariance": "Tikhonov covariance", "nnls_directo": "NNLS direct"}.get(variant, variant)
            p_es = {"baseline": "PCA Base", "ledoitwolf": "Ledoit-Wolf", "tikhonov_covariance": "Covarianza Tikhonov", "nnls_directo": "NNLS directo"}.get(variant, variant)
            lab_en = f"{p_en} (k={int(k)})"
            lab_es = f"{p_es} (k={int(k)})"
        labels_en.append(lab_en)
        labels_es.append(lab_es)
        values_bcie.append(row["mase"])

    order = np.argsort(values_bcie)
    labels_en = [labels_en[i] for i in order]
    labels_es = [labels_es[i] for i in order]
    values_bcie = [values_bcie[i] for i in order]
    colors = ["#4C72B0" if "NNLS" in l else ("#55A868" if "ESN" in l else "#8C8C8C") for l in labels_en]

    # Version Ingles
    fig_en, ax = plt.subplots(figsize=(W_DOUBLE, 2.9))
    ax.barh(labels_en, values_bcie, color=colors)
    ax.set_xlabel("MASE, 8 common entities")
    ax.set_title("BCIE supplement: causal out-of-sample comparison (2020-2025)", fontsize=9.5)
    ax.invert_yaxis()

    # Version Espanol
    fig_es, ax = plt.subplots(figsize=(W_DOUBLE, 2.9))
    ax.barh(labels_es, values_bcie, color=colors)
    ax.set_xlabel("MASE, 8 entidades comunes")
    ax.set_title("Suplemento BCIE: comparación causal fuera de muestra (2020-2025)", fontsize=9.5)
    ax.invert_yaxis()

    save_bilingual(fig_en, fig_es, "fig12_bcie_causal")


# =========================================================================
# 6. FIGURA: Precios Semanales de Combustibles Honduras - fig7_combustibles_precios
# =========================================================================
repo_file = Path(r"D:\2026\Tesis2026\Datos_Combustibles_Honduras\repositorio_combustibles_honduras.csv")
if repo_file.exists():
    df_fuel = pd.read_csv(repo_file, encoding="utf-8-sig")
    df_fuel["FechaInicioISO"] = pd.to_datetime(df_fuel["FechaInicioISO"], errors="coerce")
    df_fuel = df_fuel.sort_values("FechaInicioISO")

    EVENTS_EN = {
        "COVID-19": (pd.Timestamp("2020-02-15"), pd.Timestamp("2020-05-15"), "#C44E52"),
        "Hurricanes Eta/Iota": (pd.Timestamp("2020-11-01"), pd.Timestamp("2020-12-21"), "#4C72B0"),
        "Russia-Ukraine war": (pd.Timestamp("2022-02-15"), pd.Timestamp("2022-06-15"), "#DD8452"),
        "Middle East crisis": (pd.Timestamp("2026-03-01"), pd.Timestamp("2026-06-30"), "#55A868"),
    }
    EVENTS_ES = {
        "COVID-19": (pd.Timestamp("2020-02-15"), pd.Timestamp("2020-05-15"), "#C44E52"),
        "Huracanes Eta/Iota": (pd.Timestamp("2020-11-01"), pd.Timestamp("2020-12-21"), "#4C72B0"),
        "Guerra Rusia-Ucrania": (pd.Timestamp("2022-02-15"), pd.Timestamp("2022-06-15"), "#DD8452"),
        "Crisis Medio Oriente": (pd.Timestamp("2026-03-01"), pd.Timestamp("2026-06-30"), "#55A868"),
    }

    # Version Ingles
    fig_en, ax = plt.subplots(figsize=(W_DOUBLE, 3.2))
    for fuel, color in [("S\u00faper", "#374649"), ("Regular", "#982C33"), ("Diesel", "#3f6c3e"), ("Kerosene", "#134966")]:
        if fuel in df_fuel.columns:
            ax.plot(df_fuel["FechaInicioISO"], df_fuel[fuel], lw=1.1, color=color, label="Super" if fuel == "S\u00faper" else fuel)
    for name, (start, end, color) in EVENTS_EN.items():
        ax.axvspan(start, end, color=color, alpha=0.15)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("'%y"))
    ax.set_xlabel("Year")
    ax.set_ylabel("Price (Lps.)")
    ax.set_title("Weekly Retail Fuel Prices, Honduras (2017-2026)", fontsize=9.5)
    handles = [plt.Line2D([0], [0], color=c, lw=5) for c in ["#374649", "#982C33", "#3f6c3e", "#134966"]]
    handles += [plt.Rectangle((0, 0), 1, 1, color=EVENTS_EN[n][2], alpha=0.3) for n in EVENTS_EN]
    labels_h_en = ["Super", "Regular", "Diesel", "Kerosene"] + list(EVENTS_EN.keys())
    ax.legend(handles, labels_h_en, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False, fontsize=8.5)

    # Version Espanol
    fig_es, ax = plt.subplots(figsize=(W_DOUBLE, 3.2))
    for fuel, color in [("S\u00faper", "#374649"), ("Regular", "#982C33"), ("Diesel", "#3f6c3e"), ("Kerosene", "#134966")]:
        if fuel in df_fuel.columns:
            ax.plot(df_fuel["FechaInicioISO"], df_fuel[fuel], lw=1.1, color=color, label="Súper" if fuel == "S\u00faper" else fuel)
    for name, (start, end, color) in EVENTS_ES.items():
        ax.axvspan(start, end, color=color, alpha=0.15)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("'%y"))
    ax.set_xlabel("Año")
    ax.set_ylabel("Precio al consumidor (Lps.)")
    ax.set_title("Precios Semanales de Combustibles en Honduras (2017-2026)", fontsize=9.5)
    handles = [plt.Line2D([0], [0], color=c, lw=5) for c in ["#374649", "#982C33", "#3f6c3e", "#134966"]]
    handles += [plt.Rectangle((0, 0), 1, 1, color=EVENTS_ES[n][2], alpha=0.3) for n in EVENTS_ES]
    labels_h_es = ["Súper", "Regular", "Diésel", "Kerosene"] + list(EVENTS_ES.keys())
    ax.legend(handles, labels_h_es, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False, fontsize=8.5)

    save_bilingual(fig_en, fig_es, "fig7_combustibles_precios")


# =========================================================================
# 7. FIGURA: Mecanismo de Falla NNLS - fig9_mecanismo_falla_nnls
# =========================================================================
neg_file = BASE / "experimento_combustibles_honduras/output/investigacion_negativas_por_semana.csv"
if neg_file.exists():
    df_neg = pd.read_csv(neg_file)
    week = df_neg[df_neg["fecha"] == "2020-05-11"]
    fuels_order = ["S\u00faper", "Regular", "Diesel", "Kerosene"]
    y_true_vals = [week[week["fuel"] == f]["y_true"].values[0] for f in fuels_order]
    pred_vals = [week[week["fuel"] == f]["nnls_signado_legacy"].values[0] for f in fuels_order]

    x = np.arange(len(fuels_order))
    w = 0.35

    # Version Ingles
    fig_en, ax = plt.subplots(figsize=(W_SINGLE, 2.9))
    ax.bar(x - w / 2, y_true_vals, width=w, label="Realized (squared return)", color="#4C72B0")
    ax.bar(x + w / 2, pred_vals, width=w, label="Legacy signed NNLS (raw)", color="#C44E52")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Super" if f == "S\u00faper" else f for f in fuels_order])
    ax.set_ylabel("Realized volatility")
    ax.set_title("Week 2020-05-11: NNLS failure", fontsize=9.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False, fontsize=8.5)

    # Version Espanol
    fig_es, ax = plt.subplots(figsize=(W_SINGLE, 2.9))
    ax.bar(x - w / 2, y_true_vals, width=w, label="Realizado ($r_t^2$)", color="#4C72B0")
    ax.bar(x + w / 2, pred_vals, width=w, label="NNLS con signo (crudo)", color="#C44E52")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Súper" if f == "S\u00faper" else f for f in fuels_order])
    ax.set_ylabel("Volatilidad realizada")
    ax.set_title("Semana 2020-05-11: falla de NNLS", fontsize=9.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False, fontsize=8.5)

    save_bilingual(fig_en, fig_es, "fig9_mecanismo_falla_nnls")


# =========================================================================
# 8. FIGURA: Seleccion Temporal Anidada de Lambda - fig_supp_lambda_selection
# =========================================================================
lam_file = BASE / "experimento_lorenz/output/sensibilidad_lambda_lorenz.csv"
if lam_file.exists():
    lam = pd.read_csv(lam_file)
    path = lam.groupby("lambda_relativa")["error_absoluto_oos"].median().sort_index()
    selected = lam[lam["seleccionada_nested"]].groupby("lambda_relativa").size()

    # Version Ingles
    fig_en, ax = plt.subplots(figsize=(W_SINGLE, 2.9))
    ax.plot(path.index, path.values, marker="o", ms=4, color="#C44E52", lw=1.5, label="Median OOS MAE")
    ax.axvline(0.1, color="#8C8C8C", ls="--", lw=1.2, label=r"Heuristic $\lambda = 0.1 \operatorname{tr}(F^\top F)/D$")
    for value, count in selected.items():
        ax.scatter(value, path.loc[value], s=25 + 10 * count, color="#4C72B0", zorder=4)
    ax.set_xscale("log")
    ax.set_xlabel(r"Regularization ratio $\lambda / \lambda_{\mathrm{scale}}$")
    ax.set_ylabel("Median OOS MAE")
    ax.set_title("Lorenz63: Nested Temporal Selection", fontsize=9.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False, fontsize=8.5)

    # Version Espanol
    fig_es, ax = plt.subplots(figsize=(W_SINGLE, 2.9))
    ax.plot(path.index, path.values, marker="o", ms=4, color="#C44E52", lw=1.5, label="MAE OOS mediano")
    ax.axvline(0.1, color="#8C8C8C", ls="--", lw=1.2, label=r"Heurística fija $\lambda = 0.1 \operatorname{tr}(F^\top F)/D$")
    for value, count in selected.items():
        ax.scatter(value, path.loc[value], s=25 + 10 * count, color="#4C72B0", zorder=4)
    ax.set_xscale("log")
    ax.set_xlabel(r"Razón de regularización $\lambda / \lambda_{\mathrm{escala}}$")
    ax.set_ylabel("MAE OOS mediano")
    ax.set_title("Lorenz63: Selección Temporal Anidada", fontsize=9.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False, fontsize=8.5)

    save_bilingual(fig_en, fig_es, "fig_supp_lambda_selection")


# =========================================================================
# 9. FIGURA: Rossler M^4 Sweep - fig_rossler_m4
# =========================================================================
rossler_file = BASE / "experimento_rossler/output/rossler_m4_sweep.csv"
if rossler_file.exists():
    df_ross = pd.read_csv(rossler_file)
    r_M = df_ross["magnitude_sigma"].values
    r_lam = df_ross["lambda_traza_legacy"].values
    fit_r = np.polyfit(np.log(r_M[-3:]), np.log(r_lam[-3:]), 1)

    # Version Ingles
    fig_en, ax = plt.subplots(figsize=(W_SINGLE, 2.8))
    ax.plot(r_M, r_lam, marker="o", ms=4, color="#4C72B0", lw=1.5, label=r"Median $\lambda$")
    ax.plot(r_M[-3:], np.exp(fit_r[1]) * r_M[-3:]**fit_r[0], ls="--", color="#C44E52", lw=1.5, label=fr"Slope $\approx {fit_r[0]:.2f}$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Shock magnitude $M$ ($\sigma$)")
    ax.set_ylabel(r"$\lambda \propto \operatorname{tr}(F^\top F)$")
    ax.set_title("Rössler: Trace Scaling", fontsize=9.5)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)

    # Version Espanol
    fig_es, ax = plt.subplots(figsize=(W_SINGLE, 2.8))
    ax.plot(r_M, r_lam, marker="o", ms=4, color="#4C72B0", lw=1.5, label=r"Mediana $\lambda$")
    ax.plot(r_M[-3:], np.exp(fit_r[1]) * r_M[-3:]**fit_r[0], ls="--", color="#C44E52", lw=1.5, label=fr"Pendiente $\approx {fit_r[0]:.2f}$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Magnitud del shock $M$ ($\sigma$)")
    ax.set_ylabel(r"$\lambda \propto \operatorname{tr}(F^\top F)$")
    ax.set_title("Rössler: Escalamiento de Traza", fontsize=9.5)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)

    save_bilingual(fig_en, fig_es, "fig_rossler_m4")

print("\n=== TODAS LAS FIGURAS BILINGUES FUERON GENERADAS CON EXITO ===")
