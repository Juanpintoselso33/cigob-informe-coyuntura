# ADR-0123 — El ITVC entra al registro de circularidad (0%, y por qué)

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITVC · `procedencia_anclas.py` · `out_of_sample.py` |
| **Fecha** | 2026-07-20 |
| **Cierra** | El gap "ITVC sin medir" señalado en la auditoría metodológica del 2026-07-20 |
| **Continúa** | ADR-0103 (registro) · ADR-0120/0121 (los otros tres índices) |

## Contexto

El registro de circularidad (ADR-0103) clasifica **bandas** — los cortes que
convierten un valor crudo en puntaje. Los tres índices por bandas
(ITCM/ITCG/ITCP) estaban cubiertos; el ITVC no, porque **no tiene bandas**: cada
componente se rebasea a 100 = promedio del 4T-2023 y el índice promedia esos
niveles.

En la tabla metodológica del 2026-07-20 eso figuraba como "sin medir", que
sonaba a un control pendiente. Era un gap de la herramienta, no del índice: el
registro no le aplicaba tal como estaba escrito.

## Cómo se clasifica un índice sin bandas

La circularidad es el riesgo de fijar el criterio mirando lo que el gobierno ya
logró. En el ITVC **el ancla de cada componente es una fecha fija** —el arranque
del mandato, 4T-2023— no un rango observado. No hay cortes que elegir, así que
no hay dónde colar una calibración contra el período. Cada componente es
**conceptual por construcción**.

Verificado componente por componente: los 16 se rebasan a una fecha fija (14 al
4T-2023, `inseguridad` a ene-2024 por ADR-0032, también fija). Ninguno usa
percentiles observados ni rango del período.

**Resultado: ITVC 0% circular, 100% conceptual.** Es el único de los cuatro sin
una sola ancla de convención — no por mérito de calibración sino porque su
construcción no tiene el lugar donde la circularidad vive en los otros tres.

## La winsorización no es una excepción a esto

El único parámetro del ITVC que podía ser convención es el **techo de
winsorización a 140**. Se revisó su origen (ADR-0033): es **base + 40**, un tope
redondo con el criterio "el excedente de un boom no compensa", no un número
calibrado contra el boom observado —el 166,7 de motos es lo que el techo
*recorta*, no de donde *sale*—. Es un tope conceptual, mismo criterio que el
techo institucional de 85 del saldo comercial en el ITCM (ADR-0120). Se anota en
el motivo de los dos componentes que toca (endeudamiento y motos), no como
circularidad.

## Lo que "0% circular" NO quiere decir

No quiere decir que el ITVC no tenga limitaciones de anclaje. La base 4T-2023
**contiene la devaluación de diciembre de 2023**, de modo que parte de las
mejoras medidas es rebote del pozo — limitación real, ya declarada en la ficha
del índice y ajena a la circularidad (que es otra cosa: calibrar contra el rango
observado). El registro mide una cosa concreta; el 0% dice que esa cosa concreta
no está presente, no que el índice sea perfecto.

## Consecuencias

- Los cuatro índices quedan bajo el mismo control, con techo de trinquete
  (ADR-0105): ITCM 38% · ITCG 40% · ITCP 40% · **ITVC 0%**.
- El techo del ITVC se fija en 0,01: si algún día un componente pasara a
  anclarse al rango observado, la suite lo marca.
- `out_of_sample.py` (ADR-0104) excluye explícitamente al ITVC: ese test aplica
  las bandas de hoy a datos previos, y el ITVC no tiene bandas. La exclusión va
  en el consumidor, no en el registro — el ITVC pertenece al registro de
  procedencia, no al de out-of-sample.
- Sólo clasificación y comentarios; cero cambios de puntaje. El ITVC sigue en
  94,8.

Con esto se cierra el único gap que la auditoría metodológica del día había
dejado abierto.
