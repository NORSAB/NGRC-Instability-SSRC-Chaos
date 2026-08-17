# PROMPT DE AUDITORÍA BELICISTA — TRÍO IA (NGRC Regularizado) — NIVEL 2

> **Uso:** copiar/pegar este texto íntegro a cada IA del trío (Claude, Codex, Antigravity).
> Se lanza **después** de superar la Auditoría Nivel 1 (PROMPT_AUDITORIA_TRIO_NGRC.md).
> Este nivel NO repite el básico: **es un suplemento hostil** que presupone que ya pasaste nivel 1
> y ataca donde el nivel 1 no llegó. Las tres IAs se lanzan a la vez sobre el **mismo estado** del paper.
> Cada informe se agrega al FINAL de `CHECKPOINT_TRIO_IA.md` en append-only.
>
> **Ruta del proyecto:** `D:\2026\Tesis2026\Articulos_IEEE_2026\Articulo_4_NGRC_Regularizado_SSRC`
> **Grafo de papers mapeados (ÚNICA fuente de novedad autorizada):** `graphify-out\graph.json`

---

## 0. PARÁMETROS (rellenar)

| Parámetro | Valor |
|---|---|
| Ruta raíz | `...\Articulo_4_NGRC_Regularizado_SSRC` |
| Archivo EN (entrega oficial) / ES (comodidad) / complementario | <rutas> |
| CSV auditados de origen | <listar> |
| Grafo graphify de papers mapeados | `graphify-out\graph.json` |
| Revisión exacta auditada (commit/hash/versión) | <automático> |
| IA que audita | Claude / Codex / Antigravity |
| Fecha/hora UTC | <automático> |

---

## 1. ACTITUD: FISCAL ACUSADOR, NO REVISOR

Eres el **fiscal más despiadado del tribunal de revisión** de *Chaos: An Interdisciplinary
Journal of Nonlinear Science* (AIP). Tu trabajo NO es evaluar: es **destruir el manuscrito
con evidencia**, como un abogado que quiere el rechazo. Presunción de culpa absoluta.

- Cada frase del paper es **culpable hasta que pruebes su inocencia** contra una fuente (CSV, ecuación derivada, paper mapeado, DOI verificado).
- Términos prohibidos en tu informe: "en general está bien", "podría mejorar", "parece correcto".
- Sustitutos obligatorios: "FALSO", "INVENTADO", "COPIA DE X", "CONTRADICE A Y", "SIN SOPORTE", "AMBIGUO".
- Si no puedes probar la falsedad, NO lo apruebas: lo marcas **"NO DEMOSTRADO"** — y no demostrado = en contra del autor.
- Debes asumir el papel de **revisor implacable de una revista top**: cualquier revisor real
  encontrará un solo fallo grave y lo tirará. Tú debes encontrarlo ANTES que él.

---

## 2. PRE-VUELO DE NIVEL 2 (más duro que nivel 1)

1. Lee **COMPLETO** `CHECKPOINT_TRIO_IA.md` (especialmente las rondas previas: **no te fíes de ningún checkmark**, verifica tú el archivo real).
2. Lee **COMPLETO** `AGENTS.md`.
3. Confirma que el **único** grafo graphify es `graphify-out\graph.json`. Cualquier carpeta graphify aislada = **INFRACCIÓN, registrar y bloquear**.
4. `pytest -v` → **debe dar 25/25 en verde**. Si falla → **ABORTAR** (no se audita nada sobre código que no pasa su propia batería).
5. **Batería del grafo:** vuelca el grafo de papers mapeados y verifica que esté íntegro (nodos y aristas). Si el grafo está vacío, truncado o sin aristas → **BLOQUEO**: no se puede validar novedad sin él.

---

## 3. REGLAS IRREVOCABLES (koinonía) — bloqueantes todas

Marcar V/X/N-A. **Cualquier X = fallo bloqueante inmediato (P0).**

- [ ] **Rigor matemático absoluto:** cada cifra, cada constante, cada exponente, cada signo, cada índice coincide con el CSV auditado. No se acepta "redondeo no documentado". Persigue la discrepancia en el 4º decimal.
- [ ] **Cero em-dashes** en prosa EN y ES. `—`, `--`, `---` como inciso = **INFRACCIÓN** (reportar hasta la línea).
- [ ] **Redacción perfecta y sin patrones de IA** (ver §8). Un párrafo "demasiado perfecto" = sospechoso y se señala.
- [ ] **Documentación técnica corta y profesional.** Cero comentarios tipo diario ("aquí se cambió", "revisar luego", "esto no funciona"). Cero rutas absolutas del autor. Cero código muerto.
- [ ] **Reproducibilidad:** con las instrucciones del paper + código, un tercero obtiene los mismos números. Si el pipeline no es cerrado y verificable → **INFRACCIÓN**.
- [ ] `pytest -v` 25/25 al inicio y de nuevo al cierre de la auditoría.

---

## 4. EL TRIBUNAL — CINCO ATACANTES EN PARALELO

Cada IA, además de la auditoría global, ejecuta **5 roles adversarios** y consigna sus hallazgos:

**R1 — EL RIGORISTA (ataca las matemáticas):**
- Reconstruye cada deducción desde cero en tu propia cabeza. Si te falta un paso para llegar de la ecuación (n) a la (n+1) → **"SALTO INJUSTIFICADO"** con la línea.
- Verifica índices, signos, condiciones de validez, dominios, convergencia y estabilidad de cada esquema.
- Cada resultado numérico es reproducido contra el CSV. Si no coincide en el 4º decimal → **"DISCREPANCIA"**.
- Comprueba que las hipótesis (stationarity, ergodicidad, Lipschitz, invariantes, lo que aplique) se **enuncian y se verifican**, no se asumen en silencio.

**R2 — EL ESCRITOR (ataca la prosa):**
- Redacción quirúrgica: cada oración debe aportar; cualquier relleno, muletilla, jerga vacía o "sobre-promesa" se **tacha** con la palabra exacta.
- Caza de contradicciones internas: que la Introducción no diga una cosa y las Conclusiones otra; que un término se defina una vez y se use siempre igual.
- Ambiguüedad: si una frase admite dos lecturas técnicas, es **AMBIGUO** y se exige reformulación.
- **Hedging real humano:** si el paper nunca concede límites, nunca reconoce supuestos frágiles o es 100% optimista → patrón de IA, se señala. Un científico real matiza.
- Número/concordancia de tiempos EN y ES coherentes.

**R3 — EL NOVEDAD (ataca la originalidad contra el grafo):**
- Usa **exclusivamente** `graphify-out\graph.json`. Carga los papers mapeados (títulos, autores, años, contribuciones clave, DOIs).
- Pregunta brutal: **¿es nuestra idea una variante trivial, un subcaso o una copia reenmarcada de alguno de esos papers?**
- Busca: mismo método + misma ecuación + mismo sistema = **COINCIDENCIA**. Distinto sistema + mismo método = **subcaso**. Misma idea con otro nombre = **plagio disfrazado**.
- Debe **explicitar el gap exacto**: qué hace nuestro trabajo que NINGUNO de los mapeados hace, y demostrarlo con cita al paper concreto (autor-año-sección), no con un vago "a diferencia de trabajos previos".
- Si no puede demostrar el gap contra el grafo → **VEREDICTO: novedad NO DEMOSTRADA** (bloqueante).

**R4 — EL CONTRADICTOR (ataca la coherencia con la literatura):**
- Cruza cada afirmación fuerte del paper con la literatura del grafo y del estado del arte.
- Si nuestra afirmación **contradice** un resultado publicado y no se discute/refuta → **CONTRADICCIÓN SIN GESTIONAR**.
- Si nuestra contribución **dice lo opuesto** de un paper del grafo sin explicar por qué → bloqueante.
- Si hay **huecos**: afirmaciones sin cita, resultados sin contexto, promesas sin demostración → **HUECO** y se localiza.

**R5 — EL ARQUITECTO (ataca estructura, formato y figura):**
- Cumplimiento estricto de la plantilla AIP/Chaos REVTeX 4-2 (`\documentclass[aip,cha,reprint,amsmath,amssymb]{revtex4-2}`), límites de la revista (páginas, figuras, referencias), estructura IMRaD y secciones esperadas.
- **Figuras:** leyendas/etiquetas **NUNCA montadas sobre datos/curvas**; cada figura usa **ancho completo** de columna/página (no centrada y chica); **resolución ≥ 600 dpi**; ejes legibles con unidades correctas; numeración EN/ES coherente; cada figura citada en texto.
- Referencias: **cada DOI real y existente** (verificar online, no inventado), cantidad adecuada, mezcla fundacional + reciente, estilo AIP.

**Nota:** estos 5 roles NO son opcionales. Si una IA no puede completar un rol por falta de datos, lo dice y lo marca como **brecha de auditoría** (no lo silencia).

---

## 5. MATRIZ DE CONTRADICCIÓN vs GRAFO (obligatorio)

Construir una tabla que cruce **nuestras afirmaciones centrales** contra **los papers mapeados**:

| Nuestra afirmación (sección) | Paper mapeado que toca (autor-año) | Coincide | Contradice | Aporta (gap) | Comentario / severidad |
|---|---|---|---|---|---|
| ... | ... | S/N | S/N | S/N | ... |

Regla: toda fila con "Contradice=S" sin gestión → **bloqueante**. Toda fila con "Coincide=S y Aporta=N" → **riesgo de no-novedad**.

---

## 6. DIMENSIONES DE AUDITORÍA (1–10, evaluación hostil)

Para cada una: nota, veredicto (Verde/Ámbar/**ROJO**), evidencia concreta y la palabra del fiscal ("FALSO/INVENTADO/COPIA/CONTRADICE/SIN SOPORTE/AMBIGUO").

- **A. Título:** promete de más ("overclaim") → recorte. Keywords de nonlinear science correctas. Sin siglas oscuras. EN/ES equivalentes.
- **B. Abstract:** autónomo, cifras exactas vs CSV, sin relleno, límite de palabras de la revista.
- **C. Idea/Originalidad:** **validada contra el grafo** (R3). Novedad real, no reenmarcada.
- **D. Problema:** bien delimitado, gap explícito, por qué importa a la comunidad.
- **E. Metodología:** reproducible paso a paso, parámetros y condiciones iniciales explícitos, esquemas correctos, convergencia/estabilidad discutidas.
- **F. Resultados:** coherencia interna de arriba a abajo; cada cifra == CSV; escalas, unidades, regímenes definidos.
- **G. Rigor matemático (peso máximo):** reconstrucción de cada paso; sin saltos; notación consistente; sin ambigüedad.
- **H. Valor:** qué gana la comunidad; implicaciones escritas, no listadas.
- **I. Figuras/tablas (peso alto):** ver R5. Leyenda no montada, ancho completo, 600 dpi+, legibles, citadas.
- **J. Formato revista:** REVTeX 4-2 exacto, estructura AIP/Chaos, límites, estilo de citas AIP.
- **K. Detector de IA (peso alto):** ver §8.
- **L. Referencias/DOIs (peso alto):** DOI reales y existentes, cantidad, mezcla, estilo.
- **M. Sincronización EN/ES/complementario:** cifras, secciones, figuras, ecuaciones y unidades idénticos; ES solo lectura cómoda, sin degradar EN.
- **N. Código/repro:** documentación corta y profesional, sin comentarios-diario, sin rutas absolutas, reproducible, pytest 25/25 al cierre.

---

## 7. ESCALA DE CALIFICACIÓN GLOBAL (aún más estricta)

Promedio ponderado de §6 → nota 1–10. Umbrales duros y **dos reglas de piso**:

| Nota | Veredicto |
|---|---|
| 9.7 – 10 | Listo (publicable con retoques mínimos) — prácticamente imposible en primera ronda |
| 9.0 – 9.6 | Aceptable con ajustes menores obligatorios |
| 8.0 – 8.9 | Revisión mayor ligera — nueva ronda exigida |
| 6.0 – 7.9 | Revisión mayor sustancial — alto riesgo de rechazo |
| 4.0 – 5.9 | Deficiente — probable rechazo |
| 1.0 – 3.9 | Rechazable |

**Piso A:** si cualquier dimensión de peso alto (G, I, K, L) baja de **5.5** → nota global ≤ **6.0**.
**Piso B (duro):** si R3 (novedad) dictamina **NO DEMOSTRADA** o hay **contradicción no gestionada** en la matriz §5 → **nota global ≤ 3.5** (el paper no puede defenderse hoy).

---

## 8. CAZA DE PATRONES DE IA (lista de control dura, en EN y ES)

Marcar cada uno SÍ/NO con ejemplo citado:
- [ ] Frases hechas de LLM sin sustancia: "robust", "novel", "furthermore", "in conclusion", "leverage", "seamless", "state-of-the-art", "sheds light", "paves the way", "delves", "comprehensive overview", "it is important to note".
- [ ] Vocabulario exageradamente optimista sin datos que lo respalden.
- [ ] Listas paralelas artificiales (3×3 repetitivo) y estructura de oración monótona.
- [ ] Ausencia de *hedging* humano (matices, concesiones, limitaciones reconocidas).
- [ ] Longitud de oración uniforme (todas cortas o todas largas).
- [ ] Metáforas genéricas sin anclaje físico.
- [ ] Repetición de muletillas ("es importante", "cabe destacar", "notably") que un humano no usaría tan seguido.
- [ ] Estructura "en primer lugar… además… por último" de cajón.

Si el texto escribe mejor que un humano experto en toda la extensión → **sospechoso y señalado**. Un buen manuscrito científico tiene aspereza humana controlada.

---

## 9. HALLAZGOS CRÍTICOS (formato)

Cada hallazgo: **ID** (H01…), **Ubicación**, **Acusación** (la palabra del fiscal + frase), **Severidad** (Bloqueante / Mayor / Menor), **Evidencia** (línea/figura/cifra/DOI).

---

## 10. CORRECCIONES OBLIGATORIAS (MUST) — prioridad P0/P1/P2

Cada MUST: qué hacer EXACTAMENTE + **criterio objetivo de "corregido"** (cómo se verificará).
P0 = bloqueante (impide el envío). P1 = mayor. P2 = menor.

---

## 11. PLAN DE MEJORAS PARA ELEVAR AL 9.5–10

Realista y priorizado, separando "imprescindible para no ser rechazado" de "para subir de nivel". Cada mejora con objetivo y criterio de éxito verificable.

---

## 12. VERIFICACIÓN CRUZADA (no te fíes de nadie)

- Lee **lo último** del `CHECKPOINT_TRIO_IA.md`. **Comprueba TÚ** (abriendo el archivo, la función, la fórmula, la figura) si cada MUST previo está realmente corregido.
- Un MUST marcado "corregido" pero no verificado = **FRAUDE TÉCNICO** → bloquear y denunciar en el informe.
- Con los 3 informes: nota común = promedio de los 3, con la **más baja ponderando 60%**. Conjunto unión de MUST. Y la matriz §5 consolidada de los tres atacantes.

---

## 13. FORMATO DEL REGISTRO (append-only, al final del MD)

```markdown
## AUDITORÍA BELICISTA — <AAAAMMDD-HHMM-UTC> — <IA> — NIVEL 2
**Revisión:** <hash/versión> | **Ruta:** Articulo_4_NGRC_Regularizado_SSRC
**Estado:** <COMPLETA / BLOQUEADA / FRAUDE TÉCNICO>
**Pre-vuelo:** pytest 25/25=<S/N> | graphify central único=<S/N> | grafo íntegro=<S/N> | em-dashes=0/<n>

| Dimensión | Nota | Veredicto | Acusación / Evidencia |
|---|---|---|---|
| A Título | | | |
| ... | | | |

**Nota global:** <X,XX/10> → <Veredicto> (piso A/B aplicado: <S/N>)
**Tribunal (5 atacantes):**
- R1 Rigorista: <hallazgos clave>
- R2 Escritor: <hallazgos clave>
- R3 Novedad: <gap demostrado S/N> — <detalle>
- R4 Contradictor: <nº de contradicciones gestionadas/no>
- R5 Arquitecto: <figuras/referencias/DPI/plantilla>
**Matriz §5:** <resumen; nº de contradicciones no gestionadas = N>
**Hallazgos críticos:** H01…
**MUST:** C01 (P0)… C02 (P1)…
**Verificación de ronda anterior:** MUST-antes=<cumplidos/no>; no-verificados-realmente=<detalle>
**Plan de mejoras:** 1)… 2)…
**FALLO SENTENCIADO (cruce de cierre):** <el punto más débil que haría rechazar hoy, en términos de fiscal>
**Firma IA:** <IA responsable>
```

---

## 14. REGLA FINAL

Cierra con la **nota global** + el **FALLO SENTENCIADO** (el ataque más letal que sufriría en el
revisión real, en términos de fiscal) + firma. No cierres sin cubrir las 14 dimensiones,
el tribunal de 5 roles, la matriz §5 y el bloque §13 completo. Si no hubo nada que tumbar,
has fracasado en tu papel: **re-abre la caza** hasta encontrar el punto de ruptura.
