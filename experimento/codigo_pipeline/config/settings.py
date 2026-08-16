"""
Global Configuration Settings
"""
import matplotlib.pyplot as plt
from matplotlib import rcParams

# --- GLOBAL CONSTANTS ---
FIG_DPI = 600
LANG = "EN"
GLOBAL_SEED = 7

def get_plot_labels(lang: str) -> dict:
    """
    Retrieves the dictionary of plot labels based on the selected language.
    Args:
        lang (str): Language code ("EN" or "ES").
    Returns:
        dict: Key-value pairs for plot titles, axes, and legends.
    """
    if lang == "ES":
        return {
            "timeline_xlabel": "Año Fiscal",
            "founders": "Fundadores",
            "regional_nf": "Regional No Fundadores",
            "extra": "Extra-Regionales",
            "regional": "Entidad Regional (Spoke Programático)",
            "hub": "Hub Sistémico (Sintético)",
            "p_title": "Matriz de Acoplamiento Estructural P*",
            "influence": "Fuerza de Influencia",
            "pres_spectrum": "Espectro de Valores Propios (Dinámica Latente)",
            "pres_heatmap": "Operador de Transición Latente P_res",
            "recon_title": "Reconstrucción de Observables (Readout)",
            "scale_title": "Dinámica Regional: Reconstrucción SSRC y Divergencia de Escala",
            "obs": "Observado",
            "rec": "Reconstrucción SSRC",
            "div": "Divergencia de Escala",
            "latent_state": "Estado Latente",
            "scale_div_ylabel": "Divergencia de Escala"
        }
    else:
        return {
            "timeline_xlabel": "Fiscal Year",
            "founders": "Founding Members",
            "regional_nf": "Regional Non-Founders",
            "extra": "Extra-Regional",
            "regional": "Regional Programmatic Entity",
            "hub": "BCIE Systemic Hub (Synthetic)",
            "p_title": "Structural Coupling Matrix P*",
            "influence": "Influence Strength",
            "pres_spectrum": "Eigenvalue Spectrum (Latent Dynamics)",
            "pres_heatmap": "Latent Transition Operator P_res",
            "recon_title": "Observable Reconstruction (Readout Fit)",
            "scale_title": "Regional Dynamics: SSRC Reconstruction & Scale Divergence",
            "obs": "Observed Dynamics",
            "rec": "SSRC Reconstruction",
            "div": "Scale Divergence",
            "latent_state": "Latent State $z_t$",
            "scale_div_ylabel": "Scale Divergence $\\alpha^{Scale}$"
        }

TEXTS = get_plot_labels(LANG)

def set_plot_style():
    """
    Configures the global Matplotlib style for publication-quality figures.
    """
    plt.style.use("ggplot")
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    rcParams['font.size'] = 11
    rcParams['figure.dpi'] = FIG_DPI
    rcParams['savefig.dpi'] = FIG_DPI
    # Ensure minus signs are rendered correctly in PDF exports
    rcParams['axes.unicode_minus'] = False
