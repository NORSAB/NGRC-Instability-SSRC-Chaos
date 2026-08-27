# Variante intermedia de la base NNLS

**Script:** `run_oos_variante_intermedia.py`, sobre la misma construcción de features, QLIKE y
NNLS que `volatility_models.py` y las mismas 1,485 ventanas de la prueba principal.

| Variante | Predicciones negativas | QLIKE mediana | QLIKE media | MASE mediana | MASE media |
|---|---:|---:|---:|---:|---:|
| original con signo, heredada | 2.15 % | 1.490 | 19,733.5 | 0.533 | 1.666 |
| intermedia, heredada | 0.74 % | 1.474 | 10,828.2 | 0.518 | 1.343 |
| enteramente no negativa | **0.00 %** | **1.450** | **2.871** | **0.508** | **1.157** |

La variante intermedia usa valor absoluto en lineales, pero conserva productos cruzados con
signo: reduce errores inválidos sin eliminarlos. La base enteramente no negativa domina en las
cuatro métricas y garantiza positividad; por eso la variante intermedia no se usa en el
argumento principal. Las medias QLIKE de las bases firmadas son grandes por el recorte de
predicciones negativas a un piso diminuto.
