"""
Sensibilidad del ESN a hiperparametros del reservorio (dimension, radio espectral, leak rate),
sobre los dos regimenes que SI dependen de esos hiperparametros: filtrado de ruido y robustez
ante shocks localizados. El regimen limpio multipaso (H=5,10) no se incluye aqui porque el
mecanismo que prueba -saturacion acotada vs. divergencia polinomial- no depende de d_res/rho/leak
del reservorio (Ridge/OLS NG-RC no usan reservorio); esa conclusion ya esta establecida en
run_lorenz_30_seeds_ablation.py y no requiere una barrida de hiperparametros para sostenerse.

Esta es una revision de ROBUSTEZ, no una busqueda de hiperparametros: se reportan las 27
configuraciones completas (3 dimensiones x 3 radios espectrales x 3 leak rates), ninguna se
descarta ni se selecciona por su resultado OOS. Usa menos semillas (5 en vez de 30) y un paso mas
grueso que el experimento principal por costo computacional -es una revision de estabilidad
cualitativa, no un reemplazo del resultado principal de 30 semillas ya reportado en el paper.

Reutiliza make_ssrc/ssrc_states/select_ridge_lambda_temporal/standardize_from_prefix de
lorenz_common.py (las mismas funciones ya auditadas que usa el experimento principal). La
simulacion de la trayectoria Lorenz63 se duplica aqui deliberadamente (mismos parametros: seed=7,
dt=0.01, skip=5, burn-in=5000, 30000 puntos) porque importar run_lorenz_30_seeds_ablation.py
ejecutaria todo su experimento de 30 semillas como efecto secundario (no tiene guardia
__main__ aislable para solo la simulacion).

Salida: output/reservoir_hparam_sensitivity.csv, output/RESERVOIR_HPARAM_SENSITIVITY.md.
"""
from __future__ import annotations

import os
import time
import numpy as np
import pandas as pd

from lorenz_common import make_ssrc, select_ridge_lambda_temporal, ssrc_states, standardize_from_prefix

# ---- mismos parametros de trayectoria que run_lorenz_30_seeds_ablation.py ----
SIGMA, RHO_LORENZ, BETA = 10.0, 28.0, 8.0 / 3.0
DT_INTEGRATE = 0.01
SKIP = 5
N_BURNIN_INTEGRATE = 5000
N_FEATURE_POINTS = 30000
TRAJ_SEED = 7
K = 3
T_TRAIN = 500

# ---- reduccion de costo respecto al experimento principal (30 semillas, paso=40) ----
N_SEEDS = 5
SEEDS = [200 + i for i in range(N_SEEDS)]
STEP_NOISE = 150   # vs. 40 del experimento principal
N_NOISE_SEEDS = 3  # vs. 5 del experimento principal
NOISE_SIGMA = 0.1
SHOCK_MAGNITUDE = 15.0
SHOCK_LOCATIONS = [5000, 10000, 15000, 20000, 25000]
SHOCK_SIGNS = [-1, 1]

GRID_DRES = [25, 50, 100]
GRID_RHO = [0.5, 0.9, 0.99]
GRID_LEAK = [0.25, 0.5, 1.0]

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT_DIR, exist_ok=True)


def lorenz_rhs(s):
    x, y, z = s
    return np.array([SIGMA * (y - x), x * (RHO_LORENZ - z) - y, x * y - BETA * z])


def simulate_lorenz(n_points=N_FEATURE_POINTS, skip=SKIP, dt=DT_INTEGRATE,
                     n_burnin=N_BURNIN_INTEGRATE, seed=TRAJ_SEED):
    rng = np.random.RandomState(seed)
    state = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
    n_total = n_burnin + n_points * skip
    traj = np.zeros(n_total)
    for i in range(n_total):
        k1 = lorenz_rhs(state)
        k2 = lorenz_rhs(state + dt / 2 * k1)
        k3 = lorenz_rhs(state + dt / 2 * k2)
        k4 = lorenz_rhs(state + dt * k3)
        state = state + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[i] = state[0]
    return traj[n_burnin:][::skip]


def make_lags(x, k=K):
    n_rows = len(x) - k
    lags = np.array([x[t:t + k] for t in range(n_rows)])
    y = x[k:]
    return lags, y


print(f"=== Simulando trayectoria Lorenz63 (seed={TRAJ_SEED}, {N_FEATURE_POINTS} puntos) ===")
x_clean = simulate_lorenz()
x_clean_std = standardize_from_prefix(x_clean, T_TRAIN)
X_lags, y_target = make_lags(x_clean_std, K)
N_SAMPLES = len(X_lags)

window_starts_noise = list(range(0, N_SAMPLES - T_TRAIN - 15, STEP_NOISE))
print(f"Ventanas de ruido por semilla: {len(window_starts_noise)} (paso={STEP_NOISE})")

# Identificar la ubicacion problematica del experimento principal (si el archivo existe).
problem_location = None
cond_path = os.path.join(OUT_DIR, "lorenz_shock_by_condition.csv")
if os.path.exists(cond_path):
    df_cond = pd.read_csv(cond_path)
    df15 = df_cond[df_cond["regime"] == "shock_15sigma"]
    worst = df15.loc[df15["win_vs_ridge"].str.extract(r"(\d+)/")[0].astype(float).idxmin()]
    problem_location = int(worst["location"])
    print(f"Ubicacion problematica identificada del experimento principal: {problem_location}")


def eval_noise_filtering(d_res, rho, leak, seed):
    """MASE del ESN-lag vs proyeccion estatica, target limpio, entrada con ruido de medicion."""
    w_in, w_res = make_ssrc(d_in=K, d_res=d_res, rho=rho, density=0.1, seed=seed)
    diffs = []
    for noise_seed in range(N_NOISE_SEEDS):
        rng = np.random.RandomState(3000 + noise_seed)
        x_noisy = x_clean_std + rng.normal(0, NOISE_SIGMA, size=x_clean_std.shape)
        X_lags_noisy, _ = make_lags(x_noisy, K)
        n = min(len(X_lags_noisy), N_SAMPLES)
        H_esn, _ = ssrc_states(X_lags_noisy[:n], w_in, w_res, leak_rate=leak)
        H_static = np.tanh(X_lags_noisy[:n] @ w_in.T)
        for w_start in window_starts_noise:
            w_end = w_start + T_TRAIN
            test_idx = w_end
            if test_idx >= n:
                continue
            y_tr = y_target[w_start:w_end]
            y_te = y_target[test_idx]
            naive_mae_tr = max(float(np.mean(np.abs(np.diff(y_tr)))), 1e-6)

            w_esn, _ = select_ridge_lambda_temporal(H_esn[w_start:w_end], y_tr)
            p_esn = float(H_esn[test_idx] @ w_esn)
            mase_esn = abs(y_te - p_esn) / naive_mae_tr

            w_static, _ = select_ridge_lambda_temporal(H_static[w_start:w_end], y_tr)
            p_static = float(H_static[test_idx] @ w_static)
            mase_static = abs(y_te - p_static) / naive_mae_tr

            diffs.append(dict(mase_esn=mase_esn, mase_static=mase_static))
    d = pd.DataFrame(diffs)
    return dict(
        esn_median=float(d["mase_esn"].median()),
        static_median=float(d["mase_static"].median()),
        win_rate_esn=float((d["mase_esn"] < d["mase_static"]).mean()),
        n=len(d),
    )


def eval_shock(d_res, rho, leak, seed):
    """Por cada (ubicacion, signo): MASE del ESN-lag vs estatica en la ventana con shock."""
    w_in, w_res = make_ssrc(d_in=K, d_res=d_res, rho=rho, density=0.1, seed=seed)
    rows = []
    for loc in SHOCK_LOCATIONS:
        for sign in SHOCK_SIGNS:
            x_shk = x_clean_std.copy()
            if loc >= len(x_shk):
                continue
            x_shk[loc] = sign * SHOCK_MAGNITUDE
            X_lags_shk, _ = make_lags(x_shk, K)
            n = min(len(X_lags_shk), N_SAMPLES)
            w_start = max(0, loc - T_TRAIN)
            w_end = w_start + T_TRAIN
            test_idx = w_end
            if test_idx >= n or w_end > n:
                continue
            H_esn, _ = ssrc_states(X_lags_shk[:n], w_in, w_res, leak_rate=leak)
            H_static = np.tanh(X_lags_shk[:n] @ w_in.T)

            y_tr = y_target[w_start:w_end]
            y_te = y_target[test_idx]
            naive_mae_tr = max(float(np.mean(np.abs(np.diff(y_tr)))), 1e-6)

            w_esn, _ = select_ridge_lambda_temporal(H_esn[w_start:w_end], y_tr)
            p_esn = float(H_esn[test_idx] @ w_esn)
            mase_esn = abs(y_te - p_esn) / naive_mae_tr

            w_static, _ = select_ridge_lambda_temporal(H_static[w_start:w_end], y_tr)
            p_static = float(H_static[test_idx] @ w_static)
            mase_static = abs(y_te - p_static) / naive_mae_tr

            rows.append(dict(location=loc, sign=sign, mase_esn=mase_esn, mase_static=mase_static))
    return pd.DataFrame(rows)


records = []
t0 = time.time()
n_configs = len(GRID_DRES) * len(GRID_RHO) * len(GRID_LEAK)
cfg_i = 0
for d_res in GRID_DRES:
    for rho in GRID_RHO:
        for leak in GRID_LEAK:
            cfg_i += 1
            t_cfg = time.time()
            noise_by_seed = [eval_noise_filtering(d_res, rho, leak, seed) for seed in SEEDS]
            noise_win_rate = float(np.mean([r["win_rate_esn"] for r in noise_by_seed]))
            noise_esn_med = float(np.median([r["esn_median"] for r in noise_by_seed]))
            noise_static_med = float(np.median([r["static_median"] for r in noise_by_seed]))

            shock_frames = [eval_shock(d_res, rho, leak, seed) for seed in SEEDS]
            shock_all = pd.concat(shock_frames, ignore_index=True) if shock_frames else pd.DataFrame()
            if not shock_all.empty:
                shock_all["esn_wins"] = shock_all["mase_esn"] < shock_all["mase_static"]
                overall_win = float(shock_all["esn_wins"].mean())
                if problem_location is not None:
                    sub = shock_all[shock_all["location"] == problem_location]
                    problem_win = float(sub["esn_wins"].mean()) if len(sub) else float("nan")
                    problem_mase_ratio = float((sub["mase_esn"] / sub["mase_static"]).mean()) if len(sub) else float("nan")
                else:
                    problem_win = float("nan")
                    problem_mase_ratio = float("nan")
            else:
                overall_win = float("nan")
                problem_win = float("nan")
                problem_mase_ratio = float("nan")

            records.append(dict(
                d_res=d_res, rho=rho, leak=leak,
                noise_win_rate_esn=noise_win_rate,
                noise_esn_median=noise_esn_med,
                noise_static_median=noise_static_med,
                shock_overall_win_rate_esn=overall_win,
                shock_problem_location=problem_location,
                shock_problem_location_win_rate_esn=problem_win,
                shock_problem_location_mase_ratio_esn_over_static=problem_mase_ratio,
            ))
            print(f"[{cfg_i}/{n_configs}] d_res={d_res} rho={rho} leak={leak} "
                  f"-> noise_win={noise_win_rate:.2f} shock_win={overall_win:.2f} "
                  f"problem_loc_win={problem_win:.2f} ({time.time()-t_cfg:.1f}s)")

df_out = pd.DataFrame(records)
df_out.to_csv(os.path.join(OUT_DIR, "reservoir_hparam_sensitivity.csv"), index=False)
print(f"\nTotal: {time.time()-t0:.1f}s. Guardado en output/reservoir_hparam_sensitivity.csv")

# ---- resumen legible ----
noise_flip = df_out[df_out["noise_win_rate_esn"] < 0.5]
problem_survives = df_out[df_out["shock_problem_location_win_rate_esn"] > 0.5]

lines = []
lines.append("# Sensibilidad del ESN a hiperparametros del reservorio\n")
lines.append(f"Barrida de {n_configs} configuraciones (d_res in {GRID_DRES}, rho in {GRID_RHO}, "
              f"leak in {GRID_LEAK}), {N_SEEDS} semillas de reservorio por punto (vs. 30 en el "
              "experimento principal), paso mas grueso por costo computacional. Ninguna "
              "configuracion se selecciono por su resultado OOS; se reportan las 27 completas.\n")
lines.append("## Filtrado de ruido (ESN vs. proyeccion estatica, sigma=0.1)\n")
if len(noise_flip) == 0:
    lines.append("La ventaja del ESN sobre la proyeccion estatica bajo ruido de medicion "
                  f"**se mantiene en las {n_configs} configuraciones** (tasa de victoria del ESN "
                  f">50% en todas). Mediana de la tasa de victoria: "
                  f"{df_out['noise_win_rate_esn'].median():.1%}, "
                  f"minimo: {df_out['noise_win_rate_esn'].min():.1%}.\n")
else:
    lines.append(f"La ventaja del ESN se **invierte** en {len(noise_flip)} de {n_configs} "
                  "configuraciones (tasa de victoria <50%):\n\n")
    lines.append(noise_flip[["d_res", "rho", "leak", "noise_win_rate_esn"]].to_markdown(index=False))
    lines.append("\n")

lines.append(f"\n## Robustez ante shocks 15-sigma, ubicacion problematica = {problem_location}\n")
if problem_location is not None:
    lines.append(f"Tasa de victoria del ESN en la ubicacion problematica, por configuracion "
                  f"(mediana: {df_out['shock_problem_location_win_rate_esn'].median():.1%}, "
                  f"maximo: {df_out['shock_problem_location_win_rate_esn'].max():.1%}):\n\n")
    if len(problem_survives) == 0:
        lines.append("**El fallo en esta ubicacion se mantiene en las 27 configuraciones** "
                      "(tasa de victoria <=50% en todas) -- es consistente con un fenomeno ligado "
                      "a la geometria del atractor en ese punto, no un artefacto de una "
                      "realizacion de reservorio especifica.\n")
    else:
        lines.append(f"El fallo **no es universal**: en {len(problem_survives)} de {n_configs} "
                      "configuraciones el ESN gana mayoritariamente en esa ubicacion "
                      "(tasa de victoria >50%), sugiriendo que el fallo reportado en el "
                      "experimento principal depende en parte de la configuracion de "
                      "hiperparametros usada alli (d_res=50, rho=0.9, leak=1.0), no solo de "
                      "la ubicacion en si.\n\n")
        lines.append(problem_survives[["d_res", "rho", "leak",
                                       "shock_problem_location_win_rate_esn"]].to_markdown(index=False))
        lines.append("\n")
else:
    lines.append("No se encontro `lorenz_shock_by_condition.csv` del experimento principal; "
                  "no se pudo identificar la ubicacion problematica para esta prueba dirigida.\n")

lines.append("\n## Recomendacion\n")
if len(noise_flip) == 0 and len(problem_survives) == 0:
    lines.append("Ambos hallazgos del manuscrito (ventaja de filtrado bajo ruido; fallo "
                  "localizado y persistente ante shocks) son **estables** a traves de la grilla "
                  "de hiperparametros probada. No se requiere ningun cambio adicional en el "
                  "texto del manuscrito mas alla de lo ya declarado en la seccion de "
                  "Limitations.\n")
else:
    lines.append("Al menos uno de los dos hallazgos muestra sensibilidad a los hiperparametros "
                  "del reservorio dentro de la grilla probada (ver detalle arriba). Se "
                  "recomienda anadir una nota breve en Limitations senalando que los resultados "
                  "se reportan para la configuracion d_res=50, rho=0.9, leak=1.0 y que no se "
                  "verifico invariancia completa a traves de todos los hiperparametros "
                  "razonables.\n")

with open(os.path.join(OUT_DIR, "RESERVOIR_HPARAM_SENSITIVITY.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Guardado en output/RESERVOIR_HPARAM_SENSITIVITY.md")
