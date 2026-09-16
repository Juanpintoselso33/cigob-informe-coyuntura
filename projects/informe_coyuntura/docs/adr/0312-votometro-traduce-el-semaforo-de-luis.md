---
madr: 4
id: '0312'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'politica'
indicadores: [votometro_ventaja_lla]
archivos: ['scripts/itcp.py', 'web/src/lib/fichas.ts']
corrige: ['0121']
ambito: 'ITCP · `votometro_ventaja_lla` · semáforo'
origen: 'Doc «260915 Ajuste de los Indicadores» — umbrales de Luis, en colores de semáforo'
---

# ADR-0312 — El votómetro traduce el semáforo que pidió Luis, no ya los márgenes simétricos

| **Corrige** | ADR-0121 (los cortes ±5/±15 pp de la ventaja LLA−PJ) |

## Contexto y planteo del problema

Luis pidió otros umbrales para la ventaja LLA−PJ, y los pidió en **colores de
semáforo**, no en puntaje:

- más de +8 puntos → verde
- entre +8 y +5 → amarillo
- entre +5 y 0 → naranja
- negativo → rojo

El semáforo de un indicador en este proyecto no se declara: se **deriva** del
puntaje 0-100 vía la tensión equivalente (`parametrica.color_de_puntaje`,
cortes de tensión 4/6/8 → puntaje 60/40/20 — ADR-0181). Traducir los cortes de
Luis exige entonces elegir las anclas de `BANDAS_ITCP["votometro_ventaja_lla"]`
de modo que esos cruces de color caigan exactamente en los pp que pidió, **no**
inventar una escala de colores propia por fuera del motor.

El equipo señaló además que la redacción de la ficha estaba en orden confuso
("entre +5 y +15" en vez de "entre +15 y +5").

## Opciones consideradas

- **Reanclar `BANDAS_ITCP` para que los cruces de color caigan en 8/5/0/negativo**
  — elegida.
- **Declarar el color a mano por fuera del motor paramétrico** — descartada:
  rompería la única fuente de verdad del semáforo (`parametrica.color_de_puntaje`)
  para un solo indicador, y el color dejaría de ser consistente con la lectura
  del resto del ITCP.
- **Dejar las anclas de ADR-0121 y sólo redactar la ficha con los colores** —
  descartada: la ficha mentiría, porque con las anclas viejas el corte real
  verde/amarillo cae en +9 pp (no en +8) y el naranja/rojo en −5 (no en 0) —
  verificado antes de descartar la opción.

## Decisión

Las anclas nuevas: `(8, INF, 60), (2, 8, 40), (-2, 2, 20), (-INF, -2, 0)`.

El motor deriva el puntaje 0-100 por **interpolación lineal entre anclas**
(ADR-0021): para una banda finita el ancla es su punto medio, para una abierta
es su borde finito. Con esta tabla, las anclas quedan exactamente en **8, 5
(medio de 2–8), 0 (medio de −2–2) y −2** — los mismos pp que usó Luis para
+8/+5/0, más un borde inferior en −2 para que el rojo no quede plano en el
mismo valor en 0 y en cualquier negativo (sin un ancla debajo de 0, `puntaje(0)`
y `puntaje(−1)` habrían sido idénticos y jamás se habrían podido distinguir en
color).

Verificado numéricamente en `tests/test_itcp.py::test_banda_votometro_semaforo_traduce_umbrales_de_luis`,
que evalúa 8 valores de ventaja contra su color, incluidos los dos cortes
exactos (+5 y 0):

| ventaja (pp) | puntaje interpolado | tensión | color |
|---|---|---|---|
| +12 | 60,0 | 4,0 | verde |
| **+8** (exacto) | 60,0 | 4,0 | **verde** |
| +6 | 46,7 | 5,33 | amarillo |
| **+5** (exacto, límite amarillo/naranja) | 40,0 | 6,0 | **amarillo** |
| +2 | 28,0 | 7,2 | naranja |
| **0** (exacto, límite naranja/rojo) | 20,0 | 8,0 | **naranja** |
| −1 | 10,0 | 9,0 | rojo |
| −10 | 0,0 | 10,0 | rojo |

Los dos cortes exactos (+5 y 0) caen del lado que fija la convención del motor
(low exclusivo / high inclusivo en la tensión: `tensión ≤ tope` — ADR-0181), no
de una elección editorial nueva.

### Consecuencia real: el tope de puntaje de este indicador baja de 100 a 60

Con las anclas de ADR-0121, una ventaja de +15 pp puntuaba 100 (el máximo del
índice). Con las anclas nuevas, **el máximo alcanzable es 60**: cualquier
ventaja ≥ +8 pp es "apenas verde", no "puntaje pleno". Es una consecuencia
directa e inevitable de anclar el cruce verde/amarillo en el pp exacto que
pidió Luis (+8) — si el ancla superior valiera más de 60, el tramo intermedio
(+5 a +8) se corta antes de tiempo y una ventaja de +6 o +7 ya sale verde en
vez de amarillo (verificado al construir la tabla: con el ancla superior en
100, +7 pp puntúa 70 → tensión 3,0 → verde, incumpliendo el pedido).

Esto cambia dos tests que asumían el tope viejo de 100
(`test_calcular_itcp_pondera_dimensiones`, `test_calcular_itcp_renormaliza_ante_faltantes`):
con `votometro_ventaja_lla` en su valor más alto observado (+15 pp), el ITCP
"todo en el máximo" pasa de 100,0 a **96,1** (la dimensión imagen_voto entra
con 60 en vez de 100, pesa 7% del índice).

### Ficha

Reescrita en orden descendente y con los cortes nuevos:

> "El puntaje del índice se asigna por bandas de la ventaja, interpolado entre
> anclas: más de +8 puntos → verde, el más alto; entre +8 y +2 → amarillo, con
> el punto medio de la banda en +5 pp; entre +2 y −2 → naranja, con el punto
> medio en 0 pp; −2 o menos → rojo, el más bajo."

El texto nombra tanto los bordes reales de la tabla (8, 2, −2) como los pp de
lectura de Luis (+5, 0) — son números distintos por construcción (borde de
banda vs. punto medio interpolado) y las dos lecturas son correctas al mismo
tiempo.

### Validación externa

`scripts/validacion_externa.py` reconstruye la serie histórica del ITCP contra
las bandas vigentes; se corrió de nuevo después de este cambio (ver la
secuencia del PR) porque la reconstrucción usa las anclas nuevas para todo el
histórico.

## Más información

Sigue sin resolverse (no es alcance de este ADR) la objeción del equipo sobre
la relevancia relativa de "Sesiones caídas por falta de quórum" frente a
"Producción legislativa" y "Eficacia parlamentaria" — ver ADR-0313, que la
documenta para la dimensión de poder legislativo, no para ésta.
