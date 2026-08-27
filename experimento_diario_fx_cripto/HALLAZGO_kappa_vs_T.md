# κ(cov(F)) vs tamaño de ventana T: universo diario FX Latam + cripto

**Script:** `run_kappa_vs_T.py`. **Datos:** Yahoo Finance, 10-15 años de historia diaria real
por serie (3199-3906 puntos por serie; la barra UTC del día en curso se excluye porque puede
estar abierta). La columna constante del bloque NG-RC se excluye antes de calcular covarianza,
ya que `np.cov` centra cada columna y forzaría κ=∞ mecánicamente sin importar T.

## Resultado

Con datos diarios reales, κ es finito y razonable (5-50) para la mayoría de series ya desde
T=30, muy por debajo del umbral de preocupación (100). Con miles de puntos, las D=6-10
características del bloque NG-RC dejan de competir por muestra.

| Serie | Patrón |
|---|---|
| MXN, BRL, COP (T≤1000), CLP (T≤1000), PEN, BTC, ETH | κ estable, 5-50, en toda la grilla |
| ARS | κ se dispara a 25,000-30,000 en T=1000-3000: un día con retorno log=0.78 (~118%, kurtosis=1402) domina la covarianza al entrar en la ventana |
| COP, CLP | κ se dispara a 37,000-530,000 exactamente en T=3000 (ventana que alcanza el episodio 2015-16 de colapso de commodities) |
| GTQ | para k=3 oscila entre 80 y 394 y vuelve a superar 100 en varias T; peor condición persistente entre las series sin quiebres grandes |

## Interpretación

El mal condicionamiento de NG-RC no es solo un problema de tamaño de muestra: con miles de
puntos reales, reaparece exactamente cuando la ventana de entrenamiento cruza un quiebre
estructural o un evento extremo (devaluación del ARS, colapso de commodities 2015-16 para
COP/CLP). Un solo día dominante estira un eigenvalor mientras el resto de la dinámica en calma
comprime los demás: la firma de mal condicionamiento por outlier, no por escasez.

Esto conecta con la pregunta de robustez ante shocks del SSRC: el punto no es si hay
suficientes datos, sino si la regularización protege específicamente la ventana que atraviesa
el shock. ARS 2018/2023 es un caso de estudio natural (evento documentado, kurtosis extrema,
disponible en los mismos datos).

## Conexión con la prueba OOS

La comparación OOS (`run_oos_univariado.py`) usa un lector de referencia SSRC realmente
recurrente con λ validada temporalmente; no muestra ventaja del SSRC por QLIKE frente a EWMA o
GARCH. Con paso=20, solo cinco fechas objetivo quedaron clasificadas como shock, submuestra
insuficiente para una conclusión fuerte sobre eventos extremos.

## Archivos

- `run_kappa_vs_T.py`: script autocontenido.
- `output/kappa_vs_T.csv`: datos completos (9 series × 2 valores de k × 8 T).
- `output/kappa_vs_T_resumen.md`: tabla de T de cruce por serie.
