# AGENTS.md — Artículo 4 (NG-RC & SSRC, AIP Chaos)

Este archivo lo leen automáticamente Codex y Antigravity (y Claude vía `CLAUDE.md`) al abrir
esta carpeta directamente. Léelo antes de hacer cualquier cosa aquí.

## Antes de tocar cualquier archivo de este artículo

**Lee completo `CHECKPOINT_TRIO_IA.md` en esta misma carpeta.** Contiene la regla permanente
(rigor matemático, cómo verificar código y PDFs, cómo registrar, cómo entrar) que rige el trabajo
de los tres agentes (Claude, Codex, Antigravity) en este artículo, y el historial append-only de
lo que cada uno hizo. No se puede borrar ni reescribir nada de ese historial — solo añadir al
final, con el formato exacto que el propio archivo especifica.

## Este artículo también es parte del ecosistema completo

Este proyecto vive dentro de `Articulos_IEEE_2026/`, que tiene su propio `AGENTS.md` con reglas
del ecosistema (grafo compartido, regla de humanizar, etc.) — léelo también si no lo has hecho:
`D:\2026\Tesis2026\Articulos_IEEE_2026\AGENTS.md`.

El grafo graphify es **uno solo para todo el ecosistema**:
`D:\2026\Tesis2026\Articulos_IEEE_2026\graphify-out\graph.json`. No crear un `graphify-out/`
separado dentro de esta carpeta.

## Qué es este artículo

"Instability, Outlier Amplification, and Positivity Constraints in Next-Generation Reservoir
Computing" — Norman Reynaldo Sabillón Castro. Objetivo: *Chaos: An Interdisciplinary Journal of
Nonlinear Science* (AIP Publishing), formato REVTeX 4-2. 4 documentos en `paper_chaos_aip/`:
`main.tex`/`main_es.tex` (artículo) y `supplementary.tex`/`supplementary_es.tex` (suplemento),
sincronizados 1:1 EN↔ES. Suite de pruebas: `pytest -v` desde esta carpeta (26 pruebas al
16-ago-2026).
