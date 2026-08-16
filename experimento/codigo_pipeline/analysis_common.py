"""
Utilidades compartidas para los analisis de detalle de Articulo_4 (Tarea 1 y Tarea 2 del
encargo 2026-08-12). Este modulo reutiliza la implementacion causal de
run_ngrc_regularizado.py, con logging adicional por entidad, para poder:
  (a) capturar kappa por ENTIDAD (no solo el resumen agregado que guarda el script original), y
  (b) reevaluar con un subconjunto RESTRINGIDO de entidades (interseccion de cobertura) sin
      tocar run_ngrc_regularizado.py ni volver a descargar los datos dos veces.

run_ngrc_regularizado.py se importa UNA vez (ver load_base()) solo para reusar sus datos ya
cargados (alpha_data, active, config) y sus funciones de bajo nivel (ngrc_states, build_topology_mask,
estimate_coupling_matrix, evaluate_metrics_oos, evaluate_frobenius_oos, make_reservoir, run_reservoir).
Ese import YA ejecuta el pipeline completo original (escribe sus dos CSV de siempre sin cambios);
aqui no se le pide nada mas que sus datos/funciones.
"""
import os
import sys
import importlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_BASE_MODULE = None


def load_base():
    """Importa (o reutiliza si ya esta en sys.modules, dentro del MISMO proceso) el script
    original run_ngrc_regularizado.py. La primera vez ejecuta el pipeline completo (fetch BCIE
    en vivo + las 9 variantes) y escribe sus dos CSV oficiales sin ninguna alteracion."""
    global _BASE_MODULE
    if _BASE_MODULE is not None:
        return _BASE_MODULE
    if "run_ngrc_regularizado" in sys.modules:
        _BASE_MODULE = sys.modules["run_ngrc_regularizado"]
    else:
        _BASE_MODULE = importlib.import_module("run_ngrc_regularizado")
    return _BASE_MODULE


# ---------------------------------------------------------------------------------------------
# Envoltura de compress(), con un kappa_log propio (no toca ni comparte el global) para que
# cada corrida de este modulo
# quede auto-contenida y trazable.
# ---------------------------------------------------------------------------------------------
def compress_logged(F, k, ent, mode, kappa_log_list, target=None, fit_mask=None):
    """Llama a la implementacion causal oficial y guarda su diagnostico por entidad."""
    base = load_base()
    return base.compress(
        F, k, ent, mode, target=target, fit_mask=fit_mask,
        diagnostic_log=kappa_log_list,
    )


def make_builder_ngrc(base, mode, k, kappa_log_list):
    """Replica el builder_ngrc de run_ngrc_regularizado.py (L205-221), parametrizado."""
    def builder(ent):
        a = base.alpha_data[ent]["alpha"]
        years_alpha = np.asarray(base.alpha_data[ent]["years"])
        alpha_fit_mask = years_alpha <= (base.TEST_START_YEAR - 1)
        if alpha_fit_mask.sum() < 2:
            return None
        a_std = base.temporal_standardize(a.T, alpha_fit_mask).T
        F = base.ngrc_states(a_std, k)
        if F is None or F.shape[1] < 3:
            return None
        yrs = base.alpha_data[ent]["years"][k - 1:]
        fit_mask = np.asarray(yrs) <= (base.TEST_START_YEAR - 1)
        if fit_mask.sum() < 2:
            return None
        target = a_std[0, k - 1:] if mode == "nnls_directo" else None
        zz = compress_logged(F, k, ent, mode, kappa_log_list,
                             target=target, fit_mask=fit_mask)
        return yrs, zz
    return builder


def make_builder_reservoir(base):
    w_in, w_res = base.make_reservoir(d_res=base.RES_DIM, rho=base.SPECTRAL_RADIUS,
                                       density=base.RES_DENSITY, seed=base.GLOBAL_SEED)

    def builder(ent):
        a = base.alpha_data[ent]["alpha"]
        yrs = base.alpha_data[ent]["years"]
        if (np.asarray(yrs) <= (base.TEST_START_YEAR - 1)).sum() < 2:
            return None
        z = base.reservoir_embedding_temporal(
            a, yrs, run_reservoir=base.run_reservoir, w_in=w_in, w_res=w_res,
            train_end_year=base.TEST_START_YEAR - 1,
        )
        return yrs, z
    return builder


def evaluate_embedding_detailed(base, z_builder, label, entities_subset=None):
    """Replica evaluate_embedding() (run_ngrc_regularizado.py L155-184) pero:
      (a) opcionalmente restringe la poblacion de entidades a `entities_subset`
          (para la Tarea 2, cobertura pareja), y
      (b) retorna tambien el dict 'per_entity' completo (MASE/RMSE/years/y_true/y_pred) y la
          lista real de entidades usadas (para la Tarea 1 y para las pruebas DM de la Tarea 2).
    """
    active_pool = base.active if entities_subset is None else \
        [e for e in base.active if e in entities_subset]

    z = {}
    for ent in active_pool:
        out = z_builder(ent)
        if out is not None:
            yrs, zz = out
            z[ent] = {"years": yrs, "z": zz}
    ents = [e for e in active_pool if e in z]
    if base.SYNTHETIC_HUB_NAME not in ents:
        return None
    hub_loo = {}
    for ent in ents:
        if ent == base.SYNTHETIC_HUB_NAME:
            continue
        loo_key = "__LOO__" + ent
        out_loo = z_builder(loo_key) if loo_key in base.alpha_data else None
        if out_loo is not None:
            yrs_l, zz_l = out_loo
            hub_loo[ent] = {"years": yrs_l, "z": zz_l}
    hub_loo = hub_loo or None
    mask = base.build_topology_mask(ents, base.SYNTHETIC_HUB_NAME)
    P = base.estimate_coupling_matrix(ents, z, mask, base.SYNTHETIC_HUB_NAME,
                                       training_end_year=base.TEST_START_YEAR - 1, loo_strategy=True,
                                       hub_loo_z=hub_loo)
    frob, cov = base.evaluate_frobenius_oos(P, ents, z, mask, base.TEST_START_YEAR, hub_loo_z=hub_loo,
                                             hub_name=base.SYNTHETIC_HUB_NAME)
    met = base.evaluate_metrics_oos(P, ents, z, mask, base.TEST_START_YEAR, hub_loo_z=hub_loo,
                                     hub_name=base.SYNTHETIC_HUB_NAME)
    return dict(label=label, mase=met["MASE"], nrmse=met["NRMSE"], frob=frob, n=met["Count"],
                ents=len(ents), entities=ents, per_entity=met["per_entity"], P=P)


# ---------------------------------------------------------------------------------------------
# Inferencia de perdida emparejada robusta a la estructura entidad x anio.
# ---------------------------------------------------------------------------------------------
def dm_test_by_year(panel, loss="squared", block_length=2):
    """Compara perdidas tras agregar por anio y usa aleatorizacion exacta por bloques.

    Las entidades de un mismo anio pueden compartir shocks y regresores, por lo que no se
    cuentan como observaciones iid. Primero se promedia el diferencial dentro de cada anio;
    despues se agrupan anios consecutivos en bloques. El estadistico es un cociente tipo DM
    con varianza HAC (Bartlett, rezago 1), y el p-valor principal enumera exactamente todos
    los cambios de signo posibles de esos bloques. Con seis anios y bloques de longitud dos,
    solo hay tres unidades independientes y el p-valor minimo es 0.25; esta discrecion evita
    fabricar precision a partir de decenas de filas que comparten los mismos anios.
    """
    if not isinstance(panel, pd.DataFrame) or panel.empty:
        return np.nan, np.nan, 0, 0
    if loss == "squared":
        differential = panel["error_a"].to_numpy() ** 2 - panel["error_b"].to_numpy() ** 2
    elif loss == "absolute":
        differential = np.abs(panel["error_a"].to_numpy()) - np.abs(panel["error_b"].to_numpy())
    else:
        raise ValueError("loss debe ser 'absolute' o 'squared'")
    work = panel[["year"]].copy()
    work["d"] = differential
    d_year = work.groupby("year", sort=True)["d"].mean().to_numpy(dtype=float)
    n_years = len(d_year)
    n_pairs = len(work)
    if n_years < 3:
        return np.nan, np.nan, n_years, n_pairs

    dbar = float(d_year.mean())
    centered = d_year - dbar
    gamma0 = float(np.dot(centered, centered) / n_years)
    gamma1 = float(np.dot(centered[1:], centered[:-1]) / n_years)
    long_run_variance = max(gamma0 + gamma1, np.finfo(float).eps)  # Bartlett L=1: 2*0.5*gamma1
    dm_hac = dbar / np.sqrt(long_run_variance / n_years)

    block_length = max(1, min(int(block_length), n_years))
    blocks = [d_year[start:start + block_length] for start in range(0, n_years, block_length)]
    if len(blocks) > 16:
        raise ValueError("demasiados bloques para enumeracion exacta")
    permuted_means = []
    for code in range(1 << len(blocks)):
        signed = [block * (1.0 if code & (1 << i) else -1.0)
                  for i, block in enumerate(blocks)]
        permuted_means.append(np.concatenate(signed).mean())
    permuted_means = np.asarray(permuted_means)
    p_exact = np.mean(np.abs(permuted_means) >= abs(dbar) - 1e-15)
    return float(dm_hac), float(p_exact), n_years, n_pairs


def paired_error_panel(per_entity_a, per_entity_b, entities):
    """Panel emparejado de errores dimensionless en la escala MASE de cada embedding.

    Las variantes producen objetivos latentes con escalas distintas. Comparar errores crudos
    entre esos espacios no es valido. Se recupera el denominador naive de MASE de cada corrida
    (MAE/MASE, comun a sus entidades) y se normaliza cada error antes de comparar perdidas.
    """
    def mase_scale(per_entity):
        values = []
        for data in per_entity.values():
            mase, mae = float(data.get("MASE", np.nan)), float(data.get("MAE", np.nan))
            if np.isfinite(mase) and mase > 0 and np.isfinite(mae):
                values.append(mae / mase)
        if not values:
            raise ValueError("no se pudo recuperar el denominador MASE")
        return float(np.median(values))

    scale_a, scale_b = mase_scale(per_entity_a), mase_scale(per_entity_b)
    rows = []
    for ent in entities:
        da, db = per_entity_a.get(ent), per_entity_b.get(ent)
        if da is None or db is None:
            continue
        map_a = dict(zip(da["years"], np.asarray(da["y_true"]) - np.asarray(da["y_pred"])))
        map_b = dict(zip(db["years"], np.asarray(db["y_true"]) - np.asarray(db["y_pred"])))
        for year in sorted(set(map_a) & set(map_b)):
            rows.append(dict(entity=ent, year=int(year),
                             error_a=map_a[year] / scale_a,
                             error_b=map_b[year] / scale_b))
    return pd.DataFrame(rows, columns=["entity", "year", "error_a", "error_b"])
