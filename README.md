# Artículo 4 — NG-RC regularizado / SSRC (línea de investigación en exploración)

Carpeta **AISLADA**: contiene su propia copia completa del motor experimental
(`experimento/codigo_pipeline/`, copiado de `Articulo_2_Guatemala_Coupled-TCROC/experimento/codigo_pipeline/`
el 2026-08-12). El pipeline original de Artículo 2 **no se modificó** — esta carpeta existe
para poder experimentar libremente sin arriesgar el pipeline en producción de CONCAPAN/CFP.

## Origen de la línea

La línea estudia los *Stochastically Structured Reservoir Computers* (SSRC) y el problema de
mal condicionamiento de NG-RC ante datos ruidosos o con quiebres estructurales. **SSRC** es la
sigla usada de forma consistente en todo el Artículo 4.
Las referencias de base ya tienen versiones publicadas: *Chaos* 35, 073102 (2025),
doi:10.1063/5.0262977; *Chaos* 35, 123102 (2025), doi:10.1063/5.0278709; e
*IFAC-PapersOnLine* 59(36), 100--105, doi:10.1016/j.ifacol.2026.03.018. La línea aprovecha
que el proyecto ya probó y descartó NG-RC
(`../Articulo_2_Guatemala_Coupled-TCROC/../REGISTRO_EXPERIMENTOS/EXP_ngrc_FRACASO.md`).

## Estado

- **2026-08-13**: auditoría metodológica y reejecuciones terminadas. Se eliminó la fuga
  temporal del BCIE, se corrigió la orientación del componente principal, se adoptó la
  configuración vigente TCRA ($W=3$, $\lambda=0.88$), se implementó un SSRC recurrente real y
  se validó temporalmente el Ridge del lector. La evaluación de volatilidad incluye enlaces
  positivos, EWMA, GARCH y GJR-GARCH. Lorenz y FX quedan como experimentos principales; BCIE y
  combustibles, como validaciones secundarias. El registro corregido y compilado está en
  `paper/registro_avance.pdf`.
- **2026-08-12**: primer experimento corrido. Ver
  `experimento/EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md` — veredicto PARCIAL/MATIZADO:
  el mal condicionamiento se confirma empíricamente (κ=∞ en el bloque cuadrático crudo),
  la regularización lo corrige numéricamente, pero la ganancia en MASE es mixta y el lector
  NNLS directo gana con menor cobertura de entidades (no es aún una comparación limpia).
  Este registro se conserva como antecedente, no como resultado publicable.

## Estructura

```
experimento/
  codigo_pipeline/           copia aislada del motor (config/, src/, requirements.txt)
    run_ngrc_variant_REFERENCIA_original.py    copia intacta de Artículo 2 (no tocar)
    run_robustez_v2_REFERENCIA_original.py     copia intacta de Artículo 2 (no tocar)
    run_ngrc_regularizado.py                   script NUEVO de este experimento
    output/                                    resultados (CSV)
  EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md  hallazgo del 2026-08-12
```
