# Task 9 Report: Reescribir `docs/cinturon_politica.md`

## Status: DONE

## Contexto encontrado antes de escribir

- `docs/cinturon_politica.md` (previo) describía el cinturón bajo el **promedio simple** de 9 indicadores, con `cohesion_bloque` como "carga manual (placeholder 78%)" y `gobernadores_alineamiento` también manual. No mencionaba los 3 indicadores nuevos ni ninguna paramétrica.
- `scripts/itcp.py`, `scripts/politica.py` (con `fetch_cohesion_bloque`, `fetch_cohesion_bloque_senado`, `fetch_adhesion_reformas_provincial`, reutilización de `gestion.fetch_protestas_caba`), `data/politica/ajustes_itcp.json` y `data/politica/manuales.json` (ya sin `cohesion_bloque`) están **implementados y committeados** en la rama `feature/itcp-cohesion-bloque-politica` — confirmado por `.superpowers/sdd/progress.md` (Plan 2, tasks 1-7 completas) y por lectura directa del código.
- **Hallazgo relevante para el alcance de esta tarea**: el brief describe `docs/cinturon_gestion.md` como si ya tuviera "tabla de dimensiones y pesos" (post ADR-0013/ITCG). Verifiqué con `git log` que **eso es falso en el archivo actual**: `cinturon_gestion.md` fue tocado por última vez en el commit `2ced3e6`, ANTES del commit `4320ac6` que introdujo la paramétrica ITCG — el archivo en disco todavía describe el promedio simple viejo. `docs/cinturon_macro.md`, en cambio, sí refleja su paramétrica (ITCM) con tabla de dimensiones/pesos, tabla de bandas por indicador y bandas de interpretación. Consulté al advisor sobre este hallazgo antes de escribir: confirmó pivotear a `cinturon_macro.md` como plantilla estructural para la sección Encuadre/estructura del índice, conservando el esqueleto de `cinturon_politica.md` (tabla "Indicadores activos" + "Detalle por indicador" + "Ejecución" + "Notas de mantenimiento") para el resto. No se tocó `cinturon_gestion.md` (fuera de alcance de esta tarea) — queda señalado acá como hallazgo para quien lo retome.
- No existe todavía `docs/adr/0036-itcp-parametrica-politica.md` (Task 8 del plan, aparentemente no ejecutada todavía o en paralelo) — evité citarlo como si existiera. Solo cité `docs/adr/0037-cohesion-bloque-scraping-bloqueado-antibot.md`, que sí existe y que el brief pide explícitamente mencionar para `cohesion_bloque`. Ningún otro cinturón (macro/gestión/vida) cita números de ADR en su doc — mantuve esa misma convención (cero ADRs "sprinkled", solo el 0037 pedido).

## Qué cambié

Reescritura completa de `docs/cinturon_politica.md` (207 líneas netas, +139/-68):

1. **Encuadre**: agregada la fórmula del ITCP, la tabla de 5 dimensiones/pesos (poder_legislativo 30%, alianzas_territoriales 25%, cohesión_interna 20%, conflicto_social 15%, imagen_voto 10%, con pesos internos por indicador), la tabla de bandas por indicador (transcripta 1:1 de `itcp.py::BANDAS_ITCP`, verificada), la nota de interpolación lineal entre anclas (motor común `parametrica.py`), las bandas de interpretación agregada, y una línea sobre `ajustes_itcp.json` (mecanismo de override, sin regla automática — a diferencia de ITCM). Se preservó la nota metodológica de mayo 2026 sobre el ICG UTDT.
2. **Indicadores activos**: tabla actualizada a 12 filas (los 8 preexistentes + `cohesion_bloque_senado`, `adhesion_reformas_provincial`, `protestas_caba`; `cohesion_bloque` marcado explícitamente "bloqueado en producción").
3. **Score actual del cinturón**: cité el valor real de mi propia corrida en vivo (ver sección siguiente), con nota de continuidad explicando el salto metodológico vs. el score viejo (4,7/10 → 3,5/10 no es mejora real, es cambio de métrica — mismo patrón que ITCG).
4. **Detalle por indicador**: reescribí las 9 secciones existentes (agregué el puntaje de banda real aplicado a cada una) y agregué 3 secciones nuevas:
   - `cohesion_bloque_senado`: automático y funcionando en producción (vía independiente de Diputados).
   - `adhesion_reformas_provincial`: automático, alcance honesto (adhesión fiscal puntual, no proxy de `gobernadores_alineamiento`).
   - `protestas_caba`: reutilizado de gestión, lectura distinta (contexto allá, puntúa acá), puntúa sobre `var_vs_2023` no sobre el conteo crudo.
   - **`cohesion_bloque` reescrito con honestidad explícita**: el scraper (índice de Rice) está implementado, testeado y con backfill listo, pero **bloqueado en producción** por el muro anti-bot de `votaciones.hcdn.gob.ar` (cité `docs/adr/0037-...`). El valor publicado hoy (78%) es el **placeholder manual pre-Rice** congelado desde abril 2026, no una medición Rice real — no se presenta como "funcionando".
5. **Ejecución**: actualicé los códigos de salida (12 indicadores esperados; exit 1 es hoy el estado normal, no una falla).
6. **Notas de mantenimiento**: agregué entradas para el bloqueo de `cohesion_bloque` (con los caminos a evaluar del ADR-0037), `cohesion_bloque_senado`, `adhesion_reformas_provincial`, bandas provisionales, y ajustes vía `ajustes_itcp.json`.
7. Se conservó sin cambios la sección "Limitaciones documentadas de CKAN HCDN" (sigue vigente para `eficacia_legislativa`/`veto_quorum`/`comisiones_caidas`).

## El valor real de ITCP citado y cómo se obtuvo

Corrí el pipeline real dos veces desde `projects/informe_coyuntura/`:

```
cd projects/informe_coyuntura
python scripts/politica.py
```

Segunda corrida (la que quedó reflejada en el doc, `output/cache/politica.json` con `generated_at: 2026-07-07T18:23:25`):

- **Salida de consola**: `[OK] politica: score=3.5 frescos=11/12` — **exit code 1**.
- **`itcp.valor = 64.7`**, **`itcp.banda = "moderadamente_aflojado"`**.
- **Tensión derivada (0-10) = 3.5**.
- 11 de 12 indicadores frescos: `cohesion_bloque` no llegó a producir un valor Rice en vivo (scraper bloqueado, ADR-0037) y degradó al placeholder manual pre-automatización (78%, `desactualizado: true`, `fecha_dato: 2026-04-01`).

Verifiqué con un script Python de una línea que TODOS los números que cité en el doc (puntaje por dimensión, `puntaje_banda` por indicador, valores crudos) coinciden exactamente con lo que produjo esta corrida — incluyendo un chequeo manual de la interpolación lineal entre anclas para 3 indicadores (`ratio_dnu`, `cohesion_bloque`, `protestas_caba`) contra la fórmula de `parametrica.puntaje_interpolado()`, para no citar un puntaje mal transcripto.

Nota: el mismo `output/cache/politica.json` ya tenía una corrida previa de otro agente en paralelo (`generated_at: 2026-07-07T17:54:55`, mismo ITCP=64.7) — mi propia corrida (18:23:25) reconfirmó el mismo resultado de forma independiente, así que no hay ambigüedad sobre qué número es "el real".

## Self-review

- **Completitud vs. spec**: los 12 indicadores, las 5 dimensiones con sus pesos (30/25/20/15/10) y pesos internos, las 4 bandas provisionales marcadas como tales, y el score real están todos cubiertos.
- **Honestidad sobre `cohesion_bloque`**: releí la sección tres veces para asegurar que ningún lugar del doc insinúa que el índice de Rice está "funcionando" — siempre se aclara que el valor publicado es el placeholder viejo, no una medición nueva.
- **No cité ADRs que no existen** (`0036`) y no "espolvoreé" ADRs donde los documentos hermanos no lo hacen — solo el `0037` pedido explícitamente por el brief.
- **No toqué `cinturon_gestion.md`** pese a encontrar que está desactualizado respecto de su propia paramétrica — señalado como hallazgo, no corregido (fuera de alcance de esta tarea).
- **Verificación numérica cruzada**: todos los valores citados (ITCP, banda, tensión, puntajes por dimensión, puntaje_banda por indicador, valores crudos) fueron chequeados contra el JSON de cache real de mi propia corrida, no transcriptos de memoria del spec.
- **Consistencia de fuente**: la tabla de bandas del doc es una transcripción 1:1 de `scripts/itcp.py::BANDAS_ITCP` (no una reinterpretación).

## Concerns / limitaciones conocidas

- Ninguna que bloquee este DONE. La única nota es la staleness de `cinturon_gestion.md` mencionada arriba, que dejo señalada para una tarea futura (no es parte del alcance de la Task 9).

## Archivos modificados / commiteados

- `projects/informe_coyuntura/docs/cinturon_politica.md` — único archivo staged y commiteado.
- Commit: `bfb13f5` — `docs(politica): reescribe cinturon_politica.md reflejando la paramétrica ITCP` (rama `feature/itcp-cohesion-bloque-politica`).
- Verificado con `git show --stat HEAD`: 1 archivo, 207 líneas netas modificadas. `git status` confirma que ningún otro archivo (de los ~20 ya sucios en el árbol por otras tareas en paralelo) fue agregado al índice.
