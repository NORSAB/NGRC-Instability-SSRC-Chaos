"""Genera las figuras suplementarias de combustibles con resultados causales.

Lee output/oos_combustibles.csv y el repositorio; no vuelve a correr el experimento.
Convención fija: leyenda SIEMPRE fuera del área de graficado, abajo y centrada; eje de fechas
continuo (locator anual explícito, NO categórico)."""
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from eventos import EVENTOS
from data_paths import resolve_fuel_repository

plt.rcParams.update({"font.size": 11, "figure.dpi": 600, "savefig.dpi": 600,
                     "axes.spines.top": False, "axes.spines.right": False})

BASE = Path(__file__).resolve().parent
FIGURAS = BASE.parent / "paper" / "figuras"
OUTPUT = BASE / "output"
REPO = resolve_fuel_repository()
FUELS = ["Súper", "Regular", "Diesel", "Kerosene"]
W_FULL = 6.8
EVENTO_COLOR = {"covid_2020": "#C44E52", "eta_iota_2020": "#4C72B0",
               "ucrania_2022": "#DD8452", "medio_oriente_2026": "#55A868"}
EVENTO_LABEL = {"covid_2020": "COVID-19", "eta_iota_2020": "Huracanes Eta/Iota",
               "ucrania_2022": "Guerra Rusia-Ucrania", "medio_oriente_2026": "Crisis Medio Oriente"}


def leyenda_abajo(ax_or_fig, ncol, y=-0.18, fontsize=9):
    ax_or_fig.legend(loc="upper center", bbox_to_anchor=(0.5, y), ncol=ncol,
                     fontsize=fontsize, frameon=False)


FIGURAS.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(REPO, encoding="utf-8-sig")
df["FechaInicioISO"] = pd.to_datetime(df["FechaInicioISO"])
df = df.sort_values("FechaInicioISO")

# ---------- Fig 7: precios, ancho completo, los 4 eventos sombreados ----------
# Los eventos se identifican por color en una leyenda externa para evitar
# superposiciones dentro del area de graficado.
fig, ax = plt.subplots(figsize=(W_FULL, 4.2))
colors = {"Súper": "#374649", "Regular": "#982C33", "Diesel": "#3f6c3e", "Kerosene": "#134966"}
for fuel, c in colors.items():
    ax.plot(df["FechaInicioISO"], df[fuel], lw=1.3, label=fuel, color=c)
for nombre, (ini, fin) in EVENTOS.items():
    ax.axvspan(ini, fin, color=EVENTO_COLOR[nombre], alpha=0.13)
# eje de fechas CONTINUO (no categorico): locator anual explicito, formato de 2 digitos
# para que los ticks no se amontonen (igual criterio que la Fig. 11).
ax.xaxis.set_major_locator(mdates.YearLocator(1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("'%y"))
ax.set_xlabel("año")
ax.set_ylabel("precio (Lps.)")
ax.set_title("Precios semanales de combustibles, Honduras (2017-2026)")
handles_f, labels_f = ax.get_legend_handles_labels()
handles_ev = [plt.Rectangle((0, 0), 1, 1, color=EVENTO_COLOR[n], alpha=0.35) for n in EVENTOS]
labels_ev = [EVENTO_LABEL[n] for n in EVENTOS]
ax.legend(handles_f + handles_ev, labels_f + labels_ev, loc="upper center",
         bbox_to_anchor=(0.5, -0.16), ncol=4, fontsize=8.5, frameon=False)
fig.tight_layout()
fig.savefig(FIGURAS / "fig7_combustibles_precios.pdf", bbox_inches="tight")
plt.close(fig)

# ---------- Fig 8: comparadores justos, sin los lectores recortados de legado ----------
doos = pd.read_csv(OUTPUT / "oos_combustibles.csv")
piv = doos.groupby(["mode", "categoria"])["qlike"].median().unstack("categoria")
order = ["naive", "garch_11", "gjr_garch_11", "nnls_base_no_negativa",
         "ngrc_softplus_cv", "ssrc_recurrente_log_cv"]
labels = ["naive", "GARCH", "GJR-GARCH", "NNLS base no negativa",
          "NG-RC softplus", "SSRC recurrente"]
cats = ["calma", "covid_2020", "eta_iota_2020", "ucrania_2022", "medio_oriente_2026"]
cats = [c for c in cats if c in piv.columns]
piv = piv.loc[order, cats]
fig, ax = plt.subplots(figsize=(W_FULL, 4.4))
x = range(len(order))
w = 0.16
cat_colors = ["#8C8C8C"] + [EVENTO_COLOR[c] for c in cats[1:]]
cat_labels = ["calma"] + [EVENTO_LABEL[c] for c in cats[1:]]
for i, (cat, lab, col) in enumerate(zip(cats, cat_labels, cat_colors)):
    off = (i - (len(cats) - 1) / 2) * w
    ax.bar([xi + off for xi in x], piv[cat], width=w, label=lab, color=col)
ax.set_xticks(list(x)); ax.set_xticklabels(labels, rotation=18, ha="right")
ax.set_ylabel("QLIKE mediano (agregado, 4 combustibles)")
ax.set_title("Combustibles HN: QLIKE causal por método y ventana")
leyenda_abajo(ax, ncol=3, y=-0.22)
fig.tight_layout()
fig.savefig(FIGURAS / "fig8_combustibles_qlike.pdf", bbox_inches="tight")
plt.close(fig)

print("fig7 y fig8 regeneradas: 600 dpi, ancho completo, eje de años continuo, leyenda abajo.")
