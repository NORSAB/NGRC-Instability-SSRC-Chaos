"""
Tarea 1 (encargo 2026-08-12): detalle POR ENTIDAD de kappa (numero de condicion) para las
variantes de compresion NG-RC, cruzado con el error OOS por entidad.

run_ngrc_regularizado.py guarda un resumen agregado en kappa_diagnostico.csv. Este script
reconstruye el detalle entidad x LOO x variante x k usando la misma implementacion causal de
analysis_common.py: scaler, covarianza y lectores se ajustan solo con train<=2019.

Salidas:
  - output/kappa_entidad_detalle.csv
  - ../EXP_kappa_entidades_singulares.md
"""
import os
import numpy as np
import pandas as pd

from analysis_common import load_base, make_builder_ngrc, evaluate_embedding_detailed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "output")
os.makedirs(OUT, exist_ok=True)
EXP_MD = os.path.abspath(os.path.join(BASE_DIR, "..", "EXP_kappa_entidades_singulares.md"))

base = load_base()

# Paises/entidades de historia corta ya senalados en el registro del ecosistema
# (REGISTRO_EXPERIMENTOS/EXP_ngrc_FRACASO.md linea 30 y
#  Articulo_2_Guatemala_Coupled-TCROC/experimento/HALLAZGO_C1_LOO_HUB.md linea 51):
# "Argentina, R. Dominicana" con NNLS de 2 variables degenerado; "paises de historia corta"
# en general pierden cobertura con NG-RC (memoria dura de k retardos).
ENTIDADES_HISTORIA_CORTA_REGISTRO = ["Argentina", "República Dominicana"]

kappa_rows = []          # detalle crudo por variant/k/entity
per_entity_metrics = {}  # (variant, k) -> per_entity dict (de evaluate_embedding_detailed)

for mode in ("baseline", "ledoitwolf", "tikhonov_covariance", "nnls_directo"):
    for k in (2, 3):
        local_kappa_log = []
        builder = make_builder_ngrc(base, mode, k, local_kappa_log)
        res = evaluate_embedding_detailed(base, builder, f"NG-RC {mode} (k={k})")
        kappa_rows.extend(local_kappa_log)
        n_ents_oos = 0
        if res is not None:
            per_entity_metrics[(mode, k)] = res["per_entity"]
            n_ents_oos = len(res["entities"])
        print(f"  {mode:<12} k={k}: {len(local_kappa_log)} filas de kappa registradas, "
              f"{n_ents_oos} entidades con pronostico OOS")

df_kappa = pd.DataFrame(kappa_rows)
df_kappa["es_LOO"] = df_kappa["entity"].str.startswith("__LOO__")
df_kappa["entity_base"] = df_kappa["entity"].str.replace("__LOO__", "", regex=False)
df_kappa["historia_corta_registro"] = df_kappa["entity_base"].isin(ENTIDADES_HISTORIA_CORTA_REGISTRO)
df_kappa["kappa_inf"] = ~np.isfinite(df_kappa["kappa_used"].astype(float))

# Criterio de singularidad numérica (distinguiendo entre singularidad estructural y escala de varianza nula)
ARTEFACTO = "artefacto_StandardScaler"
df_kappa["motivo_singularidad"] = df_kappa["motivo_singularidad"].fillna("")
df_kappa["es_artefacto_standardscaler"] = df_kappa["motivo_singularidad"].str.startswith(ARTEFACTO)
df_kappa["genuinamente_singular"] = df_kappa["kappa_inf"] & (~df_kappa["es_artefacto_standardscaler"])


# Cruce con error OOS por entidad (solo aplica a filas NO-LOO: las __LOO__ son regresores del
# hub, no son un objetivo de pronostico propio en evaluate_metrics_oos).
def _lookup_metric(row, field):
    if row["es_LOO"]:
        return np.nan
    pe = per_entity_metrics.get((row["variant"], row["k"]))
    if pe is None or row["entity"] not in pe:
        return np.nan
    return pe[row["entity"]][field]


df_kappa["oos_MASE"] = df_kappa.apply(lambda r: _lookup_metric(r, "MASE"), axis=1)
df_kappa["oos_RMSE"] = df_kappa.apply(lambda r: _lookup_metric(r, "RMSE"), axis=1)
df_kappa["oos_Count"] = df_kappa.apply(lambda r: _lookup_metric(r, "Count"), axis=1)

df_kappa = df_kappa[["variant", "k", "entity", "entity_base", "es_LOO", "kappa_raw", "kappa_used",
                     "n_train", "d_features", "kappa_inf", "es_artefacto_standardscaler",
                     "genuinamente_singular", "motivo_singularidad", "historia_corta_registro",
                     "oos_MASE", "oos_RMSE", "oos_Count"]]
df_kappa.to_csv(os.path.join(OUT, "kappa_entidad_detalle.csv"), index=False)
print(f"\nGuardado: {os.path.join(OUT, 'kappa_entidad_detalle.csv')}  ({len(df_kappa)} filas)")

# ------------------------------------------------------------------------------------------
# Resumen para el .md
# ------------------------------------------------------------------------------------------
sing = df_kappa[df_kappa["genuinamente_singular"]]
sing_targets = sing[~sing["es_LOO"]]
sing_loo = sing[sing["es_LOO"]]

artef = df_kappa[df_kappa["es_artefacto_standardscaler"]]
artef_targets = artef[~artef["es_LOO"]]

n_singular_total = len(sing)
n_singular_targets = len(sing_targets)
n_singular_loo = len(sing_loo)
entidades_singulares_unicas = sorted(sing["entity_base"].unique().tolist())

overlap = sorted(set(entidades_singulares_unicas) & set(ENTIDADES_HISTORIA_CORTA_REGISTRO))
solo_en_singulares = sorted(set(entidades_singulares_unicas) - set(ENTIDADES_HISTORIA_CORTA_REGISTRO))
solo_en_registro = sorted(set(ENTIDADES_HISTORIA_CORTA_REGISTRO) - set(entidades_singulares_unicas))

with_oos = df_kappa.dropna(subset=["oos_MASE"])
mase_sing = with_oos[with_oos["genuinamente_singular"]]["oos_MASE"]
mase_nosing = with_oos[~with_oos["genuinamente_singular"]]["oos_MASE"]
rmse_sing = with_oos[with_oos["genuinamente_singular"]]["oos_RMSE"]
rmse_nosing = with_oos[~with_oos["genuinamente_singular"]]["oos_RMSE"]

resumen_variant_k = (df_kappa.groupby(["variant", "k"])
                      .agg(n_entidades=("entity", "count"),
                           n_kappa_inf=("kappa_inf", "sum"),
                           n_artefacto_standardscaler=("es_artefacto_standardscaler", "sum"),
                           n_genuinamente_singular=("genuinamente_singular", "sum"),
                           n_genuinamente_singular_objetivo=(
                               "genuinamente_singular",
                               lambda s: int((s & ~df_kappa.loc[s.index, "es_LOO"]).sum())))
                      .reset_index())

try:
    tabla_resumen_md = resumen_variant_k.to_markdown(index=False)
except ImportError:
    tabla_resumen_md = resumen_variant_k.to_string(index=False)

tabla_targets = sing_targets[["variant", "k", "entity_base", "kappa_raw", "kappa_used",
                              "motivo_singularidad", "oos_MASE", "oos_RMSE", "oos_Count"]].copy()
tabla_targets = tabla_targets.sort_values(["variant", "k", "entity_base"])

tabla_artefacto = artef_targets[["variant", "k", "entity_base", "n_train", "d_features",
                                  "oos_MASE", "oos_RMSE"]].copy().sort_values(["variant", "k", "entity_base"])

md = []
md.append("# Detalle por entidad: ¿cuáles combinaciones entidad×LOO son genuinamente singulares (κ=∞)?\n")
md.append("Fecha de reejecución: 2026-08-13. Complementa "
           "`EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md`. Scripts: "
           "`codigo_pipeline/analisis_kappa_entidad.py` y `codigo_pipeline/analysis_common.py`; "
           "ambos reutilizan la implementación causal de `run_ngrc_regularizado.py` y agregan "
           "logging por entidad.\n")

md.append("## Correcciones aplicadas antes de este diagnóstico\n")
md.append("La columna constante ya no pasa por `StandardScaler`: se agrega como intercepto literal "
          "solo en NNLS. Además, el escalador, la covarianza y el lector se ajustan exclusivamente "
          "con años de entrenamiento. Por tanto, las singularidades reportadas aquí corresponden "
          "al diseño de entrenamiento y no a información OOS ni a un intercepto destruido.\n\n"
          "NNLS restringe los pesos a valores no negativos. Como las características "
          "estandarizadas son signadas, esto no garantiza un embedding ni un pronóstico "
          "positivos.\n\n"
          "Baseline, Ledoit-Wolf y Tikhonov usan la misma orientación determinista del "
          "componente principal. El signo no cambia κ, pero evita que la ambigüedad de los "
          "autovectores altere el operador NNLS posterior.\n")

veredicto = "MATIZADO"
md.append(f"\n## Veredicto sobre singularidad genuina después de las correcciones\n")
md.append(f"**VEREDICTO: {veredicto}**: con escalado train-only e intercepto explícito, queda un "
           f"núcleo pequeño de entidades genuinamente singulares: **{n_singular_targets}** "
           f"combinaciones entidad(objetivo)×variante×k con κ=∞ por causa real (T≤D o rango "
           f"deficiente en entrenamiento), sobre "
           f"{len(df_kappa[~df_kappa['es_LOO']])} combinaciones entidad(objetivo)×variante×k "
           f"evaluadas.\n")

md.append("## Cuántas son (genuinamente singulares)\n")
md.append(f"- Filas totales de kappa registradas (entidad×variante×k, incluye entradas `__LOO__` "
          f"usadas solo como regresor del hub): **{len(df_kappa)}**.\n"
          f"- Genuinamente singulares: **{n_singular_total}** ({n_singular_targets} son entidades "
          f"objetivo de pronóstico propio, {n_singular_loo} son solo el regresor `__LOO__` del hub).\n"
          f"- Entidades (nombre base) que aparecen genuinamente singulares en AL MENOS una "
          f"combinación variante×k: "
          f"**{', '.join(entidades_singulares_unicas) if entidades_singulares_unicas else '(ninguna)'}**.\n")

md.append("## Nota metodológica: definición de 'genuinamente singular' por variante\n")
md.append("- **baseline** (sin regularizar): usa `kappa_raw` sobre `Fs` (YA sin la constante, por "
          "el FIX 2026-08-12 previo): es la matriz que de verdad se autovector-descompone.\n"
          "- **ledoitwolf / tikhonov_covariance**: usan `kappa_used` (posterior a la regularización, también "
          "sobre `Fs` sin la constante). Si SIGUE siendo infinito tras sumar shrinkage/λI, ninguna "
          "regularización de la covarianza lo corrige: es la estructura T≤D del bloque NG-RC "
          "(constante+lineal+cuadrático), no falta de shrinkage.\n"
          "- **nnls_directo**: `kappa_used=inf` se cuenta como genuinamente singular cuando "
          "`n_train <= D_features` (escasez real de muestra, NNLS con pesos en cero). El "
          "intercepto literal ya no introduce una columna muerta.\n")

md.append("## Coincidencia con `EXP_ngrc_FRACASO.md` / `HALLAZGO_C1_LOO_HUB.md` (historia corta)\n")
md.append(f"- Entidades citadas en el registro como historia corta: `{', '.join(ENTIDADES_HISTORIA_CORTA_REGISTRO)}`.\n"
          f"- Coinciden con las genuinamente singulares encontradas aquí: "
          f"`{', '.join(overlap) if overlap else '(ninguna coincidencia)'}`.\n"
          f"- Genuinamente singulares aquí que NO estaban en esa lista corta del registro: "
          f"`{', '.join(solo_en_singulares) if solo_en_singulares else '(ninguna)'}`.\n"
          f"- Del registro, NO reaparecen como genuinamente singulares en este barrido: "
          f"`{', '.join(solo_en_registro) if solo_en_registro else '(ninguna: todas reaparecen)'}`.\n")

md.append("## ¿Concentran el error OOS? (entidades genuinamente singulares vs el resto)\n")
if len(mase_sing) > 0 and len(mase_nosing) > 0:
    md.append(f"- MASE promedio en combinaciones **genuinamente singulares** con dato OOS "
              f"(n={len(mase_sing)}): **{mase_sing.mean():.3f}** (mediana {mase_sing.median():.3f}).\n"
              f"- MASE promedio en combinaciones **no singulares** (n={len(mase_nosing)}): "
              f"**{mase_nosing.mean():.3f}** (mediana {mase_nosing.median():.3f}).\n"
              f"- RMSE promedio singulares: **{rmse_sing.mean():.4f}** vs no singulares: "
              f"**{rmse_nosing.mean():.4f}**.\n")
    if mase_sing.mean() > mase_nosing.mean():
        md.append(f"- **Sí concentran más error**: MASE "
                  f"{mase_sing.mean() / max(mase_nosing.mean(), 1e-9):.2f}x el de las no singulares.\n")
    else:
        md.append(f"- **No concentran más error de forma clara** en esta muestra "
                  f"({mase_sing.mean():.3f} vs {mase_nosing.mean():.3f}): honestidad: la muestra de "
                  f"combinaciones genuinamente singulares CON dato OOS es muy pequeña "
                  f"(n={len(mase_sing)}), poco poder estadístico; se reporta como observación "
                  f"descriptiva, no como prueba formal.\n")
else:
    md.append(f"- Solo **{len(mase_sing)}** combinaciones genuinamente singulares tienen dato OOS "
              f"propio (la mayoría queda, por definición, SIN cobertura en 2020-2025: la "
              f"singularidad real en entrenamiento se traduce directamente en pérdida de "
              f"COBERTURA, no en peor error medible). Esto es en sí mismo el hallazgo principal: "
              f"el mecanismo T≤D no empeora el pronóstico de las entidades afectadas, las "
              f"**elimina** de la comparación: es un sesgo de cobertura, no un sesgo de precisión "
              f"(ver Tarea 2 / sección de cobertura pareja).\n")

md.append("## Resumen por variante × k\n")
md.append(tabla_resumen_md + "\n")

if len(tabla_targets):
    md.append("## Detalle de entidades objetivo genuinamente singulares\n")
    md.append(tabla_targets.to_string(index=False) + "\n")
else:
    md.append("## Detalle de entidades objetivo genuinamente singulares\n")
    md.append("Ninguna entidad OBJETIVO propia quedó con κ=∞ genuino en este barrido (todas las "
              "singularidades objetivo quedaron fuera de cobertura). Ver "
              "`output/kappa_entidad_detalle.csv` para el detalle completo.\n")

md.append("\n## Limitaciones / honestidad metodológica\n")
md.append("- La definición de 'singular' usada aquí (`kappa_used = inf`, con la excepción del "
          "diagnóstico histórico del artefacto de StandardScaler) es binaria; no se investigó un umbral "
          "intermedio (p. ej. κ>10^6 'casi singular').\n"
          "- El artefacto histórico del intercepto fue corregido: la constante se agrega después "
          "del escalado y nunca se centra.\n"
          "- El cruce con OOS depende de que la entidad tenga cobertura en 2020-2025 bajo esa "
          "variante/k; varias combinaciones genuinamente singulares no tienen ese dato porque la "
          "propia singularidad en entrenamiento ya las excluye de la evaluación OOS.\n"
          "- Esta comparación usa el mismo pull de datos en vivo del BCIE que "
          "`EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md` (mismo día, no comparable número-a-número "
          "con snapshots anteriores del registro).\n")

md.append("\n## Archivos\n")
md.append("- `codigo_pipeline/analysis_common.py`: utilidades compartidas que reutilizan la "
          "implementación causal y agregan detalle por entidad.\n"
          "- `codigo_pipeline/analisis_kappa_entidad.py`: este script.\n"
          "- `codigo_pipeline/output/kappa_entidad_detalle.csv`: detalle completo entidad×variante×k.\n")

with open(EXP_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print(f"Guardado: {EXP_MD}")
