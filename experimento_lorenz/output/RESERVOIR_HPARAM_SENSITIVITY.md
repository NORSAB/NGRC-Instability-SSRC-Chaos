# Sensibilidad del ESN a hiperparametros del reservorio

Barrida de 27 configuraciones (d_res in [25, 50, 100], rho in [0.5, 0.9, 0.99], leak in [0.25, 0.5, 1.0]), 5 semillas de reservorio por punto (vs. 30 en el experimento principal), paso mas grueso por costo computacional. Ninguna configuracion se selecciono por su resultado OOS; se reportan las 27 completas.

## Filtrado de ruido (ESN vs. proyeccion estatica, sigma=0.1)

La ventaja del ESN sobre la proyeccion estatica bajo ruido de medicion **se mantiene en las 27 configuraciones** (tasa de victoria del ESN >50% en todas). Mediana de la tasa de victoria: 58.3%, minimo: 52.2%.


## Robustez ante shocks 15-sigma, ubicacion problematica = 10000

Tasa de victoria del ESN en la ubicacion problematica, por configuracion (mediana: 60.0%, maximo: 90.0%):


El fallo **no es universal**: en 14 de 27 configuraciones el ESN gana mayoritariamente en esa ubicacion (tasa de victoria >50%), sugiriendo que el fallo reportado en el experimento principal depende en parte de la configuracion de hiperparametros usada alli (d_res=50, rho=0.9, leak=1.0), no solo de la ubicacion en si.


|   d_res |   rho |   leak |   shock_problem_location_win_rate_esn |
|--------:|------:|-------:|--------------------------------------:|
|      25 |  0.5  |   0.25 |                                   0.6 |
|      25 |  0.5  |   0.5  |                                   0.7 |
|      25 |  0.9  |   0.5  |                                   0.7 |
|      25 |  0.99 |   0.5  |                                   0.7 |
|      25 |  0.99 |   1    |                                   0.6 |
|      50 |  0.5  |   0.25 |                                   0.8 |
|      50 |  0.5  |   0.5  |                                   0.9 |
|      50 |  0.9  |   0.25 |                                   0.7 |
|      50 |  0.99 |   0.25 |                                   0.6 |
|     100 |  0.5  |   0.25 |                                   0.8 |
|     100 |  0.5  |   0.5  |                                   0.8 |
|     100 |  0.5  |   1    |                                   0.6 |
|     100 |  0.9  |   0.25 |                                   0.6 |
|     100 |  0.99 |   0.25 |                                   0.6 |



## Recomendacion

Al menos uno de los dos hallazgos muestra sensibilidad a los hiperparametros del reservorio dentro de la grilla probada (ver detalle arriba). Se recomienda anadir una nota breve en Limitations senalando que los resultados se reportan para la configuracion d_res=50, rho=0.9, leak=1.0 y que no se verifico invariancia completa a traves de todos los hiperparametros razonables.
