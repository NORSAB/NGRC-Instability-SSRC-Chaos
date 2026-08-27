"""
Experimento Articulo 4: ¿el mal condicionamiento del bloque cuadratico NG-RC explica
su fracaso (ver ../../../Articulo_2.../REGISTRO_EXPERIMENTOS/EXP_ngrc_FRACASO.md) y
una regularizacion de esa compresion lo corrige?
=============================================================================================
Copia AISLADA del motor de Articulo_2 (esta carpeta es independiente; el pipeline original
de Articulo_2 NO se toca). Compara, bajo protocolo causal (train<=2019, OOS 2020-2025,
datos<=2025, mascara hub-and-spoke, P* via NNLS por fila = ecuacion (3) del paper), CUATRO
formas de comprimir el estado NG-RC F_t (constante + lineal(delays) + cuadratico) a un
escalar z_t. La UNICA variable que cambia entre variantes es esa compresion; todo lo demas
(datos, mascara, estimador de acoplamiento, metricas OOS) es identico entre variantes y
identico al reservorio de referencia.

Variantes:
  A. baseline    - PCA(1) train-only sin regularizar, con orientacion de signo determinista.
  B. ledoitwolf   - PCA(1) pero sobre la covarianza con shrinkage de Ledoit-Wolf (encoge
                    hacia identidad y reduce kappa sin elegir un lambda a mano).
  C. tikhonov_covariance - componente principal de cov(F_train) + lambda_cov*I. Esta
                    regularizacion actua SOLO sobre la covarianza; no es Ridge de readout.
                    Igual que Ledoit-Wolf hacia identidad, no cambia la direccion principal
                    en aritmetica exacta. Las tres ramas usan la misma convencion de signo.
  D. nnls_directo - SIN PCA: ajusta z_t = w . F_t con pesos w >= 0 (NNLS, ajustado SOLO
                    en entrenamiento contra el canal TCRA crudo a[0]). Las features
                    estandarizadas contienen valores de ambos signos: la restriccion se
                    aplica a los PESOS y no garantiza que z_t ni el pronostico sean positivos.

Se registra ademas, por variante y por k, el numero de condicion kappa de la covarianza o
del diseno NNLS usado: la pieza diagnostica que conecta
empiricamente con el mecanismo de ill-conditioning descrito en arXiv:2505.00846.

Salida: output/ngrc_regularizado_comparison.csv, output/kappa_diagnostico.csv
"""
import os, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

from config.hyperparameters import TEST_START_YEAR, RES_DIM, SPECTRAL_RADIUS, RES_DENSITY
from config.settings import GLOBAL_SEED
from config.topology import TIME_COL, ENTITY_COL, FEATURE_COLS, SYNTHETIC_HUB_NAME, HIERARCHICAL_ORDER
from src.data.ckan_loader import CKANLoader
from src.data.preprocessor import clean_dataframe
from src.data.aggregator import aggregate_data
from src.features.tcroc import build_alpha_by_entity
from src.models.optimization import build_topology_mask, estimate_coupling_matrix
from src.models.metric_tools import evaluate_metrics_oos, evaluate_frobenius_oos
from src.models.reservoir import make_reservoir, run_reservoir
from temporal_transforms import (compress_ngrc_temporal, reservoir_embedding_temporal,
                                 temporal_standardize)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "output")
os.makedirs(OUT, exist_ok=True)

# Hiperparámetros óptimos
W_STAR, LAM_STAR = 3, 0.88

print("Cargando datos BCIE (misma fuente en vivo que Articulo_2; nada congelado)...")
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
    """Identico a run_ngrc_variant_REFERENCIA_original.py: constante + lineal(delays) +
    cuadratico (productos unicos). alpha: (2, T) -> (D_ngrc, T-k+1)."""
    T = alpha.shape[1]
    if T < k + 1:
        return None
    lin = np.array([alpha[:, t - k + 1: t + 1].flatten() for t in range(k - 1, T)])
    n = lin.shape[1]
    quad_cols = [lin[:, i] * lin[:, j] for i in range(n) for j in range(i, n)]
    F = np.hstack([np.ones((lin.shape[0], 1)), lin, np.array(quad_cols).T])
    return F.T  # (D, T-k+1)


kappa_log = []  # (variant, k, entity, kappa_raw, kappa_used)


def compress(F, k, ent, mode, target=None, fit_mask=None, diagnostic_log=None):
    """Compresion causal: scaler, covarianza, PCA y NNLS se ajustan solo en ``fit_mask``.

    ``tikhonov`` se conserva como alias de entrada por compatibilidad de los CSV historicos,
    pero el diagnostico nuevo lo denomina ``tikhonov_covariance`` para no confundirlo con
    Ridge de readout. En ``nnls_directo``, NNLS restringe los pesos; como las variables
    estandarizadas son signadas, no impone una salida positiva.
    """
    if fit_mask is None:
        raise ValueError("todas las variantes requieren fit_mask temporal")
    z, art = compress_ngrc_temporal(
        F, mode=mode, fit_mask=fit_mask, target=target, return_artifacts=True,
    )
    sink = kappa_log if diagnostic_log is None else diagnostic_log
    sink.append(dict(
        variant=art["mode"], k=k, entity=ent,
        kappa_raw=art["kappa_raw"], kappa_used=art["kappa_used"],
        n_train=art["n_train"], d_features=art["d_features"],
        motivo_singularidad=art["motivo_singularidad"],
        lambda_covariance=art.get("lambda_covariance", np.nan),
    ))
    return z


def evaluate_embedding(z_builder, label):
    """Identico a run_ngrc_variant_REFERENCIA_original.py: estima P* y evalua OOS."""
    z = {}
    for ent in active:
        out = z_builder(ent)
        if out is not None:
            yrs, zz = out
            z[ent] = {"years": yrs, "z": zz}
    ents = [e for e in active if e in z]
    if SYNTHETIC_HUB_NAME not in ents:
        print(f"  {label}: hub no disponible"); return None
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
    print(f"  {label:<32}: MASE={met['MASE']:.4f}  NRMSE={met['NRMSE']:.4f}  Frob={frob:.4f}  n={met['Count']}  ents={len(ents)}")
    return dict(label=label, mase=met["MASE"], nrmse=met["NRMSE"], frob=frob, n=met["Count"], ents=len(ents))


results = []

# --- Referencia: reservoir aleatorio del paper (seed 7), config oficial ---
w_in, w_res = make_reservoir(d_res=RES_DIM, rho=SPECTRAL_RADIUS, density=RES_DENSITY, seed=GLOBAL_SEED)

def builder_reservoir(ent):
    a = alpha_data[ent]["alpha"]
    yrs = alpha_data[ent]["years"]
    if (np.asarray(yrs) <= (TEST_START_YEAR - 1)).sum() < 2:
        return None
    z = reservoir_embedding_temporal(
        a, yrs, run_reservoir=run_reservoir, w_in=w_in, w_res=w_res,
        train_end_year=TEST_START_YEAR - 1,
    )
    return yrs, z

print(f"\n==== Config oficial W={W_STAR}, lambda={LAM_STAR}: protocolo causal (train<=2019, OOS 2020-2025) ====")
r = evaluate_embedding(builder_reservoir, "Reservoir aleatorio (seed 7, referencia)")
if r: results.append(r)

# --- NG-RC, 4 variantes de compresion x k in {2, 3} ---
for mode in ("baseline", "ledoitwolf", "tikhonov_covariance", "nnls_directo"):
    for k in (2, 3):
        def builder_ngrc(ent, k=k, mode=mode):
            a = alpha_data[ent]["alpha"]
            years_alpha = np.asarray(alpha_data[ent]["years"])
            alpha_fit_mask = years_alpha <= (TEST_START_YEAR - 1)
            if alpha_fit_mask.sum() < 2:
                return None
            a_std = temporal_standardize(a.T, alpha_fit_mask).T
            F = ngrc_states(a_std, k)
            if F is None or F.shape[1] < 3:
                return None
            yrs = alpha_data[ent]["years"][k - 1:]
            fit_mask = np.asarray(yrs) <= (TEST_START_YEAR - 1)
            if fit_mask.sum() < 2:
                return None
            target = a_std[0, k - 1:] if mode == "nnls_directo" else None
            zz = compress(F, k, ent, mode, target=target, fit_mask=fit_mask)
            return yrs, zz
        r = evaluate_embedding(builder_ngrc, f"NG-RC {mode} (k={k})")
        if r: results.append(r)

df_res = pd.DataFrame(results)
df_res.to_csv(os.path.join(OUT, "ngrc_regularizado_comparison.csv"), index=False)

df_kappa = pd.DataFrame(kappa_log)
kappa_summary = (df_kappa.groupby(["variant", "k"])
                 .agg(kappa_raw_median=("kappa_raw", "median"),
                      kappa_raw_max=("kappa_raw", "max"),
                      kappa_used_median=("kappa_used", "median"),
                      kappa_used_max=("kappa_used", "max"),
                      n_entities=("entity", "count"))
                 .reset_index())
kappa_summary.to_csv(os.path.join(OUT, "kappa_diagnostico.csv"), index=False)

print("\n==== Resumen ====")
print(df_res.to_string(index=False))
print("\n==== Diagnostico kappa (numero de condicion) ====")
print(kappa_summary.to_string(index=False))
print(f"\nGuardado en {OUT}")
