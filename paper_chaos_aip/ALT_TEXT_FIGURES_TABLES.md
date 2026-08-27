# Accessibility Alt-Text Descriptions (AIP / Chaos Publishing Standard)

This document provides standardized, peer-reviewed alt-text descriptions for all figures and tables in the main text and supplementary material. All descriptions strictly adhere to the 25–50 word standard and match empirical calculations exactly.

---

## Main Manuscript Figures

### Figure 1: Scaling of Optimal Ridge Regularization with Shock Magnitude (`fig1_ridge_scaling`)
Log-log scatter plot of optimal Ridge regularization parameter $\lambda^*$ against shock magnitude $M \in \{5, 10, 15, 20, 30\}\sigma$. Shows an empirical power-law slope of approximately $3.93$, corroborating the theoretical bound of $O(M^4)$ for out-of-manifold perturbations.

### Figure 2: Out-of-Manifold Perturbation Geometry on Lorenz63 (`fig2_shock_geometry`)
Two-dimensional $(x, z)$ phase portrait of the Lorenz63 chaotic attractor. The nominal trajectory is shown in blue, and an exogenous $+15\sigma$ perturbation at $x \approx 120.6, z \approx 20.5$ forces the trajectory out of the manifold into transient non-ergodic space.

### Figure 3: Multi-Step Forecasting Horizon Degradation (`fig3_horizon_decay`)
Semi-log plot of multi-step Mean Absolute Scaled Error (MASE) across forecasting horizons $H \in \{1,...,40\}$, parameterized in Lyapunov times $\tau$, on Lorenz63. Unconstrained polynomial NG-RC (Ridge, OLS) explodes beyond $\tau \approx 0.2$, while bounded activations (tanh) remain stable up to $\tau \approx 0.68$.

### Figure 4: Floor Sensitivity and Numerical Stability in Volatility Forecasting (`fig4_floor_sensitivity`)
Log-log plot of median QLIKE loss versus numerical positivity floor $\epsilon \in [10^{-12}, 10^{-6}]$ across nine financial return series. Ridge exhibits extreme degradation as $\epsilon \to 0$, whereas structurally non-negative NNLS remains constant at $1.4498$ for $\epsilon \le 10^{-8}$ and shifts slightly to $1.2244$ at $\epsilon = 10^{-6}$.

---

## Supplementary Figures

### Figure S1: BCIE Multilateral Lending Architecture MASE Benchmark (`figS1_bcie_mase`)
Horizontal bar chart comparing out-of-sample forecasting accuracy (MASE) across nine statistical, reservoir, and penalized regression architectures on the BCIE multilateral loan dataset. Regularized non-negative readouts achieve the lowest MASE while eliminating economically invalid negative loan volume predictions.

### Figure S2: Weekly Honduras Retail Petroleum Price Trajectories (`figS2_fuel_prices`)
Time series plot of weekly retail fuel prices in Honduras (2017–2026) for Super gasoline, Regular gasoline, Diesel, and Kerosene. Four shaded intervals highlight major global economic shock episodes, including the 2020 pandemic crash and 2022 international energy price volatility.

### Figure S3: Mechanism of an NNLS-Readout Failure Case (`figS3_fuel_nnls_failure`)
Line plots comparing realized squared return volatility against unclipped NNLS forecasts for fuel products. Illustrates that non-negative readout coefficients do not prevent negative variance predictions when input lag features contain signed raw returns.

### Figure S4: Regularization Hyperparameter Ratio Sensitivity on Lorenz63 (`figS4_ratio_sensitivity`)
Semi-log plot illustrating median out-of-sample MAE as a function of trace regularization ratio candidates on the Lorenz63 benchmark. The distribution confirms a stable minimum error region, validating the automatic trace-proportional hyperparameter selection rule under varying shock intensities.

### Figure S5: Trace Scaling on Rössler Chaotic Attractor (`figS5_rossler_scaling`)
Log-log plot of optimal trace-proportional regularization parameter $\lambda$ against shock amplitude $M$ for the Rössler chaotic attractor. The empirical slope of $3.79$ closely aligns with the $O(M^4)$ theoretical scaling law derived for out-of-manifold state disturbances.

---

## Tables

### Table I: Lorenz63 30-Seed Ablation Benchmark (`table1_ablation`)
Performance across 30 stochastic realizations on Lorenz63, reporting median MASE, percentile ranges, Clopper-Pearson win rates against Ridge, and two-way crossed block bootstrap intervals on the paired mean MASE difference across ten readout configurations. Bounded activations (tanh, ESN) outperform unconstrained polynomial NG-RC (Ridge, OLS) under noise and short-to-intermediate horizons.

### Table II: Financial Volatility Benchmark (`table2_volatility`)
Out-of-sample QLIKE across nine currency and cryptocurrency series, ranked by the median across series of mean QLIKE. Legacy signed readouts explode under a small positivity floor due to negative variance estimates, whereas structurally non-negative NNLS remains stable and avoids invalid forecasts entirely.

### Table S1: BCIE Loan Portfolio Forecasting Performance (`tableS1_bcie_comparison`)
Performance comparison table reporting out-of-sample MASE and Diebold-Mariano test p-values across eight financial forecasting architectures on the BCIE multilateral loan dataset. Non-negative readouts attain the lowest MASE point estimate (0.8155), but differences against the ESN reference (1.0356) are not statistically significant ($p \ge 0.50$).

### Table S2: Honduras Fuel Volatility Benchmark (`tableS2_fuel_comparison`)
Comparative evaluation table of volatility models for Honduras retail fuel price series reporting QLIKE, MASE, and negative prediction percentages. Unregularized OLS produces 13.7\% negative forecasts and Ridge produces 0.9\%, whereas non-negative readouts eliminate negative predictions entirely.

### Table S3: Mechanistic Comparison Across Chaotic Attractors (`tableS3_mechanistic_comparison`)
Mechanistic evaluation table comparing clean and shocked MASE, shock amplification ratios, and forecast retention horizons across candidate readout mechanisms on Lorenz63 and Rössler attractors, confirming directional replication of all three dynamical phenomena.
