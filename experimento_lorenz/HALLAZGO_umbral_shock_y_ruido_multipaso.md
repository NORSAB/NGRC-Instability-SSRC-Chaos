# Lorenz63: umbral del shock y pronóstico multipaso causal

## Umbral geométrico

El barrido extendido localiza la inversión del patrón κ shock/calma. La mediana de la razón es
2.1995 a 40 desviaciones estándar, 5.3211 a 50, 26.6085 a 75, 83.5737 a 100, 420.4373 a 150
y 1327.9881 a 200. En la grilla anterior, entre 5 y 30 desviaciones, todas las razones eran
menores que uno.

La transición es coherente con la estructura cuadrática del bloque NG-RC. Cuando el shock es
moderado, separa direcciones casi colineales; cuando es extremo, los productos cuadráticos
dominan y algunos términos de covarianza crecen como M^4. Esta es una propiedad de las
características y su covarianza, no una prueba de que Ridge sea universalmente frágil.

## Corrección del pronóstico multipaso

La versión anterior iniciaba la historia `K-1` posiciones demasiado atrás. Ahora, para el punto
exterior `t0`, la historia conocida es `x[t0:t0+K]`, cuyo último elemento es
`x[t0+K-1]`. Cada predicción se añade a esa historia.

En SSRC, el estado previo es el último estado observado antes de `t0`; cada paso pronosticado
actualiza causalmente `h` con `W_res`. No se reinicia el estado ni se consulta la trayectoria
verdadera futura. Ridge y el *readout* SSRC seleccionan λ dentro de la ventana exterior.

## Resultados

Mediana de MASE acumulada:

| H | σ ruido | Naive | NNLS | OLS | Ridge validado | SSRC recurrente |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.00 | 2.611949 | 2.529345 | 1.615064 | 1.546917 | **0.223310** |
| 5 | 0.05 | 2.487207 | 2.472640 | 1.778716 | 1.794292 | **0.403484** |
| 5 | 0.10 | 2.296232 | 2.298322 | 1.830582 | 1.841536 | **0.551168** |
| 5 | 0.20 | 1.833960 | 1.819635 | 1.557972 | 1.583287 | **0.685164** |
| 5 | 0.50 | 1.055681 | 0.963025 | 0.954165 | 0.964367 | **0.751622** |
| 10 | 0.00 | 3.479952 | 3.328130 | 2.392271 | 2.392788 | **0.500214** |
| 10 | 0.05 | 3.383836 | 3.230065 | 2.559172 | 2.572817 | **0.743137** |
| 10 | 0.10 | 3.108877 | 2.932032 | 2.469878 | 2.446364 | **0.901150** |
| 10 | 0.20 | 2.436548 | 2.232507 | 1.998604 | 2.000752 | **1.053848** |
| 10 | 0.50 | 1.325962 | 1.141699 | 1.143181 | 1.155600 | **0.936786** |

SSRC gana en los diez escenarios. La ventaja ya no puede atribuirse solo a una proyección
aleatoria acotada: el cálculo usa memoria recurrente real y `tanh`. Ridge supera ligeramente a
OLS en dos celdas y pierde por márgenes pequeños en las demás; no hay una dominancia estable
que justifique una afirmación universal en ningún sentido.

## Evidencia

- `run_lorenz_umbral_y_multipaso.py`
- `output/kappa_umbral_extendido.csv`
- `output/mase_ruido_multipaso.csv`
- `output/resumen_mase_ruido_multipaso.csv`
