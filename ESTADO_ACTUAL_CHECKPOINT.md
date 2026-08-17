# Estado Actual del Proyecto y Checkpoint de Reanudación
**Fecha:** 16 de Agosto de 2026 (revisado y corregido en esta sesión)  
**Proyecto:** Artículo 4 — Next-Generation Reservoir Computing (NG-RC) & SSRC  
**Revista Objetivo:** *Chaos: An Interdisciplinary Journal of Nonlinear Science* (AIP Publishing)  
**Formato Oficial:** REVTeX 4-2 (`\documentclass[aip,cha,reprint,amsmath,amssymb]{revtex4-2}`)  
**ID de Sesión Antigravity:** `16fb1273-3e65-443f-8afd-5a0689f842a8`

---

## 0. Corrección importante sobre este checkpoint (leer primero)

La versión anterior de este archivo afirmaba "100% verificado" sin haber comparado el PDF renderizado contra el `.tex` fuente. Al verificar visualmente (render página por página con PyMuPDF, no solo `pdflatex` sin errores) se encontraron y corrigieron **4 defectos reales** que sí estaban en los PDFs compilados de `main.tex`/`main_es.tex`:

1. **Tabla I** (`main.tex`/`main_es.tex`, Sección III): `Overfull \hbox` de 156pt — la última columna (`Δ mean [95% CI]`) estaba recortada y sus 10 filas de datos no eran visibles en el PDF, aunque sí existían en el `.tex`.
2. **Tabla II** (Sección IV): `Overfull \hbox` de 106pt — las columnas "Pooled Median" y "% Neg." se desbordaban **encima del texto de la columna derecha de la página**, produciendo texto ilegible superpuesto.
3. **Figura 4** (`fig13_qlike_piso_fx.pdf`): la leyenda colapsaba 3 métodos Ridge distintos (`log_ridge`, `ridge_clip`, `softplus_ridge`) bajo la misma etiqueta "Ridge NG-RC", mostrándola repetida 3 veces; además la leyenda se superponía con la etiqueta del eje X.
4. **Figura 3** (`fig_lyapunov_curve.pdf`): la leyenda (`loc="upper left"`) se superponía directamente sobre las curvas Ridge NG-RC/OLS NG-RC/ESN, tapando texto y marcadores.

**Causa raíz de 1–2:** `\ruledtabular` en REVTeX 4-2 fuerza `tabular*{\linewidth}` con `\extracolsep{\fill}`, así que la caja ya se declara del ancho correcto aunque el contenido no quepa — por eso un `\resizebox` exterior no tiene ningún efecto (mide una caja que ya dice medir `\linewidth`). El arreglo real fue `\scriptsize` + `\setlength{\tabcolsep}{2pt}` + encabezados abreviados (con la aclaración movida al `\caption`).

Las 4 correcciones están aplicadas en `main.tex`, `main_es.tex` y `make_figures_bilingual.py`, los 4 PDFs fueron recompilados, las **19 páginas totales fueron inspeccionadas visualmente** (render a 2.2× con PyMuPDF, no solo ausencia de errores de `pdflatex`), `pytest -v` sigue en 25/25, y `grep -c Overfull` da 0 en los 4 logs de compilación. `git diff --stat` de los cambios propios: `main.tex` (+32/-16), `main_es.tex` (+32/-16), `make_figures_bilingual.py` (+85/-46), más las 9 figuras regeneradas en `figures/` y `figures_es/`. **Ninguno de estos cambios está commiteado todavía** (aparte de un fix previo no relacionado en `supplementary.tex`/`supplementary_es.tex` — Tabla III — que ya estaba sin commitear al iniciar esta sesión).

Con esas correcciones aplicadas y verificadas, el resumen original de abajo (secciones 1–3) es ahora una descripción precisa del estado del manuscrito.

---

## 1. Resumen Ejecutivo del Estado del Manuscrito

El artículo se encuentra en estado **verificado visualmente página por página, sincronizado y reproducible**, listo para revisión de estilo y envío editorial:

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
