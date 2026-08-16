"""
Tarea 2 (seguimiento a HALLAZGO_lorenz.md): ruido de medicion como tercera dimension del
experimento Lorenz63. Referencia: arXiv:2211.05262 "Stabilizing Machine Learning Prediction
of Dynamics: Noise and Noise-inspired Regularization" -- hipotesis del documento de avance:
el mal condicionamiento de F es dañino especificamente cuando se combina con un objetivo
RUIDOSO; en Lorenz limpio y determinista (HALLAZGO_lorenz.md) ridge/nnls NO le ganan a OLS
a pesar de kappa~1e6. Aqui se prueba si añadir ruido de MEDICION (gaussiano, en x) hace que
ridge/nnls empiecen a ganarle a OLS, y en que nivel ocurre el cruce (si ocurre).

Misma simulacion, mismo bloque NG-RC (K=3, sin constante), mismos lectores
(ols/ridge/nnls/SSRC recurrente/naive), mismas ventanas (T_TRAIN=500, STEP=20).

Ruido: gaussiano, sigma_ruido in {0, 0.01, 0.05, 0.1, 0.2, 0.5} (fraccion de la desviacion
estandar de x, que ya esta normalizada a 1), aplicado a x ANTES de construir el bloque NG-RC
(afecta rezagos lineales y cuadraticos por igual). Dos variantes de target:
  - "target_limpio"  (prioridad, caso estandar en la literatura): F se construye con x RUIDOSO,
    pero y = x_limpio(t+1) (el modelo intenta recuperar la dinamica subyacente).
  - "target_ruidoso": F y target ambos con x RUIDOSO (el modelo predice la observacion ruidosa).
Se promedia sobre N_SEEDS realizaciones de ruido independientes por nivel para reducir
varianza de muestreo de una sola realizacion.

Salida:
  - output/mase_vs_ruido.csv         -- resumen: nivel x variante x modo, mediana sobre
                                         semillas (y su dispersion) de la mediana-de-ventana MASE
  - output/mase_vs_ruido_semillas.csv -- detalle: una fila por nivel x variante x semilla x modo
"""
import time
import numpy as np
import pandas as pd
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
SEED = 7
K = 3
T_TRAIN = 500
STEP = 20
RES_DIM = 50

NOISE_LEVELS = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5]
N_SEEDS = 5
NOISE_SEED_BASE = 1000
VARIANTS = ["target_limpio", "target_ruidoso"]


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


def ngrc_features_split(x_input, x_target, k):
    """Construye F desde x_input (rezagos lineales+cuadraticos) y el target y desde
    x_target -- permite separar el x usado para las features del x usado como objetivo
    (necesario para la variante 'target_limpio': F ruidoso, y limpio)."""
    T = len(x_input)
    n_rows = T - k
    lin = np.array([x_input[t:t + k] for t in range(n_rows)])
    n = lin.shape[1]
    quad = np.array([lin[:, i] * lin[:, j] for i in range(n) for j in range(i, n)]).T
    F = np.hstack([lin, quad])
    y = x_target[k:]
    return F, y


def sweep_oos(F_all, y_all, w_in, w_res):
    """Sweep OOS causal; SSRC recorre la serie una sola vez, sin mirar al futuro."""
    rows = []
    H_all, _ = ssrc_states(F_all, w_in, w_res)
    for t0 in range(T_TRAIN, len(F_all) - 1, STEP):
        F_train, y_train = F_all[t0 - T_TRAIN:t0], y_all[t0 - T_TRAIN:t0]
        F_test, y_test = F_all[t0], y_all[t0]
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
            rows.append(dict(mode=mode, mase=mase,
                             **{**empty_selection_metadata(), **metadata}))
        mase_naive = abs(y_test - naive_pred) / (naive_mae + 1e-12)
        rows.append(dict(mode="naive", mase=mase_naive, **empty_selection_metadata()))
    return rows


t_start = time.time()
print(f"Simulando Lorenz63 (RK4, dt_integracion={DT_INTEGRATE}, skip={SKIP} -> "
      f"dt_feature={DT_INTEGRATE*SKIP})...")
traj = simulate_and_subsample(N_FEATURE_POINTS, SKIP, DT_INTEGRATE, N_BURNIN_INTEGRATE)
x_clean = traj[:, 0]
x_clean = standardize_from_prefix(x_clean, T_TRAIN)
print(f"  {len(x_clean)} puntos; normalizacion ajustada solo con los primeros {T_TRAIN}")

F_probe, _ = ngrc_features_split(x_clean, x_clean, K)
w_in, w_res = make_ssrc(F_probe.shape[1], RES_DIM, seed=SEED)

detail_rows = []
n_total = len(NOISE_LEVELS) * N_SEEDS * len(VARIANTS)
i_run = 0
for level in NOISE_LEVELS:
    seeds_here = [0] if level == 0.0 else list(range(N_SEEDS))  # sin ruido, no hay que repetir
    for seed_i in seeds_here:
        rng = np.random.RandomState(NOISE_SEED_BASE + seed_i * 100 + int(level * 1000))
        noise = rng.normal(0, level, size=len(x_clean)) if level > 0 else np.zeros_like(x_clean)
        x_noisy = x_clean + noise
        for variant in VARIANTS:
            i_run += 1
            if level == 0.0 and variant == "target_ruidoso":
                # con ruido=0, target_limpio == target_ruidoso exactamente: no repetir computo
                F_all, y_all = ngrc_features_split(x_clean, x_clean, K)
            elif variant == "target_limpio":
                F_all, y_all = ngrc_features_split(x_noisy, x_clean, K)
            else:  # target_ruidoso
                F_all, y_all = ngrc_features_split(x_noisy, x_noisy, K)
            rows = sweep_oos(F_all, y_all, w_in, w_res)
            for row in rows:
                detail_rows.append(dict(nivel_ruido=level, variante=variant, semilla=seed_i,
                                         **row))
            elapsed = time.time() - t_start
            print(f"  [{i_run}/{n_total}] nivel={level} semilla={seed_i} variante={variant} "
                  f"({elapsed:.1f}s acumulado)")

df_detail_raw = pd.DataFrame(detail_rows)
# mediana por ventana -> una fila por (nivel, variante, semilla, modo)
df_seed_median = (df_detail_raw.groupby(["nivel_ruido", "variante", "semilla", "mode"])
                   .agg(mase_mediana=("mase", "median"),
                        lambda_mediana=("lambda_elegida", "median"),
                        lambda_relativa_mediana=("lambda_relativa", "median"),
                        n_ventanas=("mase", "count"))
                   .reset_index())
df_seed_median.to_csv("output/mase_vs_ruido_semillas.csv", index=False)

# resumen: promedio (y dispersion) sobre semillas de la mediana-de-ventana MASE
resumen = (df_seed_median.groupby(["nivel_ruido", "variante", "mode"])
           .agg(mase_media_semillas=("mase_mediana", "mean"),
                mase_std_semillas=("mase_mediana", "std"),
                n_semillas=("mase_mediana", "count"))
           .reset_index())
resumen.to_csv("output/mase_vs_ruido.csv", index=False)

print("\n==== MASE vs nivel de ruido (promedio sobre semillas), variante target_limpio ====")
piv = resumen[resumen.variante == "target_limpio"].pivot_table(
    index="nivel_ruido", columns="mode", values="mase_media_semillas")
print(piv.to_string())
print("\n==== MASE vs nivel de ruido (promedio sobre semillas), variante target_ruidoso ====")
piv2 = resumen[resumen.variante == "target_ruidoso"].pivot_table(
    index="nivel_ruido", columns="mode", values="mase_media_semillas")
print(piv2.to_string())

# ¿hay cruce donde ridge o nnls le ganan a ols?
print("\n==== ¿ridge/nnls superan a ols? (target_limpio) ====")
for level in NOISE_LEVELS:
    row = piv.loc[level] if level in piv.index else None
    if row is None:
        continue
    ols_v = row.get("ols", np.nan)
    ridge_v = row.get("ridge", np.nan)
    nnls_v = row.get("nnls", np.nan)
    print(f"  nivel={level}: ols={ols_v:.4f} ridge={ridge_v:.4f} "
          f"({'RIDGE GANA' if ridge_v < ols_v else 'ols gana'}) nnls={nnls_v:.4f} "
          f"({'NNLS GANA' if nnls_v < ols_v else 'ols gana'})")

print(f"\nTotal: {time.time()-t_start:.1f}s. Guardado en output/")
