"""
Structural Coupling Matrix Visualization: v6 Limpio
=====================================================
Cambios:
  LIMPIEZA: Eliminado import numpy redundante dentro de función
  MEJORA-8: Anotaciones de P* > 0.3 dentro del heatmap para paper
"""
import matplotlib.pyplot as plt
import numpy as np
from config.topology import HIERARCHICAL_ORDER
from config.settings import FIG_DPI
import pandas as pd


def plot_structure_matrix(p_matrix_active, active_ents, best_w, best_lam, output_path):
    # Construct Full Matrix Layout explicitly based on Hierarchy
    full_dim = len(HIERARCHICAL_ORDER)
    p_matrix_full = np.zeros((full_dim, full_dim))
    
    for i, ent_row in enumerate(active_ents):
        row_idx = HIERARCHICAL_ORDER.index(ent_row)
        for j, ent_col in enumerate(active_ents):
            col_idx = HIERARCHICAL_ORDER.index(ent_col)
            p_matrix_full[row_idx, col_idx] = p_matrix_active[i, j]

    # Save CSV
    csv_path = output_path.replace(".png", ".csv")
    df_struct = pd.DataFrame(p_matrix_full, index=HIERARCHICAL_ORDER, columns=HIERARCHICAL_ORDER)
    df_struct.to_csv(csv_path)
    print(f"Saved structure matrix data to {csv_path}")

    plt.figure(figsize=(12, 10), dpi=FIG_DPI)
    im = plt.imshow(p_matrix_full, aspect="auto", cmap="magma", interpolation="none")

    n_active = len(active_ents)
    plt.title(f"Structural Coupling Matrix P* (Hierarchical 16+1)\nW={best_w}, Lambda={best_lam:.3f} | {n_active} active entities")

    plt.xticks(range(full_dim), HIERARCHICAL_ORDER, rotation=90, fontsize=9)
    plt.yticks(range(full_dim), HIERARCHICAL_ORDER, fontsize=9)

    # Grid
    plt.grid(which="major", color="w", linestyle="-", linewidth=0.2, alpha=0.1)
    plt.tick_params(axis=u'both', which=u'both', length=0)

    # Anotación de coeficientes significativos en celdas
    for i in range(full_dim):
        for j in range(full_dim):
            val = p_matrix_full[i, j]
            if val > 0.3:
                text_color = "white" if val > 0.7 else "black"
                plt.text(j, i, f"{val:.2f}", ha="center", va="center", 
                         fontsize=7, color=text_color, fontweight="bold")

    cbar = plt.colorbar(im)
    cbar.set_label("Directional Influence Strength")

    plt.tight_layout()
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved structure matrix to {output_path}")
