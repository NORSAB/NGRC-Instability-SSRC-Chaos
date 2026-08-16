# Resultado corregido: variante intermedia de la base NNLS

**Fecha de revision:** 2026-08-13. **Script:** `run_oos_variante_intermedia.py`.

El guion comparte ahora la construccion de features, QLIKE y NNLS con
`volatility_models.py`. La corrida completa usa las mismas 1,485 ventanas de la prueba
principal.

| Variante | Predicciones negativas | QLIKE mediana | QLIKE media | MASE mediana | MASE media |
|---|---:|---:|---:|---:|---:|
| original con signo, heredada | 2.15 % | 1.490 | 19,733.5 | 0.533 | 1.666 |
| intermedia, heredada | 0.74 % | 1.474 | 10,828.2 | 0.518 | 1.343 |
| enteramente no negativa | **0.00 %** | **1.450** | **2.871** | **0.508** | **1.157** |

La variante intermedia usa valor absoluto en lineales, pero conserva productos cruzados con
signo. Reduce errores invalidos, aunque no los elimina. La base enteramente no negativa la
domina en las cuatro metricas y garantiza positividad, por lo que la variante intermedia no
se usa en el argumento principal.

Las medias QLIKE enormes de las dos bases firmadas provienen del recorte de predicciones
negativas a un piso diminuto. Esta es precisamente la razon para no presentar esas medias
como evidencia de un mecanismo recurrente ni de regularizacion Ridge.
