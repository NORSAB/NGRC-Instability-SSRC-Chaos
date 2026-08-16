"""
Timeline Analysis Visualization
"""
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
from config.topology import (
    HIERARCHICAL_ORDER, SYNTHETIC_HUB_NAME, TIME_COL, ENTITY_COL, 
    GROUP_FOUNDERS, GROUP_REGIONAL_NON_FOUNDERS
)
from config.settings import FIG_DPI, TEXTS
import pandas as pd
import os

def get_color_topology(pais):
    """Assigns Magma colors based on topological role."""
    if pais == SYNTHETIC_HUB_NAME: return plt.cm.magma(0.05)
    if pais == "Regional": return plt.cm.magma(0.85)
    if pais in GROUP_FOUNDERS: return plt.cm.magma(0.25)
    if pais in GROUP_REGIONAL_NON_FOUNDERS: return plt.cm.magma(0.50)
    return plt.cm.magma(0.70)

def plot_timeline(df_plot, output_path, partial_year=None):
    """partial_year: anio incompleto (e.g., 2026) dibujado con marcador hueco y nota."""
    # Determine order from HIERARCHICAL_ORDER (bottom-up for plot Y-axis)
    # We want Hub at top, so reverse index or use negative?
    # Original logic: Guatemala=1, Hub=17 via ORDEN_PAISES.
    # HIERARCHICAL_ORDER: Hub=0, Guat=1...
    # Let's map HIERARCHICAL_ORDER to index: Hub=0, Guat=1, ..., Regional=16
    # Plotting: y=0 at bottom.
    # If we want Hub at top (y=16), we invert.
    
    unique_ents = df_plot[ENTITY_COL].unique()
    valid_ents = [e for e in HIERARCHICAL_ORDER if e in unique_ents]
    
    # Map entity -> y_position. 0 is top in list, so let's reverse for plot
    # HIERARCHICAL_ORDER[0] is Hub. We want it at Y=MAX.
    n_ents = len(HIERARCHICAL_ORDER)
    y_map = {name: (n_ents - 1 - i) for i, name in enumerate(HIERARCHICAL_ORDER)}
    
    df_plot = df_plot[df_plot[ENTITY_COL].isin(y_map.keys())] 
    df_plot["Orden_Y"] = df_plot[ENTITY_COL].map(y_map)

    fig, ax = plt.subplots(figsize=(12, 9), dpi=FIG_DPI)

    # Plot lines and dots
    for ent in HIERARCHICAL_ORDER:
        if ent not in y_map: continue
        y_val = y_map[ent]
        sub = df_plot[df_plot["Orden_Y"] == y_val]
        
        if not sub.empty:
            c = get_color_topology(ent)
            ax.hlines(y_val, sub[TIME_COL].min(), sub[TIME_COL].max(), color=c, alpha=0.55, linewidth=1.2, zorder=1)
            ms = 36 if ent == SYNTHETIC_HUB_NAME else 24
            if partial_year is not None:
                full = sub[sub[TIME_COL] != partial_year]
                part = sub[sub[TIME_COL] == partial_year]
                ax.scatter(full[TIME_COL], [y_val]*len(full), color=c, s=ms, marker='D', edgecolors='white', linewidth=0.6, zorder=3)
                if not part.empty:
                    ax.scatter(part[TIME_COL], [y_val]*len(part), facecolors='none', s=ms, marker='D', edgecolors=c, linewidth=1.2, zorder=3)
            else:
                ax.scatter(sub[TIME_COL], [y_val]*len(sub), color=c, s=ms, marker='D', edgecolors='white', linewidth=0.6, zorder=3)

    # Invert mapping for labels
    # y_val -> Name
    ylabels = [ent for ent in HIERARCHICAL_ORDER]
    y_ticks = [y_map[ent] for ent in HIERARCHICAL_ORDER]

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(ylabels)

    # Save CSV
    csv_path = output_path.replace(".png", ".csv")
    df_plot.to_csv(csv_path, index=False)
    print(f"Saved timeline data to {csv_path}")
    ax.set_xlim(1958, 2027)
    ax.set_xlabel(TEXTS["timeline_xlabel"])
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))

    legs = [
        Line2D([0], [0], marker='D', color='w', label=SYNTHETIC_HUB_NAME, markerfacecolor=plt.cm.magma(0.05), markersize=8),
        Line2D([0], [0], marker='D', color='w', label=TEXTS["founders"],    markerfacecolor=plt.cm.magma(0.25), markersize=6),
        Line2D([0], [0], marker='D', color='w', label=TEXTS["regional_nf"], markerfacecolor=plt.cm.magma(0.50), markersize=6),
        Line2D([0], [0], marker='D', color='w', label=TEXTS["extra"],       markerfacecolor=plt.cm.magma(0.70), markersize=6),
        Line2D([0], [0], marker='D', color='w', label="Regional (Spoke)",   markerfacecolor=plt.cm.magma(0.85), markersize=6)
    ]
    if partial_year is not None:
        legs.append(Line2D([0], [0], marker='D', color='w', label=f"{partial_year} (partial year)",
                           markerfacecolor='none', markeredgecolor='black', markersize=6))
    ax.legend(handles=legs, loc='upper center', bbox_to_anchor=(0.5, 1.08), ncol=3, frameon=False)
    ax.grid(True, alpha=0.35)
    for s in ['top','right','bottom','left']: ax.spines[s].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved timeline plot to {output_path}")
