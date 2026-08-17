"""
Genera en ingles las figuras del suplemento (BCIE causal, precios de combustibles Honduras,
mecanismo de fallo NNLS) que hasta ahora se reusaban en espanol del pipeline original. Lee
directamente los CSV de salida auditados, igual que make_figures_english.py para el texto
principal -- no reejecuta ningun experimento.
"""
from pathlib import Path
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
FUEL_CODE = BASE / "experimento_combustibles_honduras"
if str(FUEL_CODE) not in sys.path:
    sys.path.insert(0, str(FUEL_CODE))

from data_paths import resolve_fuel_repository
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 600,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
W_SINGLE = 3.37
W_DOUBLE = 6.69
MIN_FONT_PT = 8.5


def save(fig, name):
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / name)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 1. BCIE annual panel: causal MASE by method (coverage-matched, 8 entities)
# ---------------------------------------------------------------------------
bcie_file = BASE / "experimento" / "codigo_pipeline" / "output" / "comparacion_cobertura_pareja.csv"
if not bcie_file.exists():
    raise FileNotFoundError(f"Falta {bcie_file}")
df_bcie = pd.read_csv(bcie_file)

label_map = {
    "reservoir": "Recurrent sparse ESN (ref.)",
}
labels_bcie, values_bcie = [], []
for _, row in df_bcie.iterrows():
    variant = row.get("variant", "")
    k = row.get("k", "")
    if pd.isna(variant) or variant == "" or variant == "reservoir":
        lab = "Recurrent sparse ESN (ref.)"
    else:
        pretty = {"baseline": "Baseline PCA", "ledoitwolf": "Ledoit-Wolf",
                  "tikhonov_covariance": "Tikhonov covariance", "nnls_directo": "NNLS direct"}.get(variant, variant)
        lab = f"{pretty} (k={int(k)})"
    labels_bcie.append(lab)
    values_bcie.append(row["mase"])

order = np.argsort(values_bcie)
labels_bcie = [labels_bcie[i] for i in order]
values_bcie = [values_bcie[i] for i in order]

fig, ax = plt.subplots(figsize=(W_DOUBLE, 3.0))
colors = ["#4C72B0" if "NNLS" in l else ("#55A868" if "ESN" in l else "#8C8C8C") for l in labels_bcie]
ax.barh(labels_bcie, values_bcie, color=colors)
ax.set_xlabel("MASE, 8 common entities")
ax.set_title("BCIE supplement: numerical advantage without block significance")
ax.invert_yaxis()
save(fig, "fig12_bcie_causal.pdf")
print("[fig12_bcie_causal] saved")

# ---------------------------------------------------------------------------
# 2. Honduras weekly fuel prices, 2017-2026, with shock windows
# ---------------------------------------------------------------------------
repo_file = resolve_fuel_repository()
df_fuel = pd.read_csv(repo_file, encoding="utf-8-sig")
df_fuel["FechaInicioISO"] = pd.to_datetime(df_fuel["FechaInicioISO"], errors="coerce")
df_fuel = df_fuel.sort_values("FechaInicioISO")

EVENTS = {
    "COVID-19": (pd.Timestamp("2020-02-15"), pd.Timestamp("2020-05-15"), "#C44E52"),
    "Hurricanes Eta/Iota": (pd.Timestamp("2020-11-01"), pd.Timestamp("2020-12-21"), "#4C72B0"),
    "Russia-Ukraine war": (pd.Timestamp("2022-02-15"), pd.Timestamp("2022-06-15"), "#DD8452"),
    "Middle East crisis": (pd.Timestamp("2026-03-01"), pd.Timestamp("2026-06-30"), "#55A868"),
}

fig, ax = plt.subplots(figsize=(W_DOUBLE, 3.2))
for fuel, color in [("S\u00faper", "#374649"), ("Regular", "#982C33"),
                     ("Diesel", "#3f6c3e"), ("Kerosene", "#134966")]:
    if fuel in df_fuel.columns:
        ax.plot(df_fuel["FechaInicioISO"], df_fuel[fuel], lw=1.1, color=color,
                label="Super" if fuel == "S\u00faper" else fuel)
for name, (start, end, color) in EVENTS.items():
    ax.axvspan(start, end, color=color, alpha=0.15)
ax.xaxis.set_major_locator(mdates.YearLocator(1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("'%y"))
ax.set_xlabel("year")
ax.set_ylabel("price (Lps.)")
ax.set_title("Weekly fuel prices, Honduras (2017-2026)")
handles = [plt.Line2D([0], [0], color=c, lw=6) for c in ["#374649", "#982C33", "#3f6c3e", "#134966"]]
handles += [plt.Rectangle((0, 0), 1, 1, color=EVENTS[n][2], alpha=0.3) for n in EVENTS]
labels_h = ["Super", "Regular", "Diesel", "Kerosene"] + list(EVENTS.keys())
ax.legend(handles, labels_h, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False, fontsize=MIN_FONT_PT)
save(fig, "fig7_combustibles_precios.pdf")
print("[fig7_combustibles_precios] saved")

# ---------------------------------------------------------------------------
# 3. Mechanism of failure: raw legacy signed NNLS prediction vs. realized volatility
# ---------------------------------------------------------------------------
neg_file = BASE / "experimento_combustibles_honduras" / "output" / "investigacion_negativas_por_semana.csv"
if not neg_file.exists():
    raise FileNotFoundError(f"Falta {neg_file}")
df_neg = pd.read_csv(neg_file)
week = df_neg[df_neg["fecha"] == "2020-05-11"]
if week.empty:
    raise ValueError("No se encontro la semana 2020-05-11 en investigacion_negativas_por_semana.csv")

fuels_order = ["S\u00faper", "Regular", "Diesel", "Kerosene"]
y_true_vals = [week[week["fuel"] == f]["y_true"].values[0] for f in fuels_order]
pred_vals = [week[week["fuel"] == f]["nnls_signado_legacy"].values[0] for f in fuels_order]

fig, ax = plt.subplots(figsize=(W_SINGLE, 2.8))
x = np.arange(len(fuels_order))
w = 0.35
ax.bar(x - w / 2, y_true_vals, width=w, label="Realized (squared return)", color="#4C72B0")
ax.bar(x + w / 2, pred_vals, width=w, label="Legacy signed NNLS (raw, unclipped)", color="#C44E52")
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels(["Super" if f == "S\u00faper" else f for f in fuels_order])
ax.set_ylabel("realized volatility")
ax.set_title("Week 2020-05-11: legacy NNLS predicts negative")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=1, frameon=False, fontsize=8)
save(fig, "fig9_mecanismo_falla_nnls.pdf")
print("[fig9_mecanismo_falla_nnls] saved")

print("\nSupplementary figures regenerated in English: figures/fig12_bcie_causal.pdf, "
      "figures/fig7_combustibles_precios.pdf, figures/fig9_mecanismo_falla_nnls.pdf")
