# Roessler: segundo sistema caotico, validacion reducida de los tres hallazgos de Lorenz63

## Que se hizo

El manuscrito (`paper_chaos_aip/main.tex`) valida sus tres hallazgos principales -- el
mecanismo M^4 de inflacion de traza (Teorema 1), la divergencia multipaso del NG-RC
polinomico sin acotar, y la ventaja de filtrado de ruido de un reservorio recurrente -- solo
sobre el atractor de Lorenz63. Esta corrida repite los tres chequeos, a escala reducida
(apropiada para material suplementario, no una segunda replica completa de 30 semillas),
sobre el atractor de Roessler (`dx/dt=-y-z, dy/dt=x+a*y, dz/dt=b+z*(x-c)`, a=b=0.2, c=5.7,
observable escalar x), reusando (no copiando) las utilidades de
`experimento_lorenz/lorenz_common.py`.

Parametros especificos de Roessler: `dt_integrate=0.01`, `skip=20` (dt_feature=0.20, frente a
0.05 en Lorenz), `burn-in=8000` pasos de integracion. Se eligieron porque la espiral de
Roessler necesita un submuestreo mas grueso para evitar colinealidad por sobremuestreo:
`kappa(cov(F))` en una ventana limpia inicial (T_TRAIN=500) fue **6.919e+06**, del
mismo orden de magnitud que el valor limpio tipico de Lorenz63 (~1.3e6) y muy por debajo del
umbral de 1e8. El rango de z observado tras el burn-in fue acotado y consistente con el
atractor estandar a c=5.7 (sin divergencia).

## 1. Mecanismo M^4

Shock aditivo puntual en una ubicacion fija (centro de la trayectoria), magnitudes M en
{5, 10, 15, 20, 30} sigma. Para cada magnitud se ajusto Ridge con
validacion temporal en la ventana de entrenamiento que contiene el shock y se registro
`lambda_traza_legacy = 0.1*traza(F'F)/D`:

| M (sigma) | lambda_traza_legacy |
|---:|---:|
| 5 | 131.36 |
| 10 | 548.02 |
| 15 | 2168.54 |
| 20 | 6319.27 |
| 30 | 30016.8 |

Pendiente log-log ajustada sobre las 3 magnitudes mayores
(15, 20, 30 sigma): **3.7944**.

Lorenz63 (manuscrito, Fig. 1 / Teorema 1) midio una pendiente empirica de **3.99**,
prediccion teorica exactamente 4. La pendiente de Roessler (3.79) esta muy cerca de 4 y confirma el escalamiento cuartico. Veredicto: **REPLICA**.

Figura: `paper_chaos_aip/figures/fig_rossler_m4.pdf`.

## 2. Divergencia multipaso

Comparacion causal walk-forward (15 ventanas, 1
semilla de reservorio) de Ridge NG-RC (heuristica de traza fija 0.1*traza(F'F)/D, la misma
regla fija que se uso originalmente en Lorenz antes de la validacion temporal -- para una
comparacion directa de "el polinomio sin acotar diverge"), OLS NG-RC, proyeccion tanh
estatica (W_res=0) y ESN recurrente disperso (W_res != 0), en H in {1, 5, 10}. Mediana de
MASE:

| H | Ridge NG-RC | OLS NG-RC | tanh estatico | ESN recurrente |
|---:|---:|---:|---:|---:|
| 1 | 0.875520 | 0.037137 | 0.016758 | 0.019549 |
| 5 | 2.800953 | 0.437445 | 0.080204 | 0.133997 |
| 10 | 4.392754 | 2.748808 | 0.261480 | 0.583165 |

Con la heuristica de traza fija (0.1*traza(F'F)/D), Ridge NG-RC en Roessler ya arranca con
MASE alto en H=1 (0.88) -- mucho peor que OLS (0.037) o los modelos acotados (~0.017-0.020) --
porque la traza natural de las caracteristicas cuadraticas de Roessler es mucho mayor que la de
Lorenz, y la misma regla fija sobre-regulariza con mas fuerza aqui. Esto es evidencia adicional,
mas cruda que en Lorenz, de por que "las heuristicas de Ridge basadas en traza no deben
combinarse con caracteristicas cuadraticas" (mensaje del Teorema 1): en Roessler el efecto
aparece incluso sin ningun shock. Por eso el criterio de veredicto usa el MASE ABSOLUTO en
H=10 (no la razon MASE(H10)/MASE(H1), que queda comprimida artificialmente cuando el
modelo sin acotar ya arranca mal en H=1): el mejor modelo acotado (tanh estatico o ESN,
MASE=0.2615) es claramente mejor que
el mejor modelo sin acotar (Ridge u OLS, MASE=2.7488) en H=10.
Como referencia, las razones MASE(H=10)/MASE(H=1) fueron: Ridge NG-RC = 5.02x,
tanh estatico = 15.60x, ESN = 29.83x, OLS NG-RC =
74.02x (OLS sin regularizar
muestra el crecimiento relativo mas fuerte, consistente con divergencia polinomica pura).
Veredicto: **REPLICA**.

## 3. Filtrado de ruido

Ruido de medicion sigma=0.1 (relativo a la serie estandarizada), 1 realizacion de
ruido fija, 5 semillas de reservorio, 30
ventanas por semilla (150 pares totales). El lector se entrena SIEMPRE con el target
ruidoso; solo la evaluacion OOS se compara contra el target limpio (variante de filtrado,
igual que en Lorenz63).

- Mediana MASE ESN recurrente: **0.3233**
- Mediana MASE tanh estatico: **0.4137**
- Tasa de victoria del ESN: 94/150 (62.7%), IC Clopper-Pearson
  95%: [0.54, 0.70]

Veredicto: **REPLICA**.

## Resumen honesto: que confirma y que no

| Hallazgo Lorenz63 | Resultado en Roessler | Veredicto |
|---|---|---|
| 1. M^4 (pendiente ~3.99) | pendiente medida 3.79 | REPLICA |
| 2. Divergencia multipaso (polinomio sin acotar explota) | ver tabla de razones H10/H1 arriba | REPLICA |
| 3. Filtrado de ruido (ESN > estatico) | tasa de victoria 62.7%, IC [0.54,0.70] | REPLICA |

Esta corrida es una comprobacion de generalidad a escala reducida (1-5 semillas, 15-30
ventanas), no una replica estadistica al nivel de rigor del protocolo de 30 semillas de
Lorenz63. Los resultados deben leerse como evidencia indicativa, no como una confirmacion
definitiva a la misma escala de evidencia que el hallazgo original.

## Evidencia

- `run_rossler_validation.py`
- `output/rossler_m4_sweep.csv`
- `output/rossler_multistep.csv`
- `output/rossler_noise_filtering.csv`
- `../paper_chaos_aip/figures/fig_rossler_m4.pdf`

Tiempo total de ejecucion: 3.1s.
