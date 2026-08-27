# Zenodo Reproducibility Archive & Replication Instructions
**Title:** Replication Package: Instability, Outlier Amplification, and Positivity Constraints in Next-Generation Reservoir Computing  
**Author:** Norman Reynaldo Sabillón Castro  
**Target Journal:** *Chaos: An Interdisciplinary Journal of Nonlinear Science* (AIP Publishing)  
**Zenodo DOI:** [10.5281/zenodo.22121457](https://doi.org/10.5281/zenodo.22121457) (Concept DOI: [10.5281/zenodo.22121356](https://doi.org/10.5281/zenodo.22121356))  
**License:** Dual License — MIT License (Software / Code) / Creative Commons CC-BY 4.0 (Data, Visualizations & Documentation)  

---

## 1. Overview & Package Self-Sufficiency

This repository contains the complete, self-contained replication archive for all theorems, numerical simulations, and empirical benchmarks in the main research article and supplementary material.

All simulation outputs and canonical CSV files are pre-computed and included in the `output/` subdirectories, enabling immediate validation, testing, figure generation, and LaTeX compilation without requiring proprietary external connections.

```
Articulo_4_NGRC_Regularizado_SSRC/
├── requirements.txt                 # Exact PIP dependencies (Python >= 3.10)
├── environment.yml                  # Conda / Mamba environment specification
├── LICENSE                          # MIT (Code) & CC-BY 4.0 (Docs) Dual License
├── reproduce_all.py                 # Master one-command replication orchestrator (--mode=quick/full)
├── ZENODO_REPRODUCIBILITY.md        # This replication guide and data manifest
├── paper_chaos_aip/                 # Official AIP REVTeX 4-2 manuscripts and figures
│   ├── main.tex                     # English research article
│   ├── main.pdf                     # Compiled English PDF
│   ├── supplementary.tex            # English supplementary material
│   ├── supplementary.pdf            # Compiled English Supplementary PDF
│   ├── main_es.tex                  # Spanish synchronized manuscript
│   ├── main_es.pdf                  # Compiled Spanish PDF
│   ├── supplementary_es.tex         # Spanish supplementary material
│   ├── supplementary_es.pdf         # Compiled Spanish Supplementary PDF
│   ├── ALT_TEXT_FIGURES_TABLES.md   # AIP accessibility alt-text companion (Markdown)
│   ├── alt_text_aip.txt             # Plain text alt-text companion for AIP production
│   ├── figures/                     # 600 DPI vector PDF & PNG figures (English)
│   └── figures_es/                  # 600 DPI vector PDF & PNG figures (Spanish)
├── experimento_lorenz/              # Lorenz63 dynamical simulation and ablation suite
│   ├── run_lorenz_30_seeds_ablation.py  # 30-seed stochastic ablation (288,420 rows)
│   ├── run_lorenz_lyapunov_curve.py     # Multistep Lyapunov curve (H in {1..40})
│   ├── run_two_way_block_bootstrap.py   # Two-way crossed block bootstrap (2,000 reps)
│   ├── lorenz_common.py                 # Core reservoir and evaluation routines
│   ├── test_paper_sync_and_data.py      # Automated bilingual/table-sync test suite
│   ├── test_editorial_and_reproducibility.py # Automated packaging, style, and alt-text tests
│   └── output/                          # Audited simulation CSV outputs
├── experimento_diario_fx_cripto/    # Daily FX and cryptocurrency volatility
│   ├── qlike_tail_diagnostics.py        # Tail diagnostics & per-series block bootstrap
│   ├── volatility_models.py             # Econometric and positive cone readouts
│   └── output/                          # Audited out-of-sample CSV records
├── data/                            # Raw historical datasets (Honduras retail fuel, etc.)
│   └── repositorio_combustibles_honduras.csv
├── experimento_combustibles_honduras/ # Weekly retail fuel volatility (Honduras)
│   ├── run_combustibles_hn.py           # Out-of-sample volatility forecasting
│   ├── data_paths.py                    # Relative data path resolver with env fallback
│   └── output/                          # Audited fuel results and raw weekly series
└── experimento_rossler/             # Rössler generalization check
    ├── run_rossler_validation.py        # M^4 sweep and multi-step checks
    └── output/                          # Rössler sweep CSVs
```

---

## 2. Environment Setup

### Option A: Standard PIP
```bash
pip install -r requirements.txt
```

### Option B: Conda / Mamba
```bash
conda env create -f environment.yml
conda activate ngrc-chaos-replication
```

---

## 3. One-Command Full Reproduction

The master script `reproduce_all.py` supports two execution modes:

### Quick Mode (Default — Fast Validation, Testing, Figures & LaTeX Compilation):
```bash
python reproduce_all.py --mode=quick
```
This runs the full test suite (`pytest -v`), recomputes all 600 DPI bilingual figures, and compiles all 4 PDFs with strict error checking.

### Full Simulation Mode (Runs full numerical trajectories from scratch):
```bash
python reproduce_all.py --mode=full
```
This re-executes the Lorenz63 30-seed ablation, Rössler sweeps, and financial benchmarks prior to generating figures and compiling PDFs.

---

## 4. End-to-End Traceability Matrix (Figure/Table $\leftrightarrow$ Script $\leftrightarrow$ CSV)

| Item | Description | Generating / Plotting Script | Canonical Data CSV |
| :--- | :--- | :--- | :--- |
| **Figure 1** | Scaling of Optimal Ridge $\lambda^*$ ($O(M^4)$) | `paper_chaos_aip/make_figures_bilingual.py` | `experimento_lorenz/output/oos_grid_shocks.csv` |
| **Figure 2** | Out-of-Manifold Perturbation Geometry | `paper_chaos_aip/make_figures_bilingual.py` | `experimento_lorenz/lorenz_common.py` (RK4 Trajectory) |
| **Figure 3** | Horizon Degradation (Multi-step MASE) | `paper_chaos_aip/make_figures_bilingual.py` | `experimento_lorenz/output/lorenz_lyapunov_curve_summary.csv` |
| **Figure 4** | Numerical Floor Sensitivity ($\epsilon \in [10^{-12}, 10^{-6}]$) | `paper_chaos_aip/make_figures_bilingual.py` | `experimento_diario_fx_cripto/output/qlike_tail_diagnostics.csv` |
| **Figure S1** | BCIE Loan Portfolio MASE Benchmark | `paper_chaos_aip/make_supplementary_figures_english.py` | `experimento/codigo_pipeline/output/comparacion_cobertura_pareja.csv` |
| **Figure S2** | Honduras Fuel Weekly Price Series | `paper_chaos_aip/make_supplementary_figures_english.py` | `experimento_combustibles_honduras/output/oos_combustibles.csv` |
| **Figure S3** | Realized vs Forecast Fuel Volatility (May 2020) | `paper_chaos_aip/make_supplementary_figures_english.py` | `experimento_combustibles_honduras/output/oos_combustibles.csv` |
| **Figure S4** | Trace Regularization Ratio Sensitivity | `paper_chaos_aip/make_supplementary_figures_english.py` | `experimento_lorenz/output/lorenz_rigorous_summary.csv` |
| **Figure S5** | Rössler Attractor Trace Scaling ($M^{3.79}$) | `paper_chaos_aip/make_supplementary_figures_english.py` | `experimento_rossler/output/rossler_m4_sweep.csv` |
| **Table I** | Lorenz63 30-Seed Ablation & Win Rates | `experimento_lorenz/run_two_way_block_bootstrap.py` | `experimento_lorenz/output/lorenz_rigorous_summary.csv` |
| **Table II** | Financial Volatility & Negative Forecats Benchmark | `experimento_diario_fx_cripto/qlike_tail_diagnostics.py` | `experimento_diario_fx_cripto/output/qlike_tail_diagnostics.csv` |
| **Table S1** | BCIE Lending DM-test Performance Comparison | `experimento/codigo_pipeline/ejecutar_pipeline_econometrico.py` | `experimento/codigo_pipeline/output/comparacion_cobertura_pareja.csv` |
| **Table S2** | Honduras Fuel Volatility Benchmark (13.7% vs 0.9%) | `experimento_combustibles_honduras/run_combustibles_hn.py` | `experimento_combustibles_honduras/output/oos_combustibles.csv` |
| **Table S3** | Mechanistic Comparison across Chaotic Systems | `experimento_rossler/run_rossler_validation.py` | `experimento_rossler/output/rossler_m4_sweep.csv` |

---

## 5. Third-Party Data & External Repositories

- **Honduras Fuel Dataset:** The processed weekly series are bundled inside `experimento_combustibles_honduras/output/`. If the optional raw external repository is available, its location can be specified via the `PAPER4_FUEL_REPOSITORY` environment variable.
- **FX / Cryptocurrency Data:** 9 daily series (2018–2026) are bundled in `experimento_diario_fx_cripto/output/`. Sourced via Yahoo Finance API for academic research and reproducibility; scripts for fresh retrieval are included in `experimento_diario_fx_cripto/`.
- **BCIE Loan Approvals:** Public portfolio disclosure records (1961–2025) are bundled in `experimento/codigo_pipeline/output/`.

---

## 6. Zenodo Deposit Metadata & Archive Verification

- **Zenodo Version Record:** [https://zenodo.org/records/22121457](https://zenodo.org/records/22121457)
- **Version DOI:** `10.5281/zenodo.22121457`
- **Concept DOI (All Versions):** `10.5281/zenodo.22121356`
- **Release Archive:**
  - **Filename:** `Articulo_4_AIP_Chaos_Replication_Package.zip`
  - **Verification:** Zenodo publishes the authoritative file size and MD5 checksum on the version record. These values are checked against the local deterministic build after publication.
  - **Publication Date:** 27 August 2026
  - **License:** MIT License / Creative Commons Attribution 4.0 International
- **Canonical Local Production Archive:**
  - Can be generated at any time via `python package_zenodo_release.py`.
  - **Release Integrity:** Strictly packages only scientific code, datasets, documentation, and REVTeX manuscripts. Private workflow, prompt, and checkpoint files are excluded and verified by `test_zip_package_excludes_private_workflow_files`.
  - **Test Suite Status:** 46 of 46 tests passing (100% Green).
  - **Compilation Status:** 4 of 4 REVTeX 4-2 PDFs compiled with 0 Overfull boxes.
