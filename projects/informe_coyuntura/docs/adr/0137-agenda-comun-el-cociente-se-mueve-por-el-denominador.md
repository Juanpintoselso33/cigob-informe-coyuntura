---
madr: 4
id: '0137'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
indicadores: [poder_legislativo]
ambito: 'cinturón político (ITCP), dimensión `poder_legislativo`'
---

# ADR-0137 — Agenda común: el cociente se mueve por el denominador

- **Relacionados**: ADR-0131 (protocolo), ADR-0061/0062/0063 (`eficacia_legislativa`),
  ADR-0095 (publicar el resultado incómodo), ADR-0042

## Contexto y planteo del problema

El aporte externo propone **Agenda Común**: cuánto comparten el Ejecutivo y el
Congreso la agenda legislativa. ADR-0131 lo listó como pendiente y anotó que lo
que faltaba era **«atribución causa-efecto»** — es decir, se lo dio por bloqueado
por un problema metodológico, no de fuente.

Ese diagnóstico era evitable. No hace falta atribuir causa-efecto si en lugar de
preguntar «¿el Congreso trata esto *porque* el Gobierno lo propuso?» se pregunta
**«de lo que el Congreso efectivamente sancionó, ¿cuánto nació en el
Ejecutivo?»**. Eso es composición, no causalidad, y se mide con un campo.

Porcentaje de leyes sancionadas cuyo expediente inicial nace en el Ejecutivo,
ventana móvil de 12 meses:

```
2023-12   5,9%      2024-07  28,6%      2025-02  19,6%      2025-10  46,7%
2024-03   9,7%      2024-10  11,9%      2025-05  21,7%      2025-12  52,9%
2024-05  17,4%      2024-12  11,9%      2025-09  18,9%      2026-07  24,0%
```

Rango 5,9% a 52,9%: **nace discriminando** (ADR-0042). Y **no es redundante con
`eficacia_legislativa`**, que ya está en el índice: r = **+0,071** en niveles y
**−0,051** en diferencias sobre 32 meses solapados. Mide algo genuinamente
distinto — `eficacia_legislativa` es la tasa de acierto del Ejecutivo sobre lo
que él mismo presenta; ésta es la composición de lo que el Congreso produce.

### Pero el cociente se mueve por el denominador

**El conteo de leyes de origen Ejecutivo es notablemente estable: oscila entre 5
y 10 durante todo el período.** Lo que se derrumbó es la producción legislativa
propia del Congreso.

El salto de sep-2025 (37 leyes en ventana, 18,9%) a oct-2025 (15 leyes, 46,7%)
—28 puntos en un mes— **no es que el Ejecutivo haya duplicado su agenda**: es
que salieron 22 leyes de la ventana de golpe.

Publicar el cociente solo diría «el Gobierno domina la agenda legislativa como
nunca». Lo que efectivamente pasó es que **el Congreso dejó de legislar y la
producción del Gobierno quedó plana**. Son dos hechos distintos y el cociente
los funde en uno solo, atribuyéndole al numerador un movimiento del denominador.

Se suma el ruido: en la ventana más flaca (15 leyes) **una sola ley mueve la
serie 6,7 puntos porcentuales**.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

1. **La fuente queda validada y la serie versionada** en
   `data/politica/agenda_comun_relevamiento.json`, con la serie anual desde 2008,
   la mensual de 12 meses, los conteos crudos y la correlación contra
   `eficacia_legislativa`.
2. **No se incorpora como cociente solo.** Un indicador cuyo movimiento principal
   viene del denominador y se lee como si viniera del numerador es engañoso,
   aunque cada número sea correcto. Si se incorpora, tiene que ser **como dos
   números**: el volumen de producción legislativa y la participación del
   Ejecutivo en ella. La card debe mostrar el `n` de la ventana junto al
   porcentaje, siempre.
3. **Queda pendiente la decisión editorial de orientación**, igual que en
   ADR-0134 y ADR-0135: no es evidente qué significa para la capacidad política
   del Gobierno que su participación en la producción legislativa suba cuando lo
   que la hace subir es que el Congreso produce menos.

### Consecuencias

- Se corrige el diagnóstico de ADR-0131: el obstáculo **no era** la atribución
  causa-efecto. Reformulando la pregunta de causalidad a composición, el
  indicador es medible con un campo de un dataset oficial. Queda anotado porque
  el mismo reencuadre puede destrabar otros pendientes.
- El hallazgo sobre el derrumbe de la producción legislativa propia del Congreso
  es material para el informe **con independencia de que este indicador se
  construya o no**: son 15 a 17 leyes en las ventanas de 12 meses de fines de
  2025 contra 42 a 47 un año antes.
- Si se construye, `validacion_externa.py` necesita el indicador en
  `ITCP_SERIES` en el mismo cambio — el checklist que ya falló dos veces
  (`bloqueo_sostenido` y `mora_familias`).

## Más información

### La fuente

El dataset `leyes-sancionadas` del CKAN de HCDN —el mismo portal que el proyecto
ya usa para `eficacia_legislativa`— trae 1.340 leyes con `EXPEDIENTE_INICIAL` y
`SANCION_DEFINITIVA`. **La letra del expediente codifica el origen** (formato
`NNNN-X-AAAA`):

| código | S | D | PE | JGM | sin parsear |
|---|---|---|---|---|---|
| leyes | 666 | 498 | 161 | 15 | **0** |

Cero registros sin parsear sobre 1.340. Historia hasta 2008.

> **Detalle operativo que cuesta tiempo**: hay dos recursos (CSV y JSON) y el del
> JSON devuelve **404** en `datastore_search`. Hay que resolver el `resource_id`
> por `package_show` tomando el que tiene `datastore_active`, y paginar de a 500
> como hace `_hcdn_paginate`.
