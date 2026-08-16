# Combustibles Honduras: validación causal secundaria

Transformaciones ajustadas solo con entrenamiento; Ridge y lectura SSRC seleccionan regularización mediante validación temporal interna. NNLS usa una base no negativa. Se incluyen EWMA, GARCH(1,1) y GJR-GARCH(1,1).

T_TRAIN=150, paso=4, k=3. Eventos: covid_2020: 2020-02-15-2020-05-15; eta_iota_2020: 2020-11-01-2020-12-21; ucrania_2022: 2022-02-15-2022-06-15; medio_oriente_2026: 2026-03-01-2026-06-30.

## Resultados por combustible, método y categoría

| fuel     | mode                   | categoria          |   mase_mediana |   qlike_mediana |   negativas_crudas |   n |
|:---------|:-----------------------|:-------------------|---------------:|----------------:|-------------------:|----:|
| Diesel   | ewma_094               | calma              |      0.652435  |      0.507718   |                  0 |  72 |
| Diesel   | ewma_094               | covid_2020         |      6.5695    |      0.846417   |                  0 |   4 |
| Diesel   | ewma_094               | eta_iota_2020      |      1.23565   |      0.790362   |                  0 |   2 |
| Diesel   | ewma_094               | medio_oriente_2026 |      4.39807   |      0.542453   |                  0 |   4 |
| Diesel   | ewma_094               | ucrania_2022       |      0.95554   |      0.253726   |                  0 |   4 |
| Diesel   | garch_11               | calma              |      0.466686  |      0.30991    |                  0 |  72 |
| Diesel   | garch_11               | covid_2020         |      8.13985   |      0.327822   |                  0 |   4 |
| Diesel   | garch_11               | eta_iota_2020      |      0.647713  |      0.114567   |                  0 |   2 |
| Diesel   | garch_11               | medio_oriente_2026 |      8.03718   |      2.69945    |                  0 |   4 |
| Diesel   | garch_11               | ucrania_2022       |      1.07544   |      0.39346    |                  0 |   4 |
| Diesel   | gjr_garch_11           | calma              |      0.45827   |      0.311374   |                  0 |  72 |
| Diesel   | gjr_garch_11           | covid_2020         |     12.3282    |      0.506657   |                  0 |   4 |
| Diesel   | gjr_garch_11           | eta_iota_2020      |      0.167226  |      0.0493029  |                  0 |   2 |
| Diesel   | gjr_garch_11           | medio_oriente_2026 |      8.03788   |      2.72678    |                  0 |   4 |
| Diesel   | gjr_garch_11           | ucrania_2022       |      1.02693   |      0.401767   |                  0 |   4 |
| Diesel   | naive                  | calma              |      0.340586  |      0.321898   |                  0 |  72 |
| Diesel   | naive                  | covid_2020         |      9.50378   |      0.402505   |                  0 |   4 |
| Diesel   | naive                  | eta_iota_2020      |      0.423183  |      0.0429943  |                  0 |   2 |
| Diesel   | naive                  | medio_oriente_2026 |      8.94503   |     17.2982     |                  0 |   4 |
| Diesel   | naive                  | ucrania_2022       |      1.78657   |      0.561787   |                  0 |   4 |
| Diesel   | ngrc_softplus_cv       | calma              |      0.42117   |      0.500651   |                  0 |  72 |
| Diesel   | ngrc_softplus_cv       | covid_2020         |      8.24067   |      0.468106   |                  0 |   4 |
| Diesel   | ngrc_softplus_cv       | eta_iota_2020      |      0.749111  |      0.603868   |                  0 |   2 |
| Diesel   | ngrc_softplus_cv       | medio_oriente_2026 |      1.35136   |      0.0853217  |                  0 |   4 |
| Diesel   | ngrc_softplus_cv       | ucrania_2022       |      1.5084    |      0.461532   |                  0 |   4 |
| Diesel   | nnls_base_no_negativa  | calma              |      0.476381  |      0.388777   |                  0 |  72 |
| Diesel   | nnls_base_no_negativa  | covid_2020         |      8.13474   |      0.276171   |                  0 |   4 |
| Diesel   | nnls_base_no_negativa  | eta_iota_2020      |      0.618848  |      0.223768   |                  0 |   2 |
| Diesel   | nnls_base_no_negativa  | medio_oriente_2026 |      8.22368   |     15.9393     |                  0 |   4 |
| Diesel   | nnls_base_no_negativa  | ucrania_2022       |      1.0625    |      0.280166   |                  0 |   4 |
| Diesel   | ols_clip_legacy        | calma              |      0.464394  |      0.43265    |                  6 |  72 |
| Diesel   | ols_clip_legacy        | covid_2020         |      8.23893   |      0.509188   |                  0 |   4 |
| Diesel   | ols_clip_legacy        | eta_iota_2020      |      0.208611  |      0.0115104  |                  0 |   2 |
| Diesel   | ols_clip_legacy        | medio_oriente_2026 |      7.9986    |      0.228937   |                  0 |   4 |
| Diesel   | ols_clip_legacy        | ucrania_2022       |      1.40639   |      0.29545    |                  0 |   4 |
| Diesel   | ridge_cv_clip          | calma              |      0.481827  |      0.452239   |                  1 |  72 |
| Diesel   | ridge_cv_clip          | covid_2020         |      8.14187   |      0.364757   |                  0 |   4 |
| Diesel   | ridge_cv_clip          | eta_iota_2020      |      0.723275  |      0.592829   |                  0 |   2 |
| Diesel   | ridge_cv_clip          | medio_oriente_2026 |      1.35821   |      0.0897159  |                  0 |   4 |
| Diesel   | ridge_cv_clip          | ucrania_2022       |      1.50916   |      0.462403   |                  0 |   4 |
| Diesel   | ridge_log_cv           | calma              |      0.311164  |      2.9646     |                  0 |  72 |
| Diesel   | ridge_log_cv           | covid_2020         |    305.105     |      4.07578    |                  0 |   4 |
| Diesel   | ridge_log_cv           | eta_iota_2020      |      1.03854   |      0.900609   |                  0 |   2 |
| Diesel   | ridge_log_cv           | medio_oriente_2026 |      6.13785   |      5.50629    |                  0 |   4 |
| Diesel   | ridge_log_cv           | ucrania_2022       |      2.62154   |      9.28297    |                  0 |   4 |
| Diesel   | ssrc_recurrente_log_cv | calma              |      0.341987  |      1.8456     |                  0 |  72 |
| Diesel   | ssrc_recurrente_log_cv | covid_2020         |      7.53829   |      6.96234    |                  0 |   4 |
| Diesel   | ssrc_recurrente_log_cv | eta_iota_2020      |      0.345772  |      0.443785   |                  0 |   2 |
| Diesel   | ssrc_recurrente_log_cv | medio_oriente_2026 |      5.02118   |      4.53688    |                  0 |   4 |
| Diesel   | ssrc_recurrente_log_cv | ucrania_2022       |      1.93318   |      5.52625    |                  0 |   4 |
| Kerosene | ewma_094               | calma              |      0.705797  |      0.795255   |                  0 |  72 |
| Kerosene | ewma_094               | covid_2020         |      9.53949   |      1.25055    |                  0 |   4 |
| Kerosene | ewma_094               | eta_iota_2020      |      1.06065   |      2.79279    |                  0 |   2 |
| Kerosene | ewma_094               | medio_oriente_2026 |      3.83335   |      0.355151   |                  0 |   4 |
| Kerosene | ewma_094               | ucrania_2022       |      1.40386   |      0.944786   |                  0 |   4 |
| Kerosene | garch_11               | calma              |      0.49219   |      0.347401   |                  0 |  72 |
| Kerosene | garch_11               | covid_2020         |      7.76537   |      0.430845   |                  0 |   4 |
| Kerosene | garch_11               | eta_iota_2020      |      0.38098   |      1.65848    |                  0 |   2 |
| Kerosene | garch_11               | medio_oriente_2026 |     11.0731    |      0.283417   |                  0 |   4 |
| Kerosene | garch_11               | ucrania_2022       |      2.7284    |      0.935204   |                  0 |   4 |
| Kerosene | gjr_garch_11           | calma              |      0.44134   |      0.369347   |                  0 |  72 |
| Kerosene | gjr_garch_11           | covid_2020         |     10.4545    |      0.616691   |                  0 |   4 |
| Kerosene | gjr_garch_11           | eta_iota_2020      |      0.153594  |      1.57648    |                  0 |   2 |
| Kerosene | gjr_garch_11           | medio_oriente_2026 |     11.0772    |      0.283524   |                  0 |   4 |
| Kerosene | gjr_garch_11           | ucrania_2022       |      2.92821   |      1.22601    |                  0 |   4 |
| Kerosene | naive                  | calma              |      0.335227  |      0.407436   |                  0 |  72 |
| Kerosene | naive                  | covid_2020         |     10.8219    |      0.641091   |                  0 |   4 |
| Kerosene | naive                  | eta_iota_2020      |      0.298518  |      0.873159   |                  0 |   2 |
| Kerosene | naive                  | medio_oriente_2026 |     12.0537    |      1.32318    |                  0 |   4 |
| Kerosene | naive                  | ucrania_2022       |      2.42704   |      1.43393    |                  0 |   4 |
| Kerosene | ngrc_softplus_cv       | calma              |      0.647863  |      0.476604   |                  0 |  72 |
| Kerosene | ngrc_softplus_cv       | covid_2020         |      8.96967   |      0.214219   |                  0 |   4 |
| Kerosene | ngrc_softplus_cv       | eta_iota_2020      |      0.968233  |      2.61816    |                  0 |   2 |
| Kerosene | ngrc_softplus_cv       | medio_oriente_2026 |      4.24733   |      1.27557    |                  0 |   4 |
| Kerosene | ngrc_softplus_cv       | ucrania_2022       |      1.50198   |      0.491587   |                  0 |   4 |
| Kerosene | nnls_base_no_negativa  | calma              |      0.496005  |      0.269416   |                  0 |  72 |
| Kerosene | nnls_base_no_negativa  | covid_2020         |     10.0919    |      0.55928    |                  0 |   4 |
| Kerosene | nnls_base_no_negativa  | eta_iota_2020      |      0.534449  |      1.8278     |                  0 |   2 |
| Kerosene | nnls_base_no_negativa  | medio_oriente_2026 |      1.60517   |      0.706843   |                  0 |   4 |
| Kerosene | nnls_base_no_negativa  | ucrania_2022       |      2.59687   |      1.40866    |                  0 |   4 |
| Kerosene | ols_clip_legacy        | calma              |      0.570081  |      0.515781   |                  2 |  72 |
| Kerosene | ols_clip_legacy        | covid_2020         |      8.91638   |      1.00829    |                  0 |   4 |
| Kerosene | ols_clip_legacy        | eta_iota_2020      |      0.0893606 |     59.5731     |                  1 |   2 |
| Kerosene | ols_clip_legacy        | medio_oriente_2026 |      6.69009   |      0.967647   |                  0 |   4 |
| Kerosene | ols_clip_legacy        | ucrania_2022       |      2.06541   |      0.525327   |                  0 |   4 |
| Kerosene | ridge_cv_clip          | calma              |      0.686182  |      0.506028   |                  0 |  72 |
| Kerosene | ridge_cv_clip          | covid_2020         |      8.46007   |      0.237189   |                  0 |   4 |
| Kerosene | ridge_cv_clip          | eta_iota_2020      |      0.871786  |      2.57618    |                  0 |   2 |
| Kerosene | ridge_cv_clip          | medio_oriente_2026 |      4.72328   |      1.30096    |                  0 |   4 |
| Kerosene | ridge_cv_clip          | ucrania_2022       |      1.21106   |      0.337273   |                  0 |   4 |
| Kerosene | ridge_log_cv           | calma              |      0.369863  |      1.56067    |                  0 |  72 |
| Kerosene | ridge_log_cv           | covid_2020         |     11.1682    |      3.42242    |                  0 |   4 |
| Kerosene | ridge_log_cv           | eta_iota_2020      |      1.01052   |      7.65068    |                  0 |   2 |
| Kerosene | ridge_log_cv           | medio_oriente_2026 |      3.01093   |     16.0162     |                  0 |   4 |
| Kerosene | ridge_log_cv           | ucrania_2022       |      1.52887   |      2.84941    |                  0 |   4 |
| Kerosene | ssrc_recurrente_log_cv | calma              |      0.360696  |      1.07224    |                  0 |  72 |
| Kerosene | ssrc_recurrente_log_cv | covid_2020         |     12.7415    |      3.82657    |                  0 |   4 |
| Kerosene | ssrc_recurrente_log_cv | eta_iota_2020      |      0.940635  |      4.17353    |                  0 |   2 |
| Kerosene | ssrc_recurrente_log_cv | medio_oriente_2026 |      2.46002   |      2.46081    |                  0 |   4 |
| Kerosene | ssrc_recurrente_log_cv | ucrania_2022       |      1.42937   |      5.79516    |                  0 |   4 |
| Regular  | ewma_094               | calma              |      0.648351  |      0.73949    |                  0 |  72 |
| Regular  | ewma_094               | covid_2020         |      8.47053   |      0.705619   |                  0 |   4 |
| Regular  | ewma_094               | eta_iota_2020      |      1.08664   |      1.32944    |                  0 |   2 |
| Regular  | ewma_094               | medio_oriente_2026 |      5.78232   |      0.602077   |                  0 |   4 |
| Regular  | ewma_094               | ucrania_2022       |      0.668858  |      0.0933094  |                  0 |   4 |
| Regular  | garch_11               | calma              |      0.344732  |      0.464204   |                  0 |  72 |
| Regular  | garch_11               | covid_2020         |      1.39484   |      0.376937   |                  0 |   4 |
| Regular  | garch_11               | eta_iota_2020      |      0.328592  |      0.519022   |                  0 |   2 |
| Regular  | garch_11               | medio_oriente_2026 |      3.8704    |      0.692992   |                  0 |   4 |
| Regular  | garch_11               | ucrania_2022       |      0.318175  |      0.0310293  |                  0 |   4 |
| Regular  | gjr_garch_11           | calma              |      0.356241  |      0.535165   |                  0 |  72 |
| Regular  | gjr_garch_11           | covid_2020         |      6.70013   |      0.641779   |                  0 |   4 |
| Regular  | gjr_garch_11           | eta_iota_2020      |      0.2727    |      0.525185   |                  0 |   2 |
| Regular  | gjr_garch_11           | medio_oriente_2026 |      3.86886   |      0.693372   |                  0 |   4 |
| Regular  | gjr_garch_11           | ucrania_2022       |      0.318173  |      0.031029   |                  0 |   4 |
| Regular  | naive                  | calma              |      0.275653  |      0.580475   |                  0 |  72 |
| Regular  | naive                  | covid_2020         |      7.96222   |      0.56002    |                  0 |   4 |
| Regular  | naive                  | eta_iota_2020      |      0.218244  |      0.289215   |                  0 |   2 |
| Regular  | naive                  | medio_oriente_2026 |      5.59283   |      0.252825   |                  0 |   4 |
| Regular  | naive                  | ucrania_2022       |      0.35263   |      0.0389943  |                  0 |   4 |
| Regular  | ngrc_softplus_cv       | calma              |      0.780779  |      0.866661   |                  0 |  72 |
| Regular  | ngrc_softplus_cv       | covid_2020         |      7.54669   |    227.684      |                  0 |   4 |
| Regular  | ngrc_softplus_cv       | eta_iota_2020      |      0.864143  |      1.21534    |                  0 |   2 |
| Regular  | ngrc_softplus_cv       | medio_oriente_2026 |      6.81486   |      0.849249   |                  0 |   4 |
| Regular  | ngrc_softplus_cv       | ucrania_2022       |      0.579435  |      0.167424   |                  0 |   4 |
| Regular  | nnls_base_no_negativa  | calma              |      0.460246  |      0.430912   |                  0 |  72 |
| Regular  | nnls_base_no_negativa  | covid_2020         |      7.25178   |      0.145948   |                  0 |   4 |
| Regular  | nnls_base_no_negativa  | eta_iota_2020      |      0.584704  |      0.681238   |                  0 |   2 |
| Regular  | nnls_base_no_negativa  | medio_oriente_2026 |      6.19634   |      0.460449   |                  0 |   4 |
| Regular  | nnls_base_no_negativa  | ucrania_2022       |      0.141181  |      0.00467785 |                  0 |   4 |
| Regular  | ols_clip_legacy        | calma              |      0.418509  |      1.11871    |                 17 |  72 |
| Regular  | ols_clip_legacy        | covid_2020         |      7.34283   |      8.67055    |                  1 |   4 |
| Regular  | ols_clip_legacy        | eta_iota_2020      |      0.154036  |   1168.98       |                  1 |   2 |
| Regular  | ols_clip_legacy        | medio_oriente_2026 |      6.02049   |      0.455167   |                  0 |   4 |
| Regular  | ols_clip_legacy        | ucrania_2022       |      0.432227  |      0.0699075  |                  0 |   4 |
| Regular  | ridge_cv_clip          | calma              |      0.706451  |      0.950592   |                  0 |  72 |
| Regular  | ridge_cv_clip          | covid_2020         |      7.57618   |   2185.79       |                  1 |   4 |
| Regular  | ridge_cv_clip          | eta_iota_2020      |      0.878948  |      1.22615    |                  0 |   2 |
| Regular  | ridge_cv_clip          | medio_oriente_2026 |      6.48824   |      0.622469   |                  0 |   4 |
| Regular  | ridge_cv_clip          | ucrania_2022       |      0.578609  |      0.162235   |                  0 |   4 |
| Regular  | ridge_log_cv           | calma              |      0.183201  |      1.18718    |                  0 |  72 |
| Regular  | ridge_log_cv           | covid_2020         |      7.84403   |     13.488      |                  0 |   4 |
| Regular  | ridge_log_cv           | eta_iota_2020      |      0.268829  |      0.977259   |                  0 |   2 |
| Regular  | ridge_log_cv           | medio_oriente_2026 |      7.15194   |      2.5482     |                  0 |   4 |
| Regular  | ridge_log_cv           | ucrania_2022       |      1.03128   |      4.26419    |                  0 |   4 |
| Regular  | ssrc_recurrente_log_cv | calma              |      0.166999  |      0.926871   |                  0 |  72 |
| Regular  | ssrc_recurrente_log_cv | covid_2020         |      7.31218   |      5.89569    |                  0 |   4 |
| Regular  | ssrc_recurrente_log_cv | eta_iota_2020      |      0.263854  |      1.20581    |                  0 |   2 |
| Regular  | ssrc_recurrente_log_cv | medio_oriente_2026 |      5.2213    |      5.08351    |                  0 |   4 |
| Regular  | ssrc_recurrente_log_cv | ucrania_2022       |      1.08394   |      2.99947    |                  0 |   4 |
| Súper    | ewma_094               | calma              |      0.644949  |      0.78627    |                  0 |  72 |
| Súper    | ewma_094               | covid_2020         |      6.17355   |      0.993894   |                  0 |   4 |
| Súper    | ewma_094               | eta_iota_2020      |      0.851915  |      0.867996   |                  0 |   2 |
| Súper    | ewma_094               | medio_oriente_2026 |      3.05599   |      0.598642   |                  0 |   4 |
| Súper    | ewma_094               | ucrania_2022       |      0.701934  |      0.0667679  |                  0 |   4 |
| Súper    | garch_11               | calma              |      0.379859  |      0.379594   |                  0 |  72 |
| Súper    | garch_11               | covid_2020         |      2.02534   |      0.710013   |                  0 |   4 |
| Súper    | garch_11               | eta_iota_2020      |      0.227385  |      0.273004   |                  0 |   2 |
| Súper    | garch_11               | medio_oriente_2026 |      7.57362   |      0.741221   |                  0 |   4 |
| Súper    | garch_11               | ucrania_2022       |      0.419837  |      0.062752   |                  0 |   4 |
| Súper    | gjr_garch_11           | calma              |      0.373051  |      0.37957    |                  0 |  72 |
| Súper    | gjr_garch_11           | covid_2020         |      5.80509   |      0.86523    |                  0 |   4 |
| Súper    | gjr_garch_11           | eta_iota_2020      |      0.170716  |      0.318464   |                  0 |   2 |
| Súper    | gjr_garch_11           | medio_oriente_2026 |      7.74746   |      0.80783    |                  0 |   4 |
| Súper    | gjr_garch_11           | ucrania_2022       |      0.41966   |      0.0627218  |                  0 |   4 |
| Súper    | naive                  | calma              |      0.311417  |      0.50532    |                  0 |  72 |
| Súper    | naive                  | covid_2020         |      6.398     |      1.29668    |                  0 |   4 |
| Súper    | naive                  | eta_iota_2020      |      0.12437   |      0.14809    |                  0 |   2 |
| Súper    | naive                  | medio_oriente_2026 |      6.44701   |      0.626081   |                  0 |   4 |
| Súper    | naive                  | ucrania_2022       |      0.519943  |      0.057687   |                  0 |   4 |
| Súper    | ngrc_softplus_cv       | calma              |      0.663507  |      0.62965    |                  0 |  72 |
| Súper    | ngrc_softplus_cv       | covid_2020         |      5.13613   |  35761.3        |                  0 |   4 |
| Súper    | ngrc_softplus_cv       | eta_iota_2020      |      0.682813  |      0.821605   |                  0 |   2 |
| Súper    | ngrc_softplus_cv       | medio_oriente_2026 |      8.77424   |      1.23379    |                  0 |   4 |
| Súper    | ngrc_softplus_cv       | ucrania_2022       |      0.958948  |      0.231374   |                  0 |   4 |
| Súper    | nnls_base_no_negativa  | calma              |      0.391936  |      0.36408    |                  0 |  72 |
| Súper    | nnls_base_no_negativa  | covid_2020         |      5.32794   |      0.483028   |                  0 |   4 |
| Súper    | nnls_base_no_negativa  | eta_iota_2020      |      0.417777  |      0.312034   |                  0 |   2 |
| Súper    | nnls_base_no_negativa  | medio_oriente_2026 |      7.30559   |      0.77389    |                  0 |   4 |
| Súper    | nnls_base_no_negativa  | ucrania_2022       |      0.530564  |      0.116759   |                  0 |   4 |
| Súper    | ols_clip_legacy        | calma              |      0.418404  |      0.698552   |                 17 |  72 |
| Súper    | ols_clip_legacy        | covid_2020         |      5.03338   |      5.84095    |                  1 |   4 |
| Súper    | ols_clip_legacy        | eta_iota_2020      |      0.166649  |   2105.3        |                  1 |   2 |
| Súper    | ols_clip_legacy        | medio_oriente_2026 |      5.29504   |      0.351441   |                  0 |   4 |
| Súper    | ols_clip_legacy        | ucrania_2022       |      0.648456  |      0.0942559  |                  0 |   4 |
| Súper    | ridge_cv_clip          | calma              |      0.739312  |      0.662836   |                  0 |  72 |
| Súper    | ridge_cv_clip          | covid_2020         |      5.03338   |      5.84094    |                  1 |   4 |
| Súper    | ridge_cv_clip          | eta_iota_2020      |      0.681584  |      0.818494   |                  0 |   2 |
| Súper    | ridge_cv_clip          | medio_oriente_2026 |      9.11335   |      1.60554    |                  0 |   4 |
| Súper    | ridge_cv_clip          | ucrania_2022       |      0.912525  |      0.254789   |                  0 |   4 |
| Súper    | ridge_log_cv           | calma              |      0.248592  |      1.06629    |                  0 |  72 |
| Súper    | ridge_log_cv           | covid_2020         |      5.25029   |      8.03116    |                  0 |   4 |
| Súper    | ridge_log_cv           | eta_iota_2020      |      0.444379  |      1.06295    |                  0 |   2 |
| Súper    | ridge_log_cv           | medio_oriente_2026 |      7.46794   |      1.72027    |                  0 |   4 |
| Súper    | ridge_log_cv           | ucrania_2022       |      1.87251   |     12.1171     |                  0 |   4 |
| Súper    | ssrc_recurrente_log_cv | calma              |      0.266215  |      0.997661   |                  0 |  72 |
| Súper    | ssrc_recurrente_log_cv | covid_2020         |      5.31503   |     17.327      |                  0 |   4 |
| Súper    | ssrc_recurrente_log_cv | eta_iota_2020      |      0.455365  |      1.34979    |                  0 |   2 |
| Súper    | ssrc_recurrente_log_cv | medio_oriente_2026 |      2.76613   |     17.0892     |                  0 |   4 |
| Súper    | ssrc_recurrente_log_cv | ucrania_2022       |      1.83513   |      3.19666    |                  0 |   4 |

## Sensibilidad de QLIKE al piso

| mode                   |   multiplicador_piso |    qlike |
|:-----------------------|---------------------:|---------:|
| ewma_094               |               1e-06  | 0.676554 |
| ewma_094               |               0.0001 | 0.676554 |
| ewma_094               |               0.01   | 0.676554 |
| garch_11               |               1e-06  | 0.379594 |
| garch_11               |               0.0001 | 0.379594 |
| garch_11               |               0.01   | 0.379594 |
| gjr_garch_11           |               1e-06  | 0.392152 |
| gjr_garch_11           |               0.0001 | 0.392152 |
| gjr_garch_11           |               0.01   | 0.392152 |
| naive                  |               1e-06  | 0.432279 |
| naive                  |               0.0001 | 0.432279 |
| naive                  |               0.01   | 0.408985 |
| ngrc_softplus_cv       |               1e-06  | 0.570206 |
| ngrc_softplus_cv       |               0.0001 | 0.570206 |
| ngrc_softplus_cv       |               0.01   | 0.570206 |
| nnls_base_no_negativa  |               1e-06  | 0.358875 |
| nnls_base_no_negativa  |               0.0001 | 0.358875 |
| nnls_base_no_negativa  |               0.01   | 0.358875 |
| ols_clip_legacy        |               1e-06  | 0.541826 |
| ols_clip_legacy        |               0.0001 | 0.541826 |
| ols_clip_legacy        |               0.01   | 0.502465 |
| ridge_cv_clip          |               1e-06  | 0.551891 |
| ridge_cv_clip          |               0.0001 | 0.551891 |
| ridge_cv_clip          |               0.01   | 0.551891 |
| ridge_log_cv           |               1e-06  | 1.81467  |
| ridge_log_cv           |               0.0001 | 1.81467  |
| ridge_log_cv           |               0.01   | 1.7562   |
| ssrc_recurrente_log_cv |               1e-06  | 1.31347  |
| ssrc_recurrente_log_cv |               0.0001 | 1.31347  |
| ssrc_recurrente_log_cv |               0.01   | 1.27336  |

Ajustes fallidos registrados: 0.
