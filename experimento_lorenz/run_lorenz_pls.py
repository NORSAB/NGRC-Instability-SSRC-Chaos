"""
Experimento Lorenz63: PLS(1) supervisado frente a OLS/Ridge/NNLS/SSRC recurrente.

Contexto (ver documento de avance, S2, y HALLAZGO_lorenz.md): se demostro que Ridge y
Ledoit-Wolf (regularizadores que suman lambda*I o encogen hacia la identidad) NO cambian la
direccion del eigenvector dominante de PCA -- solo estabilizan numericamente cual eigenvector
"gana" cuando hay valores propios casi empatados. Por eso Ridge y Ledoit-Wolf dieron MASE
identico entre si en experimentos anteriores. Pregunta: ¿un regularizador que SI pueda cambiar
la direccion de compresion -- porque usa informacion del target, no solo de la covarianza de
F -- ayuda mas? Aqui se prueba Partial Least Squares de 1 componente (PLS1): la direccion de
proyeccion se elige maximizando cov(F_t w, y_t+1), no solo var(F_t w).

El guion comparte ``lorenz_common`` y no importa los scripts ejecutables de esta carpeta.
Reproduce el patron de run_lorenz_shock.py: Lorenz63 RK4 dt_integracion=0.01, sub-muestreado
cada skip=5 pasos -> dt_feature=0.05; bloque NG-RC K=3 SIN columna constante; T_TRAIN=500,
paso=20, target=x_{t+1} directo (no al cuadrado).

Salida: output/mase_pls_cca.csv, HALLAZGO_pls_regularizador.md
"""
import numpy as np
import pandas as pd
from lorenz_common import (
    empty_selection_metadata,
    fit_readout as fit_regular_readout,
    make_ssrc,
    predict_readout,
    ssrc_states,
    standardize_from_prefix,
)
import warnings
warnings.filterwarnings("ignore")

SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
DT_INTEGRATE = 0.01
SKIP = 5                  # dt_feature = 0.05, igual a Gauthier et al. 2021 / run_lorenz_shock.py
N_BURNIN_INTEGRATE = 5000
N_FEATURE_POINTS = 30000
SEED = 7
K = 3
T_TRAIN = 500
STEP = 20
SHOCK_T = 20000            # misma ubicacion/magnitud que run_lorenz_shock.py, para comparabilidad
SHOCK_MAGNITUDE_SIGMA = 15.0
RES_DIM = 50

try:
    from sklearn.cross_decomposition import PLSRegression
    HAVE_SKLEARN_PLS = True
except Exception:
    HAVE_SKLEARN_PLS = False


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
    """Identico a run_lorenz_shock.py: constante EXCLUIDA, lineal(delays) + cuadratico."""
    T = len(x)
    n_rows = T - k
    lin = np.array([x[t:t + k] for t in range(n_rows)])
    n = lin.shape[1]
    quad = np.array([lin[:, i] * lin[:, j] for i in range(n) for j in range(i, n)]).T
    F = np.hstack([lin, quad])
    y = x[k:]
    return F, y


def fit_pls1_manual(F_train, y_train):
    """PLS1 univariado a mano (fallback si sklearn no esta disponible): w = F_c.T @ y_c
    normalizado, luego regresion 1-D de y sobre la proyeccion t = F_c @ w."""
    F_mean = F_train.mean(axis=0)
    y_mean = y_train.mean()
    F_c = F_train - F_mean
    y_c = y_train - y_mean
    w = F_c.T @ y_c
    norm = np.linalg.norm(w)
    if norm < 1e-12:
        w = np.zeros_like(w)
    else:
        w = w / norm
    t = F_c @ w                      # score de 1 componente
    b = (t @ y_c) / (t @ t + 1e-12)  # regresion escalar t -> y
    return dict(F_mean=F_mean, y_mean=y_mean, w=w, b=b)


def predict_pls1_manual(F_row, params):
    t = (F_row - params["F_mean"]) @ params["w"]
    return float(params["y_mean"] + params["b"] * t)


def fit_readout(F_train, y_train, mode, H_train=None):
    if mode == "pls":
        if HAVE_SKLEARN_PLS:
            model = PLSRegression(n_components=1)
            model.fit(F_train, y_train)
            return None, model, {}
        else:
            params = fit_pls1_manual(F_train, y_train)
            return None, params, {}
    weights, metadata = fit_regular_readout(F_train, y_train, mode, H_train=H_train)
    return weights, None, metadata


def predict(F_row, w, mode, model=None, H_row=None):
    if mode == "pls":
        if HAVE_SKLEARN_PLS:
            return float(np.asarray(model.predict(F_row.reshape(1, -1))).ravel()[0])
        else:
            return predict_pls1_manual(F_row, model)
    return predict_readout(F_row, w, mode, H_row=H_row)


def run_protocol(x, label, modes, w_in=None, w_res=None, shock_idx_al=None):
    """Reproduce el protocolo OOS de run_lorenz_shock.py para una serie x dada."""
    F_all, y_all = ngrc_features(x, K)
    H_all, _ = ssrc_states(F_all, w_in, w_res)
    rows = []
    for t0 in range(T_TRAIN, len(F_all) - 1, STEP):
        F_train, y_train = F_all[t0 - T_TRAIN:t0], y_all[t0 - T_TRAIN:t0]
        F_test, y_test = F_all[t0], y_all[t0]
        has_shock = (shock_idx_al is not None) and (t0 - T_TRAIN <= shock_idx_al < t0)
        naive_pred = y_all[t0 - 1]
        naive_mae = np.mean(np.abs(np.diff(y_train)))
        for mode in modes:
            try:
                H_train = H_all[t0 - T_TRAIN:t0] if mode == "ssrc" else None
                w, model, metadata = fit_readout(F_train, y_train, mode, H_train=H_train)
                yhat = predict(
                    F_test, w, mode, model=model,
                    H_row=H_all[t0] if mode == "ssrc" else None,
                )
            except Exception:
                continue
            mase = abs(y_test - yhat) / (naive_mae + 1e-12)
            metadata = {**empty_selection_metadata(), **metadata}
            rows.append(dict(escenario=label, t0=t0, mode=mode,
                             ventana_incluye_shock=bool(has_shock), mase=mase,
                             **metadata))
        mase_naive = abs(y_test - naive_pred) / (naive_mae + 1e-12)
        rows.append(dict(escenario=label, t0=t0, mode="naive",
                         ventana_incluye_shock=bool(has_shock), mase=mase_naive,
                         **empty_selection_metadata()))
    return rows


print(f"sklearn PLSRegression disponible: {HAVE_SKLEARN_PLS}")
print(f"Simulando Lorenz63 (RK4, dt_integracion={DT_INTEGRATE}, skip={SKIP} -> "
      f"dt_feature={DT_INTEGRATE*SKIP})...")
traj = simulate_and_subsample(N_FEATURE_POINTS, SKIP, DT_INTEGRATE, N_BURNIN_INTEGRATE)
x_clean = traj[:, 0]
x_clean = standardize_from_prefix(x_clean, T_TRAIN)
print(f"  {len(x_clean)} puntos; normalizacion ajustada solo con los primeros {T_TRAIN}")

F_probe, _ = ngrc_features(x_clean, K)
w_in, w_res = make_ssrc(F_probe.shape[1], RES_DIM, seed=SEED)
print(f"  D features (K={K}, sin constante) = {F_probe.shape[1]}")

# ---- FASE 1: protocolo calma, sin shock (ols, ridge, nnls, SSRC, pls, naive) ----
MODES_CALMA = ("ols", "ridge", "nnls", "ssrc", "pls")
print("\nFase 1: protocolo calma (sin shock) -- ols, ridge, nnls, ssrc, pls, naive...")
rows_calma = run_protocol(x_clean, "calma", MODES_CALMA, w_in=w_in, w_res=w_res, shock_idx_al=None)
df_calma = pd.DataFrame(rows_calma)

resumen_calma = (df_calma.groupby("mode").agg(mase_mediana=("mase", "median"),
                                               mase_media=("mase", "mean"),
                                               n=("mase", "count")).reset_index()
                  .sort_values("mase_mediana"))
print("\n==== MASE OOS, calma (mediana) ====")
print(resumen_calma.to_string(index=False))

mase_ols = float(resumen_calma.loc[resumen_calma["mode"] == "ols", "mase_mediana"].iloc[0])
mase_pls = float(resumen_calma.loc[resumen_calma["mode"] == "pls", "mase_mediana"].iloc[0])
pls_mejora_ols = mase_pls < mase_ols
print(f"\nPLS vs OLS (calma): mase_pls={mase_pls:.4f}, mase_ols={mase_ols:.4f}, "
      f"PLS mejora={pls_mejora_ols}")

# ---- FASE 2: si PLS mejora sobre OLS, probar UNA config de shock (+15 sigma en t=20000) ----
all_rows = list(rows_calma)
resumen_shock = None
if pls_mejora_ols:
    print(f"\nPLS mejoro sobre OLS en calma -> probando shock unico "
          f"(+{SHOCK_MAGNITUDE_SIGMA} sigma en t={SHOCK_T})...")
    x_shock = x_clean.copy()
    x_shock[SHOCK_T] += SHOCK_MAGNITUDE_SIGMA
    shock_idx_al = SHOCK_T - K
    rows_shock = run_protocol(x_shock, "con_shock", MODES_CALMA, w_in=w_in, w_res=w_res,
                              shock_idx_al=shock_idx_al)
    all_rows.extend(rows_shock)
    df_shock = pd.DataFrame(rows_shock)
    resumen_shock = (df_shock.groupby(["mode", "ventana_incluye_shock"])
                     .agg(mase_mediana=("mase", "median"), n=("mase", "count")).reset_index()
                     .sort_values(["mode", "ventana_incluye_shock"]))
    print("\n==== MASE OOS, con_shock (mediana, por ventana con/sin shock) ====")
    print(resumen_shock.to_string(index=False))
else:
    print("\nPLS NO mejoro sobre OLS en calma -> se omite la fase de shock "
          "(instrucciones: solo investigar shock si PLS ayuda en calma).")

df_all = pd.DataFrame(all_rows)
df_all.to_csv("output/mase_pls_cca.csv", index=False)
print("\nGuardado output/mase_pls_cca.csv")

resumen_calma.to_csv("output/resumen_mase_pls_calma.csv", index=False)
if resumen_shock is not None:
    resumen_shock.to_csv("output/resumen_mase_pls_shock.csv", index=False)
