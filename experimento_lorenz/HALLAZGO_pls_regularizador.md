# PLS(1) frente al bloque NG-RC completo en Lorenz63

PLS separa dos objetos matemáticos: sumar λI a una matriz de covarianza no cambia sus
eigenvectores, mientras que la λ de una regresión Ridge sí cambia los coeficientes. PLS añade
una tercera opción: una dirección supervisada por el objetivo.

## Protocolo

La trayectoria se normalizó con los primeros 500 puntos, sin estadísticas futuras. Ridge y el
*readout* del SSRC seleccionan λ por validación temporal interna; el SSRC usa `W_res` y un
estado secuencial real. PLS se ajusta únicamente con la ventana exterior de entrenamiento.

## Resultado en calma

| Lector | MASE mediana | MASE media |
|---|---:|---:|
| SSRC recurrente | **0.088629** | 0.118511 |
| Ridge con validación temporal | 0.252189 | 0.287276 |
| OLS | 0.252346 | 0.286127 |
| Naive | 0.861371 | 1.003408 |
| NNLS | 0.873664 | 1.007303 |
| PLS(1) | 1.995561 | 2.173376 |

PLS(1) pierde demasiada información al comprimir las nueve características NG-RC a una sola
dirección; la supervisión por el objetivo no compensa esa reducción. No superó a OLS en calma,
por lo que el protocolo predefinido omitió la fase de shock. El resultado es acotado: una sola
componente PLS no representa bien esta dinámica, mientras Ridge validado conserva el bloque
completo y empata con OLS.

## Evidencia

- `run_lorenz_pls.py`
- `output/mase_pls_cca.csv`
- `output/resumen_mase_pls_calma.csv`
