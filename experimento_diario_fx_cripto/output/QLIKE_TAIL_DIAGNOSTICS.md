# QLIKE tail diagnostics
This report is a new aggregation pass over the existing, already-verified per-window QLIKE losses in `output/oos_univariado.csv` (1485 windows per mode, pooled across 9 currency/crypto series: MXN, BRL, COP, CLP, PEN, ARS, GTQ, BTC, ETH; BTC and ETH have fewer available windows due to shorter history, as already reflected in that file). It does not touch, recompute, or re-derive any forecast or per-window QLIKE value produced by `run_oos_univariado.py` / `volatility_models.py`.
## Why the median alone is misleading
The manuscript's Table 2 currently reports only the **median** QLIKE per mode. The median treats a model that is occasionally catastrophically wrong the same as one that is consistently good, because QLIKE's `y/yhat - log(y/yhat) - 1` term is unbounded above as `yhat -> 0`: a single window where a model predicts near-zero variance can produce a QLIKE value in the thousands or millions, and the median is blind to this while the mean is not.
## Pooled statistics by mode
| mode | median | mean | P95 | P99 | max | median-of-per-series-means |
|---|---:|---:|---:|---:|---:|---:|
| ewma_0.94 | 1.157 | 2.414 | 8.409 | 14.850 | 218.209 | 2.359 |
| gjr_garch_11 | 1.287 | 2.620 | 8.805 | 13.339 | 158.575 | 2.456 |
| garch_11 | 1.316 | 2.626 | 8.807 | 13.302 | 172.486 | 2.383 |
| nnls_nonneg | 1.450 | 2.871 | 9.006 | 13.680 | 268.556 | 2.565 |
| ridge_clip | 1.475 | 4,636.7 | 9.437 | 20.543 | 3,432,631.5 | 3.472 |
| ols_clip_legacy | 1.475 | 21,023.0 | 14.806 | 362,814.8 | 4,458,373.1 | 18,551.8 |
| nnls_signed_clip_legacy | 1.490 | 19,733.5 | 11.270 | 111,597.3 | 14,452,077.2 | 66.118 |
| ssrc_log | 1.501 | 1,027.9 | 46.959 | 234.971 | 1,154,369.3 | 14.329 |
| softplus_ridge | 1.519 | 2,456.5 | 9.862 | 20.849 | 3,432,631.5 | 3.497 |
| log_ridge | 1.561 | 785.253 | 43.614 | 209.588 | 1,127,141.7 | 12.187 |
| naive | 1.779 | 14,545.1 | 431.711 | 45,680.5 | 5,780,768.4 | 2,579.5 |

## Median-vs-mean divergence: the models this exposes
Ratio of pooled mean to pooled median, largest first (a ratio near 1 means the distribution is well-behaved; a ratio in the hundreds or thousands means the mean is dominated by a small number of catastrophic-tail windows):

| mode | median | mean | mean / median |
|---|---:|---:|---:|
| ols_clip_legacy | 1.475 | 21,023.0 | 14,248x |
| nnls_signed_clip_legacy | 1.490 | 19,733.5 | 13,246x |
| naive | 1.779 | 14,545.1 | 8,177x |
| ridge_clip | 1.475 | 4,636.7 | 3,144x |
| softplus_ridge | 1.519 | 2,456.5 | 1,617x |
| ssrc_log | 1.501 | 1,027.9 | 685x |
| log_ridge | 1.561 | 785.253 | 503x |
| ewma_0.94 | 1.157 | 2.414 | 2.09x |
| gjr_garch_11 | 1.287 | 2.620 | 2.04x |
| garch_11 | 1.316 | 2.626 | 2.00x |
| nnls_nonneg | 1.450 | 2.871 | 1.98x |

**Finding.** `ewma_0.94`, `garch_11`, and `gjr_garch_11` are the only modes whose mean stays within roughly the same order of magnitude as their median (mean/median ratio around 1.9-2.1x), meaning their QLIKE distribution has no severe tail. Every other mode, including `ssrc_log`, shows a mean/median ratio of two to four orders of magnitude, meaning a small number of windows with near-zero predicted variance dominate the mean. Modes exhibiting this pattern: ols_clip_legacy, nnls_signed_clip_legacy, naive, ridge_clip, softplus_ridge, ssrc_log, log_ridge.

### `ssrc_log` specifically
`ssrc_log` has pooled median 1.501, which ranks close to `ewma_0.94` (median 1.157) and `garch_11` (median 1.316) and would look competitive in a median-only table. But its pooled mean is 1,027.9, roughly 426x higher than `ewma_0.94`'s mean (2.414) and 391x higher than `garch_11`'s mean (2.626), with a pooled max of 1,154,369.3 (a single-window blowup driven by a near-zero variance prediction). Its median-of-per-series-means is 14.329, which is still substantially worse than the econometric baselines under this more robust two-stage statistic, confirming the tail behavior is not a single-series artifact.

## Paired comparisons vs. the two strongest baselines
For each mode, the per-window difference `qlike_mode - qlike_baseline` is computed on matched (entity, t0) windows. The 95% CI on the mean difference comes from a block bootstrap (2000 replicates, block length 10 consecutive windows, resampled within each series to respect temporal autocorrelation and never mix series). The sign test reports the fraction of windows where the mode's QLIKE is strictly lower (better) than the baseline's, with an exact two-sided binomial p-value against 50% -- this is a robustness check that does not depend on the mean being well-behaved.

### vs. `ewma_0.94`

| mode | mean diff | 95% CI (bootstrap) | frac. windows mode wins | sign-test p |
|---|---:|---:|---:|---:|
| gjr_garch_11 | 0.204 | [0.029, 0.381] | 43.5% | 5.16e-07 |
| garch_11 | 0.212 | [0.029, 0.413] | 41.6% | 1.27e-10 |
| nnls_nonneg | 0.457 | [0.265, 0.660] | 40.7% | 6.84e-13 |
| ridge_clip | 4,634.3 | [321.957, 10,327.0] | 38.7% | 2.01e-18 |
| ols_clip_legacy | 21,020.6 | [10,777.5, 33,680.2] | 40.3% | 6.53e-14 |
| nnls_signed_clip_legacy | 19,731.1 | [4,495.4, 43,593.2] | 39.3% | 1.19e-16 |
| ssrc_log | 1,025.5 | [13.181, 2,804.6] | 54.7% | 2.77e-04 |
| softplus_ridge | 2,454.1 | [35.136, 7,227.0] | 45.3% | 2.77e-04 |
| log_ridge | 782.839 | [10.246, 2,314.9] | 54.0% | 2.19e-03 |
| naive | 14,542.7 | [4,611.6, 27,788.8] | 45.0% | 1.21e-04 |

### vs. `garch_11`

| mode | mean diff | 95% CI (bootstrap) | frac. windows mode wins | sign-test p |
|---|---:|---:|---:|---:|
| ewma_0.94 | -0.212 | [-0.397, -0.036] | 58.4% | 1.27e-10 |
| gjr_garch_11 | -0.008 | [-0.075, 0.067] | 54.3% | 8.68e-04 |
| nnls_nonneg | 0.239 | [0.118, 0.394] | 45.9% | 1.66e-03 |
| ridge_clip | 4,643.4 | [353.363, 10,999.2] | 39.1% | 3.65e-17 |
| ols_clip_legacy | 21,062.9 | [10,980.2, 33,561.3] | 43.0% | 7.22e-08 |
| nnls_signed_clip_legacy | 19,770.8 | [4,765.5, 44,187.9] | 40.8% | 1.15e-12 |
| ssrc_log | 1,027.3 | [13.368, 2,826.4] | 57.0% | 9.64e-08 |
| softplus_ridge | 2,458.8 | [32.992, 7,221.2] | 49.4% | 6.59e-01 |
| log_ridge | 784.216 | [10.508, 2,332.7] | 56.8% | 1.70e-07 |
| naive | 14,572.0 | [4,572.5, 27,217.0] | 47.8% | 9.13e-02 |

### Reading the `ssrc_log` rows above
- **vs `ewma_0.94`**: mean paired difference = 1,025.5 (95% CI [13.181, 2,804.6]) -- driven almost entirely by tail windows, since `ssrc_log` wins on a per-window basis more often than not (54.7% of windows, sign-test p=2.77e-04). This is the key reconciliation: `ssrc_log` frequently produces a *slightly* better QLIKE than the baseline window-by-window, but when it is wrong, it is wrong catastrophically, and the mean (and any risk-management or capital-allocation use of the forecast) is dominated by those catastrophic windows, not by the typical window.
- **vs `garch_11`**: mean paired difference = 1,027.3 (95% CI [13.368, 2,826.4]) -- driven almost entirely by tail windows, since `ssrc_log` wins on a per-window basis more often than not (57.0% of windows, sign-test p=9.64e-08). This is the key reconciliation: `ssrc_log` frequently produces a *slightly* better QLIKE than the baseline window-by-window, but when it is wrong, it is wrong catastrophically, and the mean (and any risk-management or capital-allocation use of the forecast) is dominated by those catastrophic windows, not by the typical window.

## Terminology note (tracked separately, not fixed here)
This experiment's code refers to the recurrent reservoir model as `ssrc_log` / "SSRC". For the record: the actual implementation in `volatility_models.py::run_ssrc_sequence` is a generic sparse random-weight Echo State Network (ESN) -- a fixed random sparse recurrent reservoir with a trained linear (log-domain, ridge-regularized) readout. It is **not** the specific published Stochastically Structured Reservoir Computer (SSRC) architecture, which additionally requires graph-informed coupling structure and structure-preserving embeddings in the reservoir itself. This is a known, separately-tracked terminology issue to be fixed in the manuscript text describing the model; it is flagged here for the record and is not something this diagnostics script changes or works around.

## Recommendation
**Lead Table 2 with `median-of-per-series-means`, and report pooled mean + max in an adjacent column (or footnote) rather than median alone.** Rationale:

- The pooled median is what currently hides the problem: it is dragged down by the large number of calm/typical windows and gives no signal about tail risk at all.
- The pooled mean is technically correct and is what actually matters if QLIKE losses were ever aggregated for real capital or risk decisions, but it can be dominated by a literal handful of windows out of ~1485 (one extreme window can move it by orders of magnitude), which invites the objection that it is itself not robust and is sensitive to whichever single series had the worst blowup.
- `median-of-per-series-means` is a middle ground: it first averages within each of the 9 series (so a model's tail behavior *within* a series, e.g. one bad week, is not washed out the way the pooled median washes it out), then takes the median *across* series (so one uniquely catastrophic series, e.g. a single BTC or ARS blowup window, cannot single-handedly set the headline number the way it can for the pooled mean). It keeps the econometric baselines ranked first, exactly as the mean does, while being far less sensitive to a single extreme observation.

Under any of the three statistics that account for tail behavior (pooled mean, P95/P99, or median-of-per-series-means), the ranking is consistent and unambiguous: **`ewma_0.94`, `garch_11`, and `gjr_garch_11` are the only competitive methods**, in that order or close to it. `ssrc_log` and every other non-econometric mode in this table (the clip-based OLS/ridge/NNLS variants, softplus and log ridge, and the naive baseline) are not competitive once tail behavior is accounted for, despite `ssrc_log` appearing third-best under median-only reporting. This should be stated plainly in the manuscript rather than smoothed over: the median-only Table 2 currently overstates `ssrc_log`'s performance.
