# Panel BCIE: compresión NG-RC sin fuga temporal

Código: `codigo_pipeline/run_ngrc_regularizado.py`. Copia aislada; no modifica el pipeline de
los artículos 2 o 3.

## Protocolo

Para cada entidad, en orden estricto: (1) el escalador del canal TCRA se ajusta solo con años
hasta 2019; (2) los estados NG-RC se construyen causalmente; (3) el escalador de
características, la covarianza y el lector se ajustan solo en train; (4) los objetos ya
ajustados se aplican a 2020-2025; (5) el operador de acoplamiento se estima con train y se
evalúa fuera de muestra. La columna constante no se estandariza; en NNLS se incorpora como
intercepto literal de unos. NNLS impone pesos no negativos, no una salida no negativa: las
características estandarizadas toman ambos signos.

## Resultados causales con cobertura propia

Datos BCIE en vivo; TCRA $W=3$, $\lambda=0.88$, train hasta 2019, OOS 2020-2025.

| Variante | k | MASE | NRMSE | Frob | n | entidades |
|---|---:|---:|---:|---:|---:|---:|
| Reservorio aleatorio, seed 7 | : | 1.0158 | 0.2828 | 0.8750 | 32 | 10 |
| NG-RC baseline PCA | 2 | 1.2928 | 0.1763 | 0.9947 | 32 | 9 |
| NG-RC baseline PCA | 3 | 1.2437 | 0.1730 | 0.9328 | 28 | 8 |
| NG-RC Ledoit-Wolf | 2 | 1.2928 | 0.1763 | 0.9947 | 32 | 9 |
| NG-RC Ledoit-Wolf | 3 | 1.2437 | 0.1730 | 0.9328 | 28 | 8 |
| NG-RC Tikhonov sobre covarianza | 2 | 1.2928 | 0.1763 | 0.9947 | 32 | 9 |
| NG-RC Tikhonov sobre covarianza | 3 | 1.2437 | 0.1730 | 0.9328 | 28 | 8 |
| NG-RC NNLS directo | 2 | **0.8181** | 0.1952 | 0.9692 | 32 | 9 |
| NG-RC NNLS directo | 3 | 0.8189 | 0.1940 | 0.9676 | 32 | 8 |

Baseline, Ledoit-Wolf y Tikhonov producen las mismas métricas para cada $k$ hasta precisión
numérica (diferencia máxima $3.4\times10^{-16}$): sumar $\lambda I$ no cambia los autovectores
exactos de una matriz simétrica, y Ledoit-Wolf hacia identidad pertenece a la misma familia
$aC+bI$. Las tres ramas usan la misma convención determinista de signo (carga de mayor
magnitud positiva, desempate por índice); un test automatizado confirma equivalencia de
componentes y embeddings hasta tolerancia numérica.

## Condicionamiento (solo en entrenamiento)

| Variante | k | κ crudo mediana | κ usado mediana | κ usado máximo |
|---|---:|---:|---:|---:|
| baseline | 2 | 6,601.13 | 6,601.13 | 3.93×10¹⁸⁰ |
| baseline | 3 | 28,459.46 | 28,459.46 | ∞ |
| Ledoit-Wolf | 2 | 6,601.13 | 8.91 | 3.93×10¹⁸⁰ |
| Ledoit-Wolf | 3 | 28,459.46 | 12.22 | 27.51 |
| Tikhonov sobre covarianza | 2 | 6,601.13 | 28.24 | 57.00 |
| Tikhonov sobre covarianza | 3 | 28,459.46 | 46.13 | 59.85 |
| NNLS directo | 2 | 6,601.13 | 81.25 | ∞ |
| NNLS directo | 3 | 28,459.46 | 168.70 | ∞ |

`tikhonov_covariance` designa exclusivamente $C_{train}+\lambda_{cov}I$: no es Ridge y no
regulariza los coeficientes de una regresión.

## Cobertura pareja

Intersección de las nueve configuraciones (8 entidades: BCIE Systemic Hub, Colombia, Costa
Rica, El Salvador, Guatemala, Honduras, Nicaragua, Panamá):

| Variante | k | MASE con cobertura pareja |
|---|---:|---:|
| Reservorio | : | 1.0356 |
| baseline | 2 | 1.3125 |
| baseline | 3 | 1.2437 |
| Ledoit-Wolf | 2 | 1.3125 |
| Ledoit-Wolf | 3 | 1.2437 |
| Tikhonov sobre covarianza | 2 | 1.3125 |
| Tikhonov sobre covarianza | 3 | 1.2437 |
| NNLS directo | 2 | **0.8155** |
| NNLS directo | 3 | 0.8189 |

## Inferencia emparejada sin pseudo-replicación

El diferencial de pérdida se promedia primero dentro de cada año y los años consecutivos se
tratan en bloques de longitud dos; el p-valor enumera exactamente todos los cambios de signo
posibles de esos bloques. Los errores se normalizan por el denominador MASE de cada embedding.
Con seis años OOS (tres bloques), el p-valor bilateral mínimo posible es 0.25. Ninguna de las
ocho comparaciones alcanza α=0.05; para NNLS k=2 y k=3, el p-valor exacto es 0.50 (pérdida
absoluta) y 1.00 (pérdida cuadrática). NNLS gana numéricamente en esta muestra, pero la escala
anual no permite sostener significancia estadística.

## Archivos

- `codigo_pipeline/temporal_transforms.py`: transformaciones causales compartidas.
- `codigo_pipeline/tests/test_temporal_no_leakage.py`: seis pruebas de no fuga, orientación e
  inferencia.
- `codigo_pipeline/output/ngrc_regularizado_comparison.csv`: resultados con cobertura propia.
- `codigo_pipeline/output/kappa_diagnostico.csv`: condicionamiento train-only.
- `codigo_pipeline/output/comparacion_cobertura_pareja.csv`: cobertura pareja e inferencia.
- `codigo_pipeline/output/kappa_entidad_detalle.csv`: diagnóstico por entidad.
