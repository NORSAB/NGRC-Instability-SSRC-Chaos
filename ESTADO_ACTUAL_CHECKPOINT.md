# Estado Actual del Proyecto y Checkpoint de Reanudación
**Fecha:** 16 de Agosto de 2026  
**Proyecto:** Artículo 4 — Next-Generation Reservoir Computing (NG-RC) & SSRC  
**Revista Objetivo:** *Chaos: An Interdisciplinary Journal of Nonlinear Science* (AIP Publishing)  
**Formato Oficial:** REVTeX 4-2 (`\documentclass[aip,cha,reprint,amsmath,amssymb]{revtex4-2}`)  
**ID de Sesión Antigravity:** `16fb1273-3e65-443f-8afd-5a0689f842a8`

---

## 1. Resumen Ejecutivo del Estado del Manuscrito

El artículo se encuentra en estado **100% verificado, sincronizado y reproducible**, listo para revisión de estilo y envío editorial:

1. **Documentos Compilados (4 PDFs en `paper_chaos_aip/`):**
   - `main.pdf` (7 páginas): Manuscrito oficial en inglés en plantilla oficial AIP REVTeX 4-2 reprint.
   - `supplementary.pdf` (3 páginas): Suplemento oficial en inglés.
   - `main_es.pdf` (6 páginas): Manuscrito oficial en español sincronizado 1:1, con todas las figuras en español y cero cuadros vacíos.
   - `supplementary_es.pdf` (3 páginas): Suplemento oficial en español sincronizado 1:1 (`figures_es/`).

2. **Figuras en Alta Resolución ($\ge 600$ DPI, tipografía $\ge 8.5\,\text{pt}$):**
   - Inglés: `paper_chaos_aip/figures/` (`fig5_ridge_fragilidad.pdf`, `fig2b_lorenz_atractor.pdf`, `fig_lyapunov_curve.pdf`, `fig13_qlike_piso_fx.pdf`, `fig12_bcie_causal.pdf`, `fig7_combustibles_precios.pdf`, `fig9_mecanismo_falla_nnls.pdf`, `fig_supp_lambda_selection.pdf`, `fig_rossler_m4.pdf`).
   - Español: `paper_chaos_aip/figures_es/` (mismas 9 figuras con etiquetas en español).
   - Alt Text: Documentado en `paper_chaos_aip/ALT_TEXT_FIGURES_TABLES.md`.

3. **Cálculos y Validación Estadística:**
   - Lorenz63: 30 semillas estocásticas evaluadas en 288,420 ventanas (`lorenz_rigorous_ablation_full.csv`).
   - Curva de Lyapunov ($H \in \{1, 2, 3, 5, 8, 10, 15, 20, 30, 40\}$) con denominador MASE estandarizado sobre $T_{\text{train}}=500$.
   - Two-way crossed block bootstrap (2,000 réplicas): con ubicaciones pareadas por signos ($15\sigma$: $[-0.233, +3.093]$, $50\sigma$: $[-0.316, +3.710]$).
   - Volatilidad FX/Cripto: Mediana entre series del QLIKE medio (EWMA 2.36, GARCH 2.38, GJR 2.46, NNLS+ 2.57, ESN 14.33).
   - Suite de Tests: 25 unit tests pasando en `pytest` (`25 passed in 2.60s`).
   - Graphify: 5,063 nodos, 5,914 aristas, 816 comunidades con `graphify-out/graph.html` y `graphify-out/GRAPH_TREE.html` sincronizados.

---

## 2. Comandos para Recompilar y Validar

```powershell
# En la carpeta de Articulo_4_NGRC_Regularizado_SSRC:
pytest -v

# Para regenerar todas las figuras bilingües a 600 DPI:
cd paper_chaos_aip
python make_figures_bilingual.py

# Para compilar los cuatro PDFs:
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode supplementary.tex
pdflatex -interaction=nonstopmode main_es.tex
pdflatex -interaction=nonstopmode supplementary_es.tex
```

---

## 3. Instrucción para Reanudar en un Nuevo Chat

Si abres una nueva ventana o conversación con el agente IA, envía este mensaje exacto:
> *"Por favor lee `d:\2026\Tesis2026\Articulos_IEEE_2026\Articulo_4_NGRC_Regularizado_SSRC\ESTADO_ACTUAL_CHECKPOINT.md` para cargar el estado completo del Artículo 4 (AIP Chaos) y continuar desde allí."*
