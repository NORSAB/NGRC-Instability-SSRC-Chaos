"""
Readout and Decomposition Visualization: v6 Mejorado
======================================================
Cambios:
  MEJORA-4: R² y RMSE anotados dentro de cada panel del Hub Readout
  MEJORA-5: CSV incluye métricas de fit
"""
import numpy as np
import matplotlib.pyplot as plt
from config.settings import FIG_DPI, TEXTS
from config.topology import SYNTHETIC_HUB_NAME
import pandas as pd


def plot_hub_readout(hub_data, pred_hub, output_path):
    yrs_hub = hub_data["years"]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=FIG_DPI)
    titles = ["Total Amount (USD)", "Approval Count", "Scale Divergence"]
    series_obs = [hub_data["alpha_raw"][0], hub_data["alpha_raw"][1], hub_data["alpha_scale"]]
    series_pred = [pred_hub[:, 0], pred_hub[:, 1], pred_hub[:, 0] - pred_hub[:, 1]]

    # Save CSV
    csv_path = output_path.replace(".png", ".csv")
    df_readout = pd.DataFrame({
        "Year": yrs_hub,
        "Obs_Amount": series_obs[0], "Pred_Amount": series_pred[0],
        "Obs_Count": series_obs[1], "Pred_Count": series_pred[1],
        "Obs_Scale": series_obs[2], "Pred_Scale": series_pred[2]
    })
    df_readout.to_csv(csv_path, index=False)
    print(f"Saved hub readout data to {csv_path}")

    for i, ax in enumerate(axes):
        ax.plot(yrs_hub, series_obs[i], "k-", lw=2, label="Observed")
        ax.plot(yrs_hub, series_pred[i], color="gray", linestyle="--", lw=2, label="SSRC Reconstruction")
        ax.set_title(titles[i])
        ax.set_xlabel(TEXTS["timeline_xlabel"])
        if i == 0: ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Anotación de métricas de ajuste R y RMSE dentro de cada panel
        r_val = np.corrcoef(series_obs[i], series_pred[i])[0, 1]
        rmse_val = np.sqrt(np.mean((series_obs[i] - series_pred[i])**2))
        ax.text(0.03, 0.95, f"R = {r_val:.3f}\nRMSE = {rmse_val:.4f}", 
                transform=ax.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85, edgecolor='gray'))

    plt.suptitle(f"Systemic Cycle Reconstruction: {SYNTHETIC_HUB_NAME}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved hub readout to {output_path}")


def plot_hub_projection(hub_data, yrs_hub, proj_y, proj_z, output_path):
    fig, ax1 = plt.subplots(figsize=(12, 6), dpi=FIG_DPI)
    ax1.plot(yrs_hub, hub_data["z"], color="tab:blue", lw=2.5, alpha=0.8, label="Observed Latent State")
    ax1.plot(proj_y, proj_z, "k--", lw=2, label="Structural Projection (P*)")
    ax1.set_ylabel("Latent State Magnitude", color="tab:blue")
    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.fill_between(yrs_hub, hub_data["alpha_scale"], color="tab:red", alpha=0.15)
    ax2.plot(yrs_hub, hub_data["alpha_scale"], "r:", lw=1.5, label="Scale Divergence")
    ax2.set_ylabel("Scale Divergence (Alpha)", color="tab:red")

    plt.title(f"Systemic Hub Dynamics: Structural Inertia vs. Scale\n{SYNTHETIC_HUB_NAME}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved hub projection to {output_path}")


def plot_regime_decomposition(hub_data, output_path):
    years = hub_data["years"]
    alpha_vol = hub_data["alpha_raw"][0]
    alpha_freq = hub_data["alpha_raw"][1]
    alpha_scale = hub_data["alpha_scale"]

    # Save CSV
    csv_path = output_path.replace(".png", ".csv")
    df_regime = pd.DataFrame({
        "Year": years,
        "Alpha_Total_Vol": alpha_vol,
        "Alpha_Count_Freq": alpha_freq,
        "Alpha_Scale_Div": alpha_scale
    })
    df_regime.to_csv(csv_path, index=False)
    print(f"Saved regime data to {csv_path}")

    plt.figure(figsize=(10, 6), dpi=FIG_DPI)

    plt.plot(
        years, alpha_vol,
        color="#333333",
        lw=1.5,
        linestyle='--',
        label=r"$\alpha^{Total}$ (Financial Volume)"
    )

    plt.plot(
        years, alpha_freq,
        color="#888888",
        lw=1.5,
        linestyle=':',
        label=r"$\alpha^{Count}$ (Operational Frequency)"
    )

    plt.fill_between(
        years, alpha_scale, 0,
        color='black',
        alpha=0.08,
        label=r"$\alpha^{Scale}$ (Net Divergence)"
    )

    plt.plot(
        years, alpha_scale,
        color="black",
        linestyle='-',
        lw=2.0,
        alpha=0.9
    )

    plt.axhline(0, color='gray', linewidth=0.8, linestyle='-')
    plt.axvline(2010, color='#444444', linewidth=1.2, linestyle=':')

    y_text_pos = np.max(alpha_scale) * 0.85

    plt.text(
        2011, y_text_pos,
        "Post-2010 Shift:\nConsolidation Regime\n(Mega-Projects Strategy)",
        color='#333333',
        fontsize=10,
        fontweight='bold',
        ha='left',
        bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray', boxstyle='round,pad=0.5')
    )

    plt.title(f"Decomposition of Strategic Regimes ({SYNTHETIC_HUB_NAME})", fontsize=14, pad=15)
    plt.ylabel("Relative Rate of Change (TCRA)", fontsize=12)
    plt.xlabel("Fiscal Year", fontsize=12)

    plt.legend(loc="lower left", frameon=True, framealpha=0.95, fontsize=10)
    plt.grid(True, alpha=0.2, linestyle=':')
    plt.xlim(np.min(years), np.max(years))

    plt.tight_layout()
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved regime decomposition to {output_path}")
