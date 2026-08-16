# OOS univariado causal: calma y shocks

Los modelos `legacy` o `clip` no garantizan positividad estructural. `ssrc_log` es recurrente y su readout usa lambda validado temporalmente.

| mode                    | categoria        |   mase_mediana |    mase_media |   qlike_mediana |      qlike_media |   pct_pred_negativa_cruda |   n |
|:------------------------|:-----------------|---------------:|--------------:|----------------:|-----------------:|--------------------------:|----:|
| ewma_0.94               | ambos            |     90.3212    |  90.3212      |       9.20547   |      9.20547     |                0          |   2 |
| ewma_0.94               | calma_total      |      0.521035  |   0.877066    |       0.942566  |      1.91953     |                0          | 801 |
| ewma_0.94               | test_es_shock    |     88.9881    |  77.3232      |      57.9567    |    102.464       |                0          |   3 |
| ewma_0.94               | train_tuvo_shock |      0.351634  |   0.957184    |       1.42505   |      2.53502     |                0          | 679 |
| garch_11                | ambos            |     32.3036    |  32.3036      |       0.689487  |      0.689487    |                0          |   2 |
| garch_11                | calma_total      |      0.541903  |   0.887401    |       0.965936  |      1.8655      |                0          | 801 |
| garch_11                | test_es_shock    |     89.0491    |  77.3051      |      60.7174    |     88.3328      |                0          |   3 |
| garch_11                | train_tuvo_shock |      0.500446  |   0.924287    |       1.89424   |      3.15184     |                0          | 676 |
| gjr_garch_11            | ambos            |     37.3648    |  37.3648      |      19.2426    |     19.2426      |                0          |   2 |
| gjr_garch_11            | calma_total      |      0.533234  |   0.872859    |       0.980607  |      1.86961     |                0          | 801 |
| gjr_garch_11            | test_es_shock    |     89.0491    |  77.3357      |      60.7173    |     86.1114      |                0          |   3 |
| gjr_garch_11            | train_tuvo_shock |      0.497963  |   0.924199    |       1.88765   |      3.08945     |                0          | 676 |
| log_ridge               | ambos            |     97.2952    |  97.2952      |    1534.08      |   1534.08        |                0          |   2 |
| log_ridge               | calma_total      |      0.134136  |   0.774266    |       1.50476   |      6.56042     |                0          | 801 |
| log_ridge               | test_es_shock    |     90.0836    |  78.0821      |     266.492     |    638.517       |                0          |   3 |
| log_ridge               | train_tuvo_shock |      0.0545104 |   7.61821e+22 |       1.56966   |   1702.3         |                0          | 679 |
| naive                   | ambos            |      5.52449   |   5.52449     |       0.0136556 |      0.0136556   |                0          |   2 |
| naive                   | calma_total      |      0.349272  |   1.03765     |       1.87672   |  11019.2         |                0          | 801 |
| naive                   | test_es_shock    |     88.0161    |  77.3667      |     108.349     |      1.55762e+06 |                0          |   3 |
| naive                   | train_tuvo_shock |      0.0957513 |   1.27434     |       1.65912   |  11929.7         |                0          | 679 |
| nnls_nonneg             | ambos            |     77.2141    |  77.2141      |       3.23498   |      3.23498     |                0          |   2 |
| nnls_nonneg             | calma_total      |      0.572445  |   0.915383    |       1.02759   |      1.9636      |                0          | 801 |
| nnls_nonneg             | test_es_shock    |     89.2577    |  77.5145      |      72.3693    |    127.777       |                0          |   3 |
| nnls_nonneg             | train_tuvo_shock |      0.477719  |   0.880719    |       2.11892   |      3.38789     |                0          | 679 |
| nnls_signed_clip_legacy | ambos            |     38.3307    |  38.3307      |       0.126868  |      0.126868    |                0          |   2 |
| nnls_signed_clip_legacy | calma_total      |      0.563675  |   0.894907    |       1.00874   |    150.841       |                0.0062422  | 801 |
| nnls_signed_clip_legacy | test_es_shock    |     89.3703    |  77.5306      |      80.5997    |    116.526       |                0          |   3 |
| nnls_signed_clip_legacy | train_tuvo_shock |      0.501949  |   2.13346     |       2.23571   |  42979.5         |                0.0397644  | 679 |
| ols_clip_legacy         | ambos            |     40.3005    |  40.3005      |       0.166419  |      0.166419    |                0          |   2 |
| ols_clip_legacy         | calma_total      |      0.561921  |   0.885577    |       0.953674  |    247.529       |                0.0062422  | 801 |
| ols_clip_legacy         | test_es_shock    |     89.4344    |  77.5595      |      86.1257    |    115.41        |                0          |   3 |
| ols_clip_legacy         | train_tuvo_shock |      0.490456  |   2.34027     |       2.37399   |  45685.7         |                0.083947   | 679 |
| ridge_clip              | ambos            |     76.9604    |  76.9604      |      18.3475    |     18.3475      |                0          |   2 |
| ridge_clip              | calma_total      |      0.606547  |   0.898433    |       1.01054   |     33.4518      |                0.00124844 | 801 |
| ridge_clip              | test_es_shock    |     89.6191    |  77.577       |     107.032     |    119.131       |                0          |   3 |
| ridge_clip              | train_tuvo_shock |      0.619201  |   0.896603    |       2.13739   |  10100.6         |                0.0132548  | 679 |
| softplus_ridge          | ambos            |     76.7195    |  76.7195      |      19.8098    |     19.8098      |                0          |   2 |
| softplus_ridge          | calma_total      |      0.422304  |   0.821034    |       1.08      |     33.6075      |                0          | 801 |
| softplus_ridge          | test_es_shock    |     89.7587    |  77.6847      |     130.592     |    129.758       |                0          |   3 |
| softplus_ridge          | train_tuvo_shock |      0.505662  |   0.854682    |       2.27491   |   5332.15        |                0          | 679 |
| ssrc_log                | ambos            |     97.3352    |  97.3352      |  168995         | 168995           |                0          |   2 |
| ssrc_log                | calma_total      |      0.13935   |   0.777083    |       1.48892   |      6.62281     |                0          | 801 |
| ssrc_log                | test_es_shock    |     90.2123    |  78.1238      |     426.016     |    682.533       |                0          |   3 |
| ssrc_log                | train_tuvo_shock |      0.0600959 | 175.92        |       1.49666   |   1739.42        |                0          | 679 |

## Sensibilidad de QLIKE al piso (medianas globales)

| mode                    |   qlike_floor_1e-12 |   qlike_floor_1e-10 |   qlike_floor_1e-08 |   qlike_floor_1e-06 |
|:------------------------|--------------------:|--------------------:|--------------------:|--------------------:|
| ewma_0.94               |             1.15719 |             1.15719 |             1.15719 |            0.962277 |
| garch_11                |             1.31576 |             1.31576 |             1.31576 |            1.06596  |
| gjr_garch_11            |             1.28695 |             1.28695 |             1.28695 |            1.08843  |
| log_ridge               |             1.56134 |             1.56134 |             1.56134 |            1.13286  |
| naive                   |             1.77886 |             1.77886 |             1.73912 |            1.21593  |
| nnls_nonneg             |             1.44978 |             1.44978 |             1.44978 |            1.22443  |
| nnls_signed_clip_legacy |             1.48975 |             1.48975 |             1.48975 |            1.18061  |
| ols_clip_legacy         |             1.47649 |             1.47548 |             1.47548 |            1.15177  |
| ridge_clip              |             1.47476 |             1.47476 |             1.47476 |            1.19281  |
| softplus_ridge          |             1.51917 |             1.51917 |             1.51917 |            1.21275  |
| ssrc_log                |             1.50131 |             1.50131 |             1.50131 |            1.08545  |
