# Pronóstico OOS de volatilidad diaria

**Script:** `run_oos_univariado.py`.

## Protocolo

- Nueve series: MXN, BRL, COP, CLP, PEN, ARS, GTQ, BTC y ETH.
- Objetivo: retorno al cuadrado del siguiente día; T=500, paso=20, k=3.
- Cada ventana exterior usa solo `[t0-500, t0)`; el escalado y la selección de λ se ajustan
  dentro de ese bloque, con el último 20% como validación temporal interna.
- `ssrc_log` calcula `h_t=(1-leak)h_{t-1}+leak*tanh(W_in x_t+W_res h_{t-1})`; el readout
  log-Ridge produce varianza positiva. Una prueba automatizada confirma que cambiar `W_res`
  cambia los estados.
- `nnls_nonneg` usa una base enteramente no negativa y pesos NNLS, sin recorte.
- Se incluyen log-varianza, enlace softplus, EWMA(0.94), GARCH(1,1) y GJR-GARCH(1,1) (ajuste
  por máxima verosimilitud gaussiana con restricciones de estacionariedad vía SciPy SLSQP,
  tres inicializaciones). OLS, Ridge-identidad y NNLS sobre base con signo quedan etiquetados
  como especificaciones heredadas o con recorte.
- QLIKE se evalúa con pisos 1e-12, 1e-10, 1e-8 y 1e-6.

## Resultado global

Medianas sobre 1,485 ventanas por método (GARCH/GJR-GARCH: 1,482):

| Método | QLIKE | MASE | Positividad estructural |
|---|---:|---:|---|
| EWMA(0.94) | **1.157** | 0.458 | sí |
| GJR-GARCH(1,1) | 1.287 | 0.502 | sí |
| GARCH(1,1) | 1.316 | 0.503 | sí |
| NNLS con base no negativa | 1.450 | 0.508 | sí |
| Ridge-identidad con recorte | 1.475 | 0.615 | no |
| OLS con recorte, heredado | 1.475 | 0.540 | no |
| NNLS con base firmada, heredado | 1.490 | 0.533 | no |
| SSRC recurrente con enlace log | 1.501 | **0.110** | sí |
| Ridge con enlace softplus | 1.519 | 0.462 | sí |
| Ridge sobre log-varianza | 1.561 | **0.106** | sí |
| Persistencia | 1.779 | 0.225 | sí |

El SSRC recurrente no gana este benchmark de volatilidad por QLIKE: supera a persistencia,
pero queda por detrás de EWMA, GARCH, GJR-GARCH y NNLS no negativo. Su MASE bajo no compensa
el QLIKE, porque MASE favorece pronósticos cercanos a cero en días tranquilos y penaliza poco
la subestimación de saltos. El ranking por QLIKE es estable entre pisos 1e-12 y 1e-8; con
1e-6 cambian algunas posiciones intermedias, pero EWMA sigue primero (sensibilidad completa en
`output/oos_resumen_calma_vs_shock.md`).

## Selección de λ

Cada uno de los cuatro readouts Ridge (`ridge_clip`, `log_ridge`, `softplus_ridge`,
`ssrc_log`) selecciona un multiplicador entre 1e-6, 1e-4, 1e-2, 1 y 100 dentro de cada ventana;
en las 1,485 ventanas aparecen varios valores de la grilla. La invariancia de autovectores bajo
$A + \lambda I$ aplica al desplazamiento de una misma matriz de covarianza, no a una regresión
Ridge donde los coeficientes cambian con λ.

## Convergencia

GARCH y GJR-GARCH no convergieron en tres ventanas cada uno, todas de ARS; esas seis filas se
excluyeron (de ahí n=1,482). Los 2,964 ajustes restantes convergieron.

## Archivos

- `volatility_models.py`: implementación compartida.
- `test_volatility_models.py`: seis pruebas de recurrencia, causalidad, λ y positividad.
- `output/oos_univariado.csv`: 16,329 filas de resultados.
- `output/oos_resumen_calma_vs_shock.md`: resumen y sensibilidad de QLIKE.
