# Validación secundaria: combustibles de Honduras con protocolo causal

**Reejecución:** 2026-08-13. **Script:** `run_combustibles_hn.py`. **Datos:** snapshot local de
496 semanas, del 2 de enero de 2017 al 10 de agosto de 2026. Esta evidencia se conserva como
validación secundaria; no define la contribución principal del Artículo 4.

## Qué se corrigió

La corrida anterior no es comparable con esta. Estandarizaba cada serie completa, llamaba
“reservorio” a una proyección aleatoria sin memoria, fijaba el Ridge mediante
`0.1*tr(F'F)/D`, restringía solo los pesos de NNLS aunque la base tenía valores negativos y
evaluaba QLIKE después de recortar las predicciones. La reejecución aplica cuatro cambios:

1. cada ventana ajusta sus transformaciones únicamente con observaciones pasadas;
2. el SSRC usa de verdad `W_res` y actualiza el estado en secuencia;
3. el Ridge del lector elige `lambda` mediante validación temporal interna, sobre columnas
   escaladas con entrenamiento, sin usar la traza como regla de escala;
4. se comparan base NNLS realmente no negativa, enlace softplus, log-varianza, EWMA,
   GARCH(1,1) y GJR-GARCH(1,1). El QLIKE se calcula además con tres pisos causales.

Las pruebas de `test_modelos_volatilidad.py` verifican recurrencia, causalidad y positividad.
La corrida terminó con 344 ventanas y **cero ajustes fallidos**.

## Resultado agregado

Medianas sobre las 344 ventanas, sin interpretar las ventanas de eventos como una muestra
independiente:

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

El mensaje cambió. La base NNLS no negativa obtiene el menor QLIKE agregado, pero no domina
MASE; el SSRC recurrente y Ridge-log reducen MASE, pero quedan claramente por detrás en QLIKE.
GARCH y GJR-GARCH son referencias competitivas que la comparación anterior omitía. Por tanto,
no se sostiene una ventaja general de NNLS ni del SSRC.

## Eventos y sensibilidad de QLIKE

En calma, la mediana QLIKE fue 0.366 para NNLS no negativo, 0.388 para GARCH, 0.404 para GJR
y 0.437 para naive. En COVID, NNLS obtuvo 0.259 frente a 0.517 de GARCH, pero su MASE fue
7.75. En Eta/Iota solo hay ocho ventanas y gana naive por QLIKE; en Ucrania gana GARCH; en la
ventana de Medio Oriente 2026 gana OLS legado, con una ventana definida después de observar la
serie. Estos cortes se reportan como descriptivos, no como pruebas confirmatorias.

El orden agregado es estable para pisos iguales a `1e-6` y `1e-4` veces la mediana de la
varianza de entrenamiento. Con `1e-2`, cambian algunas medianas de métodos con predicciones
muy pequeñas. Esta sensibilidad confirma que cualquier resultado basado en recortes debe
mostrar el piso explícitamente.

## Alcance correcto

La corrida corrige el artefacto de NNLS con base signada: el nuevo NNLS no produjo ninguna
varianza negativa. También demuestra que una salida positiva no basta para ganar: softplus,
log-varianza y SSRC-log son válidos por construcción, pero sus resultados difieren según la
métrica. Combustibles no prueba el mecanismo causal del manuscrito; sirve para mostrar que las
decisiones de enlace, regularización y métrica cambian el orden de los modelos en datos reales.

Los valores completos están en `output/oos_combustibles.csv`; la sensibilidad al piso, en
`output/sensibilidad_piso_combustibles.csv`; y cualquier fallo de optimización, en
`output/fallos_ajuste_combustibles.csv`.
