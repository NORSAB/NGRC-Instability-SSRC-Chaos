"""
Sensitivity Analysis Heatmap
"""
import matplotlib.pyplot as plt
from config.settings import FIG_DPI

def plot_sensitivity_heatmap(pivot_table, best_w, best_lam, output_path, metric_name="MASE"):
    # Save CSV
    csv_path = output_path.replace(".png", ".csv")
    pivot_table.to_csv(csv_path)
    print(f"Saved sensitivity data to {csv_path}")

    # Configure labels based on metric
    if metric_name == "Frobenius":
        title = "Sensitivity Heatmap: OOS Frobenius Error (Lower is Better)"
        cbar_label = "Relative Frobenius Error (OOS)"
    else:
        title = "Sensitivity Analysis: OOS MASE (Lower is Better)"
        cbar_label = "Mean Absolute Scaled Error (MASE)"

    fig, ax = plt.subplots(figsize=(14, 5), dpi=FIG_DPI)
    
    im = ax.imshow(
        pivot_table.values,
        aspect="auto",
        origin="lower",
        cmap="inferno_r", # IEEE-friendly: perceptually uniform, B/W readable
        interpolation="nearest"
    )
    
    ax.set_title(title)
    ax.set_ylabel("Window Size (W) [Years]")
    ax.set_xlabel("Decay Factor (Lambda)")
    
    ax.set_yticks(range(len(pivot_table.index)))
    ax.set_yticklabels([str(w) for w in pivot_table.index])
    
    ax.set_xticks(range(len(pivot_table.columns)))
    ax.set_xticklabels([f"{c:.2f}" for c in pivot_table.columns], rotation=90)
    
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    
    if best_w is not None:
        try:
            w_idx = list(pivot_table.index).index(best_w)
            l_idx = list(pivot_table.columns).index(best_lam)
            ax.scatter([l_idx], [w_idx], s=150, marker="o", facecolors="white", 
                       edgecolors="black", linewidth=2.5, label="Optimal")
            ax.legend(loc="upper right")
        except ValueError: pass

    plt.tight_layout()
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved sensitivity heatmap to {output_path}")

