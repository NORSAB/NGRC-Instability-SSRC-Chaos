# Hallazgo: κ(cov(F)) vs tamaño de ventana T — universo diario FX Latam + cripto

**Fecha:** 2026-08-12. Script: `run_kappa_vs_T.py`. Datos: Yahoo Finance (público, sin
autenticación), 10-15 años de historia diaria real por serie (3199-3905 cierres completos).
La barra UTC del día en curso se excluye porque puede estar abierta.

## Bug encontrado y corregido ANTES de reportar nada

Dos problemas invalidaban la primera corrida:

1. **Datos**: `range="max"` en el endpoint de Yahoo devuelve barras MENSUALES para pares FX
   sin avisar (274 puntos en 23 años). Corregido con `period1`/`period2` explícitos → 3199-3906
   puntos diarios reales por serie.
2. **Más importante — el mismo bug afecta el hallazgo "κ=∞" del experimento BCIE anual**:
   la columna constante (sesgo) del bloque NG-RC, al pasar por `np.cov` (que SIEMPRE centra
   cada columna restando su media), queda en varianza EXACTA cero tras centrar — eso fuerza
   κ=∞ **mecánicamente, sin importar T ni las demás columnas**. No es un hallazgo real, es un
   defecto del diagnóstico. Corregido excluyendo la columna constante antes de calcular
   covarianza (PCA no la necesita: el centrado ya absorbe la media). **Pendiente: aplicar la
   misma corrección al experimento BCIE anual** (`../experimento/EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md`,
   punto 1 de "qué se confirma") — la comparación de MASE de ese experimento NO se ve afectada
   (sklearn.PCA usa SVD y es robusto a la columna constante), solo el diagnóstico de κ.

## Resultado, ya corregido

Con datos diarios reales y el diagnóstico corregido, κ **es finito y razonable (5-50) para la
mayoría de series ya desde T=30**, muy por debajo del umbral de preocupación (100). Esto
confirma la intuición original: con miles de puntos, D=6-10 features del bloque NG-RC dejan
de competir por muestra.

**Pero apareció algo más interesante que la hipótesis original ("más datos = mejor
condicionado" no es monótono):**

| Serie | Patrón |
|---|---|
| MXN, BRL, COP (T≤1000), CLP (T≤1000), PEN, BTC, ETH | κ estable, 5-50, en TODA la grilla — el caso "limpio" |
| **ARS** | κ **se dispara a 25,000-30,000** en T=1000-3000 — un solo día con retorno log=0.78 (~118%, kurtosis=1402) domina la covarianza en cuanto la ventana lo incluye |
| **COP, CLP** | κ se dispara a 37,000-530,000 exactamente en T=3000 (ventana que alcanza a incluir el episodio 2015-16 de colapso del petróleo/commodities) |
| **GTQ** | para k=3 oscila entre 80 y 394 y vuelve a superar 100 en varias T; sigue siendo el caso persistente de peor condición entre las series sin los quiebres gigantes de ARS/COP/CLP |

## Por qué importa (esto SÍ es el hallazgo, más afilado que el original)

El mal condicionamiento de NG-RC **no es (solo) un problema de tamaño de muestra** — la
literatura (arXiv:2505.00846) lo prueba en Lorenz63, una serie larga y homogénea. Aquí, con
miles de puntos reales, el problema **reaparece exactamente cuando la ventana de
entrenamiento cruza un quiebre estructural o un evento extremo** (la devaluación del ARS,
el colapso de commodities de 2015-16 para COP/CLP): un solo día dominante estira un eigenvalor
mientras el resto de la dinámica (calma) comprime los demás — la firma clásica de mal
condicionamiento por outlier, no por escasez.

**Esto reconecta directamente con la pregunta original de SSRC** (robustez ante shocks) mejor
que la hipótesis de partida: el punto no es "¿hay suficientes datos?" sino "¿la regularización
protege específicamente la ventana que atraviesa el shock?" — testable con ARS 2018/2023 como
caso de estudio natural (evento documentado, kurtosis extrema, disponible en los mismos datos).

## Conexion con la prueba OOS ya corregida

La comparacion OOS se rehizo en `run_oos_univariado.py`. El lector de referencia es ahora un
SSRC realmente recurrente y el lambda de su readout se valida temporalmente. La prueba no
demuestra una ventaja del SSRC por QLIKE frente a EWMA o GARCH. Ademas, con paso=20 solo cinco
fechas objetivo quedaron clasificadas como shock; esa submuestra no permite una conclusion
fuerte sobre eventos extremos. Un estudio dirigido a ARS 2018/2023 sigue siendo una prueba
distinta y deberia usar paso diario alrededor de fechas preespecificadas.

## Archivos

- `run_kappa_vs_T.py` — script (autocontenido, no depende del pipeline BCIE).
- `output/kappa_vs_T.csv` — datos completos (9 series × 2 valores de k × 8 T).
- `output/kappa_vs_T_resumen.md` — tabla de T de cruce por serie.
