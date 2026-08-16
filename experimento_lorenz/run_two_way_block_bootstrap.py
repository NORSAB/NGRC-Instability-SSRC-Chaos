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
        sub = df[(df["regime"] == regime) & (df["horizon"] == H)]
        unique_windows = np.sort(sub["window_start"].unique())
        unique_noise_seeds = np.sort(sub["noise_seed"].unique())
        unique_seeds = np.sort(sub["seed"].unique())
        n_w = len(unique_windows)
        n_ns = len(unique_noise_seeds)
        n_s = len(unique_seeds)

        tensor_esn = np.zeros((n_w, n_ns, n_s))
        tensor_stat = np.zeros((n_w, n_ns, n_s))
        tensor_ridge = np.zeros((n_w, n_ns, n_s))

        for w_i, w in enumerate(unique_windows):
            for ns_i, ns in enumerate(unique_noise_seeds):
                sub_wns = sub[(sub["window_start"] == w) & (sub["noise_seed"] == ns)]
                for s_i, sd in enumerate(unique_seeds):
                    row = sub_wns[sub_wns["seed"] == sd].iloc[0]
                    tensor_esn[w_i, ns_i, s_i] = row["mase_ssrc_lag"]
                    tensor_stat[w_i, ns_i, s_i] = row["mase_static_lag"]
                    tensor_ridge[w_i, ns_i, s_i] = row["mase_ridge"]

        diff_ridge_sample = float(np.mean(tensor_esn - tensor_ridge))
        diff_stat_sample = float(np.mean(tensor_esn - tensor_stat))

        boot_diff_ridge = []
        boot_diff_stat = []

        for _ in range(N_BOOT):
            w_idx = block_bootstrap_indices(n_w, BLOCK_SIZE, rng)
            ns_idx = rng.choice(n_ns, size=n_ns, replace=True)
            s_idx = rng.choice(n_s, size=n_s, replace=True)

            esn_b = tensor_esn[w_idx[:, None, None], ns_idx[None, :, None], s_idx[None, None, :]]
            stat_b = tensor_stat[w_idx[:, None, None], ns_idx[None, :, None], s_idx[None, None, :]]
            ridge_b = tensor_ridge[w_idx[:, None, None], ns_idx[None, :, None], s_idx[None, None, :]]

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
        sub = df[(df["regime"] == regime) & (df["horizon"] == 1)]
        unique_locs = np.sort(sub["location"].unique())
        n_locs = len(unique_locs)
        unique_seeds = np.sort(sub["seed"].unique())
        n_s = len(unique_seeds)

        diff_ridge_sample = float(np.mean(sub["mase_ssrc_lag"] - sub["mase_ridge"]))
        diff_stat_sample = float(np.mean(sub["mase_ssrc_lag"] - sub["mase_static_lag"]))

        # Tensor de ubicaciones: (n_locs, 2_signs, n_seeds)
        tensor_esn_shk = np.zeros((n_locs, 2, n_s))
        tensor_stat_shk = np.zeros((n_locs, 2, n_s))
        tensor_ridge_shk = np.zeros((n_locs, 2, n_s))

        for l_i, loc in enumerate(unique_locs):
            for sgn_i, sgn in enumerate([+1, -1]):
                sub_ls = sub[(sub["location"] == loc) & (sub["sign"] == sgn)]
                for s_i, sd in enumerate(unique_seeds):
                    row = sub_ls[sub_ls["seed"] == sd].iloc[0]
                    tensor_esn_shk[l_i, sgn_i, s_i] = row["mase_ssrc_lag"]
                    tensor_stat_shk[l_i, sgn_i, s_i] = row["mase_static_lag"]
                    tensor_ridge_shk[l_i, sgn_i, s_i] = row["mase_ridge"]

        boot_diff_ridge = []
        boot_diff_stat = []

        for _ in range(N_BOOT):
            # Remuestrear las ubicaciones completas (conservando pareados los signos + y -)
            loc_idx = rng.choice(n_locs, size=n_locs, replace=True)
            s_idx = rng.choice(n_s, size=n_s, replace=True)

            esn_b = tensor_esn_shk[loc_idx[:, None, None], :, s_idx[None, None, :]]
            stat_b = tensor_stat_shk[loc_idx[:, None, None], :, s_idx[None, None, :]]
            ridge_b = tensor_ridge_shk[loc_idx[:, None, None], :, s_idx[None, None, :]]

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
