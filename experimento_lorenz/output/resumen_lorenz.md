# Lorenz63: kappa y pronostico OOS, limpio vs con shock sintetico

Shock: spike aditivo de 15.0 sigma en t=20000 (indice interno).

## kappa(cov(F)) por escenario

| escenario   | ventana_incluye_shock   |   kappa_raw_mediana |    kappa_raw_max |    n |
|:------------|:------------------------|--------------------:|-----------------:|-----:|
| con_shock   | False                   |         1.28436e+06 |      1.76534e+06 | 1450 |
| con_shock   | True                    |     50471.4         | 119382           |   25 |
| limpio      | False                   |         1.28703e+06 |      1.76534e+06 | 1475 |

## MASE OOS por escenario/metodo

| escenario   | mode   | ventana_incluye_shock   |   mase_mediana |    n |
|:------------|:-------|:------------------------|---------------:|-----:|
| con_shock   | naive  | False                   |      0.860922  | 1450 |
| con_shock   | naive  | True                    |      0.849714  |   25 |
| con_shock   | nnls   | False                   |      0.870654  | 1450 |
| con_shock   | nnls   | True                    |      1.19979   |   25 |
| con_shock   | ols    | False                   |      0.252214  | 1450 |
| con_shock   | ols    | True                    |      0.230864  |   25 |
| con_shock   | ridge  | False                   |      0.251206  | 1450 |
| con_shock   | ridge  | True                    |      0.342772  |   25 |
| con_shock   | ssrc   | False                   |      0.0891059 | 1450 |
| con_shock   | ssrc   | True                    |      0.270098  |   25 |
| limpio      | naive  | False                   |      0.861371  | 1475 |
| limpio      | nnls   | False                   |      0.873664  | 1475 |
| limpio      | ols    | False                   |      0.252346  | 1475 |
| limpio      | ridge  | False                   |      0.252189  | 1475 |
| limpio      | ssrc   | False                   |      0.0886293 | 1475 |

Ridge y el readout del SSRC seleccionan lambda mediante un holdout temporal interno. La heuristica 0.1*traza(X'X)/D queda solo como columna de auditoria y no determina el ajuste.
