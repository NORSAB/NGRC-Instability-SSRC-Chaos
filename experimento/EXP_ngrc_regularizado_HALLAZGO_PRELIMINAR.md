# Experimento BCIE del Artículo 4: compresión NG-RC sin fuga temporal

Fecha de reejecución: 2026-08-13. Código: `codigo_pipeline/run_ngrc_regularizado.py`.
Esta es una copia aislada. No se modificó el pipeline de los artículos 2 o 3.

## Corrección metodológica

La corrida anterior ajustaba `StandardScaler`, PCA, Ledoit-Wolf y la covarianza de Tikhonov
con la serie completa. Por tanto, sus cifras, incluido el MASE 0.739 de NNLS directo, quedan
retiradas y no deben citarse. La implementación vigente sigue este orden para cada entidad:

1. ajusta el escalador del canal TCRA solo con años hasta 2019;
2. construye los estados NG-RC causalmente;
3. ajusta el escalador de características, la covarianza y el lector solo en train;
4. aplica los objetos ya ajustados a 2020-2025;
5. estima el operador de acoplamiento con train y evalúa fuera de muestra.

La columna constante no se estandariza. En NNLS se incorpora después como un intercepto
literal de unos. Las pruebas de regresión perturban únicamente el futuro y verifican que ni
los parámetros ajustados ni el embedding anterior al corte cambien.

NNLS impone pesos no negativos, no una salida no negativa. Las características
estandarizadas toman valores de ambos signos, de modo que $z_t$ y su pronóstico pueden ser
negativos. No se presenta este lector como un enlace de positividad.

## Resultados causales con cobertura propia

Datos BCIE descargados en vivo el 2026-08-13; TCRA $W=3$, $\lambda=0.88$, train hasta
2019 y OOS 2020-2025.

| Variante | k | MASE | NRMSE | Frob | n | entidades |
|---|---:|---:|---:|---:|---:|---:|
| Reservorio aleatorio, seed 7 | — | 1.0158 | 0.2828 | 0.8750 | 32 | 10 |
| NG-RC baseline PCA | 2 | 1.2928 | 0.1763 | 0.9947 | 32 | 9 |
| NG-RC baseline PCA | 3 | 1.2437 | 0.1730 | 0.9328 | 28 | 8 |
| NG-RC Ledoit-Wolf | 2 | 1.2928 | 0.1763 | 0.9947 | 32 | 9 |
| NG-RC Ledoit-Wolf | 3 | 1.2437 | 0.1730 | 0.9328 | 28 | 8 |
| NG-RC Tikhonov sobre covarianza | 2 | 1.2928 | 0.1763 | 0.9947 | 32 | 9 |
| NG-RC Tikhonov sobre covarianza | 3 | 1.2437 | 0.1730 | 0.9328 | 28 | 8 |
| NG-RC NNLS directo | 2 | **0.8181** | 0.1952 | 0.9692 | 32 | 9 |
| NG-RC NNLS directo | 3 | 0.8189 | 0.1940 | 0.9676 | 32 | 8 |

El NNLS directo conserva una ventaja numérica en MASE, pero la magnitud es menor que la
reportada con fuga. Baseline, Ledoit-Wolf y Tikhonov producen ahora las mismas métricas para
cada $k$ hasta precisión numérica (diferencia máxima $3.4\times10^{-16}$). La divergencia
extrema observada antes no era una mejora ni una
inestabilidad del shrinkage: provenía de orientar con signos distintos la misma dirección
principal antes de estimar el operador cuyos coeficientes se restringen a ser no negativos.

## Condicionamiento calculado solo en entrenamiento

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

`tikhonov_covariance` designa exclusivamente $C_{train}+\lambda_{cov}I$. No es Ridge y no
regulariza los coeficientes de una regresión. Además, sumar $\lambda I$ no cambia los
autovectores exactos de una matriz simétrica. Ledoit-Wolf hacia identidad pertenece a la
misma familia $aC+bI$ y tampoco cambia la dirección. Las tres ramas usan ahora la misma
convención determinista de signo: la carga de mayor magnitud se hace positiva, con desempate
por índice. El test automatizado confirma equivalencia de componentes y embeddings hasta
tolerancia numérica. Por eso no corresponde extrapolar desde este barrido a afirmaciones
sobre la sensibilidad del λ de un readout Ridge.

## Cobertura pareja

La intersección de las nueve configuraciones contiene ocho entidades: BCIE Systemic Hub,
Colombia, Costa Rica, El Salvador, Guatemala, Honduras, Nicaragua y Panamá.

| Variante | k | MASE con cobertura pareja |
|---|---:|---:|
| Reservorio | — | 1.0356 |
| baseline | 2 | 1.3125 |
| baseline | 3 | 1.2437 |
| Ledoit-Wolf | 2 | 1.3125 |
| Ledoit-Wolf | 3 | 1.2437 |
| Tikhonov sobre covarianza | 2 | 1.3125 |
| Tikhonov sobre covarianza | 3 | 1.2437 |
| NNLS directo | 2 | **0.8155** |
| NNLS directo | 3 | 0.8189 |

La ventaja numérica de NNLS no depende únicamente de una canasta más fácil. Sin embargo,
eso no basta para declarar superioridad estadística.

## Inferencia emparejada sin pseudo-replicación

La versión anterior apilaba entidad×año como si cada fila fuera iid. La versión vigente
promedia primero el diferencial de pérdida dentro de cada año y trata años consecutivos en
bloques de longitud dos. El p-valor enumera exactamente todos los cambios de signo posibles
de esos bloques.

Los errores se normalizan primero por el denominador MASE de cada embedding, porque los
objetivos latentes no comparten escala. Solo hay seis años OOS, equivalentes a tres bloques.
El p-valor bilateral mínimo posible es 0.25. Ninguna de las ocho comparaciones alcanza
α=0.05; para NNLS k=2 y k=3, el p-valor exacto es 0.50 con pérdida absoluta y 1.00 con
pérdida cuadrática. El resultado honesto es:
NNLS gana numéricamente en esta descarga, pero la muestra anual no permite sostener una
diferencia estadísticamente significativa.

## Archivos auditables

- `codigo_pipeline/temporal_transforms.py`: transformaciones causales compartidas.
- `codigo_pipeline/tests/test_temporal_no_leakage.py`: seis pruebas de no fuga, orientación e inferencia.
- `codigo_pipeline/output/ngrc_regularizado_comparison.csv`: resultados con cobertura propia.
- `codigo_pipeline/output/kappa_diagnostico.csv`: condicionamiento train-only.
- `codigo_pipeline/output/comparacion_cobertura_pareja.csv`: cobertura pareja e inferencia.
- `codigo_pipeline/output/kappa_entidad_detalle.csv`: diagnóstico por entidad.

Los archivos `*_REFERENCIA_original.py` permanecen intactos.
