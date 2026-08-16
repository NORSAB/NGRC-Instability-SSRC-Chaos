# Zenodo Reproducibility Archive & Replication Instructions
**Title:** Data and Code Replication Package for "Instability, Outlier Amplification, and Positivity Constraints in Next-Generation Reservoir Computing"  
**Author:** Norman Reynaldo Sabillón Castro  
**Target Journal:** *Chaos: An Interdisciplinary Journal of Nonlinear Science* (AIP Publishing)  
**License:** MIT License / CC-BY 4.0  

---

## 1. Overview & Directory Structure

This repository provides full end-to-end reproducibility pipelines for all analytical theorems, dynamical simulations, and empirical financial experiments presented in the manuscript and supplementary material.

```
Articulo_4_NGRC_Regularizado_SSRC/
├── paper_chaos_aip/                 # Official AIP REVTeX 4-2 manuscripts and figures
│   ├── main.tex                     # English research article
│   ├── main.pdf                     # Compiled English PDF
│   ├── supplementary.tex            # English supplementary material
│   ├── supplementary.pdf            # Compiled English Supplementary PDF
│   ├── main_es.tex                  # Spanish synchronized manuscript
│   ├── main_es.pdf                  # Compiled Spanish PDF
│   ├── supplementary_es.tex         # Spanish supplementary material
│   ├── supplementary_es.pdf         # Compiled Spanish Supplementary PDF
│   ├── ALT_TEXT_FIGURES_TABLES.md   # AIP accessibility alt-text companion
│   ├── figures/                     # 600 DPI vector PDF & PNG figures (English)
│   └── figures_es/                  # 600 DPI vector PDF & PNG figures (Spanish)
├── experimento_lorenz/              # Lorenz63 dynamical simulation and ablation suite
│   ├── run_lorenz_30_seeds_ablation.py  # 30-seed stochastic ablation (288,420 rows)
│   ├── run_lorenz_lyapunov_curve.py     # Multistep Lyapunov curve (H in {1..40})
│   ├── run_two_way_block_bootstrap.py   # Two-way crossed block bootstrap (2,000 reps)
│   ├── lorenz_common.py                 # Core reservoir and evaluation routines
│   └── output/                          # Audited simulation CSV outputs
├── experimento_diario_fx_cripto/    # Daily FX and cryptocurrency volatility
│   ├── qlike_tail_diagnostics.py        # Tail diagnostics & per-series block bootstrap
│   ├── volatility_models.py             # Econometric and positive cone readouts
│   └── output/                          # Audited out-of-sample CSV records
├── experimento_combustibles_honduras/ # Weekly retail fuel volatility (Honduras)
│   ├── run_experimento_combustibles.py  # Out-of-sample volatility forecasting
│   └── output/                          # Audited fuel results
├── experimento_rossler/             # Rössler generalization check
│   ├── run_rossler_all.py               # M^4 sweep and multi-step checks
│   └── output/                          # Rössler sweep CSVs
└── test_paper_sync_and_data.py      # Automated 25-item test suite
```

---

## 2. Environment Setup

The pipelines require Python $\ge 3.10$ and standard scientific computing packages:

```bash
pip install numpy scipy pandas matplotlib pytest
```

---

## 3. One-Command Full Reproduction

To reproduce all numerical tables, figure files, and verify statistical parity:

```bash
# 1. Run all 25 automated unit and regression tests
pytest -v

# 2. Re-generate all high-resolution figures (English & Spanish at 600 DPI)
cd paper_chaos_aip
python make_figures_bilingual.py

# 3. Re-compile all four LaTeX documents
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode supplementary.tex
pdflatex -interaction=nonstopmode main_es.tex
pdflatex -interaction=nonstopmode supplementary_es.tex
```

---

## 4. Exact CSV Data Traceability

- **Table I (Lorenz63 30-Seed Ablation):** `experimento_lorenz/output/lorenz_rigorous_summary.csv` and `lorenz_two_way_block_bootstrap.csv`.
- **Figure 1 & Theorem 1 ($M^4$ Trace Inflation):** `experimento_lorenz/output/oos_grid_shocks.csv`.
- **Figure 3 (Lyapunov Multistep Curve):** `experimento_lorenz/output/lorenz_lyapunov_curve_summary.csv`.
- **Table II & Figure 4 (FX/Crypto Volatility & Floor Sensitivity):** `experimento_diario_fx_cripto/output/qlike_tail_diagnostics.csv` and `oos_univariado.csv`.
- **Table S1 & Figure S1 (BCIE Lending Panel):** `experimento/codigo_pipeline/output/comparacion_cobertura_pareja.csv`.
- **Table S2 & Figure S2 (Honduras Fuel Volatility):** `experimento_combustibles_honduras/output/investigacion_negativas_por_semana.csv`.
- **Table S3 & Figure S5 (Rössler Generalization):** `experimento_rossler/output/rossler_m4_sweep.csv`.
