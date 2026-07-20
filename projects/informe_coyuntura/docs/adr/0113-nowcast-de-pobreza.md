# ADR-0113 — La pobreza se publica, con la única fuente mensual que existe

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITVC · `pobreza_nowcast` (contexto) · colector `utdt_nowcast_pobreza` |
| **Fecha** | 2026-07-20 |
| **Origen** | Auditoría de Vida Cotidiana, punto 3.6 (pobreza/indigencia) |
| **Corrige** | ADR-0111, que cerró el punto sin buscar lo suficiente |

## Qué corrige de ADR-0111

ADR-0111 descartó la pobreza con dos argumentos. El primero sigue en pie; el
segundo era una rendición temprana:

1. **`brecha_salario_cbt` ya mide contra la línea de pobreza** — cierto, y por
   eso la *línea* no entra como componente.
2. *"Es semestral con rezago largo, en un cinturón mensual"* — **falso como
   afirmación general.** La tasa del INDEC lo es; la medición de pobreza en la
   Argentina, no.

Existe el **Nowcast de Pobreza de Martín González-Rozada (UTDT)**: proyecta la
estructura del mercado laboral y los deciles de ingreso total familiar de la EPH
contra la canasta básica total, y publica un informe **todos los meses** con el
semestre móvil vigente. Es la única medición de pobreza de frecuencia mensual
del país, y es la que sigue la prensa.

Encontrarla exigió cinco pasos —notas de prensa, perfil de RPubs (congelado en
2021), un enlace acortado de X, la página del autor en la UTDT— y ADR-0111 se
detuvo en el primero.

## De dónde sale el dato

`https://www.utdt.edu/profesores/mrozada/pobreza` lista los informes en PDF, uno
por mes. El `fname` de cada uno es un timestamp, así que el mayor es el más
reciente sin necesidad de parsear fechas.

**Por qué el PDF y no otra vía**: la serie estuvo en RPubs hasta 2021 y hoy se
publica como app Shiny más estos informes. Scrapear Shiny exige mantener un
websocket y se rompe con cada cambio de la app; el PDF es el formato estable y
citable.

Del informe se extraen el semestre, la tasa y el intervalo de confianza al 95%.
Hoy: **31,6% para enero-junio de 2026, IC [30,1% – 33,0%]**.

## Se publica como CONTEXTO, no puntúa

Tres razones, en orden de peso:

1. **No hay base 4T-2023.** Los informes publicados arrancan en 2025; sin el
   valor del trimestre de referencia no hay forma de rebasearlo a 100 como al
   resto de los componentes. Reconstruirlo desde otra fuente sería mezclar dos
   mediciones distintas en la misma serie.
2. **Es una estimación de terceros con incertidumbre declarada** (±1,5 pp). El
   resto de los componentes son mediciones, no proyecciones.
3. **Solapa parcialmente con `brecha_salario_cbt`**, que compara ingreso contra
   la misma canasta.

Como card de contexto conserva lo que la auditoría buscaba —la variable de mayor
carga simbólica del cinturón, visible y actualizada— sin forzar la escala ni
duplicar señal en el puntaje.

## Consecuencias

- El colector baja **sólo el informe más reciente** en la corrida diaria. Con
  `historico=True` recorre los 23 publicados y arma la serie; se reservó para
  `descargar_series` porque son ~20 MB de PDFs.
- Los informes viejos tienen otro layout y no parsean: `_leer_informe` devuelve
  `None` en vez de propagar, para que eso no impida leer los recientes. De 23
  publicados, 18 parsean hoy.
- El tablero pasa a **61 indicadores**. El ITVC no cambia: sigue en 94,7 con sus
  16 componentes.

## Lo que queda afuera

La **tasa oficial del INDEC** (`64.2_POBLACION_NUA_0_0_34_74`, semestral,
nacional, desde 2003) es la referencia autorizada y tiene la historia larga que
al nowcast le falta: 40,1% (S2-2023) → 52,9% (S2-2024) → 28,2% (S2-2025).
Publicarla junto al nowcast —una como ancla histórica, el otro como pulso
mensual— es una mejora posible y no se hizo acá para no abrir dos cards de lo
mismo sin decisión editorial.
