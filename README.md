<div align="center">

# Instability, Outlier Amplification, and Positivity Constraints in Next-Generation Reservoir Computing

**Replication Package and Scientific Codebase**

[![Target Venue: AIP Chaos](https://img.shields.io/badge/Target_Venue-AIP_Chaos_(2026)-00629B?style=for-the-badge&logo=physics&logoColor=white)](https://pubs.aip.org/aip/cha)
[![Format: REVTeX 4-2](https://img.shields.io/badge/Format-REVTeX_4--2-0284C7?style=for-the-badge&logo=latex&logoColor=white)](paper_chaos_aip/)
[![Test Suite: 46 Passed](https://img.shields.io/badge/PyTest-46%2F46_Passed_(100%25)-10B981?style=for-the-badge&logo=pytest&logoColor=white)](experimento_lorenz/)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Zenodo DOI](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.22121457-0891B2?style=for-the-badge&logo=zenodo&logoColor=white)](https://doi.org/10.5281/zenodo.22121457)
[![Dual License: MIT + CC-BY-4.0](https://img.shields.io/badge/License-MIT_%2F_CC--BY--4.0-F59E0B?style=for-the-badge)](LICENSE)

<br>

**Norman Reynaldo Sabillón Castro**  
*Department of Mathematics, Universidad Nacional Autónoma de Honduras (UNAH), Tegucigalpa, Honduras*  
*Contact:* [sabillonrey2004@gmail.com](mailto:sabillonrey2004@gmail.com) &middot; [GitHub Profile](https://github.com/NORSAB) &middot; [IEEE Xplore Author](https://ieeexplore.ieee.org/document/11512574)

</div>

---

## 📌 Executive Overview

Next-Generation Reservoir Computing (**NG-RC**) replaces high-dimensional random recurrent neural networks with explicit polynomial feature maps of time-lagged observables, offering dramatic parameter efficiency. However, empirical deployments frequently encounter severe numerical ill-conditioning and forecast degradation under measurement noise, return asymmetries, or localized outlier shocks.

This repository hosts the **complete mathematical derivations, 30-seed stochastic ablation pipelines, and empirical volatility/chaotic benchmark suites** accompanying the paper:

> **Sabillón Castro, N. R. (2026).** *Instability, Outlier Amplification, and Positivity Constraints in Next-Generation Reservoir Computing.* Target: *Chaos: An Interdisciplinary Journal of Nonlinear Science* (AIP Publishing).

---

## 🔬 Core Scientific Findings & Theorems

### 1. Analytical Mechanism of Quartic Trace Scaling ($\sim M^4$) — Theorem 1
When an isolated outlier shock of magnitude $M$ enters a time series, the trace of the quadratic NG-RC Gram matrix scales as:
$$\operatorname{tr}(\mathbf{F}^\top\mathbf{F}) = \mathcal{O}(M^4) + \mathcal{O}(M^2) + \mathcal{O}(T(C^2+C^4))$$
Consequently, heuristic trace-based Ridge regularizations ($\lambda \propto \operatorname{tr}(\mathbf{F}^\top\mathbf{F})$) inflate $\lambda$ by orders of magnitude, causing catastrophic over-regularization across calm dynamical regimes. Empirically verified across chaotic attractors with a measured log-log slope of **3.93**.

### 2. Spectral Invariance under Covariance Regularization — Theorem 2
Tikhonov spectral shifts $\mathbf{C} + \lambda\mathbf{I}$ on sample covariances preserve principal eigenvectors identically:
$$\mathbf{v}_i(\mathbf{C} + \lambda\mathbf{I}) = \mathbf{v}_i(\mathbf{C}), \quad \mu_i = \sigma_i^2 + \lambda$$
This mathematically decouples covariance conditioning from readout regularization, ensuring that spectral stabilization does not rotate principal dynamical subspaces.

### 3. 30-Seed Stochastic Robustness and Recurrent Ablation
Across **30 independent reservoir realizations** and **288,420 window evaluations** on the Lorenz-63 attractor, evaluated via a two-way crossed block bootstrap:
- **Bounded Activations ($\tanh$):** Prevent polynomial divergence and delay the onset of iterated error amplification across intermediate forecast horizons ($H \le 15$).
- **Recurrent Memory ($\mathbf{W}_{\text{res}} \neq \mathbf{0}$):** Delivers a statistically significant noise-filtering advantage over static projections under Gaussian observation noise ($\sigma=0.10$), with bootstrap 95% confidence intervals on the paired mean MASE difference strictly excluding zero.
- **Shock Robustness:** Is condition-dependent rather than uniform across the attractor phase space.

### 4. Conical Constraints & Tail-Sensitive Volatility Forecasting
In daily FX and cryptocurrency volatility series, Non-Negative Least Squares (**NNLS**) over strictly positive feature bases mathematically guarantees non-negative variance forecasts without arbitrary floor clipping ($r_t^2 \ge 0$). However, when tail-sensitive loss metrics (mean across series of QLIKE) are evaluated, unconstrained reservoirs underperform specialized econometric models (EWMA, GARCH, GJR-GARCH).

---

## 📊 Benchmark Summary Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BENCHMARK EXPERIMENTS & VALIDATIONS                                    │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────────────────────┤
│ Domain / Benchmark       │ Methodological Focus        │ Key Result / Statistical Metric               │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────────────────────┤
│ Lorenz-63 Attractor      │ Noise Filtering & Shocks    │ 30 seeds, 288k windows: ESN filters noise     │
│ (Chaotic Flow)           │ 2-Way Block Bootstrap       │ (MASE CI excludes 0); bounded delay for H<=15 │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────────────────────┤
│ Rössler Attractor        │ Quartic Scaling Audit       │ Confirms log-log scaling slope = 3.93         │
│ (Phase-Coherent Chaos)   │ Trace-proportional Ridge    │ under interior isolated shock of magnitude M  │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────────────────────┤
│ Daily FX & Crypto        │ Positivity & Loss Tails     │ NNLS guarantees positive variance; GARCH/     │
│ (10-15 Years Daily Data) │ QLIKE / MSE-vol / Kappa     │ GJR-GARCH retain superior tail calibration    │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────────────────────┤
│ Honduras Weekly Fuel     │ Emerging Market Panel       │ Positivity constraints eliminate invalid      │
│ (2017–2025 Ledger)       │ Structural Break 2022       │ negative prices across 5 fuel categories      │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
.
├── paper_chaos_aip/                 # Bilingual AIP Chaos / REVTeX 4-2 Manuscripts
│   ├── main.tex                     # Main Manuscript (English, REVTeX 4-2)
│   ├── main_es.tex                  # Manuscrito Principal (Español)
│   ├── supplementary.tex            # Supplementary Material (English, 5 pp)
│   ├── supplementary_es.tex         # Material Suplementario (Español, 5 pp)
│   ├── references.bib               # 46 canonical bibliographic entries
│   ├── figures/                     # High-resolution vector & raster figures (EN)
│   └── figures_es/                  # Figuras en alta resolución (ES)
├── experimento_lorenz/              # Lorenz-63 30-seed simulation & ablation suite
│   ├── run_30seeds_lorenz.py        # 30-seed crossed bootstrap pipeline
│   ├── run_shock_sweep_lorenz.py    # Outlier shock amplification experiment
│   ├── run_lyapunov_analysis.py     # Multi-step iterated error growth
│   └── test_*.py                    # Unit and integration tests
├── experimento_diario_fx_cripto/    # Daily financial volatility benchmark
│   ├── run_volatility_benchmark.py  # NNLS vs GARCH/GJR-GARCH/EWMA
│   └── test_volatility_models.py    # Conical constraint verification
├── experimento_combustibles_honduras/ # Weekly national fuel price modeling
│   ├── run_fuel_benchmark.py        # Micro-panel price forecasting
│   └── test_modelos_volatilidad.py  # Positivity test suite
├── data/                            # Curated open datasets and derived statistics
├── docs/                            # Deep technical documentation and proofs
├── reproduce_all.py                 # Master one-command replication entrypoint
├── requirements.txt                 # Exact pinned dependency environment
├── environment.yml                  # Conda environment definition
├── ZENODO_REPRODUCIBILITY.md        # Open science & Zenodo replication record
└── LICENSE                          # MIT (Code) / CC-BY-4.0 (Manuscript/Data)
```

---

## ⚡ Quick Start & Reproduction

### 1. Environment Setup

Clone the repository and install the verified dependencies:

```bash
git clone https://github.com/NORSAB/NGRC-Instability-SSRC-Chaos.git
cd NGRC-Instability-SSRC-Chaos

# Using standard pip with pinned versions
pip install -r requirements.txt

# Or using Conda
conda env create -f environment.yml
conda activate ngrc-chaos
```

### 2. Automated Test Suite (46 Tests)

Run the full verification suite covering mathematical invariances, no-leakage guarantees, and statistical reproductions:

```bash
pytest -v
```

### 3. Run Full Experimental Replication

Execute all experiments and regenerate figures and CSV tables:

```bash
python reproduce_all.py
```

### 4. Compile Manuscripts (REVTeX 4-2)

Compile both English and Spanish manuscripts and supplementary documents:

```bash
cd paper_chaos_aip
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
pdflatex supplementary.tex && pdflatex supplementary.tex
pdflatex main_es.tex && bibtex main_es && pdflatex main_es.tex && pdflatex main_es.tex
pdflatex supplementary_es.tex && pdflatex supplementary_es.tex
```

---

## 🧪 Verified Software Environment

| Package | Version | Package | Version |
| :--- | :--- | :--- | :--- |
| **Python** | `3.10+ / 3.13.14` | **NumPy** | `2.4.6` |
| **SciPy** | `1.17.1` | **Pandas** | `2.2.3` |
| **Scikit-Learn** | `1.6.1` | **PyTest** | `9.0.3` |
| **Matplotlib** | `3.10.0` | **Arch** | `7.1.0` |

---

## 📖 Citation

If you utilize this codebase, theorems, or benchmark data in your research, please cite:

```bibtex
@article{Sabillon2026NGRCInstability,
  author    = {Norman Reynaldo Sabill{\'o}n Castro},
  title     = {Instability, Outlier Amplification, and Positivity Constraints in Next-Generation Reservoir Computing},
  journal   = {Chaos: An Interdisciplinary Journal of Nonlinear Science},
  year      = {2026},
  note      = {Under review},
  doi       = {10.5281/zenodo.22121457},
  url       = {https://github.com/NORSAB/NGRC-Instability-SSRC-Chaos}
}
```

---

## 📜 License & Open Science

- **Code and Scripts:** Licensed under the [MIT License](LICENSE).
- **Manuscripts, Figures, and Documentation:** Licensed under [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/).
- **Data Provenance:** Zenodo Archive DOI: [`10.5281/zenodo.22121457`](https://doi.org/10.5281/zenodo.22121457).
