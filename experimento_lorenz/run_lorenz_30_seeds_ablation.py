"""
Lorenz63: Protocolo estricto de robustez estocastica (30 semillas), ablacion de
recurrencia, filtrado de ruido (5 semillas) y shocks en multiples ubicaciones.

Modelos evaluados:
1. SSRC-lag: entrada de k rezagos crudos (d_in = 3), W_res != 0.
2. SSRC-NGRC: entrada de caracteristicas cuadraticas (d_in = 9), W_res != 0.
3. Static-lag: proyeccion tanh estatica (W_res = 0), mismo W_in que SSRC-lag.
4. Static-NGRC: proyeccion tanh estatica (W_res = 0), mismo W_in que SSRC-NGRC.
5. Ridge NG-RC: seleccion temporal causal de lambda (calculado 1 sola vez por ventana).
6. OLS NG-RC: pseudoinversa sin regularizar (calculado 1 sola vez por ventana).

Regimenes:
- Limpio 1-paso (H=1) y multipaso iterado (H=5, H=10).
- Ruido de medicion: 5 semillas de ruido x 30 semillas de reservorio:
    * Variante A (Filtrado de senal): entrada ruidosa -> target limpio.
    * Variante B (Control observacional): entrada ruidosa -> target ruidoso.
- Shocks puntuales: 5 ubicaciones x 2 signos x magnitudes {15 sigma, 50 sigma}.

Estadistica:
- Rango percentil 2.5 - 97.5 entre semillas.
- Intervalos Clopper-Pearson / Binomial exactos para tasas de victoria.
- Bootstrap jerarquico por bloques temporales para diferencias pareadas.
"""
from __future__ import annotations

import os
import time
import numpy as np
import pandas as pd
from scipy.stats import beta, binomtest
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
N_BURNIN_INTEGRATE = 5000
N_FEATURE_POINTS = 30000
K = 3
T_TRAIN = 500
STEP = 40
RES_DIM = 50
N_SEEDS = 30
SEEDS = [100 + i for i in range(N_SEEDS)]
NOISE_SEEDS = [42, 123, 456, 789, 999]
TRAJ_SEED = 7  # Preserva continuidad historica

# --- Bootstrap jerarquico por bloques (diferencias pareadas) ---
# Longitud de bloque: aproxima el numero de pasos STEP contenidos en una
# ventana de entrenamiento T_TRAIN, de forma que un bloque cubra ~una
# ventana no solapada y absorba la autocorrelacion introducida por el
# solapamiento de ventanas consecutivas (STEP=40 << T_TRAIN=500).
BOOT_BLOCK_LEN = int(np.ceil(T_TRAIN / STEP))  # = 13
N_BOOT = 2000
BOOT_SEED = 2026

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


def clopper_pearson(k_successes: int, n_trials: int, alpha: float = 0.05) -> tuple[float, float]:
    if n_trials == 0:
        return 0.0, 0.0
    if k_successes == 0:
        low = 0.0
    else:
        low = float(beta.ppf(alpha / 2, k_successes, n_trials - k_successes + 1))
    if k_successes == n_trials:
        high = 1.0
    else:
        high = float(beta.ppf(1 - alpha / 2, k_successes + 1, n_trials - k_successes))
    return low, high


def _block_means_circular(arr: np.ndarray, block_len: int) -> tuple[np.ndarray, int]:
    """Medias de bloque movil circular (moving block bootstrap).

    Devuelve, para una secuencia ordenada temporalmente ``arr`` de longitud
    ``L``, el vector de ``L`` medias de bloque (una por posicion de inicio,
    envolviendo circularmente al final de la serie) junto con el numero de
    bloques ``n_draws = ceil(L / block_len)`` requerido para reconstruir,
    por remuestreo con reemplazo de esas medias de bloque, una serie
    resampleada de longitud aproximadamente igual a ``L``. Muestrear con
    reemplazo ``n_draws`` medias de bloque y promediarlas es equivalente
    (para bloques de longitud constante) a concatenar los bloques crudos
    resampleados y tomar la media de la serie completa, pero evita
    materializar arreglos de tamano ``n_boot x L``.
    """
    arr = np.asarray(arr, dtype=float)
    L = len(arr)
    b = max(1, min(block_len, L))
    if b == 1:
        return arr.copy(), L
    arr_ext = np.concatenate([arr, arr[:b - 1]])
    csum = np.cumsum(np.insert(arr_ext, 0, 0.0))
    block_means = (csum[b:b + L] - csum[0:L]) / b
    n_draws = int(np.ceil(L / b))
    return block_means, n_draws


def hierarchical_block_bootstrap_diff(
    subdf: pd.DataFrame,
    diff_col: str,
    is_shock: bool,
    block_len: int = BOOT_BLOCK_LEN,
    n_boot: int = N_BOOT,
    rng: np.random.Generator | None = None,
) -> tuple[float, float, float]:
    """Bootstrap jerarquico de 2 niveles para una diferencia pareada.

    Nivel 1 (bloques temporales): dentro de cada semilla de reservorio, se
    remuestrean BLOQUES de ventanas consecutivas (no ventanas individuales)
    con reemplazo, via remuestreo de medias de bloque moviles circulares
    (ver ``_block_means_circular``). Esto absorbe la autocorrelacion entre
    ventanas solapadas (STEP=40 << T_TRAIN=500).

    Nivel 2 (semillas): se remuestrean las semillas de reservorio (30, o
    las que aplique al grupo) con reemplazo; para cada replica, cada
    semilla resampleada aporta su propia media bootstrap de nivel 1 de esa
    misma replica (bootstrap anidado simple, sin recalcular nivel 1 dos
    veces).

    Para el regimen de shocks, cada semilla solo aporta 1 punto por cada
    una de las 5 ubicaciones x 2 signos (ventanas no solapadas, separadas
    por 5000 puntos); ahi ``block_len`` se colapsa automaticamente a 1
    (bootstrap i.i.d. estandar sobre esas 10 condiciones), pues no existe
    solapamiento temporal que justifique bloques mayores.

    Ordena cada secuencia por (noise_seed, window_start) o (location, sign)
    o window_start segun el regimen, para preservar la contigueidad
    temporal real al calcular las medias de bloque. Para el regimen de
    ruido esto concatena las 5 sub-secuencias (una por noise_seed) de forma
    contigua; en las ~5 fronteras entre noise_seed algun bloque puede
    solapar dos realizaciones de ruido distintas, un efecto de borde
    minusculo (5 fronteras sobre ~1840 puntos por semilla) que se acepta
    por simplicidad.
    """
    if rng is None:
        rng = np.random.default_rng(BOOT_SEED)

    if is_shock:
        sort_cols = ["location", "sign"]
        b_len = 1
    elif "noise_seed" in subdf.columns and subdf["noise_seed"].notna().any():
        sort_cols = ["noise_seed", "window_start"]
        b_len = block_len
    else:
        sort_cols = ["window_start"]
        b_len = block_len

    seeds = sorted(subdf["seed"].unique())
    n_seeds = len(seeds)
    if n_seeds == 0:
        return float("nan"), float("nan"), float("nan")

    M = np.full((n_boot, n_seeds), np.nan)
    for i, sd in enumerate(seeds):
        seed_df = subdf.loc[subdf["seed"] == sd].sort_values(sort_cols)
        arr = seed_df[diff_col].to_numpy(dtype=float)
        arr = arr[~np.isnan(arr)]
        if len(arr) == 0:
            continue
        block_means, n_draws = _block_means_circular(arr, b_len)
        draws = rng.choice(block_means, size=(n_boot, n_draws), replace=True)
        M[:, i] = draws.mean(axis=1)

    seed_idx_draws = rng.integers(0, n_seeds, size=(n_boot, n_seeds))
    boot_replicates = np.nanmean(M[np.arange(n_boot)[:, None], seed_idx_draws], axis=1)
    boot_mean = float(np.nanmean(boot_replicates))
    ci_low, ci_high = (float(v) for v in np.nanpercentile(boot_replicates, [2.5, 97.5]))
    return boot_mean, ci_low, ci_high


def seed_level_bootstrap_diff(
    diffs_per_seed: np.ndarray,
    n_boot: int = N_BOOT,
    rng: np.random.Generator | None = None,
) -> tuple[float, float, float]:
    """Bootstrap simple (1 nivel) de la media de una diferencia pareada,
    remuestreando semillas con reemplazo. Se usa para el desglose por
    condicion de shock, donde cada semilla aporta un unico punto (sin
    estructura de bloques temporales que resolver)."""
    if rng is None:
        rng = np.random.default_rng(BOOT_SEED)
    arr = np.asarray(diffs_per_seed, dtype=float)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    draws = rng.choice(arr, size=(n_boot, n), replace=True)
    boot_replicates = draws.mean(axis=1)
    boot_mean = float(np.mean(boot_replicates))
    ci_low, ci_high = (float(v) for v in np.percentile(boot_replicates, [2.5, 97.5]))
    return boot_mean, ci_low, ci_high


def run_experiment_suite():
    print(f"=== Simulando trayectoria Lorenz63 limpia (seed={TRAJ_SEED}, {N_FEATURE_POINTS} puntos) ===")
    x_clean = simulate_lorenz()
    x_clean_std = standardize_from_prefix(x_clean, T_TRAIN)

    F_ngrc, y_target, X_lags = build_ngrc(x_clean_std, K)
    N_SAMPLES = len(F_ngrc)
    D_NGRC = F_ngrc.shape[1]

    window_starts = list(range(0, N_SAMPLES - T_TRAIN - 15, STEP))
    n_windows = len(window_starts)
    print(f"Total ventanas de evaluacion: {n_windows} (T_train={T_TRAIN}, paso={STEP})")

    # =========================================================================
    # 1. EVALUACION DE MODELOS BASE (NG-RC Ridge y OLS) UNA SOLA VEZ
    # =========================================================================
    print("=== Evaluando NG-RC Ridge y OLS (independientes de la semilla del reservorio) ===")
    base_results = {}
    for w_start in window_starts:
        w_end = w_start + T_TRAIN
        test_idx = w_end
        y_tr = y_target[w_start:w_end]
        y_te = y_target[test_idx]
        naive_mae_tr = max(float(np.mean(np.abs(np.diff(y_tr)))), 1e-6)

        # 1-paso
        w_ridge, _ = select_ridge_lambda_temporal(F_ngrc[w_start:w_end], y_tr)
        p_ridge = float(F_ngrc[test_idx] @ w_ridge)
        mase_ridge = abs(y_te - p_ridge) / naive_mae_tr

        w_ols, *_ = np.linalg.lstsq(F_ngrc[w_start:w_end], y_tr, rcond=None)
        p_ols = float(F_ngrc[test_idx] @ w_ols)
        mase_ols = abs(y_te - p_ols) / naive_mae_tr

        # Multi-paso
        multi_dict = {}
        for H in (5, 10):
            if test_idx + H <= N_SAMPLES:
                y_true_m = y_target[test_idx:test_idx + H]

                # Ridge multi
                curr_l = x_clean_std[test_idx:test_idx + K].copy()
                preds_r = []
                for _ in range(H):
                    lin = curr_l
                    quad = np.array([lin[i] * lin[j] for i in range(K) for j in range(i, K)])
                    f_row = np.hstack([lin, quad])
                    p = float(f_row @ w_ridge)
                    preds_r.append(p)
                    curr_l = np.append(curr_l[1:], p)
                mase_r_multi = float(np.mean(np.abs(y_true_m - preds_r))) / naive_mae_tr

                # OLS multi
                curr_l_o = x_clean_std[test_idx:test_idx + K].copy()
                preds_o = []
                for _ in range(H):
                    lin = curr_l_o
                    quad = np.array([lin[i] * lin[j] for i in range(K) for j in range(i, K)])
                    f_row = np.hstack([lin, quad])
                    p = float(f_row @ w_ols)
                    preds_o.append(p)
                    curr_l_o = np.append(curr_l_o[1:], p)
                mase_o_multi = float(np.mean(np.abs(y_true_m - preds_o))) / naive_mae_tr

                multi_dict[H] = (mase_r_multi, mase_o_multi)

        base_results[w_start] = {
            "mase_ridge_1": mase_ridge,
            "mase_ols_1": mase_ols,
            "multi": multi_dict,
            "naive_mae_tr": naive_mae_tr,
            "w_ridge": w_ridge,
            "w_ols": w_ols,
        }

    # =========================================================================
    # 2. EVALUACION DE 30 SEMILLAS EN REGIMEN LIMPIO
    # =========================================================================
    print(f"\n=== Evaluando 30 semillas de SSRC-lag, SSRC-NGRC y proyecciones estaticas (Limpio) ===")
    records = []
    t0_eval = time.time()

    for s_idx, seed in enumerate(SEEDS):
        # A) SSRC-lag (d_in = K = 3)
        w_in_lag, w_res_lag = make_ssrc(d_in=K, d_res=RES_DIM, rho=0.9, density=0.1, seed=seed)
        H_ssrc_lag, _ = ssrc_states(X_lags, w_in_lag, w_res_lag)
        H_static_lag = np.tanh(X_lags @ w_in_lag.T)

        # B) SSRC-NGRC (d_in = D = 9)
        w_in_ngrc, w_res_ngrc = make_ssrc(d_in=D_NGRC, d_res=RES_DIM, rho=0.9, density=0.1, seed=seed)
        H_ssrc_ngrc, _ = ssrc_states(F_ngrc, w_in_ngrc, w_res_ngrc)
        H_static_ngrc = np.tanh(F_ngrc @ w_in_ngrc.T)

        for w_start in window_starts:
            w_end = w_start + T_TRAIN
            test_idx = w_end
            y_tr = y_target[w_start:w_end]
            y_te = y_target[test_idx]
            naive_mae_tr = base_results[w_start]["naive_mae_tr"]
            mase_r1 = base_results[w_start]["mase_ridge_1"]
            mase_o1 = base_results[w_start]["mase_ols_1"]

            # 1-paso
            w_ssrc_l, _ = select_ridge_lambda_temporal(H_ssrc_lag[w_start:w_end], y_tr)
            p_ssrc_l = float(H_ssrc_lag[test_idx] @ w_ssrc_l)
            m_ssrc_l = abs(y_te - p_ssrc_l) / naive_mae_tr

            w_stat_l, _ = select_ridge_lambda_temporal(H_static_lag[w_start:w_end], y_tr)
            p_stat_l = float(H_static_lag[test_idx] @ w_stat_l)
            m_stat_l = abs(y_te - p_stat_l) / naive_mae_tr

            w_ssrc_ng, _ = select_ridge_lambda_temporal(H_ssrc_ngrc[w_start:w_end], y_tr)
            p_ssrc_ng = float(H_ssrc_ngrc[test_idx] @ w_ssrc_ng)
            m_ssrc_ng = abs(y_te - p_ssrc_ng) / naive_mae_tr

            w_stat_ng, _ = select_ridge_lambda_temporal(H_static_ngrc[w_start:w_end], y_tr)
            p_stat_ng = float(H_static_ngrc[test_idx] @ w_stat_ng)
            m_stat_ng = abs(y_te - p_stat_ng) / naive_mae_tr

            records.append(dict(
                regime="clean_1step", horizon=1, seed=seed, window_start=w_start,
                mase_ssrc_lag=m_ssrc_l, mase_static_lag=m_stat_l,
                mase_ssrc_ngrc=m_ssrc_ng, mase_static_ngrc=m_stat_ng,
                mase_ridge=mase_r1, mase_ols=mase_o1
            ))

            # Multi-paso (H=5, 10)
            for H in (5, 10):
                if test_idx + H <= N_SAMPLES:
                    y_true_m = y_target[test_idx:test_idx + H]
                    mase_r_m, mase_o_m = base_results[w_start]["multi"][H]

                    # SSRC-lag multi
                    curr_st = H_ssrc_lag[test_idx - 1].copy()
                    curr_lg = x_clean_std[test_idx:test_idx + K].copy()
                    preds_sl = []
                    for _ in range(H):
                        curr_st = ssrc_step(curr_lg, curr_st, w_in_lag, w_res_lag)
                        p = float(curr_st @ w_ssrc_l)
                        preds_sl.append(p)
                        curr_lg = np.append(curr_lg[1:], p)
                    m_ssrc_l_m = float(np.mean(np.abs(y_true_m - preds_sl))) / naive_mae_tr

                    # Static-lag multi
                    curr_lg_s = x_clean_std[test_idx:test_idx + K].copy()
                    preds_stl = []
                    for _ in range(H):
                        h_st = np.tanh(w_in_lag @ curr_lg_s)
                        p = float(h_st @ w_stat_l)
                        preds_stl.append(p)
                        curr_lg_s = np.append(curr_lg_s[1:], p)
                    m_stat_l_m = float(np.mean(np.abs(y_true_m - preds_stl))) / naive_mae_tr

                    # SSRC-NGRC multi
                    curr_st_ng = H_ssrc_ngrc[test_idx - 1].copy()
                    curr_lg_ng = x_clean_std[test_idx:test_idx + K].copy()
                    preds_sng = []
                    for _ in range(H):
                        lin_f = curr_lg_ng
                        quad_f = np.array([lin_f[i] * lin_f[j] for i in range(K) for j in range(i, K)])
                        f_curr = np.hstack([lin_f, quad_f])
                        curr_st_ng = ssrc_step(f_curr, curr_st_ng, w_in_ngrc, w_res_ngrc)
                        p = float(curr_st_ng @ w_ssrc_ng)
                        preds_sng.append(p)
                        curr_lg_ng = np.append(curr_lg_ng[1:], p)
                    m_ssrc_ng_m = float(np.mean(np.abs(y_true_m - preds_sng))) / naive_mae_tr

                    # Static-NGRC multi
                    curr_lg_stng = x_clean_std[test_idx:test_idx + K].copy()
                    preds_stng = []
                    for _ in range(H):
                        lin_f = curr_lg_stng
                        quad_f = np.array([lin_f[i] * lin_f[j] for i in range(K) for j in range(i, K)])
                        f_curr = np.hstack([lin_f, quad_f])
                        h_st = np.tanh(w_in_ngrc @ f_curr)
                        p = float(h_st @ w_stat_ng)
                        preds_stng.append(p)
                        curr_lg_stng = np.append(curr_lg_stng[1:], p)
                    m_stat_ng_m = float(np.mean(np.abs(y_true_m - preds_stng))) / naive_mae_tr

                    records.append(dict(
                        regime="clean_multistep", horizon=H, seed=seed, window_start=w_start,
                        mase_ssrc_lag=m_ssrc_l_m, mase_static_lag=m_stat_l_m,
                        mase_ssrc_ngrc=m_ssrc_ng_m, mase_static_ngrc=m_stat_ng_m,
                        mase_ridge=mase_r_m, mase_ols=mase_o_m
                    ))

        if (s_idx + 1) % 10 == 0 or s_idx == N_SEEDS - 1:
            print(f"  Semillas limpias: {s_idx + 1}/{N_SEEDS} ({time.time() - t0_eval:.1f}s)")

    # =========================================================================
    # 3. EXPERIMENTO DE RUIDO: 5 SEMILLAS DE RUIDO x 30 RESERVORIOS
    # =========================================================================
    print(f"\n=== Evaluando Ruido (sigma in {{0.1, 0.5}}): 5 semillas de ruido x 30 reservorios ===")
    for sigma_noise in (0.1, 0.5):
        for n_seed in NOISE_SEEDS:
            rng_n = np.random.RandomState(n_seed)
            noise_vec = rng_n.normal(0, sigma_noise, size=len(x_clean_std))
            x_noisy = x_clean_std + noise_vec
            F_noisy, y_noisy, X_lags_noisy = build_ngrc(x_noisy, K)

            # Precalcular Ridge y OLS ruidosos 1 sola vez
            base_noise = {}
            for w_start in window_starts[::2]:
                w_end = w_start + T_TRAIN
                test_idx = w_end
                y_tr = y_noisy[w_start:w_end]
                y_te_noisy = y_noisy[test_idx]
                y_te_clean = y_target[test_idx]
                naive_mae_tr = max(float(np.mean(np.abs(np.diff(y_tr)))), 1e-6)

                w_ridge, _ = select_ridge_lambda_temporal(F_noisy[w_start:w_end], y_tr)
                p_r = float(F_noisy[test_idx] @ w_ridge)

                w_ols, *_ = np.linalg.lstsq(F_noisy[w_start:w_end], y_tr, rcond=None)
                p_o = float(F_noisy[test_idx] @ w_ols)

                base_noise[w_start] = {
                    "p_ridge": p_r, "p_ols": p_o,
                    "y_te_noisy": y_te_noisy, "y_te_clean": y_te_clean,
                    "naive_mae_tr": naive_mae_tr,
                }

            # Evaluar 30 reservorios
            for seed in SEEDS:
                w_in_lag, w_res_lag = make_ssrc(d_in=K, d_res=RES_DIM, rho=0.9, density=0.1, seed=seed)
                H_ssrc_l, _ = ssrc_states(X_lags_noisy, w_in_lag, w_res_lag)
                H_stat_l = np.tanh(X_lags_noisy @ w_in_lag.T)

                for w_start in window_starts[::2]:
                    w_end = w_start + T_TRAIN
                    test_idx = w_end
                    y_tr = y_noisy[w_start:w_end]
                    info = base_noise[w_start]
                    naive_mae_tr = info["naive_mae_tr"]

                    w_sl, _ = select_ridge_lambda_temporal(H_ssrc_l[w_start:w_end], y_tr)
                    p_sl = float(H_ssrc_l[test_idx] @ w_sl)

                    w_stl, _ = select_ridge_lambda_temporal(H_stat_l[w_start:w_end], y_tr)
                    p_stl = float(H_stat_l[test_idx] @ w_stl)

                    # Variante A: Filtering (Target limpio)
                    records.append(dict(
                        regime=f"noise_{sigma_noise}_filtering", horizon=1, seed=seed, noise_seed=n_seed,
                        window_start=w_start,
                        mase_ssrc_lag=abs(info["y_te_clean"] - p_sl) / naive_mae_tr,
                        mase_static_lag=abs(info["y_te_clean"] - p_stl) / naive_mae_tr,
                        mase_ssrc_ngrc=np.nan, mase_static_ngrc=np.nan,
                        mase_ridge=abs(info["y_te_clean"] - info["p_ridge"]) / naive_mae_tr,
                        mase_ols=abs(info["y_te_clean"] - info["p_ols"]) / naive_mae_tr,
                    ))

                    # Variante B: Observational (Target ruidoso)
                    records.append(dict(
                        regime=f"noise_{sigma_noise}_observational", horizon=1, seed=seed, noise_seed=n_seed,
                        window_start=w_start,
                        mase_ssrc_lag=abs(info["y_te_noisy"] - p_sl) / naive_mae_tr,
                        mase_static_lag=abs(info["y_te_noisy"] - p_stl) / naive_mae_tr,
                        mase_ssrc_ngrc=np.nan, mase_static_ngrc=np.nan,
                        mase_ridge=abs(info["y_te_noisy"] - info["p_ridge"]) / naive_mae_tr,
                        mase_ols=abs(info["y_te_noisy"] - info["p_ols"]) / naive_mae_tr,
                    ))

    # =========================================================================
    # 4. EXPERIMENTO DE SHOCKS: 5 UBICACIONES x 2 SIGNOS x {15 sigma, 50 sigma}
    # =========================================================================
    print("\n=== Evaluando Shocks: 5 ubicaciones x 2 signos x {15 sigma, 50 sigma} ===")
    SHOCK_LOCS = [5000, 10000, 15000, 20000, 25000]
    SHOCK_SIGNS = [1, -1]

    for mag_shock in (15, 50):
        for loc in SHOCK_LOCS:
            for sgn in SHOCK_SIGNS:
                x_shk = x_clean_std.copy()
                x_shk[loc] += sgn * mag_shock
                F_shk, y_shk, X_lags_shk = build_ngrc(x_shk, K)

                w_shk_start = loc - 250
                w_shk_end = w_shk_start + T_TRAIN
                test_idx = w_shk_end

                y_tr = y_shk[w_shk_start:w_shk_end]
                y_te = y_shk[test_idx]
                naive_mae_tr = max(float(np.mean(np.abs(np.diff(y_tr)))), 1e-6)

                w_ridge, _ = select_ridge_lambda_temporal(F_shk[w_shk_start:w_shk_end], y_tr)
                p_r = float(F_shk[test_idx] @ w_ridge)
                mase_r = abs(y_te - p_r) / naive_mae_tr

                w_ols, *_ = np.linalg.lstsq(F_shk[w_shk_start:w_shk_end], y_tr, rcond=None)
                p_o = float(F_shk[test_idx] @ w_ols)
                mase_o = abs(y_te - p_o) / naive_mae_tr

                for seed in SEEDS:
                    w_in_lag, w_res_lag = make_ssrc(d_in=K, d_res=RES_DIM, rho=0.9, density=0.1, seed=seed)
                    X_win = X_lags_shk[w_shk_start:w_shk_end + 1]
                    H_ssrc_l, _ = ssrc_states(X_win, w_in_lag, w_res_lag)
                    H_stat_l = np.tanh(X_win @ w_in_lag.T)

                    w_sl, _ = select_ridge_lambda_temporal(H_ssrc_l[:-1], y_tr)
                    p_sl = float(H_ssrc_l[-1] @ w_sl)

                    w_stl, _ = select_ridge_lambda_temporal(H_stat_l[:-1], y_tr)
                    p_stl = float(H_stat_l[-1] @ w_stl)

                    records.append(dict(
                        regime=f"shock_{mag_shock}sigma", horizon=1, seed=seed,
                        location=loc, sign=sgn, window_start=w_shk_start,
                        mase_ssrc_lag=abs(y_te - p_sl) / naive_mae_tr,
                        mase_static_lag=abs(y_te - p_stl) / naive_mae_tr,
                        mase_ssrc_ngrc=np.nan, mase_static_ngrc=np.nan,
                        mase_ridge=mase_r, mase_ols=mase_o
                    ))

    df_all = pd.DataFrame(records)
    df_all.to_csv(os.path.join(OUT_DIR, "lorenz_rigorous_ablation_full.csv"), index=False)
    print(f"\nDatos crudos guardados: {len(df_all)} registros totales.")

    # =========================================================================
    # 5. AGREGACION ESTADISTICA FORMAL
    # =========================================================================
    print("\n" + "="*95)
    print("RESUMEN ESTADISTICO FORMAL (MEDIANA, RANGO 2.5-97.5% Y TEST BINOMIAL CLOPPER-PEARSON)")
    print("="*95)

    # Mediana por semilla en cada regimen/horizonte
    by_seed = df_all.groupby(["regime", "horizon", "seed"]).agg(
        mase_ssrc_lag=("mase_ssrc_lag", "median"),
        mase_static_lag=("mase_static_lag", "median"),
        mase_ssrc_ngrc=("mase_ssrc_ngrc", "median"),
        mase_static_ngrc=("mase_static_ngrc", "median"),
        mase_ridge=("mase_ridge", "median"),
        mase_ols=("mase_ols", "median"),
    ).reset_index()

    by_seed["diff_ssrc_vs_static"] = by_seed["mase_ssrc_lag"] - by_seed["mase_static_lag"]
    by_seed["diff_ssrc_vs_ridge"] = by_seed["mase_ssrc_lag"] - by_seed["mase_ridge"]
    by_seed["diff_ssrc_vs_ols"] = by_seed["mase_ssrc_lag"] - by_seed["mase_ols"]

    # Diferencias pareadas por VENTANA (crudas, no agregadas por semilla), para
    # el bootstrap jerarquico por bloques temporales.
    df_all = df_all.copy()
    df_all["_diff_static"] = df_all["mase_ssrc_lag"] - df_all["mase_static_lag"]
    df_all["_diff_ridge"] = df_all["mase_ssrc_lag"] - df_all["mase_ridge"]
    df_all["_diff_ols"] = df_all["mase_ssrc_lag"] - df_all["mase_ols"]

    print(f"\n=== Bootstrap jerarquico por bloques (n_boot={N_BOOT}, block_len={BOOT_BLOCK_LEN}) ===")
    t0_boot = time.time()
    boot_rng = np.random.default_rng(BOOT_SEED)
    boot_by_group: dict[tuple[str, int], dict[str, tuple[float, float, float]]] = {}
    for (regime, horizon), raw_sub in df_all.groupby(["regime", "horizon"]):
        is_shock = "location" in raw_sub.columns and raw_sub["location"].notna().any()
        boot_by_group[(regime, horizon)] = {
            "static": hierarchical_block_bootstrap_diff(raw_sub, "_diff_static", is_shock, rng=boot_rng),
            "ridge": hierarchical_block_bootstrap_diff(raw_sub, "_diff_ridge", is_shock, rng=boot_rng),
            "ols": hierarchical_block_bootstrap_diff(raw_sub, "_diff_ols", is_shock, rng=boot_rng),
        }
    print(f"  Bootstrap completado en {time.time() - t0_boot:.1f}s")

    summary_rows = []
    for (regime, horizon), group in by_seed.groupby(["regime", "horizon"]):
        n_s = len(group)
        wins_static = int(np.sum(group["diff_ssrc_vs_static"] < 0))
        wins_ridge = int(np.sum(group["diff_ssrc_vs_ridge"] < 0))
        wins_ols = int(np.sum(group["diff_ssrc_vs_ols"] < 0))

        cp_static_low, cp_static_high = clopper_pearson(wins_static, n_s)
        cp_ridge_low, cp_ridge_high = clopper_pearson(wins_ridge, n_s)
        cp_ols_low, cp_ols_high = clopper_pearson(wins_ols, n_s)

        boot_static_mean, boot_static_lo, boot_static_hi = boot_by_group[(regime, horizon)]["static"]
        boot_ridge_mean, boot_ridge_lo, boot_ridge_hi = boot_by_group[(regime, horizon)]["ridge"]
        boot_ols_mean, boot_ols_lo, boot_ols_hi = boot_by_group[(regime, horizon)]["ols"]

        row = {
            "regime": regime,
            "horizon": horizon,
            "ssrc_lag_median": float(group["mase_ssrc_lag"].median()),
            "ssrc_lag_p2_5": float(np.percentile(group["mase_ssrc_lag"], 2.5)),
            "ssrc_lag_p97_5": float(np.percentile(group["mase_ssrc_lag"], 97.5)),
            "ssrc_lag_iqr": float(np.percentile(group["mase_ssrc_lag"], 75) - np.percentile(group["mase_ssrc_lag"], 25)),
            "static_lag_median": float(group["mase_static_lag"].median()),
            "static_lag_iqr": float(np.percentile(group["mase_static_lag"], 75) - np.percentile(group["mase_static_lag"], 25)),
            "ssrc_ngrc_median": float(group["mase_ssrc_ngrc"].median()) if not group["mase_ssrc_ngrc"].isna().all() else np.nan,
            "ridge_median": float(group["mase_ridge"].median()),
            "ols_median": float(group["mase_ols"].median()),
            "win_vs_static": f"{wins_static}/{n_s} ({wins_static/n_s:.1%}) [{cp_static_low:.2f},{cp_static_high:.2f}]",
            "win_vs_ridge": f"{wins_ridge}/{n_s} ({wins_ridge/n_s:.1%}) [{cp_ridge_low:.2f},{cp_ridge_high:.2f}]",
            "win_vs_ols": f"{wins_ols}/{n_s} ({wins_ols/n_s:.1%}) [{cp_ols_low:.2f},{cp_ols_high:.2f}]",
            # Bootstrap jerarquico por bloques temporales (2000 replicas, ver
            # hierarchical_block_bootstrap_diff): media e IC 2.5-97.5% de la
            # diferencia pareada MASE(ssrc_lag) - MASE(X). Negativo = ssrc_lag mejor.
            "boot_diff_vs_static_mean": boot_static_mean,
            "boot_diff_vs_static_ci_low": boot_static_lo,
            "boot_diff_vs_static_ci_high": boot_static_hi,
            "boot_diff_vs_ridge_mean": boot_ridge_mean,
            "boot_diff_vs_ridge_ci_low": boot_ridge_lo,
            "boot_diff_vs_ridge_ci_high": boot_ridge_hi,
            "boot_diff_vs_ols_mean": boot_ols_mean,
            "boot_diff_vs_ols_ci_low": boot_ols_lo,
            "boot_diff_vs_ols_ci_high": boot_ols_hi,
        }
        summary_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(os.path.join(OUT_DIR, "lorenz_rigorous_summary.csv"), index=False)
    print(df_summary.to_string(index=False))

    # =========================================================================
    # 6. DESGLOSE DE SHOCKS POR CONDICION INDIVIDUAL (5 ubicaciones x 2 signos)
    # =========================================================================
    # El win-rate agrupado de la seccion 5 pool-ea 30 semillas x 10 condiciones
    # (5 ubicaciones x 2 signos) en un solo denominador, lo que puede ocultar si
    # la robustez esta concentrada en pocas condiciones. Aqui se desglosa cada
    # una de las 10 condiciones por separado (n=30 semillas cada una).
    print("\n=== Desglose de shocks por condicion individual (ubicacion x signo) ===")
    shock_condition_rows = []
    for regime in sorted(df_all.loc[df_all["regime"].str.startswith("shock_"), "regime"].unique()):
        sub_regime = df_all[df_all["regime"] == regime]
        for (loc, sgn), g in sub_regime.groupby(["location", "sign"]):
            n_c = len(g)
            wins_static_c = int(np.sum(g["_diff_static"] < 0))
            wins_ridge_c = int(np.sum(g["_diff_ridge"] < 0))
            wins_ols_c = int(np.sum(g["_diff_ols"] < 0))

            cp_s_lo, cp_s_hi = clopper_pearson(wins_static_c, n_c)
            cp_r_lo, cp_r_hi = clopper_pearson(wins_ridge_c, n_c)
            cp_o_lo, cp_o_hi = clopper_pearson(wins_ols_c, n_c)

            boot_s = seed_level_bootstrap_diff(g["_diff_static"].to_numpy(), rng=boot_rng)
            boot_r = seed_level_bootstrap_diff(g["_diff_ridge"].to_numpy(), rng=boot_rng)
            boot_o = seed_level_bootstrap_diff(g["_diff_ols"].to_numpy(), rng=boot_rng)

            shock_condition_rows.append({
                "regime": regime,
                "location": int(loc),
                "sign": int(sgn),
                "n_seeds": n_c,
                "ssrc_lag_median": float(g["mase_ssrc_lag"].median()),
                "static_lag_median": float(g["mase_static_lag"].median()),
                "ridge_median": float(g["mase_ridge"].median()),
                "ols_median": float(g["mase_ols"].median()),
                "win_vs_static": f"{wins_static_c}/{n_c} ({wins_static_c/n_c:.1%}) [{cp_s_lo:.2f},{cp_s_hi:.2f}]",
                "win_vs_ridge": f"{wins_ridge_c}/{n_c} ({wins_ridge_c/n_c:.1%}) [{cp_r_lo:.2f},{cp_r_hi:.2f}]",
                "win_vs_ols": f"{wins_ols_c}/{n_c} ({wins_ols_c/n_c:.1%}) [{cp_o_lo:.2f},{cp_o_hi:.2f}]",
                "boot_diff_vs_static_mean": boot_s[0], "boot_diff_vs_static_ci_low": boot_s[1], "boot_diff_vs_static_ci_high": boot_s[2],
                "boot_diff_vs_ridge_mean": boot_r[0], "boot_diff_vs_ridge_ci_low": boot_r[1], "boot_diff_vs_ridge_ci_high": boot_r[2],
                "boot_diff_vs_ols_mean": boot_o[0], "boot_diff_vs_ols_ci_low": boot_o[1], "boot_diff_vs_ols_ci_high": boot_o[2],
            })

    df_shock_cond = pd.DataFrame(shock_condition_rows)
    df_shock_cond.to_csv(os.path.join(OUT_DIR, "lorenz_shock_by_condition.csv"), index=False)
    print(df_shock_cond.to_string(index=False))

    return df_summary


if __name__ == "__main__":
    run_experiment_suite()
