"""
Lorenz63: Curva de pronostico multipaso en funcion de tiempos de Lyapunov.
H in {1, 2, 3, 5, 8, 10, 15, 20, 30, 40}.
dt = 0.05 (skip=5, dt_int=0.01)
lambda_max(Lorenz63) = 0.9056
tau_lyap = H * dt * lambda_max = H * 0.05 * 0.9056 = H * 0.04528

Denominador MASE: mean(abs(diff(y_tr))) sobre exactamente las T_train=500 observaciones de entrenamiento.
"""
from __future__ import annotations

import os
import time
import numpy as np
import pandas as pd
from lorenz_common import (
    make_ssrc,
    select_ridge_lambda_temporal,
    ssrc_states,
    ssrc_step,
    standardize_from_prefix,
)

SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
DT_INTEGRATE = 0.01
SKIP = 5
DT_FEATURE = DT_INTEGRATE * SKIP  # 0.05
LAMBDA_MAX_LORENZ = 0.9056
N_BURNIN_INTEGRATE = 5000
N_FEATURE_POINTS = 30000
K = 3
T_TRAIN = 500
STEP = 40
RES_DIM = 50
N_SEEDS = 30
SEEDS = [100 + i for i in range(N_SEEDS)]
TRAJ_SEED = 7

HORIZONS = [1, 2, 3, 5, 8, 10, 15, 20, 30, 40]

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT_DIR, exist_ok=True)


def lorenz_rhs(s):
    x, y, z = s
    return np.array([SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z])


def simulate_lorenz(n_points=N_FEATURE_POINTS, skip=SKIP, dt=DT_INTEGRATE, n_burnin=N_BURNIN_INTEGRATE, seed=TRAJ_SEED):
    rng = np.random.RandomState(seed)
    state = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
    n_total = n_burnin + n_points * skip
    traj = np.zeros((n_total, 3))
    for i in range(n_total):
        k1 = lorenz_rhs(state)
        k2 = lorenz_rhs(state + dt / 2 * k1)
        k3 = lorenz_rhs(state + dt / 2 * k2)
        k4 = lorenz_rhs(state + dt * k3)
        state = state + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[i] = state
    return traj[n_burnin:][::skip, 0]


def build_ngrc(x, k=K):
    T = len(x)
    n_rows = T - k
    lin = np.array([x[t:t + k] for t in range(n_rows)])
    n = lin.shape[1]
    quad = np.array([lin[:, i] * lin[:, j] for i in range(n) for j in range(i, n)]).T
    F = np.hstack([lin, quad])
    y = x[k:]
    return F, y, lin


def run_lyapunov_curve():
    print(f"=== Lorenz63: Evaluando Curva Fina Multipaso vs Tiempos de Lyapunov ===")
    x_clean = simulate_lorenz()
    x_clean_std = standardize_from_prefix(x_clean, T_TRAIN)

    F_ngrc, y_target, X_lags = build_ngrc(x_clean_std, K)
    N_SAMPLES = len(F_ngrc)

    max_H = max(HORIZONS)
    window_starts = list(range(0, N_SAMPLES - T_TRAIN - max_H - 5, STEP))
    print(f"Total ventanas evaluadas: {len(window_starts)}, Horizontes: {HORIZONS}")

    # 1. Precomputar Ridge y OLS NG-RC (independientes de las semillas del reservorio)
    print("Precalculando Ridge y OLS NG-RC...")
    base_multi = {}
    for w_start in window_starts:
        w_end = w_start + T_TRAIN
        test_idx = w_end
        y_tr = y_target[w_start:w_end]
        # Denominador MASE estricto: mean(abs(diff(y_tr))) sobre el vector y de entrenamiento (T_train = 500)
        naive_mae_tr = max(float(np.mean(np.abs(np.diff(y_tr)))), 1e-6)

        w_ridge, _ = select_ridge_lambda_temporal(F_ngrc[w_start:w_end], y_tr)
        w_ols, *_ = np.linalg.lstsq(F_ngrc[w_start:w_end], y_tr, rcond=None)

        # Simular trayectoria iterada completa hasta max_H
        curr_lr = x_clean_std[test_idx:test_idx + K].copy()
        preds_r = []
        for _ in range(max_H):
            lin = curr_lr
            quad = np.array([lin[i] * lin[j] for i in range(K) for j in range(i, K)])
            p = float(np.hstack([lin, quad]) @ w_ridge)
            preds_r.append(p)
            curr_lr = np.append(curr_lr[1:], p)

        curr_lo = x_clean_std[test_idx:test_idx + K].copy()
        preds_o = []
        for _ in range(max_H):
            lin = curr_lo
            quad = np.array([lin[i] * lin[j] for i in range(K) for j in range(i, K)])
            p = float(np.hstack([lin, quad]) @ w_ols)
            preds_o.append(p)
            curr_lo = np.append(curr_lo[1:], p)

        base_multi[w_start] = {
            "naive_mae_tr": naive_mae_tr,
            "preds_ridge": np.array(preds_r),
            "preds_ols": np.array(preds_o),
        }

    records = []
    t0 = time.time()
    for s_idx, seed in enumerate(SEEDS):
        w_in_lag, w_res_lag = make_ssrc(d_in=K, d_res=RES_DIM, rho=0.9, density=0.1, seed=seed)
        H_ssrc_lag, _ = ssrc_states(X_lags, w_in_lag, w_res_lag)
        H_stat_lag = np.tanh(X_lags @ w_in_lag.T)

        for w_start in window_starts:
            w_end = w_start + T_TRAIN
            test_idx = w_end
            y_tr = y_target[w_start:w_end]
            info = base_multi[w_start]
            naive_mae_tr = info["naive_mae_tr"]

            # Entrenar lectores
            w_ssrc_l, _ = select_ridge_lambda_temporal(H_ssrc_lag[w_start:w_end], y_tr)
            w_stat_l, _ = select_ridge_lambda_temporal(H_stat_lag[w_start:w_end], y_tr)

            # Iterar SSRC-lag
            curr_st = H_ssrc_lag[test_idx - 1].copy()
            curr_lg = x_clean_std[test_idx:test_idx + K].copy()
            preds_sl = []
            for _ in range(max_H):
                curr_st = ssrc_step(curr_lg, curr_st, w_in_lag, w_res_lag)
                p = float(curr_st @ w_ssrc_l)
                preds_sl.append(p)
                curr_lg = np.append(curr_lg[1:], p)
            preds_sl = np.array(preds_sl)

            # Iterar Static-lag
            curr_lg_s = x_clean_std[test_idx:test_idx + K].copy()
            preds_stl = []
            for _ in range(max_H):
                h_st = np.tanh(w_in_lag @ curr_lg_s)
                p = float(h_st @ w_stat_l)
                preds_stl.append(p)
                curr_lg_s = np.append(curr_lg_s[1:], p)
            preds_stl = np.array(preds_stl)

            # Extraer MASE para cada horizonte H
            for H in HORIZONS:
                y_true_H = y_target[test_idx:test_idx + H]
                m_sl = float(np.mean(np.abs(y_true_H - preds_sl[:H]))) / naive_mae_tr
                m_stl = float(np.mean(np.abs(y_true_H - preds_stl[:H]))) / naive_mae_tr
                m_r = float(np.mean(np.abs(y_true_H - info["preds_ridge"][:H]))) / naive_mae_tr
                m_o = float(np.mean(np.abs(y_true_H - info["preds_ols"][:H]))) / naive_mae_tr
                tau = H * DT_FEATURE * LAMBDA_MAX_LORENZ

                records.append(dict(
                    seed=seed, window_start=w_start, horizon=H, tau_lyapunov=tau,
                    mase_esn_lag=m_sl, mase_static_lag=m_stl,
                    mase_ridge=m_r, mase_ols=m_o
                ))

        if (s_idx + 1) % 10 == 0 or s_idx == N_SEEDS - 1:
            print(f"  Semillas procesadas: {s_idx + 1}/{N_SEEDS} ({time.time() - t0:.1f}s)")

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(OUT_DIR, "lorenz_lyapunov_curve_raw.csv"), index=False)

    # Resumen por horizonte
    by_h = df.groupby("horizon").agg(
        tau_lyapunov=("tau_lyapunov", "first"),
        esn_lag_median=("mase_esn_lag", "median"),
        esn_lag_p25=("mase_esn_lag", lambda x: np.percentile(x, 25)),
        esn_lag_p75=("mase_esn_lag", lambda x: np.percentile(x, 75)),
        static_lag_median=("mase_static_lag", "median"),
        static_lag_p25=("mase_static_lag", lambda x: np.percentile(x, 25)),
        static_lag_p75=("mase_static_lag", lambda x: np.percentile(x, 75)),
        ridge_median=("mase_ridge", "median"),
        ridge_p25=("mase_ridge", lambda x: np.percentile(x, 25)),
        ridge_p75=("mase_ridge", lambda x: np.percentile(x, 75)),
        ols_median=("mase_ols", "median"),
        ols_p25=("mase_ols", lambda x: np.percentile(x, 25)),
        ols_p75=("mase_ols", lambda x: np.percentile(x, 75)),
    ).reset_index()

    # Calcular tasa de victorias de ESN vs Ridge por horizonte
    win_rates = []
    for H in HORIZONS:
        sub_h = df[df["horizon"] == H]
        wins_by_seed = sub_h.groupby("seed").apply(lambda g: (g["mase_esn_lag"] < g["mase_ridge"]).mean() > 0.5).sum()
        win_rates.append(f"{wins_by_seed}/{N_SEEDS}")
    by_h["esn_wins_vs_ridge_seeds"] = win_rates

    by_h.to_csv(os.path.join(OUT_DIR, "lorenz_lyapunov_curve_summary.csv"), index=False)
    print("\n=== RESUMEN DE CURVA MULTIPASO VS TIEMPOS DE LYAPUNOV ===")
    print(by_h.to_string(index=False))
    return by_h


if __name__ == "__main__":
    run_lyapunov_curve()
