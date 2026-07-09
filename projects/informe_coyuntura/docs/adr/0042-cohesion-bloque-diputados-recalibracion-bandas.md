# ADR-0042 — cohesion_bloque (Diputados): recalibración de bandas ITCP con backfill mensual real

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Ámbito** | `scripts/itcp.py` (`BANDAS_ITCP["cohesion_bloque"]`) · `tests/test_itcp.py` |

## Contexto

ADR-0041 (mismo día) construyó la serie mensual real de `cohesion_bloque`
(Diputados): 31 puntos, dic-2023 a jun-2026, ventana rolling de 90 días,
gracias a la caché permanente por acta. Con esa serie en la mano, el mismo
chequeo que ya se le había hecho a `alineamiento_senadores_prov` (ADR-0038)
y `cohesion_bloque_senado` (ADR-0039) el mismo día: ¿las anclas vigentes
(90/75/60/40, una fórmula ad hoc original, nunca validada contra datos
propios) siguen siendo razonables?

No. El rango real observado es 96,7–100,0 (media 99,2, mediana 99,8): el
techo de 90 saturaba en **31 de 31 meses (100%)** — ni un solo punto de la
serie completa quedó por debajo del ancla superior. Es el caso de
saturación más extremo de los tres indicadores recalibrados hoy (Senado
saturaba 25/29 = 86%, alineamiento 8/29 = 28%): el bloque propio de LLA en
Diputados es mucho más grande que en el Senado, así que un solo disidente
mueve mucho menos el promedio, y la cohesión observada es naturalmente más
alta y más apretada (apenas 3,3 puntos de rango) que en cualquiera de los
otros dos indicadores de esta familia.

Regla del proyecto (lanzamiento público agosto 2026): no esperar más datos
sobre un gap PROVISIONAL cuando ya hay serie real disponible — recalibrar
ahora.

## Decisión

Anclas nuevas: **99,9 / 99,0 / 98,0 / 97,0** (antes 90/75/60/40),
chequeadas contra los 31 puntos reales: 14/7/4/3/3 por banda (de la más
alta a la más baja), todas con datos reales — a diferencia de la
recalibración de `cohesion_bloque_senado`, que dejó un hueco vacío en una
banda intermedia, acá las 5 bandas tienen observaciones propias.

14 de los 31 meses (45%) tuvieron cohesión perfecta (100,0 exacto) — esos
puntos son indistinguibles entre sí por diseño matemático (el índice de
Rice con cero disidencias siempre da exactamente 100), así que caen todos
en la misma banda superior sin importar dónde se trace el corte; no es un
defecto de la calibración, es la naturaleza del dato.

Tramos extremos siguen ABIERTOS (`INF`/`-INF`) — mismo criterio ya
documentado en ADR-0038/0039: un tramo superior finito desplazaría la
saturación al punto medio del motor interpolado en vez de resolverla.

## Opciones consideradas

- **Copiar las anclas de `cohesion_bloque_senado` (95/90/85/80)** —
  descartada: esas anclas se calibraron contra un rango de 22,2 puntos
  (77,8–100,0); aplicadas al rango de Diputados (96,7–100,0, apenas 3,3
  puntos) seguirían saturando en la enorme mayoría de los meses, mismo
  problema que se está corrigiendo, solo con un número distinto.
- **Forzar 5 bandas equidistribuidas (~6 puntos cada una)** — descartada:
  con 14/31 meses en el valor idéntico 100,0, no existe ningún corte que
  logre eso; los cortes 99,9/99,0/98,0/97,0 son los números redondos que
  mejor separan la porción no empatada de la serie (96,7–99,9, 17 puntos
  distintos) sin inventar bandas vacías.

## Consecuencias

- `cohesion_bloque` sale del estado PROVISIONAL con datos propios, mismo
  camino que `alineamiento_senadores_prov` (ADR-0038) y
  `cohesion_bloque_senado` (ADR-0039) — de los indicadores con banda propia
  del ITCP, solo `adhesion_reformas_provincial` y `protestas_caba` (ver
  ADR-0036) siguen provisionales.
- El puntaje de `cohesion_bloque` para valores dentro del rango históricamente
  observado (96,7–100,0) ahora varía de verdad según el mes en vez de
  aplanarse siempre en 100 — afecta directo el 65% de la dimensión
  "cohesión interna" del ITCP (20% del índice total).
- Si la cohesión real de Diputados se mueve fuera del rango observado hasta
  ahora (por ejemplo, cae por debajo de 96,7% en algún mes futuro), el
  puntaje seguirá interpolando correctamente gracias al motor de
  `parametrica.puntaje_interpolado` (ADR-0021) — no hace falta volver a
  tocar las anclas solo porque aparezca un valor nuevo dentro de un rango
  razonable; recalibrar de nuevo tendría sentido si el rango observado se
  desplaza de forma sostenida, no ante un punto aislado.
