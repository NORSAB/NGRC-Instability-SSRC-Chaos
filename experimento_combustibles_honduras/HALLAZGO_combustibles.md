# Validación secundaria: combustibles de Honduras con protocolo causal

**Script:** `run_combustibles_hn.py`. **Datos:** 496 semanas, del 2 de enero de 2017 al 10 de
agosto de 2026. Esta evidencia se conserva como validación secundaria; no define la
contribución principal del Artículo 4.

## Protocolo

Cada ventana ajusta sus transformaciones únicamente con observaciones pasadas. El SSRC usa
`W_res` y actualiza el estado en secuencia. El Ridge del lector elige `lambda` por validación
temporal interna, sobre columnas escaladas con entrenamiento. Se comparan una base NNLS
realmente no negativa, enlace softplus, log-varianza, EWMA, GARCH(1,1) y GJR-GARCH(1,1); QLIKE
se calcula con tres pisos causales. `test_modelos_volatilidad.py` verifica recurrencia,
causalidad y positividad. La corrida terminó con 344 ventanas y cero ajustes fallidos.

## Resultado agregado

Medianas sobre 344 ventanas:

| Método | QLIKE | MASE | Predicciones crudas negativas |
|---|---:|---:|---:|
| NNLS, base no negativa | **0.359** | 0.485 | 0 |
| GARCH(1,1) | 0.380 | 0.454 | 0 |
| GJR-GARCH(1,1) | 0.392 | 0.442 | 0 |
| Naive | 0.432 | 0.369 | 0 |
| OLS con recorte, legado | 0.542 | 0.587 | 47 |
| Ridge CV con recorte | 0.552 | 0.734 | 3 |
| NG-RC softplus CV | 0.570 | 0.713 | 0 |
| EWMA(0.94) | 0.677 | 0.736 | 0 |
| SSRC recurrente log-CV | 1.313 | **0.338** | 0 |
| Ridge log-CV | 1.815 | 0.342 | 0 |

La base NNLS no negativa obtiene el menor QLIKE agregado, pero no domina MASE; el SSRC
recurrente y Ridge-log reducen MASE, pero quedan por detrás en QLIKE. GARCH y GJR-GARCH son
referencias competitivas. No hay ventaja general de NNLS ni del SSRC en esta serie.

## Eventos y sensibilidad de QLIKE

En calma, mediana QLIKE: 0.366 (NNLS no negativo), 0.388 (GARCH), 0.404 (GJR), 0.437 (naive).
En COVID, NNLS obtuvo 0.259 frente a 0.517 de GARCH, con MASE 7.75. En Eta/Iota (8 ventanas)
gana naive por QLIKE; en Ucrania gana GARCH; en la ventana de Medio Oriente 2026 gana OLS
legado. Estos cortes son descriptivos, no pruebas confirmatorias.

El orden agregado es estable para pisos de `1e-6` y `1e-4` veces la mediana de la varianza de
entrenamiento; con `1e-2` cambian algunas medianas de métodos con predicciones muy pequeñas.

## Alcance

El NNLS con base realmente no negativa no produjo ninguna varianza negativa. Una salida
positiva no basta para ganar: softplus, log-varianza y SSRC-log son válidos por construcción,
pero sus resultados difieren según la métrica. Combustibles no prueba el mecanismo causal del
manuscrito; muestra que las decisiones de enlace, regularización y métrica cambian el orden de
los modelos en datos reales.

## Archivos

- `output/oos_combustibles.csv`: valores completos.
- `output/sensibilidad_piso_combustibles.csv`: sensibilidad al piso.
- `output/fallos_ajuste_combustibles.csv`: fallos de optimización.
