"""
IEEE Visualization Styles
"""
from config.settings import set_plot_style, get_plot_labels, FIG_DPI

def apply_ieee_style():
    set_plot_style()

def get_labels(lang="EN"):
    return get_plot_labels(lang)
