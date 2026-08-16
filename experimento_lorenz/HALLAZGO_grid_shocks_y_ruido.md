# Lorenz63: grilla de shocks y ruido de medición, protocolo corregido

## Cambios de protocolo

Las corridas del 13 de agosto de 2026 usan un SSRC recurrente real y validación temporal
interna para la λ de Ridge y del *readout* SSRC. La normalización se ajusta con los primeros
500 puntos. Ninguna estadística del punto OOS exterior participa en la selección.

### Estado de la lectura histórica

Quedan retiradas las tablas y conclusiones de la corrida anterior que atribuían a Ridge un
ΔMASE cercano a `+1.261`, describían al antiguo “reservorio” como estable o proponían validar
en el futuro la regla fija `λ = 0.1*traza(X'X)/D`. Esas cifras provenían del protocolo ya
reemplazado. La validación temporal de λ ya está implementada y los únicos valores vigentes
son los reproducidos abajo desde los CSV actuales. No se mezclan resultados históricos con la
corrida corregida.

## Grilla de 50 shocks

Se probaron cinco ubicaciones, cinco magnitudes entre 5 y 30 desviaciones estándar y ambos
signos. Cada configuración recorre la trayectoria completa y separa las ventanas que incluyen
el shock de las ventanas de calma.

### Geometría

| Magnitud | Mediana κ shock/calma | Mínimo | Máximo | Configuraciones con razón < 1 |
|---:|---:|---:|---:|---:|
| 5 | 0.002859 | 0.001688 | 0.004027 | 10/10 |
| 10 | 0.008095 | 0.005842 | 0.014965 | 10/10 |
| 15 | 0.038967 | 0.028630 | 0.062040 | 10/10 |
| 20 | 0.125391 | 0.092379 | 0.182036 | 10/10 |
| 30 | 0.653232 | 0.480586 | 0.841262 | 10/10 |

Hasta 30 desviaciones estándar, el shock reduce κ en todas las configuraciones. El efecto se
debilita al crecer la magnitud y se invierte en el barrido extendido desde 40 desviaciones.

### Error de pronóstico

Mediana de `MASE_shock - MASE_calma` sobre ubicación y signo:

| Magnitud | OLS | Ridge validado | NNLS | SSRC recurrente | Naive |
|---:|---:|---:|---:|---:|---:|
| 5 | 0.073365 | 0.098401 | -0.032399 | 0.070120 | 0.123746 |
| 10 | 0.048004 | 0.084508 | -0.025337 | 0.087102 | 0.051558 |
| 15 | -0.005991 | 0.078400 | -0.025210 | 0.118657 | -0.014595 |
| 20 | -0.027812 | 0.029806 | -0.018351 | 0.152339 | -0.072801 |
| 30 | -0.051584 | -0.009999 | -0.054696 | 0.238701 | -0.168100 |

La interpretación antigua ya no se sostiene. Con λ validada, Ridge no es el lector que más se
desestabiliza. El SSRC es el mejor en calma, pero su deterioro local aumenta con la magnitud
del shock. El signo negativo de algunos deltas tampoco significa una mejora causal: el
denominador MASE se calcula dentro de una ventana que contiene el shock y puede aumentar.

## Ruido de medición

Para cada nivel distinto de cero se usaron cinco semillas y dos objetivos: recuperar la señal
limpia o predecir la observación ruidosa. En el objetivo limpio, la media entre semillas de la
mediana por ventana fue:

| σ ruido | OLS | Ridge validado | NNLS | SSRC recurrente | Naive |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0.252346 | 0.252189 | 0.873664 | **0.088629** | 0.861371 |
| 0.01 | 0.262908 | 0.262937 | 0.876097 | **0.112006** | 0.861371 |
| 0.05 | 0.493550 | 0.495115 | 0.895651 | **0.245871** | 0.861371 |
| 0.10 | 0.674825 | 0.676239 | 0.938986 | **0.384446** | 0.861371 |
| 0.20 | 0.944122 | 0.945945 | 1.042255 | **0.661544** | 0.861371 |
| 0.50 | 1.501430 | 1.505813 | 1.500478 | **1.428322** | 0.861371 |

SSRC conserva la menor MASE entre los lectores aprendidos en todos los niveles, aunque pierde
ventaja conforme el ruido domina la señal. Ridge y OLS permanecen muy próximos. NNLS solo se
acerca a ellos cuando todos los lectores están ya en un régimen de error alto; no aparece una
ventaja robusta de la restricción no negativa en este objetivo con signo.

## Conclusión acotada

El experimento no respalda una afirmación universal contra Ridge. Respalda tres resultados más
precisos: κ puede bajar ante un shock y el error subir; Ridge validado permanece cerca de OLS
y no muestra el deterioro extremo atribuido a la corrida retirada; y un SSRC realmente
recurrente domina en Lorenz, aunque también acusa los shocks y el ruido extremos.

## Evidencia

- `run_lorenz_grid_shocks.py` y `output/resumen_grid_shocks.csv`
- `run_lorenz_noise.py` y `output/mase_vs_ruido.csv`
- Las salidas detalladas guardan la λ elegida y la razón correspondiente por ventana.
