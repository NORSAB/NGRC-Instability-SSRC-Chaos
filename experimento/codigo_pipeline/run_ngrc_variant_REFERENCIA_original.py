"""
Variante NG-RC determinista vs reservorio aleatorio (protocolo identico).
==========================================================================
NG-RC (Gauthier et al. 2021, Nat. Commun.): en lugar de un reservorio recurrente
aleatorio, el estado es una expansion polinomial determinista de los delays del
input. Sin pesos aleatorios -> CERO varianza por semilla.

Estado NG-RC en t (input bivariado alpha_t = [a_Total, a_Count]):
  lineal     = [alpha_t, alpha_{t-1}, ..., alpha_{t-k+1}]   (2k dims)
  cuadratico = productos unicos del bloque lineal           (2k(2k+1)/2 dims)
  constante  = 1
Luego: StandardScaler + PCA(1) -> z, mascara hub + NNLS LOO -> P*, metricas OOS.
Protocolo identico al paper: train <= 2019, OOS 2020-2024, datos <= 2025.

Comparacion reportada:
  - Reservoir aleatorio (paper): seed 7 -> MASE 0.924; 20 seeds -> 1.014 +/- 0.079 (CV 7.8%)
  - NG-RC k=2 y k=3: numero unico, determinista.
"""
import os, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from config.hyperparameters import TEST_START_YEAR
from config.topology import TIME_COL, ENTITY_COL, FEATURE_COLS, SYNTHETIC_HUB_NAME, HIERARCHICAL_ORDER
from src.data.ckan_loader import CKANLoader
from src.data.preprocessor import clean_dataframe
from src.data.aggregator import aggregate_data
from src.features.tcroc import build_alpha_by_entity
from src.models.optimization import build_topology_mask, estimate_coupling_matrix
from src.models.metric_tools import evaluate_metrics_oos, evaluate_frobenius_oos

OUT = os.path.join(os.getcwd(), "output_2025")
os.makedirs(OUT, exist_ok=True)
W_STAR, LAM_STAR = 2, 1.0

print("Cargando datos BCIE...")
df = aggregate_data(clean_dataframe(CKANLoader().fetch_data()))
df = df[df[TIME_COL] <= 2025].copy()
ents_all = sorted(df[ENTITY_COL].dropna().unique().tolist())
alpha_data = build_alpha_by_entity(df, ents_all, W_STAR, LAM_STAR)
active = [e for e in HIERARCHICAL_ORDER if e in alpha_data]
print(f"Entidades activas: {len(active)}")

# Construcción de series agregadas crudas LOO del nodo central para cada variante
hub_raw = df[df[ENTITY_COL] == SYNTHETIC_HUB_NAME].groupby(TIME_COL)[FEATURE_COLS].sum()
_frames = []
for _k in [e for e in active if e != SYNTHETIC_HUB_NAME]:
    _k_raw = df[df[ENTITY_COL] == _k].groupby(TIME_COL)[FEATURE_COLS].sum()
    _d = hub_raw.sub(_k_raw, fill_value=0.0).clip(lower=0.0).reset_index()
    _d[ENTITY_COL] = "__LOO__" + _k
    _frames.append(_d)
alpha_data.update(build_alpha_by_entity(
    pd.concat(_frames, ignore_index=True),
    ["__LOO__" + e for e in active if e != SYNTHETIC_HUB_NAME], W_STAR, LAM_STAR
))


def ngrc_states(alpha, k):
    """Expansion NG-RC: constante + lineal (delays) + cuadratico (productos unicos).
    alpha: (2, T) -> retorna (D_ngrc, T-k+1) y el offset temporal k-1."""
    T = alpha.shape[1]
    if T < k + 1:
        return None
    lin = np.array([alpha[:, t - k + 1: t + 1].flatten() for t in range(k - 1, T)])  # (T-k+1, 2k)
    n = lin.shape[1]
    quad_cols = [lin[:, i] * lin[:, j] for i in range(n) for j in range(i, n)]
    F = np.hstack([np.ones((lin.shape[0], 1)), lin, np.array(quad_cols).T])
    return F.T


def evaluate_embedding(z_builder, label):
    """z_builder(ent) -> (years, z) o None. Estima P* y evalua OOS."""
    z = {}
    for ent in active:
        out = z_builder(ent)
        if out is not None:
            yrs, zz = out
            z[ent] = {"years": yrs, "z": zz}
    ents = [e for e in active if e in z]
    if SYNTHETIC_HUB_NAME not in ents:
        print(f"  {label}: hub no disponible"); return None
    # Incrustación LOO del nodo central para la variante actual
    hub_loo = {}
    for ent in ents:
        if ent == SYNTHETIC_HUB_NAME:
            continue
        out_loo = z_builder("__LOO__" + ent) if ("__LOO__" + ent) in alpha_data else None
        if out_loo is not None:
            yrs_l, zz_l = out_loo
            hub_loo[ent] = {"years": yrs_l, "z": zz_l}
    hub_loo = hub_loo or None
    mask = build_topology_mask(ents, SYNTHETIC_HUB_NAME)
    P = estimate_coupling_matrix(ents, z, mask, SYNTHETIC_HUB_NAME,
                                 training_end_year=TEST_START_YEAR - 1, loo_strategy=True,
                                 hub_loo_z=hub_loo)
    frob, cov = evaluate_frobenius_oos(P, ents, z, mask, TEST_START_YEAR,
                                       hub_loo_z=hub_loo, hub_name=SYNTHETIC_HUB_NAME)
    met = evaluate_metrics_oos(P, ents, z, mask, TEST_START_YEAR,
                               hub_loo_z=hub_loo, hub_name=SYNTHETIC_HUB_NAME)
    print(f"  {label:<28}: MASE={met['MASE']:.4f}  NRMSE={met['NRMSE']:.4f}  Frob={frob:.4f}  n={met['Count']}  ents={len(ents)}")
    return dict(label=label, mase=met["MASE"], nrmse=met["NRMSE"], frob=frob, n=met["Count"], ents=len(ents))


results = []

# --- Referencia: reservoir aleatorio del paper (seed 7) ---
from src.models.reservoir import make_reservoir, run_reservoir
from config.settings import GLOBAL_SEED
from config.hyperparameters import RES_DIM, SPECTRAL_RADIUS, RES_DENSITY
w_in, w_res = make_reservoir(d_res=RES_DIM, rho=SPECTRAL_RADIUS, density=RES_DENSITY, seed=GLOBAL_SEED)

def builder_reservoir(ent):
    a = alpha_data[ent]["alpha"]
    a_std = StandardScaler().fit_transform(a.T).T
    h = run_reservoir(a_std, w_in, w_res)
    return alpha_data[ent]["years"], PCA(n_components=1).fit_transform(h.T).flatten()

print("\n==== Comparacion bajo protocolo identico (train<=2019, OOS 2020-2024) ====")
r = evaluate_embedding(builder_reservoir, "Reservoir aleatorio (seed 7)")
if r: results.append(r)

# --- NG-RC determinista, k=2 y k=3 ---
for k in (2, 3):
    def builder_ngrc(ent, k=k):
        a = alpha_data[ent]["alpha"]
        a_std = StandardScaler().fit_transform(a.T).T
        F = ngrc_states(a_std, k)
        if F is None or F.shape[1] < 3:
            return None
        Fs = StandardScaler().fit_transform(F.T)
        zz = PCA(n_components=1).fit_transform(Fs).flatten()
        return alpha_data[ent]["years"][k - 1:], zz
    r = evaluate_embedding(builder_ngrc, f"NG-RC determinista (k={k})")
    if r: results.append(r)

pd.DataFrame(results).to_csv(os.path.join(OUT, "ngrc_comparison.csv"), index=False)
print("\nReferencia del paper: reservoir 20 seeds -> MASE 1.014 +/- 0.079 (rango 0.918-1.165, CV 7.8%)")
print("NG-RC: sin aleatorizacion -> varianza por semilla = 0 por construccion.")
print(f"Guardado en {os.path.join(OUT, 'ngrc_comparison.csv')}")
