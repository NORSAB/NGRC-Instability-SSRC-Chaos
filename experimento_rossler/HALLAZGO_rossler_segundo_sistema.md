# Rössler: segundo sistema caótico, validación reducida de los tres hallazgos de Lorenz63

El manuscrito (`paper_chaos_aip/main.tex`) valida sus tres hallazgos principales (mecanismo M^4
de inflación de traza, Teorema 1; divergencia multipaso del NG-RC polinómico sin acotar;
ventaja de filtrado de ruido de un reservorio recurrente) sobre el atractor de Lorenz63. Esta
corrida repite los tres chequeos, a escala reducida (material suplementario, no una segunda
réplica completa de 30 semillas), sobre el atractor de Rössler
(`dx/dt=-y-z, dy/dt=x+a*y, dz/dt=b+z*(x-c)`, a=b=0.2, c=5.7, observable escalar x), reutilizando
las utilidades de `experimento_lorenz/lorenz_common.py`.

Parámetros de Rössler: `dt_integrate=0.01`, `skip=20` (dt_feature=0.20, frente a 0.05 en
Lorenz), burn-in de 8000 pasos de integración; la espiral de Rössler necesita un submuestreo
más grueso para evitar colinealidad por sobremuestreo. `kappa(cov(F))` en una ventana limpia
inicial (T_TRAIN=500) fue **6.919e+06**, del mismo orden de magnitud que el valor típico en
calma de Lorenz63 (~1.3e6) y muy por debajo del umbral de 1e8. El rango de z observado tras el
burn-in fue acotado y consistente con el atractor estándar a c=5.7.

## 1. Mecanismo M^4

Shock aditivo puntual en el centro de la trayectoria, magnitudes M en {5, 10, 15, 20, 30}
sigma. Ridge se ajustó con validación temporal en la ventana de entrenamiento que contiene el
shock, registrando `lambda_traza_legacy = 0.1*traza(F'F)/D`:

| M (sigma) | lambda_traza_legacy |
|---:|---:|
| 5 | 131.36 |
| 10 | 548.02 |
| 15 | 2168.54 |
| 20 | 6319.27 |
| 30 | 30016.8 |

Pendiente log-log sobre las 3 magnitudes mayores (15, 20, 30 sigma): **3.7944**, cercana a la
predicción teórica de 4 y a la pendiente medida en Lorenz63 (3.99, Fig. 1 / Teorema 1 del
manuscrito). Figura: `paper_chaos_aip/figures/fig_rossler_m4.pdf`.

## 2. Divergencia multipaso

Comparación causal walk-forward (15 ventanas, 1 semilla de reservorio) de Ridge NG-RC
(heurística de traza fija 0.1*traza(F'F)/D), OLS NG-RC, proyección tanh estática (W_res=0) y
ESN recurrente disperso (W_res≠0), en H en {1, 5, 10}. Mediana de MASE:

| H | Ridge NG-RC | OLS NG-RC | tanh estático | ESN recurrente |
|---:|---:|---:|---:|---:|
| 1 | 0.875520 | 0.037137 | 0.016758 | 0.019549 |
| 5 | 2.800953 | 0.437445 | 0.080204 | 0.133997 |
| 10 | 4.392754 | 2.748808 | 0.261480 | 0.583165 |

Con la heurística de traza fija, Ridge NG-RC en Rössler ya arranca con MASE alto en H=1 (0.88):
la traza natural de las características cuadráticas de Rössler es mayor que la de Lorenz, y la
misma regla fija sobre-regulariza con más fuerza. El mejor modelo acotado (tanh estático o ESN,
MASE=0.2615) es claramente mejor que el mejor modelo sin acotar (Ridge u OLS, MASE=2.7488) en
H=10. Razones MASE(H=10)/MASE(H=1): Ridge NG-RC 5.02x, tanh estático 15.60x, ESN 29.83x, OLS
NG-RC 74.02x (consistente con divergencia polinómica pura sin regularizar).

## 3. Filtrado de ruido

Ruido de medición sigma=0.1 (relativo a la serie estandarizada), 1 realización de ruido fija,
5 semillas de reservorio, 30 ventanas por semilla (150 pares totales). El lector se entrena
siempre con el target ruidoso; solo la evaluación OOS se compara contra el target limpio.

- Mediana MASE ESN recurrente: **0.3233**
- Mediana MASE tanh estático: **0.4137**
- Tasa de victoria del ESN: 94/150 (62.7%), IC Clopper-Pearson 95%: [0.54, 0.70]

## Resumen frente a Lorenz63

| Hallazgo Lorenz63 | Resultado en Rössler |
|---|---|
| M^4 (pendiente ~3.99) | pendiente medida 3.79 |
| Divergencia multipaso (polinomio sin acotar explota) | confirmada, ver razones H10/H1 |
| Filtrado de ruido (ESN > estático) | tasa de victoria 62.7%, IC [0.54,0.70] |

Esta corrida es una comprobación de generalidad a escala reducida (1-5 semillas, 15-30
ventanas), no una réplica estadística al nivel del protocolo de 30 semillas de Lorenz63; los
resultados son evidencia indicativa, no confirmación a la misma escala.

## Evidencia

- `run_rossler_validation.py`
- `output/rossler_m4_sweep.csv`
- `output/rossler_multistep.csv`
- `output/rossler_noise_filtering.csv`
- `../paper_chaos_aip/figures/fig_rossler_m4.pdf`
