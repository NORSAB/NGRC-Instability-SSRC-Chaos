# Detalle por entidad: ¿cuáles combinaciones entidad×LOO son genuinamente singulares (κ=∞)?

Fecha de reejecución: 2026-08-13. Complementa `EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md`. Scripts: `codigo_pipeline/analisis_kappa_entidad.py` y `codigo_pipeline/analysis_common.py`; ambos reutilizan la implementación causal de `run_ngrc_regularizado.py` y agregan logging por entidad.

## Correcciones aplicadas antes de este diagnóstico

La columna constante ya no pasa por `StandardScaler`: se agrega como intercepto literal solo en NNLS. Además, el escalador, la covarianza y el lector se ajustan exclusivamente con años de entrenamiento. Por tanto, las singularidades reportadas aquí corresponden al diseño de entrenamiento y no a información OOS ni a un intercepto destruido.

NNLS restringe los pesos a valores no negativos. Como las características estandarizadas son signadas, esto no garantiza un embedding ni un pronóstico positivos.

Baseline, Ledoit-Wolf y Tikhonov usan la misma orientación determinista del componente
principal. El signo no cambia κ, pero evita que la ambigüedad de los autovectores altere el
operador NNLS posterior.


## Veredicto sobre singularidad genuina después de las correcciones

**VEREDICTO: MATIZADO** — con escalado train-only e intercepto explícito, queda un núcleo pequeño de entidades genuinamente singulares: **6** combinaciones entidad(objetivo)×variante×k con κ=∞ por causa real (T≤D o rango deficiente en entrenamiento), sobre 68 combinaciones entidad(objetivo)×variante×k evaluadas.

## Cuántas son (genuinamente singulares)

- Filas totales de kappa registradas (entidad×variante×k, incluye entradas `__LOO__` usadas solo como regresor del hub): **128**.
- Genuinamente singulares: **6** (6 son entidades objetivo de pronóstico propio, 0 son solo el regresor `__LOO__` del hub).
- Entidades (nombre base) que aparecen genuinamente singulares en AL MENOS una combinación variante×k: **Colombia, Panamá, República Dominicana**.

## Nota metodológica: definición de 'genuinamente singular' por variante

- **baseline** (sin regularizar): usa `kappa_raw` sobre `Fs` (YA sin la constante, por el FIX 2026-08-12 previo) — es la matriz que de verdad se autovector-descompone.
- **ledoitwolf / tikhonov_covariance**: usan `kappa_used` (posterior a la regularización, también sobre `Fs` sin la constante). Si SIGUE siendo infinito tras sumar shrinkage/λI, ninguna regularización de la covarianza lo corrige — es la estructura T≤D del bloque NG-RC (constante+lineal+cuadrático), no falta de shrinkage.
- **nnls_directo**: `kappa_used=inf` se cuenta como genuinamente singular cuando `n_train <= D_features` (escasez real de muestra, NNLS con pesos en cero). El intercepto literal ya no introduce una columna muerta.

## Coincidencia con `EXP_ngrc_FRACASO.md` / `HALLAZGO_C1_LOO_HUB.md` (historia corta)

- Entidades citadas en el registro como historia corta: `Argentina, República Dominicana`.
- Coinciden con las genuinamente singulares encontradas aquí: `República Dominicana`.
- Genuinamente singulares aquí que NO estaban en esa lista corta del registro: `Colombia, Panamá`.
- Del registro, NO reaparecen como genuinamente singulares en este barrido: `Argentina`.

## ¿Concentran el error OOS? (entidades genuinamente singulares vs el resto)

- MASE promedio en combinaciones **genuinamente singulares** con dato OOS (n=1): **1.455** (mediana 1.455).
- MASE promedio en combinaciones **no singulares** (n=56): **1.154** (mediana 0.784).
- RMSE promedio singulares: **2.3393** vs no singulares: **2.4231**.

- **Sí concentran más error**: MASE 1.26x el de las no singulares.

## Resumen por variante × k

| variant             |   k |   n_entidades |   n_kappa_inf |   n_artefacto_standardscaler |   n_genuinamente_singular |   n_genuinamente_singular_objetivo |
|:--------------------|----:|--------------:|--------------:|-----------------------------:|--------------------------:|-----------------------------------:|
| baseline            |   2 |            17 |             0 |                            0 |                         0 |                                  0 |
| baseline            |   3 |            15 |             1 |                            0 |                         1 |                                  1 |
| ledoitwolf          |   2 |            17 |             0 |                            0 |                         0 |                                  0 |
| ledoitwolf          |   3 |            15 |             0 |                            0 |                         0 |                                  0 |
| nnls_directo        |   2 |            17 |             3 |                            0 |                         3 |                                  3 |
| nnls_directo        |   3 |            15 |             2 |                            0 |                         2 |                                  2 |
| tikhonov_covariance |   2 |            17 |             0 |                            0 |                         0 |                                  0 |
| tikhonov_covariance |   3 |            15 |             0 |                            0 |                         0 |                                  0 |

## Detalle de entidades objetivo genuinamente singulares

     variant  k          entity_base     kappa_raw  kappa_used                        motivo_singularidad  oos_MASE  oos_RMSE  oos_Count
    baseline  3             Colombia           inf         inf             singular_real_en_entrenamiento  1.455456  2.339329        1.0
nnls_directo  2             Colombia  4.039246e+17         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN        NaN
nnls_directo  2               Panamá  2.237096e+17         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN        NaN
nnls_directo  2 República Dominicana 3.931539e+180         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN        NaN
nnls_directo  3             Colombia           inf         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN        NaN
nnls_directo  3               Panamá  4.655203e+17         inf insuficiente_muestra (n_train<=D_features)       NaN       NaN        NaN


## Limitaciones / honestidad metodológica

- La definición de 'singular' usada aquí (`kappa_used = inf`, con la excepción del diagnóstico histórico del artefacto de StandardScaler) es binaria; no se investigó un umbral intermedio (p. ej. κ>10^6 'casi singular').
- El artefacto histórico del intercepto fue corregido: la constante se agrega después del escalado y nunca se centra.
- El cruce con OOS depende de que la entidad tenga cobertura en 2020-2025 bajo esa variante/k; varias combinaciones genuinamente singulares no tienen ese dato porque la propia singularidad en entrenamiento ya las excluye de la evaluación OOS.
- Esta comparación usa el mismo pull de datos en vivo del BCIE que `EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md` (mismo día, no comparable número-a-número con snapshots anteriores del registro).


## Archivos

- `codigo_pipeline/analysis_common.py` — utilidades compartidas que reutilizan la implementación causal y agregan detalle por entidad.
- `codigo_pipeline/analisis_kappa_entidad.py` — este script.
- `codigo_pipeline/output/kappa_entidad_detalle.csv` — detalle completo entidad×variante×k.
