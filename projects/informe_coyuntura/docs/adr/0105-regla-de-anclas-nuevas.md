# ADR-0105 — Regla para las anclas nuevas, con trinquete

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Todo indicador que se incorpore a un índice paramétrico |
| **Fecha** | 2026-07-20 |
| **Cierra** | El punto 3.2 de la auditoría de gestión (circularidad) |
| **Continúa** | ADR-0103 (procedencia), ADR-0104 (por qué no se puede validar hacia atrás) |

## Por qué hace falta

ADR-0103 midió cuánta de la puntuación descansa en anclas calibradas contra el
período que se está midiendo: entre 51% y 83% según el índice. ADR-0104
estableció que ese stock **no se puede auditar hacia atrás** — no hay ventana
previa para 36 de los 42 indicadores, y donde la hay, la prueba no distingue una
banda mal puesta de un cambio de régimen real.

Queda entonces un solo lugar donde la circularidad se puede *evitar* en vez de
medirse: el momento en que se define un ancla nueva. Ahí todavía se puede elegir
el criterio **antes** de mirar el dato.

## La regla

Al incorporar un indicador puntuable, las anclas se justifican en este orden, y
**se usa la primera opción viable**:

1. **Referencia externa** — un estudio publicado, la práctica de otros
   gobiernos, un estándar internacional. (Como ACIJ para `ratio_dnu` o
   Directorio Legislativo para `eficacia_legislativa`.)
2. **Valor con significado propio** — el cero, la paridad, el 100%, un umbral
   legal o institucional. (Como `brecha_obra_publica`, anclada alrededor del
   cero por ADR-0088.)
3. **Historia del propio indicador anterior a dic-2023**, si existe y es
   suficiente.
4. **Convención calibrada sobre el rango observado** — sólo si las tres
   anteriores fallaron, y declarando por qué.

**La búsqueda de las opciones 1-3 se documenta aunque falle.** Un "no hay
referencia externa" sin las consultas escritas al lado no es un hallazgo: es una
suposición que cierra el tema. El proyecto ya se quemó con eso tres veces en un
día (ADR sobre cuenta corriente y demanda eléctrica: las fuentes existían y
aparecieron al variar los términos de búsqueda). Las consultas van en el ADR del
indicador, de modo que el negativo sea auditable y alguien pueda refutarlo.

La procedencia elegida se declara en `PROCEDENCIA` de
`scripts/procedencia_anclas.py`. Eso ya es obligatorio: sin entrada, la suite
falla (ADR-0103).

## El trinquete

Una regla de orden de preferencia se erosiona sola. Cada indicador nuevo con
anclas de conveniencia es defendible **de a uno**; lo que nadie defiende es la
suma, porque nadie la mira.

`TECHOS`, en `scripts/procedencia_anclas.py`, congela el estado del 2026-07-20:

| índice | circular | sin declarar |
|---|---|---|
| ITCM | 83,0% | 45,3% |
| ITCP | 61,0% | 20,6% |
| ITCG | 51,0% | 16,3% |

La suite falla si alguno **sube**. Incorporar un indicador con ancla circular
sigue siendo posible —a veces no hay alternativa— pero obliga a editar el techo
a mano, y ese cambio aparece en el diff, que es donde se puede discutir. Deja de
ser gratis y silencioso.

`sin_declarar` tiene techo propio y más estricto por una razón: una convención
sin alternativa externa a veces es inevitable, pero una convención **sin
declarar** nunca lo es. Sólo hay que escribir de dónde salió. Que ese número
suba no tiene defensa posible.

Un tercer test exige que el techo **baje cuando el número baje** (holgura máxima
de 5 puntos). Un techo que quedó muy por encima del valor real dejó de frenar
algo; bajarlo es lo que convierte una mejora puntual en una que no se puede
deshacer sin que alguien lo note.

Los tres disparan de verdad — se verificó degradando `ratio_dnu` de `externa` a
`convencion` (ITCP 60,9% → 66,6%, falla) y a `sin_declarar` (20,6% → 26,3%,
falla). Un trinquete que nunca se probó no se sabe si frena.

## Lo que esta regla no hace

**No baja el stock heredado.** Los techos de hoy son altos porque el proyecto
es lo que es: 30 de 42 indicadores no existían antes de dic-2023. La regla
gobierna el flujo, no el stock. Bajarlo es el trabajo que ADR-0103 dejó
listado, en este orden:

1. Los cinco indicadores con historia previa desaprovechada
   (`iaf_transferencias` desde dic-2018, `ipc_total`, `recaudacion`, `emae_ia`,
   `saldo_comercial_12m`): se puede anclar contra gobiernos anteriores y hoy no
   se hace.
2. Las siete bandas `sin_declarar` del ITCM: no requieren recalibrar nada, sólo
   escribir de dónde salieron — y si no se puede reconstruir, decirlo.

**No convierte una convención en algo mejor de lo que es.** Si tras buscar en
serio no aparece referencia externa, la respuesta correcta es calibrar contra lo
observado y declararlo `convencion`, no forzar una externa endeble para que el
número del trinquete quede lindo. Mover un peso para que un test dé mejor está
prohibido por ADR-0045, y esto es el mismo vicio con otra cara.
