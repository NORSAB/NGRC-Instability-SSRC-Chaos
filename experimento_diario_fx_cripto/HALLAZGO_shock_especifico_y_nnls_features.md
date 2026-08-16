# Resultado corregido: shocks y base no negativa

**Fecha de revision:** 2026-08-13. **Script:** `run_oos_v2_shock_y_nnls.py`.

Este guion ya no descarga datos ni copia lectores. Deriva ambos anexos desde
`output/oos_univariado.csv`, lo que impide que reaparezca una version feed-forward del SSRC.

## Clasificacion causal de shocks

El umbral de 6 sigma se estima por ventana usando solo retornos de entrenamiento. Se separa
si el train tuvo un shock y si el dia objetivo es un shock:

| Categoria | n |
|---|---:|
| calma total | 801 |
| train tuvo shock, test normal | 679 |
| test es shock, train sin shock | 3 |
| train y test con shock | 2 |

Hay solo cinco dias objetivo clasificados como shock. Por tanto, sus tablas son descriptivas
y no tienen potencia para afirmar superioridad durante eventos extremos. El cambio frente a
la version anterior tambien muestra que clasificar con la sigma de la serie completa era una
forma innecesaria de mirar hacia el futuro.

En los tres casos `test_es_shock`, todos los metodos subestiman fuertemente el salto. No se
afirma que la recurrencia lo anticipe. Para una prueba de shocks con potencia haria falta
evaluar cada fecha extrema, es decir, usar paso diario alrededor del evento o un protocolo
dirigido preespecificado.

## NNLS: pesos no negativos no bastan

| Variante | Predicciones crudas negativas | QLIKE mediana | MASE mediana | n |
|---|---:|---:|---:|---:|
| NNLS sobre base con signo, heredado | 2.15 % | 1.490 | 0.533 | 1,485 |
| NNLS sobre base no negativa | **0.00 %** | **1.450** | **0.508** | 1,485 |

La especificacion coherente usa `|r_i|` y `|r_i||r_j|` como columnas, mas intercepto y pesos
no negativos. La prediccion es no negativa por construccion y mejora QLIKE y MASE medianos en
esta nueva corrida. La especificacion con signo se conserva solo como control heredado y
requiere recorte cuando produce valores imposibles.

## Archivos vigentes

- `output/oos_test_vs_train_shock.csv` y su resumen.
- `output/oos_nnls_features_noneg.csv` y su resumen.
