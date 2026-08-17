"""
Eigenvalue Spectrum Visualization — v6 Mejorado
================================================
Cambios:
  MEJORA-6: Anotar ρ, n_eigenvalues, |eig|_mean dentro del plot
  MEJORA-7: CSV incluye estadísticas resumen
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from config.settings import FIG_DPI
import pandas as pd


def plot_eigenvalue_spectrum(pres_matrix, output_path):
    # Compute Eigenvalues
    eigenvals = np.linalg.eigvals(pres_matrix)
    rho_measured = np.max(np.abs(eigenvals))
    has_outliers = rho_measured > 1.0 + 1e-6
    abs_eigs = np.abs(eigenvals)

    # Save CSV
    csv_path = output_path.replace(".png", ".csv")
    df_eig = pd.DataFrame({
        "Real": eigenvals.real, 
        "Imag": eigenvals.imag, 
        "Abs": abs_eigs
    })
    df_eig.to_csv(csv_path, index=False)
    print(f"Saved eigenvalue data to {csv_path}")
    
    # ── MEJORA-7: Resumen de estadísticas ──
    stats_path = output_path.replace(".png", "_stats.csv")
    pd.DataFrame([{
        "rho": rho_measured,
        "n_eigenvalues": len(eigenvals),
        "abs_min": np.min(abs_eigs),
        "abs_mean": np.mean(abs_eigs),
        "abs_median": np.median(abs_eigs),
        "abs_max": np.max(abs_eigs),
        "n_real_positive": np.sum(eigenvals.real > 0),
        "n_real_negative": np.sum(eigenvals.real < 0),
        "n_complex_pairs": np.sum(np.abs(eigenvals.imag) > 1e-10) // 2,
        "all_stable": int(np.all(abs_eigs < 1.0))
    }]).to_csv(stats_path, index=False)
    print(f"Saved eigenvalue stats to {stats_path}")

    fig, ax = plt.subplots(figsize=(7, 7), dpi=FIG_DPI)
    theta = np.linspace(0, 2*np.pi, 500)

    # Main Plot
    ax.plot(np.cos(theta), np.sin(theta), "--", color="gray", lw=1.5, label="Unit Circle")
    ax.scatter(eigenvals.real, eigenvals.imag, marker="x", color="black", s=60, label="Eigenvalues")
    ax.axhline(0, color='black', lw=0.5)
    ax.axvline(0, color='black', lw=0.5)
    ax.set_aspect("equal")
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    ax.set_title(f"Eigenvalue Spectrum of Latent Operator P_res\nMeasured Rho: {rho_measured:.4f}")
    ax.set_xlabel("Real Part")
    ax.set_ylabel("Imaginary Part")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # Minimap for outliers
    if has_outliers:
        axins = inset_axes(ax, width="35%", height="35%", loc="lower left", borderpad=1)
        axins.plot(np.cos(theta), np.sin(theta), "--", color="gray", lw=0.8, alpha=0.6)
        axins.axhline(0, color='black', lw=0.4)
        axins.axvline(0, color='black', lw=0.4)
        
        mask_inner = np.abs(eigenvals) <= 1.0
        ev_inner = eigenvals[mask_inner]
        ev_outer = eigenvals[~mask_inner]
        
        axins.scatter(ev_inner.real, ev_inner.imag, marker=".", color="tab:blue", s=5, alpha=0.4)
        axins.scatter(ev_outer.real, ev_outer.imag, marker="x", color="tab:red", s=40, linewidth=1.5)
        
        limit = rho_measured * 1.15
        axins.set_xlim(-limit, limit)
        axins.set_ylim(-limit, limit)
        axins.set_title("Full Spectrum View", fontsize=8)
        axins.tick_params(labelsize=6)
        axins.grid(True, alpha=0.2)
    else:
        # Anotación de estadísticas espectrales
        n_complex = np.sum(np.abs(eigenvals.imag) > 1e-10) // 2
        ax.text(0.05, 0.05, 
                f"System Stable: All eigenvalues within unit circle.\n"
                f"n = {len(eigenvals)}, |eig|_mean = {np.mean(abs_eigs):.3f}, "
                f"complex pairs = {n_complex}",
                transform=ax.transAxes, fontsize=9, 
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.4'))

    plt.tight_layout()
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved eigenvalue spectrum to {output_path}")
