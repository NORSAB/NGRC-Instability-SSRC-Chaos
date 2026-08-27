# Lorenz63: control sintético con SSRC recurrente

El lector SSRC es recurrente: cada estado satisface `h_t = tanh(W_in F_t + W_res h_{t-1})`,
con `W_res` escalado a radio espectral 0.9. Ridge y el *readout* del SSRC seleccionan λ por
validación temporal interna (80% ajuste / 20% validación por ventana exterior de 500
observaciones, sin usar el punto OOS). La normalización de la trayectoria usa solo los primeros
500 puntos.

## Resultado de un paso

Mediana de MASE, 1,475 ventanas en calma:

| Lector | MASE mediana |
|---|---:|
| SSRC recurrente | **0.088629** |
| Ridge con validación temporal | 0.252189 |
| OLS | 0.252346 |
| Naive | 0.861371 |
| NNLS | 0.873664 |

Ridge, seleccionado dentro de la ventana, empata con OLS.

## Shock de 15 desviaciones estándar

La mediana de κ(cov(F)) pasa de ~`1.287e6` en calma a `5.047e4` en las 25 ventanas que
contienen el shock. En esas ventanas, las medianas de MASE fueron 0.230864 (OLS), 0.342772
(Ridge), 0.270098 (SSRC) y 1.199792 (NNLS). κ es un diagnóstico geométrico, no una función de
pérdida: que baje no implica que el pronóstico mejore.

## Escalamiento M^4

El barrido explícito de λ (14 ventanas, dos escenarios) muestra mediana del error absoluto OOS
de 0.065206 con selección temporal frente a 0.181025 con la regla fija de razón 0.1. Un shock
de magnitud M puede llevar términos de la covarianza a escala M^4; una λ fijada como proporción
de la traza hereda esa sensibilidad.

## NNLS

NNLS no ayuda aquí: `x(t+1)` cambia de signo y la restricción actúa sobre los pesos, no sobre
un objetivo naturalmente no negativo.

## Evidencia

- `run_lorenz_shock.py`: control limpio y shock único.
- `run_lorenz_lambda_sensitivity.py`: barrido explícito y comparación con la heurística 0.1.
- `output/oos_lorenz.csv`: predicciones exteriores y λ elegida por ventana.
- `output/sensibilidad_lambda_lorenz.csv`: camino de validación y error OOS por candidato.
- `test_lorenz_protocol.py`: pruebas de recurrencia, causalidad y respuesta de λ a la escala.
