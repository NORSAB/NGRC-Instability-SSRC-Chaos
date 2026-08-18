"""
Inferencia Rigurosa: Two-Way Block Bootstrap Cruzado para Lorenz63.
Maneja la dependencia temporal entre ventanas y la estructura cruzada de semillas.
Para shocks: remuestrea las 5 ubicaciones manteniendo pareados los signos (+ y -).
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
IN_CSV = os.path.join(OUT_DIR, "lorenz_rigorous_ablation_full.csv")

N_BOOT = 2000
BLOCK_SIZE = 13  # ceil(500 / 40)


def block_bootstrap_indices(n_items: int, block_size: int, rng: np.random.RandomState) -> np.ndarray:
    n_blocks = int(np.ceil(n_items / block_size))
    starts = rng.randint(0, max(1, n_items - block_size + 1), size=n_blocks)
    indices = []
    for s in starts:
        indices.extend(range(s, min(s + block_size, n_items)))
    return np.array(indices[:n_items])


def resample_two_way_block_diff(
    piv_a: np.ndarray,
    piv_b: np.ndarray,
    block_size: int = BLOCK_SIZE,
    n_boot: int = N_BOOT,
    rng: np.random.RandomState | None = None
) -> tuple[float, float, float]:
    """Calcula la diferencia muestral y el intervalo percentil de bootstrap de dos vías con tiempo compartido."""
    if rng is None:
        rng = np.random.RandomState(42)
    n_w, n_s = piv_a.shape
    diff_sample = float(np.mean(piv_a - piv_b))
    boot_diffs = []
    for _ in range(n_boot):
        w_idx = block_bootstrap_indices(n_w, block_size, rng)
        s_idx = rng.choice(n_s, size=n_s, replace=True)
        a_b = piv_a[w_idx[:, None], s_idx]
        b_b = piv_b[w_idx[:, None], s_idx]
        boot_diffs.append(np.mean(a_b - b_b))
    ci_low, ci_high = np.percentile(boot_diffs, [2.5, 97.5])
    return diff_sample, float(ci_low), float(ci_high)


def run_bootstrap_analysis():
    print("Leyendo datos completos de ablacion estocastica...")
    df = pd.read_csv(IN_CSV)
    rng = np.random.RandomState(42)

    results = []

    # 1. Regimenes Limpios (clean_1step, clean_multistep)
    clean_regimes = [
        ("clean_1step", 1),
        ("clean_multistep", 5),
        ("clean_multistep", 10),
    ]

    for regime, H in clean_regimes:
        sub = df[(df["regime"] == regime) & (df["horizon"] == H)]
        unique_windows = np.sort(sub["window_start"].unique())
        unique_seeds = np.sort(sub["seed"].unique())
        n_w = len(unique_windows)
        n_s = len(unique_seeds)

        piv_esn = sub.pivot(index="window_start", columns="seed", values="mase_ssrc_lag").loc[unique_windows, unique_seeds].values
        piv_stat = sub.pivot(index="window_start", columns="seed", values="mase_static_lag").loc[unique_windows, unique_seeds].values
        piv_ridge = sub.pivot(index="window_start", columns="seed", values="mase_ridge").loc[unique_windows, unique_seeds].values

        diff_ridge_sample = float(np.mean(piv_esn - piv_ridge))
        diff_stat_sample = float(np.mean(piv_esn - piv_stat))

        boot_diff_ridge = []
        boot_diff_stat = []

        for _ in range(N_BOOT):
            w_idx = block_bootstrap_indices(n_w, BLOCK_SIZE, rng)
            s_idx = rng.choice(n_s, size=n_s, replace=True)

            esn_b = piv_esn[w_idx[:, None], s_idx]
            stat_b = piv_stat[w_idx[:, None], s_idx]
            ridge_b = piv_ridge[w_idx[:, None], s_idx]

            boot_diff_ridge.append(np.mean(esn_b - ridge_b))
            boot_diff_stat.append(np.mean(esn_b - stat_b))

        ci_ridge_low, ci_ridge_high = np.percentile(boot_diff_ridge, [2.5, 97.5])
        ci_stat_low, ci_stat_high = np.percentile(boot_diff_stat, [2.5, 97.5])

        results.append({
            "regime": regime,
            "horizon": H,
            "diff_mean_vs_ridge": diff_ridge_sample,
            "ci_vs_ridge_2.5": float(ci_ridge_low),
            "ci_vs_ridge_97.5": float(ci_ridge_high),
            "diff_mean_vs_static": diff_stat_sample,
            "ci_vs_static_2.5": float(ci_stat_low),
            "ci_vs_static_97.5": float(ci_stat_high),
        })

    # 2. Regimenes de Ruido: (window_start x noise_seed) cruzado con reservoir seeds
    noise_regimes = [
        ("noise_0.1_filtering", 1),
        ("noise_0.1_observational", 1),
        ("noise_0.5_filtering", 1),
        ("noise_0.5_observational", 1),
    ]

    for regime, H in noise_regimes:
        sub = df[(df["regime"] == regime) & (df["horizon"] == H)].sort_values(["window_start", "noise_seed", "seed"])
        unique_windows = np.sort(sub["window_start"].unique())
        unique_noise_seeds = np.sort(sub["noise_seed"].unique())
        unique_seeds = np.sort(sub["seed"].unique())
        n_w = len(unique_windows)
        n_ns = len(unique_noise_seeds)
        n_s = len(unique_seeds)

        # Vectorized pivot to 3D tensor: (n_w, n_ns, n_s)
        piv_3d_esn = sub.pivot_table(index=["window_start", "noise_seed"], columns="seed", values="mase_ssrc_lag").values.reshape(n_w, n_ns, n_s)
        piv_3d_stat = sub.pivot_table(index=["window_start", "noise_seed"], columns="seed", values="mase_static_lag").values.reshape(n_w, n_ns, n_s)
        piv_3d_ridge = sub.pivot_table(index=["window_start", "noise_seed"], columns="seed", values="mase_ridge").values.reshape(n_w, n_ns, n_s)

        diff_ridge_sample = float(np.mean(piv_3d_esn - piv_3d_ridge))
        diff_stat_sample = float(np.mean(piv_3d_esn - piv_3d_stat))

        boot_diff_ridge = []
        boot_diff_stat = []

        for _ in range(N_BOOT):
            w_idx = block_bootstrap_indices(n_w, BLOCK_SIZE, rng)
            ns_idx = rng.choice(n_ns, size=n_ns, replace=True)
            s_idx = rng.choice(n_s, size=n_s, replace=True)

            esn_b = piv_3d_esn[w_idx[:, None, None], ns_idx[None, :, None], s_idx[None, None, :]]
            stat_b = piv_3d_stat[w_idx[:, None, None], ns_idx[None, :, None], s_idx[None, None, :]]
            ridge_b = piv_3d_ridge[w_idx[:, None, None], ns_idx[None, :, None], s_idx[None, None, :]]

            boot_diff_ridge.append(np.mean(esn_b - ridge_b))
            boot_diff_stat.append(np.mean(esn_b - stat_b))

        ci_ridge_low, ci_ridge_high = np.percentile(boot_diff_ridge, [2.5, 97.5])
        ci_stat_low, ci_stat_high = np.percentile(boot_diff_stat, [2.5, 97.5])

        results.append({
            "regime": regime,
            "horizon": H,
            "diff_mean_vs_ridge": diff_ridge_sample,
            "ci_vs_ridge_2.5": float(ci_ridge_low),
            "ci_vs_ridge_97.5": float(ci_ridge_high),
            "diff_mean_vs_static": diff_stat_sample,
            "ci_vs_static_2.5": float(ci_stat_low),
            "ci_vs_static_97.5": float(ci_stat_high),
        })

    # 3. Regimenes de Shocks Puntuales: Remuestreo de las 5 UBICACIONES manteniendo pareados ambos signos (+ y -)
    for mag in (15, 50):
        regime = f"shock_{mag}sigma"
        sub = df[(df["regime"] == regime) & (df["horizon"] == 1)].sort_values(["location", "sign", "seed"])
        unique_locs = np.sort(sub["location"].unique())
        n_locs = len(unique_locs)
        unique_seeds = np.sort(sub["seed"].unique())
        n_s = len(unique_seeds)

        # Tensor de ubicaciones: (n_locs, 2_signs, n_s)
        piv_shk_esn = sub.pivot_table(index=["location", "sign"], columns="seed", values="mase_ssrc_lag").values.reshape(n_locs, 2, n_s)
        piv_shk_stat = sub.pivot_table(index=["location", "sign"], columns="seed", values="mase_static_lag").values.reshape(n_locs, 2, n_s)
        piv_shk_ridge = sub.pivot_table(index=["location", "sign"], columns="seed", values="mase_ridge").values.reshape(n_locs, 2, n_s)

        diff_ridge_sample = float(np.mean(piv_shk_esn - piv_shk_ridge))
        diff_stat_sample = float(np.mean(piv_shk_esn - piv_shk_stat))

        boot_diff_ridge = []
        boot_diff_stat = []

        for _ in range(N_BOOT):
            loc_idx = rng.choice(n_locs, size=n_locs, replace=True)
            s_idx = rng.choice(n_s, size=n_s, replace=True)

            esn_b = piv_shk_esn[loc_idx[:, None, None], :, s_idx[None, None, :]]
            stat_b = piv_shk_stat[loc_idx[:, None, None], :, s_idx[None, None, :]]
            ridge_b = piv_shk_ridge[loc_idx[:, None, None], :, s_idx[None, None, :]]

            boot_diff_ridge.append(np.mean(esn_b - ridge_b))
            boot_diff_stat.append(np.mean(esn_b - stat_b))

        ci_ridge_low, ci_ridge_high = np.percentile(boot_diff_ridge, [2.5, 97.5])
        ci_stat_low, ci_stat_high = np.percentile(boot_diff_stat, [2.5, 97.5])

        results.append({
            "regime": regime,
            "horizon": 1,
            "diff_mean_vs_ridge": diff_ridge_sample,
            "ci_vs_ridge_2.5": float(ci_ridge_low),
            "ci_vs_ridge_97.5": float(ci_ridge_high),
            "diff_mean_vs_static": diff_stat_sample,
            "ci_vs_static_2.5": float(ci_stat_low),
            "ci_vs_static_97.5": float(ci_stat_high),
        })

    df_boot = pd.DataFrame(results)
    out_csv = os.path.join(OUT_DIR, "lorenz_two_way_block_bootstrap.csv")
    df_boot.to_csv(out_csv, index=False)
    print("\n=== RESULTADOS DEL TWO-WAY BLOCK BOOTSTRAP CRUZADO (SIGNOS PAREADOS) ===")
    print(df_boot.to_string(index=False))
    return df_boot


if __name__ == "__main__":
    run_bootstrap_analysis()
