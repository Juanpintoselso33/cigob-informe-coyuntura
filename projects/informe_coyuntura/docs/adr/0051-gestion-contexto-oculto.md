---
madr: 4
id: '0051'
estado: 'aceptado'
fecha: 2026-07-11
cinturon: 'gestion'
archivos: ['scripts/publicar.py', 'web/src/lib/fichas.ts', 'tests/test_publicar.py']
supersede: ['0017']
relacionado: ['0053']
continuado_por: ['0189']
ambito: '`scripts/publicar.py` · `web/src/lib/fichas.ts` · `tests/test_publicar.py`'
---

# ADR-0051 — Gestión: las cards de contexto salen del tablero (regla pareja en los 5 cinturones)

| **Precedente directo** | ADR-0022 (`MACRO_OCULTOS`), ADR-0048 (`POLITICA_OCULTOS` + regla editorial), ADR-0049 (`ESPIRITU_OCULTOS`) — supersede la parte de VISIBILIDAD de ADR-0017/0023 (que las declararon contexto visible) |

## Contexto y planteo del problema

La regla editorial confirmada el 10-jul (ADR-0048) es que **el tablero solo
muestra lo que integra las dimensiones del índice**. Se aplicó a macro
(ADR-0022), a política (ADR-0048) y a espíritu de época (ADR-0049), pero
gestión seguía publicando sus 2 indicadores de contexto como cards visibles
bajo el bloque "No integran el índice":

- `alertas_manifestacion` (GCBA, GTFS-RT) — serie recién nacida, sin línea de
  base 2023 (ADR-0014).
- `protestas_caba` (ACLED) — no puntúa por razón declarada: puntuar volumen
  de protesta premiaría "menos marchas" (ADR-0017).

El usuario lo marcó el 2026-07-11 al ver el tablero de gestión: los
indicadores que no integran las dimensiones no deben aparecer.

## Opciones consideradas

- **Que puntúen para poder mostrarlos**: descartado — la razón por la que no
  puntúan es de fondo (ADR-0017: el volumen de protesta es un derecho
  ejercido, no un resultado de gestión), no un pendiente técnico.
- **Dejar el bloque de contexto visible solo en gestión**: descartado — era
  exactamente la inconsistencia señalada; la excepción no tenía una razón
  editorial distinta a la que ya se rechazó en política (ADR-0048, donde el
  editor descartó el patrón "cards de contexto visibles, estilo gestión").

## Decisión

`publicar.GESTION_OCULTOS = set(itcg.INDICADORES_CONTEXTO)` — los 2 se popean
del snapshot en `aplicar_scoring`, igual que los ocultos de macro, política y
espíritu. El bloque "Contexto" de la página de gestión desaparece solo (la
sección se renderiza únicamente si hay filas). **Nada deja de medirse**: los
colectores, stores (`piquetes_alertas.json`, `protestas_caba.json`) y series
siguen corriendo como seguimiento interno; las razones de no puntuar siguen
documentadas en `itcg.INDICADORES_CONTEXTO`. Las fichas metodológicas de
ambos se retiran de /metodologia (los ocultos no tienen ficha — precedente
`badlar`/`rotacion_gabinete`/`clima_electoral`); la ficha del ITCG y el
`dobleUso` de protocolo antipiquetes se reescriben para referir el
seguimiento interno en lugar de la card.

Con esto, los 5 cinturones quedan bajo la misma regla: **ningún cinturón
publica cards de contexto** — todo lo visible puntúa en su índice o score.

### Consecuencias

- El score del cinturón NO cambia (el contexto nunca puntuó); gestión pasa de
  17 tiles a 15.
- `protestas_caba` queda sin ninguna lectura pública (ya estaba oculto en
  política desde ADR-0048; ahora también en gestión) — su serie completa
  2018→hoy sigue en el pipeline interno y puede reincorporarse si una
  revisión futura lo pide.
- `alertas_manifestacion` sigue acumulando su serie GTFS-RT como insumo para
  automatizar el protocolo antipiquetes cuando tenga ~12 meses de historia
  (plan de ADR-0014, sin cambios).
- Las entradas de labels/unidades/descripciones/fórmulas de ambos quedan
  inertes en `web/src/lib/*` (precedente `rotacion_gabinete`); la excepción
  G3 de `protestas_caba` en `gate_calidad.py` queda inerte (el gate solo
  itera indicadores publicados).
- `tests/test_publicar.py::test_gestion_itcg_reconcilia` pinea la composición
  nueva: contexto publicado == {} y los 2 ausentes del snapshot.
