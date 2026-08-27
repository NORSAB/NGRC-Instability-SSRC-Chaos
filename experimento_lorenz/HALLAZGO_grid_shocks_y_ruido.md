# Lorenz63: grilla de shocks y ruido de medición

El SSRC es recurrente (`W_res` real) con validación temporal interna para la λ de Ridge y del
*readout* SSRC. La normalización se ajusta con los primeros 500 puntos; ninguna estadística del
punto OOS exterior participa en la selección.

## Grilla de 50 shocks

Cinco ubicaciones, cinco magnitudes entre 5 y 30 desviaciones estándar, ambos signos. Cada
configuración recorre la trayectoria completa y separa ventanas con shock de ventanas en calma.

### Geometría

| Magnitud | Mediana κ shock/calma | Mínimo | Máximo | Configuraciones con razón < 1 |
|---:|---:|---:|---:|---:|
| 5 | 0.002859 | 0.001688 | 0.004027 | 10/10 |
| 10 | 0.008095 | 0.005842 | 0.014965 | 10/10 |
| 15 | 0.038967 | 0.028630 | 0.062040 | 10/10 |
| 20 | 0.125391 | 0.092379 | 0.182036 | 10/10 |
| 30 | 0.653232 | 0.480586 | 0.841262 | 10/10 |

Hasta 30 desviaciones estándar, el shock reduce κ en todas las configuraciones; el efecto se
debilita al crecer la magnitud y se invierte desde 40 desviaciones (ver
`HALLAZGO_umbral_shock_y_ruido_multipaso.md`).

### Error de pronóstico

Mediana de `MASE_shock - MASE_calma` sobre ubicación y signo:

| Magnitud | OLS | Ridge validado | NNLS | SSRC recurrente | Naive |
|---:|---:|---:|---:|---:|---:|
| 5 | 0.073365 | 0.098401 | -0.032399 | 0.070120 | 0.123746 |
| 10 | 0.048004 | 0.084508 | -0.025337 | 0.087102 | 0.051558 |
| 15 | -0.005991 | 0.078400 | -0.025210 | 0.118657 | -0.014595 |
| 20 | -0.027812 | 0.029806 | -0.018351 | 0.152339 | -0.072801 |
| 30 | -0.051584 | -0.009999 | -0.054696 | 0.238701 | -0.168100 |

Con λ validada, Ridge no es el lector que más se desestabiliza; el SSRC es el mejor en calma,
pero su deterioro local aumenta con la magnitud del shock. Un delta negativo no implica mejora
causal: el denominador MASE se calcula dentro de una ventana que contiene el shock y puede
aumentar.

## Ruido de medición

Cinco semillas por nivel de ruido, dos objetivos: recuperar la señal limpia o predecir la
observación ruidosa. Objetivo limpio, media entre semillas de la mediana por ventana:

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
acerca a ellos en el régimen de error alto; no hay ventaja robusta de la restricción no
negativa en este objetivo con signo.

## Conclusión

κ puede bajar ante un shock y el error subir; Ridge validado permanece cerca de OLS; un SSRC
realmente recurrente domina en Lorenz, aunque también acusa los shocks y el ruido extremos.

## Evidencia

- `run_lorenz_grid_shocks.py` y `output/resumen_grid_shocks.csv`
- `run_lorenz_noise.py` y `output/mase_vs_ruido.csv`
- Las salidas detalladas guardan la λ elegida y la razón correspondiente por ventana.
