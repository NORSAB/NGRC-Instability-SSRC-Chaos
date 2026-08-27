# Shocks y base no negativa

**Script:** `run_oos_v2_shock_y_nnls.py`. Deriva ambos anexos desde `output/oos_univariado.csv`
(no descarga datos ni copia lectores).

## Clasificación causal de shocks

El umbral de 6 sigma se estima por ventana usando solo retornos de entrenamiento; se separa si
el train tuvo un shock y si el día objetivo es un shock:

| Categoría | n |
|---|---:|
| calma total | 801 |
| train tuvo shock, test normal | 679 |
| test es shock, train sin shock | 3 |
| train y test con shock | 2 |

Solo cinco días objetivo quedan clasificados como shock; las tablas correspondientes son
descriptivas, sin potencia para afirmar superioridad durante eventos extremos. En los tres
casos `test_es_shock`, todos los métodos subestiman fuertemente el salto.

## NNLS: pesos no negativos no bastan

| Variante | Predicciones crudas negativas | QLIKE mediana | MASE mediana | n |
|---|---:|---:|---:|---:|
| NNLS sobre base con signo, heredado | 2.15 % | 1.490 | 0.533 | 1,485 |
| NNLS sobre base no negativa | **0.00 %** | **1.450** | **0.508** | 1,485 |

La especificación coherente usa `|r_i|` y `|r_i||r_j|` como columnas, más intercepto y pesos
no negativos: la predicción es no negativa por construcción y mejora QLIKE y MASE medianos. La
especificación con signo se conserva solo como control heredado y requiere recorte cuando
produce valores imposibles.

## Archivos

- `output/oos_test_vs_train_shock.csv` y su resumen.
- `output/oos_nnls_features_noneg.csv` y su resumen.
