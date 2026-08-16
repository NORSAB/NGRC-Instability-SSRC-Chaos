# Lorenz63: control sintético corregido

## Qué se corrigió

La corrida del 13 de agosto de 2026 reemplaza dos decisiones que impedían interpretar el
experimento anterior:

1. El método llamado “reservorio” era una proyección aleatoria fila a fila. Ahora es un SSRC
   realmente recurrente: cada estado satisface
   `h_t = tanh(W_in F_t + W_res h_{t-1})`, con `W_res` escalada a radio espectral 0.9.
2. Ridge y el *readout* del SSRC ya no usan de forma fija
   `0.1*traza(X'X)/D`. En cada ventana exterior de 500 observaciones, el 80% inicial ajusta
   nueve candidatos de λ y el 20% final los valida sin barajar. El punto OOS queda fuera.

Además, la normalización de la trayectoria usa solo los primeros 500 puntos. Así se evita que
la media o la desviación estándar del futuro entren en las ventanas tempranas.

## Resultado de un paso

Mediana de MASE, 1,475 ventanas en calma:

| Lector | MASE mediana |
|---|---:|
| SSRC recurrente | **0.088629** |
| Ridge con validación temporal | 0.252189 |
| OLS | 0.252346 |
| Naive | 0.861371 |
| NNLS | 0.873664 |

El cambio de arquitectura es sustantivo: el SSRC recurrente mejora con claridad a OLS. Esta
cifra no puede compararse con la del antiguo “reservorio”, porque aquel cálculo nunca usó
`W_res`. La explicación que ahora sí corresponde es conjunta: la memoria recurrente conserva
información secuencial y `tanh` limita la amplitud del estado.

Ridge, una vez seleccionado dentro de la ventana, prácticamente empata con OLS. Por tanto, el
resultado anterior no demostraba que Ridge fuera inútil; mostraba que la regla fija
proporcional a la traza podía sobre-regularizar.

## Shock de 15 desviaciones estándar

El patrón geométrico se mantiene. La mediana de κ(cov(F)) pasa de aproximadamente
`1.287e6` en calma a `5.047e4` en las 25 ventanas que contienen el shock. Que κ baje no
significa que el pronóstico mejore: en esas ventanas, las medianas de MASE fueron 0.230864
para OLS, 0.342772 para Ridge, 0.270098 para SSRC y 1.199792 para NNLS.

El shock cambia la escala y separa direcciones antes casi colineales. Ese efecto puede reducir
el número de condición a la vez que aumenta el error de algunos lectores. κ sigue siendo un
diagnóstico geométrico, no una función de pérdida.

## Qué queda de M^4

El barrido explícito de λ usa 14 ventanas de dos escenarios. La validación interna eligió
cuatro razones de λ distintas. En esa muestra, la mediana del error absoluto OOS fue 0.065206
con selección temporal y 0.181025 con la regla fija de razón 0.1.

Por eso M^4 queda acotado a una afirmación verificable: las características cuadráticas hacen
que un shock de magnitud M pueda llevar términos de la covarianza a escala M^4, y una λ fijada
como proporción de la traza hereda esa sensibilidad de escala. No implica que toda solución
Ridge sea frágil ni que barrer λ sea inútil.

## Lectura de NNLS

NNLS no ayuda aquí porque `x(t+1)` cambia de signo y la restricción actúa sobre los pesos, no
sobre un objetivo naturalmente no negativo. Este control no contradice un posible beneficio
de NNLS en volatilidad; impide generalizarlo fuera de ese tipo de objetivo.

## Evidencia reproducible

- `run_lorenz_shock.py`: control limpio y shock único.
- `run_lorenz_lambda_sensitivity.py`: barrido explícito y comparación con la heurística 0.1.
- `output/oos_lorenz.csv`: predicciones exteriores y λ elegida por ventana.
- `output/sensibilidad_lambda_lorenz.csv`: camino de validación y error OOS por candidato.
- `test_lorenz_protocol.py`: pruebas de recurrencia, causalidad y respuesta de λ a la escala.
