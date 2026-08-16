"""
Tarea 1 (seguimiento a HALLAZGO_lorenz.md): grilla de shocks sintéticos sobre Lorenz63 —
ubicación x magnitud x signo — para confirmar o acotar el patrón "shock BAJA kappa(cov(F))"
encontrado con un solo shock (t=20000, +15 sigma, n=25 ventanas).

El guion comparte ``lorenz_common`` y no importa ``run_lorenz_shock.py``, por lo que no
ejecuta otra corrida como efecto secundario. Misma simulación (RK4, dt_integracion=0.01, skip=5 ->
dt_feature=0.05), mismo bloque NG-RC (K=3, target x(t+1) directo, sin constante), mismos
lectores (ols/ridge/nnls/SSRC recurrente/naive), mismas ventanas (T_TRAIN=500, STEP=20).

Grilla:
  - Ubicaciones: t in {5000, 10000, 15000, 20000, 25000} (5 fases distintas del atractor)
  - Magnitudes: {5, 10, 15, 20, 30} sigma
  - Signo: {+1, -1}
  = 50 configuraciones. Para cada una: sweep COMPLETO de kappa(cov(F)) y MASE OOS sobre toda
  la trayectoria (igual que run_lorenz_shock.py), clasificando cada ventana como
  "incluye_shock" o "calma" (comparable, mismo T=500) dentro de la MISMA corrida.

Salida:
  - output/kappa_grid_shocks.csv   -- kappa por ventana, las 50 configuraciones (completo)
  - output/oos_grid_shocks.csv     -- MASE OOS por ventana/lector, las 50 configuraciones (completo)
  - output/resumen_grid_shocks.csv -- una fila por configuración, medianas agregadas
  - output/resumen_grid_shocks.md  -- version legible + agregado por magnitud (a traves de
    ubicacion y signo) para ver si hay una magnitud umbral donde el patron se invierte.
"""
import time
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from lorenz_common import (
    empty_selection_metadata,
    fit_readout,
    make_ssrc,
    predict_readout,
    ssrc_states,
    standardize_from_prefix,
)
import warnings
warnings.filterwarnings("ignore")

SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
DT_INTEGRATE = 0.01
SKIP = 5
N_BURNIN_INTEGRATE = 5000
N_FEATURE_POINTS = 30000
N_STEPS_INTEGRATE = N_FEATURE_POINTS * SKIP
SEED = 7
K = 3
T_TRAIN = 500
STEP = 20
RES_DIM = 50

LOCATIONS = [5000, 10000, 15000, 20000, 25000]
MAGNITUDES = [5, 10, 15, 20, 30]
SIGNS = [1, -1]


def lorenz_rhs(state):
    x, y, z = state
    return np.array([SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z])


def simulate_lorenz(n_steps, dt, seed=SEED):
    rng = np.random.RandomState(seed)
    state = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
    traj = np.zeros((n_steps, 3))
    for i in range(n_steps):
        k1 = lorenz_rhs(state)
        k2 = lorenz_rhs(state + dt / 2 * k1)
        k3 = lorenz_rhs(state + dt / 2 * k2)
        k4 = lorenz_rhs(state + dt * k3)
        state = state + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[i] = state
    return traj


def simulate_and_subsample(n_feature_points, skip, dt_integrate, n_burnin, seed=SEED):
    n_total = n_burnin + n_feature_points * skip
    traj = simulate_lorenz(n_total, dt_integrate, seed=seed)
    traj = traj[n_burnin:]
    return traj[::skip]


def ngrc_features(x, k):
    T = len(x)
    n_rows = T - k
    lin = np.array([x[t:t + k] for t in range(n_rows)])
    n = lin.shape[1]
    quad = np.array([lin[:, i] * lin[:, j] for i in range(n) for j in range(i, n)]).T
    F = np.hstack([lin, quad])
    y = x[k:]
    return F, y


def kappa_raw_lw(F_window):
    cov = np.cov(F_window, rowvar=False)
    kappa_raw = float(np.linalg.cond(cov))
    try:
        kappa_lw = float(np.linalg.cond(LedoitWolf().fit(F_window).covariance_))
    except Exception:
        kappa_lw = np.nan
    return kappa_raw, kappa_lw


def sweep_one_series(x, shock_loc, w_in, w_res):
    """Sweep completo de kappa y OOS-MASE sobre toda la serie x. shock_loc: indice (en la
    serie sub-muestreada) del punto shockeado, o None si no hay shock (serie limpia)."""
    F_all, y_all = ngrc_features(x, K)
    H_all, _ = ssrc_states(F_all, w_in, w_res)
    shock_idx_al = (shock_loc - K) if shock_loc is not None else None

    kappa_rows = []
    for t0 in range(T_TRAIN, len(F_all), STEP):
        window = F_all[t0 - T_TRAIN:t0]
        has_shock = (shock_idx_al is not None) and (t0 - T_TRAIN <= shock_idx_al < t0)
        kr, kl = kappa_raw_lw(window)
        kappa_rows.append((t0, kr, kl, has_shock))

    oos_rows = []
    for t0 in range(T_TRAIN, len(F_all) - 1, STEP):
        F_train, y_train = F_all[t0 - T_TRAIN:t0], y_all[t0 - T_TRAIN:t0]
        F_test, y_test = F_all[t0], y_all[t0]
        has_shock = (shock_idx_al is not None) and (t0 - T_TRAIN <= shock_idx_al < t0)
        naive_pred = y_all[t0 - 1]
        naive_mae = np.mean(np.abs(np.diff(y_train)))
        for mode in ("ols", "ridge", "nnls", "ssrc"):
            try:
                H_train = H_all[t0 - T_TRAIN:t0] if mode == "ssrc" else None
                w, metadata = fit_readout(F_train, y_train, mode, H_train=H_train)
                yhat = predict_readout(
                    F_test, w, mode, H_row=H_all[t0] if mode == "ssrc" else None
                )
            except Exception:
                continue
            mase = abs(y_test - yhat) / (naive_mae + 1e-12)
            oos_rows.append(dict(t0=t0, mode=mode, ventana_incluye_shock=bool(has_shock),
                                 mase=mase,
                                 **{**empty_selection_metadata(), **metadata}))
        mase_naive = abs(y_test - naive_pred) / (naive_mae + 1e-12)
        oos_rows.append(dict(t0=t0, mode="naive", ventana_incluye_shock=bool(has_shock),
                             mase=mase_naive, **empty_selection_metadata()))

    return kappa_rows, oos_rows


t_start = time.time()
print(f"Simulando Lorenz63 (RK4, dt_integracion={DT_INTEGRATE}, skip={SKIP} -> "
      f"dt_feature={DT_INTEGRATE*SKIP})...")
traj = simulate_and_subsample(N_FEATURE_POINTS, SKIP, DT_INTEGRATE, N_BURNIN_INTEGRATE)
x_clean = traj[:, 0]
x_clean = standardize_from_prefix(x_clean, T_TRAIN)
print(f"  {len(x_clean)} puntos; normalizacion ajustada solo con los primeros {T_TRAIN}")

F_probe, _ = ngrc_features(x_clean, K)
w_in, w_res = make_ssrc(F_probe.shape[1], RES_DIM, seed=SEED)

all_kappa = []
all_oos = []
n_configs = len(LOCATIONS) * len(MAGNITUDES) * len(SIGNS)
i_cfg = 0
for loc in LOCATIONS:
    for mag in MAGNITUDES:
        for sign in SIGNS:
            i_cfg += 1
            x_shock = x_clean.copy()
            x_shock[loc] += sign * mag
            kappa_rows, oos_rows = sweep_one_series(x_shock, loc, w_in, w_res)
            for (t0, kr, kl, has_shock) in kappa_rows:
                all_kappa.append(dict(ubicacion=loc, magnitud_sigma=mag, signo=sign, t0=t0,
                                       kappa_raw=kr, kappa_lw=kl,
                                       ventana_incluye_shock=bool(has_shock)))
            for row in oos_rows:
                all_oos.append(dict(ubicacion=loc, magnitud_sigma=mag, signo=sign, **row))
            elapsed = time.time() - t_start
            print(f"  [{i_cfg}/{n_configs}] loc={loc} mag={mag} signo={sign:+d} "
                  f"({elapsed:.1f}s acumulado)")

df_kappa = pd.DataFrame(all_kappa)
df_kappa.to_csv("output/kappa_grid_shocks.csv", index=False)

df_oos = pd.DataFrame(all_oos)
df_oos.to_csv("output/oos_grid_shocks.csv", index=False)

# ---- resumen por configuracion (una fila por ubicacion x magnitud x signo) ----
kappa_by_cfg = (df_kappa.groupby(["ubicacion", "magnitud_sigma", "signo", "ventana_incluye_shock"])
                .agg(kappa_raw_mediana=("kappa_raw", "median"), n=("kappa_raw", "count"))
                .reset_index())
kappa_wide = kappa_by_cfg.pivot_table(index=["ubicacion", "magnitud_sigma", "signo"],
                                       columns="ventana_incluye_shock",
                                       values=["kappa_raw_mediana", "n"])
kappa_wide.columns = ["_".join([str(c) for c in col]) for col in kappa_wide.columns]
kappa_wide = kappa_wide.rename(columns={
    "kappa_raw_mediana_False": "kappa_raw_mediana_calma",
    "kappa_raw_mediana_True": "kappa_raw_mediana_shock",
    "n_False": "n_ventanas_calma",
    "n_True": "n_ventanas_shock",
}).reset_index()
kappa_wide["kappa_ratio_shock_sobre_calma"] = (kappa_wide["kappa_raw_mediana_shock"]
                                                / kappa_wide["kappa_raw_mediana_calma"])
kappa_wide["patron_shock_baja_kappa"] = kappa_wide["kappa_ratio_shock_sobre_calma"] < 1.0

oos_by_cfg = (df_oos.groupby(["ubicacion", "magnitud_sigma", "signo", "mode",
                               "ventana_incluye_shock"])
              .agg(mase_mediana=("mase", "median")).reset_index())
oos_wide = oos_by_cfg.pivot_table(index=["ubicacion", "magnitud_sigma", "signo", "mode"],
                                   columns="ventana_incluye_shock", values="mase_mediana")
oos_wide.columns = ["mase_calma" if c is False else "mase_shock" for c in oos_wide.columns]
oos_wide = oos_wide.reset_index()
oos_wide["delta_mase_shock_menos_calma"] = oos_wide["mase_shock"] - oos_wide["mase_calma"]

# una fila por config x modo, con las columnas de kappa repetidas (mas facil de leer/filtrar
# que un pivot ancho por modo)
resumen = oos_wide.merge(
    kappa_wide[["ubicacion", "magnitud_sigma", "signo", "kappa_raw_mediana_calma",
                "kappa_raw_mediana_shock", "kappa_ratio_shock_sobre_calma",
                "patron_shock_baja_kappa", "n_ventanas_shock"]],
    on=["ubicacion", "magnitud_sigma", "signo"], how="left")
resumen.to_csv("output/resumen_grid_shocks.csv", index=False)

# ---- agregado por magnitud (a traves de ubicacion y signo): ¿hay umbral donde se invierte? ----
agg_by_mag = (kappa_wide.groupby("magnitud_sigma")
              .agg(kappa_ratio_mediana=("kappa_ratio_shock_sobre_calma", "median"),
                   kappa_ratio_min=("kappa_ratio_shock_sobre_calma", "min"),
                   kappa_ratio_max=("kappa_ratio_shock_sobre_calma", "max"),
                   frac_patron_baja=("patron_shock_baja_kappa", "mean"),
                   n_configs=("patron_shock_baja_kappa", "count"))
              .reset_index())

# ---- agregado por signo (a traves de ubicacion y magnitud): ¿importa el signo? ----
agg_by_signo = (kappa_wide.groupby("signo")
                .agg(kappa_ratio_mediana=("kappa_ratio_shock_sobre_calma", "median"),
                     frac_patron_baja=("patron_shock_baja_kappa", "mean"),
                     n_configs=("patron_shock_baja_kappa", "count"))
                .reset_index())

# ---- agregado por ubicacion (a traves de magnitud y signo) ----
agg_by_loc = (kappa_wide.groupby("ubicacion")
              .agg(kappa_ratio_mediana=("kappa_ratio_shock_sobre_calma", "median"),
                   frac_patron_baja=("patron_shock_baja_kappa", "mean"),
                   n_configs=("patron_shock_baja_kappa", "count"))
              .reset_index())

with open("output/resumen_grid_shocks.md", "w", encoding="utf-8") as f:
    f.write("# Grilla de shocks Lorenz63: kappa(cov(F)) y MASE OOS, 50 configuraciones\n\n")
    f.write(f"Ubicaciones: {LOCATIONS}. Magnitudes (sigma): {MAGNITUDES}. Signos: {SIGNS}.\n")
    f.write(f"T_TRAIN={T_TRAIN}, STEP={STEP}, K={K}. Sweep completo por configuracion "
            f"(no solo ventanas cercanas al shock).\n\n")
    f.write("## Kappa: ratio shock/calma por configuracion (< 1 = shock BAJA kappa, "
            "coincide con el hallazgo original)\n\n")
    f.write(kappa_wide[["ubicacion", "magnitud_sigma", "signo", "kappa_raw_mediana_calma",
                         "kappa_raw_mediana_shock", "kappa_ratio_shock_sobre_calma",
                         "n_ventanas_shock"]].to_markdown(index=False, floatfmt=".4g"))
    f.write("\n\n## Agregado por magnitud (a traves de 5 ubicaciones x 2 signos = 10 "
            "configuraciones por magnitud)\n\n")
    f.write(agg_by_mag.to_markdown(index=False, floatfmt=".4g"))
    f.write("\n\n## Agregado por signo (a traves de 5 ubicaciones x 5 magnitudes = 25 "
            "configuraciones por signo)\n\n")
    f.write(agg_by_signo.to_markdown(index=False, floatfmt=".4g"))
    f.write("\n\n## Agregado por ubicacion (a traves de 5 magnitudes x 2 signos = 10 "
            "configuraciones por ubicacion)\n\n")
    f.write(agg_by_loc.to_markdown(index=False, floatfmt=".4g"))
    f.write("\n")

print("\n==== Agregado por magnitud ====")
print(agg_by_mag.to_string(index=False))
print("\n==== Agregado por signo ====")
print(agg_by_signo.to_string(index=False))
print("\n==== Agregado por ubicacion ====")
print(agg_by_loc.to_string(index=False))
print(f"\nTotal: {time.time()-t_start:.1f}s. Guardado en output/")
