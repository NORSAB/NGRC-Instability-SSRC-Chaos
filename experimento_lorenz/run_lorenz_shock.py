"""
Experimento de control: Lorenz63, el benchmark CLASICO de NG-RC (Gauthier et al. 2021,
tambien usado por arXiv:2505.00846, arXiv:2407.08641, arXiv:2507.08738: todos SOLO en
regimen limpio, sin shocks). Comparte solo las utilidades causales de ``lorenz_common``;
no importa ni ejecuta los otros experimentos. El SSRC de control es recurrente: cada estado
usa W_res y el estado anterior.

Dos preguntas:
  1. Control positivo: ¿el pipeline reproduce el comportamiento esperado de la literatura
     en el sistema donde NG-RC es conocido por funcionar bien? (trayectoria limpia, sin shock)
  2. Extension que la literatura NO prueba: se inyecta UN shock sintetico (spike aditivo de
     magnitud conocida en un punto conocido) sobre una trayectoria por lo demas limpia: la prueba mas controlada posible de si kappa(cov(F)) se dispara por el shock en si
     (aislado de todo el ruido real de mercado que trae FX/cripto), y si el lector NNLS/
     regularizado sostiene mejor el pronostico OOS alrededor del shock que OLS/Ridge.

Target: x(t+1) directo (NO x(t+1)^2: a diferencia del experimento de volatilidad FX, aqui
NO hay razon a priori de no-negatividad; si NNLS igual ayuda, es evidencia independiente).

Salida: output/kappa_lorenz.csv, output/oos_lorenz.csv, output/resumen_lorenz.md
"""
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
DT_INTEGRATE = 0.01       # paso fino de RK4 (precision numerica)
SKIP = 5                  # Submuestreo temporal: dt_feature = SKIP * dt_integrate = 0.05 (Gauthier et al. 2021)
N_BURNIN_INTEGRATE = 5000
N_FEATURE_POINTS = 30000
N_STEPS_INTEGRATE = N_FEATURE_POINTS * SKIP
SEED = 7
K = 3
T_TRAIN = 500
STEP = 20
SHOCK_T = 20000           # indice (en la serie YA sub-muestreada) donde se inyecta el shock
SHOCK_MAGNITUDE_SIGMA = 15.0  # tamano del spike en unidades de desviacion estandar de x
RES_DIM = 50


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
    """Integra a paso fino (precision) y sub-muestrea cada `skip` pasos para las features
    NG-RC (dt_feature = dt_integrate*skip): evita la cuasi-colinealidad de sobremuestreo."""
    n_total = n_burnin + n_feature_points * skip
    traj = simulate_lorenz(n_total, dt_integrate, seed=seed)
    traj = traj[n_burnin:]
    return traj[::skip]  # (n_feature_points, 3)


def ngrc_features(x, k):
    """Identico en definicion a los otros dos experimentos: constante EXCLUIDA (fix del
    12-ago), lineal(delays) + cuadratico. x: (T,). Retorna F (T-k, D) alineado a
    y[i] = x[i+k] (prediccion 1 paso adelante: NO al cuadrado, a diferencia del target
    de volatilidad FX)."""
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


print(f"Simulando Lorenz63 (RK4, dt_integracion={DT_INTEGRATE}, skip={SKIP} -> "
      f"dt_feature={DT_INTEGRATE*SKIP})...")
traj = simulate_and_subsample(N_FEATURE_POINTS, SKIP, DT_INTEGRATE, N_BURNIN_INTEGRATE)
x_clean = traj[:, 0]
x_clean = standardize_from_prefix(x_clean, T_TRAIN)
print(f"  {len(x_clean)} puntos; normalizacion ajustada solo con los primeros {T_TRAIN}")

x_shock = x_clean.copy()
x_shock[SHOCK_T] += SHOCK_MAGNITUDE_SIGMA  # spike aditivo de un solo punto, magnitud conocida
print(f"  Shock inyectado en t={SHOCK_T}, magnitud={SHOCK_MAGNITUDE_SIGMA} sigma")

kappa_rows = []
for label, x in (("limpio", x_clean), ("con_shock", x_shock)):
    F_all, y_all = ngrc_features(x, K)
    shock_idx_al = SHOCK_T - K if label == "con_shock" else None
    for t0 in range(T_TRAIN, len(F_all), STEP):
        window = F_all[t0 - T_TRAIN:t0]
        has_shock = (shock_idx_al is not None) and (t0 - T_TRAIN <= shock_idx_al < t0)
        kr, kl = kappa_raw_lw(window)
        kappa_rows.append(dict(escenario=label, t0=t0, kappa_raw=kr, kappa_lw=kl,
                               ventana_incluye_shock=bool(has_shock)))

df_kappa = pd.DataFrame(kappa_rows)
df_kappa.to_csv("output/kappa_lorenz.csv", index=False)

oos_rows = []
w_in, w_res = None, None
for label, x in (("limpio", x_clean), ("con_shock", x_shock)):
    F_all, y_all = ngrc_features(x, K)
    if w_in is None:
        w_in, w_res = make_ssrc(F_all.shape[1], RES_DIM, seed=SEED)
    H_all, _ = ssrc_states(F_all, w_in, w_res)
    shock_idx_al = SHOCK_T - K if label == "con_shock" else None
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
            metadata = {**empty_selection_metadata(), **metadata}
            oos_rows.append(dict(escenario=label, t0=t0, mode=mode,
                                 ventana_incluye_shock=bool(has_shock), mase=mase,
                                 **metadata))
        mase_naive = abs(y_test - naive_pred) / (naive_mae + 1e-12)
        oos_rows.append(dict(escenario=label, t0=t0, mode="naive",
                             ventana_incluye_shock=bool(has_shock), mase=mase_naive,
                             **empty_selection_metadata()))

df_oos = pd.DataFrame(oos_rows)
df_oos.to_csv("output/oos_lorenz.csv", index=False)

kappa_summary = (df_kappa.groupby(["escenario", "ventana_incluye_shock"])
                 .agg(kappa_raw_mediana=("kappa_raw", "median"),
                      kappa_raw_max=("kappa_raw", "max"), n=("kappa_raw", "count"))
                 .reset_index())
oos_summary = (df_oos.groupby(["escenario", "mode", "ventana_incluye_shock"])
               .agg(mase_mediana=("mase", "median"), n=("mase", "count"))
               .reset_index())

with open("output/resumen_lorenz.md", "w", encoding="utf-8") as f:
    f.write("# Lorenz63: kappa y pronostico OOS, limpio vs con shock sintetico\n\n")
    f.write(f"Shock: spike aditivo de {SHOCK_MAGNITUDE_SIGMA} sigma en t={SHOCK_T} (indice interno).\n\n")
    f.write("## kappa(cov(F)) por escenario\n\n")
    f.write(kappa_summary.to_markdown(index=False))
    f.write("\n\n## MASE OOS por escenario/metodo\n\n")
    f.write(oos_summary.to_markdown(index=False))
    f.write("\n\nRidge y el readout del SSRC seleccionan lambda mediante validación temporal interna. "
            "La heurística 0.1*traza(X'X)/D se incluye como referencia analítica.\n")

print("\n==== kappa por escenario ====")
print(kappa_summary.to_string(index=False))
print("\n==== MASE OOS por escenario/metodo ====")
print(oos_summary.to_string(index=False))
print("\nGuardado en output/")
