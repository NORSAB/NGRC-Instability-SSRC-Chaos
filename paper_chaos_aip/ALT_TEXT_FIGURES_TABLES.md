# Alt Text for Figures and Tables: Next-Generation Reservoir Computing Investigation
**Author:** Norman Reynaldo Sabillón Castro  
**Target Journal:** *Chaos: An Interdisciplinary Journal of Nonlinear Science* (AIP Publishing)

---

## Main Manuscript Figures

### Figure 1 (`fig5_ridge_fragilidad.pdf`)
- **Short Alt Text:** Log-log plot showing quartic scaling of trace-proportional Ridge regularization parameter lambda versus shock magnitude M.
- **Detailed Description:** A log-log coordinate graph displaying the regularization parameter $\lambda = \gamma \operatorname{tr}(\mathbf{F}^\top\mathbf{F})/D$ on the vertical axis against the injected outlier magnitude $M$ (in standard deviation units $\sigma$, ranging from 1 to 50) on the horizontal axis. Blue circular markers show the median $\lambda$ across shock windows from Lorenz63 simulations. A dashed red line shows a fitted power-law with an empirical slope of approximately $3.99$, closely matching the theoretical quartic scaling $M^4$ predicted by Theorem 1.

### Figure 2 (`fig2b_lorenz_atractor.pdf`)
- **Short Alt Text:** 2D phase portrait of the Lorenz63 chaotic attractor with an exogenous outlier point outside the manifold.
- **Detailed Description:** Scatter plot showing the $(x, z)$ projection of the chaotic Lorenz63 attractor in blue with low alpha transparency, forming the characteristic two-lobed butterfly geometry. A red "X" marker at $(x \approx 65, z \approx 25)$ highlights a synthetic additive outlier shock of magnitude $+15\sigma$, illustrating how localized shocks force trajectory states far outside the low-dimensional invariant fractal manifold.

### Figure 3 (`fig_lyapunov_curve.pdf`)
- **Short Alt Text:** Line plot comparing iterative multi-step forecast error (MASE) against forecast horizon in Lyapunov times for reservoir and polynomial models.
- **Detailed Description:** A semi-log plot displaying median out-of-sample MASE on the vertical axis (log scale from $10^{-2}$ to $10^1$) versus the forecast horizon $\tau$ in Lyapunov times ($\tau \in [0, 1.8]$, corresponding to $H \in \{1, 2, 3, 5, 8, 10, 15, 20, 30, 40\}$) on the horizontal axis. Static tanh (green circles) and recurrent ESN-lag (blue squares) remain below the naive baseline (MASE=1) for $\tau \le 0.45$ ($H \le 10$), whereas Ridge NG-RC (red triangles) and OLS NG-RC (orange inverted triangles) rapidly explode to MASE $> 2.50$ due to unconstrained polynomial error feedback. Beyond $\tau \approx 1.0$, all models saturate at the attractor scale, where static tanh retains lower median error than recurrent ESN.

### Figure 4 (`fig13_qlike_piso_fx.pdf`)
- **Short Alt Text:** Log-log plot of median QLIKE loss as a function of numerical variance evaluation floor epsilon across 9 FX and cryptocurrency series.
- **Detailed Description:** A log-log plot showing median QLIKE loss on the vertical axis against the evaluation floor $\epsilon$ (ranging from $10^{-12}$ to $10^{-6}$) on the horizontal axis. Unconstrained legacy Ridge NG-RC (red curve) explodes by orders of magnitude as $\epsilon \to 0$ due to negative variance predictions. In contrast, Non-negative NNLS (green squares) and Log-Readout Sparse ESN (blue circles) remain completely horizontal and invariant, proving strict non-negativity across all evaluation windows.

---

## Supplementary Figures

### Figure S1 (`fig12_bcie_causal.pdf`)
- **Short Alt Text:** Horizontal bar chart comparing causal out-of-sample MASE across eight multilateral lending methods on the BCIE panel.
- **Detailed Description:** Horizontal bar chart showing causal out-of-sample MASE for eight common member country loan approval series (2020-2025). Methods are sorted by error: NNLS direct achieves the lowest point estimate (MASE 0.8155), followed by Recurrent Sparse ESN reference (MASE 1.0356), while Tikhonov covariance, Ledoit-Wolf shrinkage, and Baseline PCA achieve MASE 1.2437 to 1.3125. All pairwise Diebold-Mariano tests against the ESN reference yield $p \ge 0.50$, indicating non-significance under block-exact resampling.

### Figure S2 (`fig7_combustibles_precios.pdf`)
- **Short Alt Text:** Time series plot of weekly retail fuel prices in Honduras from 2017 to 2026 with shaded historical shock windows.
- **Detailed Description:** Line chart showing weekly retail prices in Lempiras per gallon for Super gasoline, Regular gasoline, Diesel, and Kerosene in Honduras from 2017 through 2026. Four shaded vertical bands highlight major geopolitical and climate shock periods: COVID-19 lockdown (spring 2020), Hurricanes Eta and Iota (late 2020), Russia-Ukraine war price surge (2022), and Middle East strait tensions (2026).

### Figure S3 (`fig9_mecanismo_falla_nnls.pdf`)
- **Short Alt Text:** Bar chart illustrating negative prediction failure in legacy signed NNLS for the week of May 11, 2020.
- **Detailed Description:** Paired bar chart for the week of May 11, 2020, comparing realized squared log-returns in blue against raw unclipped predictions from legacy signed NNLS in red across four fuels. For Super and Regular gasoline, legacy signed NNLS predicts negative volatility values (reaching below zero), demonstrating that enforcing non-negative weights $w \ge 0$ fails when input features retain signed lags.

### Figure S4 (`fig_supp_lambda_selection.pdf`)
- **Short Alt Text:** Line plot showing median out-of-sample MAE versus regularization ratio and distribution of selected lambda parameters.
- **Detailed Description:** A semi-log plot displaying median out-of-sample MAE across candidate regularization ratios $\lambda / \lambda_{\text{scale}} \in [10^{-6}, 10^2]$ on Lorenz63. Blue bubble markers indicate the empirical frequency of lambda values selected by internal temporal validation across outer test windows, contrasting with a fixed heuristic choice $\lambda = 0.1$.

### Figure S5 (`fig_rossler_m4.pdf`)
- **Short Alt Text:** Log-log plot of trace-proportional lambda versus shock magnitude M on the Rossler chaotic attractor.
- **Detailed Description:** Log-log coordinate plot showing trace-proportional regularization parameter $\lambda$ on the vertical axis against shock magnitude $M$ on the horizontal axis for the Rössler attractor. A power-law fit over large shock magnitudes yields a slope of $3.79$, validating the cross-system generality of Theorem 1's quartic scaling.
