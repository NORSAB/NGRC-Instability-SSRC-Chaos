# Detalle por entidad: singularidad genuina (κ=∞) en el panel BCIE

Scripts: `codigo_pipeline/analisis_kappa_entidad.py` y `codigo_pipeline/analysis_common.py`,
sobre la implementación causal de `run_ngrc_regularizado.py` con logging por entidad. El
escalador, la covarianza y el lector se ajustan exclusivamente con años de entrenamiento; la
columna constante se agrega como intercepto literal solo en NNLS, sin pasar por
`StandardScaler`.

## Veredicto

Con escalado train-only e intercepto explícito, quedan **6** combinaciones
entidad(objetivo)×variante×k genuinamente singulares (κ=∞ por T≤D o rango deficiente en
entrenamiento), sobre 68 combinaciones evaluadas.

- Filas totales de kappa registradas (incluye entradas `__LOO__` como regresor del hub): **128**.
- Genuinamente singulares: **6** (todas entidades objetivo de pronóstico propio).
- Entidades con al menos una combinación singular: Colombia, Panamá, República Dominicana.

## Definición por variante

- **baseline**: `kappa_raw` sobre `Fs` sin la constante.
- **ledoitwolf / tikhonov_covariance**: `kappa_used` posterior a la regularización; si sigue
  infinito tras sumar shrinkage/λI, es la estructura T≤D del bloque NG-RC, no falta de
  shrinkage.
- **nnls_directo**: `kappa_used=inf` cuenta como singular cuando `n_train <= D_features`.

## Concentración de error OOS

- MASE promedio en combinaciones singulares (n=1): **1.455**.
- MASE promedio en combinaciones no singulares (n=56): **1.154** (mediana 0.784).
- RMSE promedio: 2.3393 (singulares) vs 2.4231 (no singulares).
- Las singulares concentran 1.26x más error.

## Resumen por variante × k

| variant             |   k |   n_entidades |   n_kappa_inf |   n_genuinamente_singular |
|:--------------------|----:|--------------:|--------------:|--------------------------:|
| baseline            |   2 |            17 |             0 |                         0 |
| baseline            |   3 |            15 |             1 |                         1 |
| ledoitwolf          |   2 |            17 |             0 |                         0 |
| ledoitwolf          |   3 |            15 |             0 |                         0 |
| nnls_directo        |   2 |            17 |             3 |                         3 |
| nnls_directo        |   3 |            15 |             2 |                         2 |
| tikhonov_covariance |   2 |            17 |             0 |                         0 |
| tikhonov_covariance |   3 |            15 |             0 |                         0 |

## Detalle de entidades objetivo genuinamente singulares

     variant  k          entity_base     kappa_raw  kappa_used                        motivo_singularidad  oos_MASE  oos_RMSE
    baseline  3             Colombia           inf         inf             singular_real_en_entrenamiento  1.455456  2.339329
nnls_directo  2             Colombia  4.039246e+17         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN
nnls_directo  2               Panamá  2.237096e+17         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN
nnls_directo  2 República Dominicana 3.931539e+180         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN
nnls_directo  3             Colombia           inf         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN
nnls_directo  3               Panamá  4.655203e+17         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN

## Limitaciones

- La definición de 'singular' (`kappa_used = inf`) es binaria; no se investigó un umbral
  intermedio (p. ej. κ>10^6, "casi singular").
- El cruce con OOS depende de que la entidad tenga cobertura en 2020-2025 bajo esa
  variante/k; varias combinaciones singulares carecen de ese dato porque la singularidad en
  entrenamiento ya las excluye de la evaluación OOS.

## Archivos

- `codigo_pipeline/analysis_common.py`: utilidades compartidas de la implementación causal.
- `codigo_pipeline/analisis_kappa_entidad.py`: este script.
- `codigo_pipeline/output/kappa_entidad_detalle.csv`: detalle completo entidad×variante×k.
