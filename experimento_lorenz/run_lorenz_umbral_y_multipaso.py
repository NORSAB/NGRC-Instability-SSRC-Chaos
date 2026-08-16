"""
Lorenz63: umbral geométrico del shock y pronóstico multipaso causal.

Tarea 1: ¿existe un umbral de magnitud (>30 sigma) donde "shock baja kappa" se invierte?
Tarea 2: ruido de medicion con pronostico ITERADO multi-paso (H=5, H=10) -- ¿cambia la
         conclusion de que Ridge/NNLS no le ganan a OLS con ruido?

El guion comparte ``lorenz_common`` y no importa otros scripts ejecutables. Mismo patron:
RK4 dt_integracion=0.01, skip=5 -> dt_feature=0.05, bloque NG-RC K=3 sin constante,
T_TRAIN=500, paso=20 (Tarea 1) / paso=40 (Tarea 2, mas caro por el horizonte iterado).
El SSRC se actualiza con W_res en cada paso; Ridge y su readout seleccionan lambda con
validacion temporal interna dentro de cada ventana de entrenamiento.
"""
import numpy as np
import pandas as pd
from lorenz_common import (
    empty_selection_metadata,
    fit_readout,
    make_ssrc,
    predict_readout,
    ssrc_states,
    ssrc_step,
    standardize_from_prefix,
)
import warnings
warnings.filterwarnings("ignore")

SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
DT_INTEGRATE = 0.01
SKIP = 5
N_BURNIN_INTEGRATE = 5000
N_FEATURE_POINTS = 30000
SEED = 7
K = 3
T_TRAIN = 500
RES_DIM = 50


def lorenz_rhs(s):
    x, y, z = s
    return np.array([SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z])


def simulate_and_subsample(n_feature_points, skip, dt, n_burnin, seed=SEED):
    rng = np.random.RandomState(seed)
    state = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
    n_total = n_burnin + n_feature_points * skip
    traj = np.zeros((n_total, 3))
    for i in range(n_total):
        k1 = lorenz_rhs(state); k2 = lorenz_rhs(state + dt / 2 * k1)
        k3 = lorenz_rhs(state + dt / 2 * k2); k4 = lorenz_rhs(state + dt * k3)
        state = state + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[i] = state
    return traj[n_burnin:][::skip]


def ngrc_features(x, k):
    T = len(x); n_rows = T - k
    lin = np.array([x[t:t + k] for t in range(n_rows)])
    n = lin.shape[1]
    quad = np.array([lin[:, i] * lin[:, j] for i in range(n) for j in range(i, n)]).T
    F = np.hstack([lin, quad])
    return F, x[k:]


# =====================================================================
# TAREA 1: umbral de inversion de kappa arriba de 30 sigma
# =====================================================================
print("=== TAREA 1: umbral de inversion de kappa (magnitudes 40-200 sigma) ===")
traj = simulate_and_subsample(N_FEATURE_POINTS, SKIP, DT_INTEGRATE, N_BURNIN_INTEGRATE)
x_base = traj[:, 0]
x_base = standardize_from_prefix(x_base, T_TRAIN)

UBICACIONES = [5000, 10000, 15000, 20000, 25000]
MAGNITUDES = [40, 50, 75, 100, 150, 200]
SIGNOS = [1, -1]
filas_umbral = []

for ubic in UBICACIONES:
    for mag in MAGNITUDES:
        for signo in SIGNOS:
            xs = x_base.copy()
            xs[ubic] += signo * mag
            F_all, _ = ngrc_features(xs, K)
            shock_idx = ubic - K
            # ventana de calma de referencia (lejos del shock) y ventana que lo incluye
            t0_shock = shock_idx + 250  # shock queda dentro de los 500 puntos previos
            if t0_shock - T_TRAIN < 0 or t0_shock >= F_all.shape[0]:
                continue
            F_shock_win = F_all[t0_shock - T_TRAIN:t0_shock]
            # ventana de calma: la misma ubicacion relativa pero SIN el shock (serie limpia)
            F_calma_win = ngrc_features(x_base, K)[0][t0_shock - T_TRAIN:t0_shock]
            k_shock = float(np.linalg.cond(np.cov(F_shock_win, rowvar=False)))
            k_calma = float(np.linalg.cond(np.cov(F_calma_win, rowvar=False)))
            ratio = k_shock / k_calma if k_calma > 0 else np.nan
            filas_umbral.append(dict(ubicacion=ubic, magnitud_sigma=mag, signo=signo,
                                     kappa_shock=k_shock, kappa_calma=k_calma, ratio=ratio))

df_umbral = pd.DataFrame(filas_umbral)
df_umbral.to_csv("output/kappa_umbral_extendido.csv", index=False)
resumen_umbral = df_umbral.groupby("magnitud_sigma")["ratio"].agg(["median", "min", "max"]).reset_index()
print(resumen_umbral.to_string(index=False))
cruce = resumen_umbral[resumen_umbral["median"] >= 1.0]
if len(cruce):
    print(f"\nCRUCE detectado: ratio mediana >= 1.0 a partir de magnitud={cruce.iloc[0]['magnitud_sigma']}sigma")
else:
    print(f"\nNO se detecto cruce hasta {MAGNITUDES[-1]}sigma. Ratio mediana maxima observada: "
         f"{resumen_umbral['median'].max():.4f} en magnitud={resumen_umbral.loc[resumen_umbral['median'].idxmax(),'magnitud_sigma']}sigma")

# =====================================================================
# TAREA 2: ruido de medicion, pronostico ITERADO multi-paso
# =====================================================================
print("\n=== TAREA 2: ruido de medicion, pronostico iterado (H=5, H=10) ===")
F_probe, _ = ngrc_features(x_base, K)
w_in, w_res = make_ssrc(F_probe.shape[1], RES_DIM, seed=SEED)

NIVELES_RUIDO = [0.0, 0.05, 0.1, 0.2, 0.5]
HORIZONTES = [5, 10]
STEP2 = 60  # mas caro que Tarea 1 (cada punto requiere H pasos iterados), paso mas largo
SEMILLAS_RUIDO = [1, 2, 3]

filas_multipaso = []
y_clean_all = ngrc_features(x_base, K)[1]
for H in HORIZONTES:
    for sigma_ruido in NIVELES_RUIDO:
        for semilla in (SEMILLAS_RUIDO if sigma_ruido > 0 else [0]):
            rng = np.random.RandomState(1000 + semilla)
            if sigma_ruido > 0:
                ruido = rng.normal(0, sigma_ruido, size=x_base.shape)
                x_noisy = x_base + ruido
            else:
                x_noisy = x_base.copy()
            F_all, y_all = ngrc_features(x_noisy, K)
            H_all, _ = ssrc_states(F_all, w_in, w_res)

            for t0 in range(T_TRAIN, len(F_all) - H, STEP2):
                F_train, y_train = F_all[t0 - T_TRAIN:t0], y_all[t0 - T_TRAIN:t0]
                naive_mae = np.mean(np.abs(np.diff(y_train)))
                y_true_h_clean = y_clean_all[t0:t0 + H]

                for mode in ("ols", "ridge", "nnls", "ssrc"):
                    try:
                        H_train = H_all[t0 - T_TRAIN:t0] if mode == "ssrc" else None
                        w, metadata = fit_readout(F_train, y_train, mode, H_train=H_train)
                    except Exception:
                        continue
                    # pronostico iterado: la prediccion de un paso alimenta el siguiente
                    # F[t0] usa x[t0:t0+K]; por tanto el ultimo dato conocido al origen
                    # es x[t0+K-1]. La version anterior arrancaba K-1 pasos demasiado atras.
                    hist = list(x_noisy[t0:t0 + K])
                    state = H_all[t0 - 1].copy() if mode == "ssrc" else None
                    errs = []
                    for h in range(H):
                        lin = np.array(hist[-K:])
                        n = len(lin)
                        quad = np.array([lin[i] * lin[j] for i in range(n) for j in range(i, n)])
                        F_step = np.hstack([lin, quad])
                        try:
                            if mode == "ssrc":
                                state = ssrc_step(F_step, state, w_in, w_res)
                            yhat = predict_readout(F_step, w, mode, H_row=state)
                        except Exception:
                            yhat = np.nan
                        errs.append(abs(y_true_h_clean[h] - yhat) if h < len(y_true_h_clean) else np.nan)
                        hist.append(yhat)
                    mase_h = np.nanmean(errs) / (naive_mae + 1e-12)
                    metadata = {**empty_selection_metadata(), **metadata}
                    filas_multipaso.append(dict(H=H, sigma_ruido=sigma_ruido, semilla=semilla,
                                                t0=t0, mode=mode, mase_acumulado=mase_h,
                                                **metadata))
                # naive iterado: repite el ultimo valor conocido para los H pasos
                naive_val = x_noisy[t0 + K - 1]
                errs_n = [abs(y_true_h_clean[h] - naive_val) for h in range(min(H, len(y_true_h_clean)))]
                filas_multipaso.append(dict(H=H, sigma_ruido=sigma_ruido, semilla=semilla,
                                            t0=t0, mode="naive",
                                            mase_acumulado=np.mean(errs_n) / (naive_mae + 1e-12),
                                            **empty_selection_metadata()))

df_multi = pd.DataFrame(filas_multipaso)
df_multi.to_csv("output/mase_ruido_multipaso.csv", index=False)
resumen_multi = (df_multi.groupby(["H", "sigma_ruido", "mode"])["mase_acumulado"]
                .median().unstack("mode").reset_index())
print(resumen_multi.to_string(index=False))
resumen_multi.to_csv("output/resumen_mase_ruido_multipaso.csv", index=False)

print("\nGuardado: output/kappa_umbral_extendido.csv, output/mase_ruido_multipaso.csv, "
     "output/resumen_mase_ruido_multipaso.csv")
