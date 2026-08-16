# Resultado corregido: pronostico OOS de volatilidad diaria

**Fecha de revision:** 2026-08-13. **Script:** `run_oos_univariado.py`.

Este resultado reemplaza las tablas anteriores de esta carpeta. Aquellas tablas llamaban
"reservorio" a una transformacion `tanh(X @ W_in.T)` que nunca usaba `W_res`, fijaban el
lambda de Ridge como `0.1*traza(F'F)/D` y comparaban lectores recortados contra QLIKE sin
GARCH. Ninguna interpretacion causal sobre recurrencia basada en esa version sigue vigente.

## Protocolo corregido

- Nueve series: MXN, BRL, COP, CLP, PEN, ARS, GTQ, BTC y ETH.
- Target: retorno al cuadrado del siguiente dia; T=500, paso=20 y k=3.
- Cada ventana exterior usa solo `[t0-500, t0)`. El escalado y la seleccion de lambda se
  ajustan dentro de ese bloque, con el ultimo 20 % como validacion temporal interna.
- `ssrc_log` calcula
  `h_t=(1-leak)h_{t-1}+leak*tanh(W_in x_t+W_res h_{t-1})`; el readout log-Ridge produce
  varianza positiva. Una prueba automatizada confirma que cambiar `W_res` cambia los estados.
- `nnls_nonneg` usa una base enteramente no negativa y pesos NNLS, sin recorte.
- Se agregaron log-varianza, enlace softplus, EWMA(0.94), GARCH(1,1) y GJR-GARCH(1,1).
  Como `arch` no esta instalado, GARCH se ajusta con maxima verosimilitud gaussiana y
  restricciones de estacionariedad mediante SciPy SLSQP. Se intentan tres inicializaciones.
- OLS, Ridge-identidad y NNLS sobre base con signo quedan etiquetados como especificaciones
  heredadas o con recorte, no como comparaciones positivas principales.
- QLIKE se evalua con pisos 1e-12, 1e-10, 1e-8 y 1e-6.

## Resultado global

Medianas sobre 1,485 ventanas por metodo, salvo GARCH/GJR-GARCH (1,482):

| Metodo | QLIKE | MASE | Positividad estructural |
|---|---:|---:|---|
| EWMA(0.94) | **1.157** | 0.458 | si |
| GJR-GARCH(1,1) | 1.287 | 0.502 | si |
| GARCH(1,1) | 1.316 | 0.503 | si |
| NNLS con base no negativa | 1.450 | 0.508 | si |
| Ridge-identidad con recorte | 1.475 | 0.615 | no |
| OLS con recorte, heredado | 1.475 | 0.540 | no |
| NNLS con base firmada, heredado | 1.490 | 0.533 | no |
| SSRC recurrente con enlace log | 1.501 | **0.110** | si |
| Ridge con enlace softplus | 1.519 | 0.462 | si |
| Ridge sobre log-varianza | 1.561 | **0.106** | si |
| Persistencia | 1.779 | 0.225 | si |

La conclusion importante es negativa y util: **el SSRC recurrente no gana este benchmark de
volatilidad por QLIKE**. Supera a persistencia, pero queda por detras de EWMA, GARCH,
GJR-GARCH y NNLS no negativo. Su MASE bajo no compensa el QLIKE, porque MASE favorece
pronosticos cercanos a cero en muchos dias tranquilos y penaliza poco la subestimacion de
saltos. Por tanto, esta evidencia no sostiene que la recurrencia estabilice mejor la
volatilidad financiera.

El ranking por QLIKE es estable para pisos entre 1e-12 y 1e-8. Con 1e-6 cambian algunas
posiciones intermedias, pero EWMA sigue primero. La sensibilidad queda completa en
`output/oos_resumen_calma_vs_shock.md`.

## Lambda de Ridge no es Tikhonov sobre covarianza

Cada uno de los cuatro readouts Ridge (`ridge_clip`, `log_ridge`, `softplus_ridge` y
`ssrc_log`) selecciona un multiplicador entre 1e-6, 1e-4, 1e-2, 1 y 100 dentro de cada
ventana. En las 1,485 ventanas aparecen varios valores de la grilla; no se reproduce la
afirmacion de que "barrer lambda no aporta nada". Esa invariancia solo aplica al desplazamiento
`A + lambda I` cuando se conservan los eigenvectores de una misma matriz de covarianza, no a
una regresion Ridge donde los coeficientes cambian con lambda.

## Incidencias honestas

GARCH y GJR-GARCH no convergieron en tres ventanas cada uno, todas de ARS. Esas seis filas se
excluyeron en vez de usar parametros no convergentes; por eso sus n son 1,482. No se imputaron
resultados. Los 2,964 ajustes restantes convergieron.

## Archivos vigentes

- `volatility_models.py`: implementacion compartida.
- `test_volatility_models.py`: seis pruebas de recurrencia, causalidad, lambda y positividad.
- `output/oos_univariado.csv`: 16,329 filas de resultados corregidos.
- `output/oos_resumen_calma_vs_shock.md`: resumen y sensibilidad de QLIKE.
