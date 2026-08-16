# Sensibilidad de Ridge a lambda en Lorenz63

La validacion es temporal: el 80% inicial de cada ventana ajusta cada candidato, el 20% final selecciona y el punto OOS permanece fuera. Por ello este control evalua la fragilidad de la heuristica proporcional a la traza, no una supuesta inutilidad universal de Ridge.

|   lambda_relativa |   mae_validacion_mediana |   error_oos_mediana |   veces_seleccionada |   n |
|------------------:|-------------------------:|--------------------:|---------------------:|----:|
|            1e-08  |                0.0685006 |           0.081052  |                    2 |  14 |
|            1e-06  |                0.0684959 |           0.0809021 |                    5 |  14 |
|            0.0001 |                0.0685268 |           0.0722705 |                    6 |  14 |
|            0.001  |                0.0877967 |           0.08486   |                    0 |  14 |
|            0.01   |                0.153304  |           0.112455  |                    0 |  14 |
|            0.1    |                0.284388  |           0.181025  |                    1 |  14 |
|            1      |                0.480726  |           0.273036  |                    0 |  14 |
|           10      |                0.731286  |           0.692954  |                    0 |  14 |
|          100      |                0.822113  |           0.619717  |                    0 |  14 |

Lambda relativa seleccionada: 4 valores distintos en 14 ventanas. Mediana del error OOS de la seleccion nested: 0.0652062. Mediana con la heuristica fija 0.1: 0.181025.
