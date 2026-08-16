"""
Comparacion con cobertura pareja e inferencia robusta por anio.

El NNLS directo "gana" en MASE evaluando sobre 8-9 entidades en vez de 10-11 (descarta las de
historia corta). Este script re-corre las 9 variantes (reservoir + 8 combinaciones NG-RC)
restringidas TODAS a la INTERSECCION de entidades con datos validos en TODAS las variantes, y
compara cada variante NG-RC con el reservorio. No apila entidad×anio como si fueran
observaciones iid: agrega el diferencial de perdida por anio y calcula el p-valor mediante
aleatorizacion exacta por cambios de signo de bloques anuales consecutivos (L=2).

No se toca run_ngrc_regularizado.py: se reutilizan sus datos ya cargados (alpha_data, active,
funciones de bajo nivel) via analysis_common.load_base(), y se reevalua con
evaluate_embedding_detailed(..., entities_subset=...) restringido a la interseccion.

Salida: output/comparacion_cobertura_pareja.csv.
"""
import os
import numpy as np
import pandas as pd

from analysis_common import (load_base, make_builder_ngrc, make_builder_reservoir,
                              evaluate_embedding_detailed, dm_test_by_year,
                              paired_error_panel)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "output")
os.makedirs(OUT, exist_ok=True)

base = load_base()

VARIANTS = [("baseline", 2), ("baseline", 3), ("ledoitwolf", 2), ("ledoitwolf", 3),
            ("tikhonov_covariance", 2), ("tikhonov_covariance", 3),
            ("nnls_directo", 2), ("nnls_directo", 3)]

# ------------------------------------------------------------------------------------------
# 1. Corrida SIN restringir (misma cobertura que EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md,
#    para determinar la interseccion real de entidades entre las 9 variantes).
# ------------------------------------------------------------------------------------------
print("==== Paso 1: corrida sin restringir (para hallar la interseccion de cobertura) ====")
unrestricted = {}
builder_res = make_builder_reservoir(base)
r = evaluate_embedding_detailed(base, builder_res, "Reservoir aleatorio (seed 7, referencia)")
unrestricted["reservoir"] = r
print(f"  reservoir: {r['ents']} entidades -> {sorted(r['entities'])}")

for mode, k in VARIANTS:
    kap = []
    b = make_builder_ngrc(base, mode, k, kap)
    r = evaluate_embedding_detailed(base, b, f"NG-RC {mode} (k={k})")
    unrestricted[(mode, k)] = r
    print(f"  {mode} k={k}: {r['ents']} entidades -> {sorted(r['entities'])}")

all_entity_sets = [set(unrestricted["reservoir"]["entities"])] + \
    [set(unrestricted[(m, k)]["entities"]) for m, k in VARIANTS]
interseccion = sorted(set.intersection(*all_entity_sets))
print(f"\nInterseccion de cobertura entre las 9 variantes ({len(interseccion)} entidades): {interseccion}")

# Verificacion honesta: ¿coincide con la hipotesis del encargo ("probablemente las 8 que
# sobreviven en nnls_directo k=3, el caso mas restrictivo")?
nnls_k3_set = set(unrestricted[("nnls_directo", 3)]["entities"])
coincide_hipotesis = (set(interseccion) == nnls_k3_set)
print(f"¿Interseccion == entidades de nnls_directo k=3? {coincide_hipotesis}")
print(f"  nnls_directo k=3 ({len(nnls_k3_set)}): {sorted(nnls_k3_set)}")

# ------------------------------------------------------------------------------------------
# 2. Corrida RESTRINGIDA a la interseccion, para las 9 variantes.
# ------------------------------------------------------------------------------------------
print(f"\n==== Paso 2: re-evaluando las 9 variantes restringidas a las {len(interseccion)} "
      f"entidades comunes ====")
restricted = {}
builder_res2 = make_builder_reservoir(base)
r = evaluate_embedding_detailed(base, builder_res2, "Reservoir aleatorio (seed 7, referencia)",
                                 entities_subset=interseccion)
restricted["reservoir"] = r
print(f"  reservoir (restringido): MASE={r['mase']:.4f} NRMSE={r['nrmse']:.4f} Frob={r['frob']:.4f} "
      f"n={r['n']} ents={r['ents']}")

for mode, k in VARIANTS:
    kap = []
    b = make_builder_ngrc(base, mode, k, kap)
    r = evaluate_embedding_detailed(base, b, f"NG-RC {mode} (k={k})", entities_subset=interseccion)
    restricted[(mode, k)] = r
    if r is not None:
        print(f"  {mode} k={k} (restringido): MASE={r['mase']:.4f} NRMSE={r['nrmse']:.4f} "
              f"Frob={r['frob']:.4f} n={r['n']} ents={r['ents']}")
    else:
        print(f"  {mode} k={k} (restringido): SIN hub disponible / falla")

# ------------------------------------------------------------------------------------------
# 3. Diferencial de perdida por anio + aleatorizacion exacta por bloques (L=2). Las entidades
#    del mismo anio forman un cluster y NO incrementan artificialmente los grados de libertad.
# ------------------------------------------------------------------------------------------
print("\n==== Paso 3: Diebold-Mariano vs reservoir (restringido a cobertura pareja) ====")
ref_pe = restricted["reservoir"]["per_entity"]
rows = []

# Fila de referencia (reservoir) tambien va en la tabla, sin DM contra si misma.
rows.append(dict(label="Reservoir aleatorio (seed 7, referencia)", variant="reservoir", k=np.nan,
                  mase=restricted["reservoir"]["mase"], nrmse=restricted["reservoir"]["nrmse"],
                  frob=restricted["reservoir"]["frob"], n=restricted["reservoir"]["n"],
                  ents=restricted["reservoir"]["ents"],
                  dm_hac_abs=np.nan, dm_p_block_exact_abs=np.nan, dm_years_abs=np.nan,
                  dm_n_pairs_abs=np.nan, dm_sig_abs="",
                  dm_hac_sq=np.nan, dm_p_block_exact_sq=np.nan, dm_years_sq=np.nan,
                  dm_n_pairs_sq=np.nan, dm_sig_sq=""))

for mode, k in VARIANTS:
    r = restricted[(mode, k)]
    if r is None:
        rows.append(dict(label=f"NG-RC {mode} (k={k})", variant=mode, k=k,
                          mase=np.nan, nrmse=np.nan, frob=np.nan, n=np.nan, ents=np.nan,
                          dm_hac_abs=np.nan, dm_p_block_exact_abs=np.nan, dm_years_abs=np.nan,
                          dm_n_pairs_abs=np.nan, dm_sig_abs="sin datos",
                          dm_hac_sq=np.nan, dm_p_block_exact_sq=np.nan, dm_years_sq=np.nan,
                          dm_n_pairs_sq=np.nan, dm_sig_sq="sin datos"))
        continue
    panel = paired_error_panel(r["per_entity"], ref_pe, interseccion)
    n_pairs = len(panel)
    if panel["year"].nunique() >= 3:
        dm_a, p_a, n_years_a, n_pairs_a = dm_test_by_year(panel, loss="absolute")
        dm_s, p_s, n_years_s, n_pairs_s = dm_test_by_year(panel, loss="squared")
        sig_a = "SI (NG-RC mejor)" if (p_a is not None and p_a < 0.05 and dm_a < 0) else \
                ("SI (reservoir mejor)" if (p_a is not None and p_a < 0.05 and dm_a > 0) else "no")
        sig_s = "SI (NG-RC mejor)" if (p_s is not None and p_s < 0.05 and dm_s < 0) else \
                ("SI (reservoir mejor)" if (p_s is not None and p_s < 0.05 and dm_s > 0) else "no")
    else:
        dm_a = p_a = n_years_a = n_pairs_a = np.nan
        dm_s = p_s = n_years_s = n_pairs_s = np.nan
        sig_a = sig_s = f"insuficiente (anios={panel['year'].nunique()})"
    if isinstance(dm_a, float) and not np.isnan(dm_a):
        print(f"  {mode} k={k}: anios={n_years_a} n_pares={n_pairs}  "
              f"DM-HAC(abs)={dm_a:.3f}  p_bloques_exacto={p_a:.4f}  -> {sig_a}")
    else:
        print(f"  {mode} k={k}: n_pares={n_pairs} (insuficiente para DM) -> {sig_a}")
    rows.append(dict(label=f"NG-RC {mode} (k={k})", variant=mode, k=k,
                      mase=r["mase"], nrmse=r["nrmse"], frob=r["frob"], n=r["n"], ents=r["ents"],
                      dm_hac_abs=dm_a, dm_p_block_exact_abs=p_a, dm_years_abs=n_years_a,
                      dm_n_pairs_abs=n_pairs_a, dm_sig_abs=sig_a,
                      dm_hac_sq=dm_s, dm_p_block_exact_sq=p_s, dm_years_sq=n_years_s,
                      dm_n_pairs_sq=n_pairs_s, dm_sig_sq=sig_s))

df_out = pd.DataFrame(rows)
df_out.to_csv(os.path.join(OUT, "comparacion_cobertura_pareja.csv"), index=False)
print(f"\nGuardado: {os.path.join(OUT, 'comparacion_cobertura_pareja.csv')}")
print(df_out.to_string(index=False))

# ------------------------------------------------------------------------------------------
# 4. También guardamos la comparación de cobertura ANTES/DESPUÉS (para el .md) — cuántas
#    entidades pierde cada variante al pasar de cobertura propia a cobertura pareja.
# ------------------------------------------------------------------------------------------
cobertura_rows = []
cobertura_rows.append(dict(variant="reservoir", k=np.nan,
                            ents_propia=unrestricted["reservoir"]["ents"],
                            ents_pareja=restricted["reservoir"]["ents"],
                            mase_propia=unrestricted["reservoir"]["mase"],
                            mase_pareja=restricted["reservoir"]["mase"]))
for mode, k in VARIANTS:
    u = unrestricted[(mode, k)]
    rr = restricted[(mode, k)]
    cobertura_rows.append(dict(variant=mode, k=k,
                                ents_propia=u["ents"] if u else np.nan,
                                ents_pareja=rr["ents"] if rr else np.nan,
                                mase_propia=u["mase"] if u else np.nan,
                                mase_pareja=rr["mase"] if rr else np.nan))
df_cobertura = pd.DataFrame(cobertura_rows)
print("\n==== Cobertura propia vs pareja, y su efecto en MASE ====")
print(df_cobertura.to_string(index=False))

print("\nEl hallazgo metodologico se mantiene en "
      "../EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md; este script solo actualiza el CSV.")
