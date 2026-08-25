---
madr: 4
id: '0243'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'vida'
indicadores: [consumo_supermercados]
archivos: ['scripts/vida_cotidiana/collectors/indec_supermercados.py', 'scripts/publicar.py', 'scripts/descargar_series.py', 'web/src/lib/datos.ts', 'tests/test_consumo_supermercados.py']
relacionado: ['0225', '0220']
ambito: 'Cinturón vida cotidiana · ITVC · `consumo_supermercados` · de dónde sale la base del índice y qué período se publica'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «la base real es 2017=100»'
---

# ADR-0243 — La base del índice la declara la fuente

## Contexto y planteo del problema

La card de `consumo_supermercados` publicaba `índice (2004 = 100,
desestacionalizado)`. La Encuesta de Supermercados vigente usa **base
2017=100**, y la serie que el colector baja **no tiene ningún punto anterior a
enero de 2017**: el rótulo no describía nada.

Sobrevivió por la razón de siempre: era un **literal repetido en tres archivos**
—`publicar.py`, `descargar_series.py` y `web/src/lib/datos.ts`— y no había nada
contra qué compararlo. La API declara la base en el campo `units` de sus
metadatos (`"Índice base 2017=100"`) y el colector nunca lo pedía.

La auditoría del 25-ago-2026 señaló tres cosas en esta card. Dos se resuelven
acá y **la tercera no**, así que conviene separarlas:

| Hallazgo | Estado |
|---|---|
| Base rotulada 2004=100 cuando es 2017=100 | **corregido** |
| Revisión de mayo (83,2 → 83,0) no incorporada | **ya se incorporaba sola**; ahora hay test |
| Junio de 2026 (82,1) no publicado | **abierto** — ver más abajo |

Sobre la segunda: el colector pide el histórico completo en cada corrida, así
que una revisión del INDEC entra sola. Eso era cierto y no estaba probado, que
en este repo es la forma habitual de que deje de serlo.

## Factores de decisión

- **Un metadato que la fuente publica no se transcribe a mano.** Tres copias de
  un rótulo son tres oportunidades de que quede viejo, y ninguna de que se note.
- **Un rótulo que no se puede verificar contra nada no debería poder
  publicarse.**
- **La tolerancia a revisiones tiene que estar probada**, no deducida del
  diseño.

## Opciones consideradas

- **A — Cambiar el literal de 2004 a 2017** en los tres archivos.
- **B — Leer la base de los metadatos de la API** y derivar el rótulo de ahí,
  con el colector como única fuente.

## Decisión

**Opción B.** El colector pide `metadata=full`, extrae el año base de `units` y
devuelve la unidad ya armada. `publicar.py` la propaga; `descargar_series.py` y
la web quedan alineados. Si la API dejara de declarar la base, el colector
**falla** en vez de inventar un rótulo.

Se agrega además un control que no estaba en la auditoría y que salió al mirar
esto: si la serie trajera puntos **anteriores al año base declarado**, hay dos
bases empalmadas y el nivel no es comparable. También hace fallar. Es
exactamente la contradicción que había —una serie desde 2017 rotulada
2004=100—, sólo que ahora se detecta.

### Consecuencias

- La unidad pasa a `índice (2017 = 100, desestacionalizado)` en card, serie y
  web. **El valor y el puntaje no cambian**: el rebase del ITVC es contra
  4T-2023 y nunca usó la base de la fuente.
- Un cambio de base del INDEC se refleja solo.

### Lo que queda abierto: el rezago del espejo

La auditoría pide publicar **junio de 2026 = 82,1**. No se hizo, y no por
descuido:

- El INDEC publicó junio el **21-ago-2026** (informe `super_08_26…`), con la
  serie desestacionalizada en 82,1 y mayo revisado a 83,0. Verificado en el PDF
  oficial, Cuadro 1.
- La **API de series de datos.gob.ar todavía termina en mayo-2026** con el valor
  sin revisar (83,222). El espejo tarda unas dos semanas más que la publicación.
- El PDF del informe **no es direccionable**: su nombre lleva un hash
  (`super_08_262444C24851.pdf`) y no hay listado desde donde derivarlo. Se
  probaron el sitemap, `/rss`, `/feed`, el directorio `uploads/informesdeprensa/`
  y el patrón corto sin hash: el sitio devuelve **200 con el shell HTML de la
  SPA para cualquier ruta**, así que ni siquiera se puede distinguir un archivo
  que existe de uno que no.

Cerrar esto requiere una fuente nueva —descubrir y parsear el informe de prensa,
o incorporar los cuadros del INDEC— y eso es una decisión de alcance, no una
corrección. **Hasta entonces la card publica el último punto que la API espeja**,
que es lo que viene haciendo, y `gate_calidad.MAX_DIAS` sigue en 140 por ese
rezago encadenado.

Lo que sí queda cubierto: el día que la API espeje junio, la card pasa a 82,1 y
mayo se corrige a 83,0 **sin intervención**, y hay un test que lo prueba con esos
números exactos.

### Confirmación

`tests/test_consumo_supermercados.py`:

- la base sale de la fuente y da 2017;
- **`2004` no puede volver a aparecer** en la unidad;
- si la fuente cambiara a 2021=100, el rótulo la sigue;
- sin base declarada, el colector levanta;
- una serie con puntos anteriores a su base declarada levanta;
- **la revisión real** —mayo 83,222 → 83,0 con junio 82,1 detrás— reemplaza la
  lectura anterior en vez de conservarla, y la card pasa a junio.

Probado rompiéndolo: repuesto el literal `2004 = 100`, fallan cinco guardas.

## Pros y contras de las opciones

### A — Cambiar el literal

- Bueno, porque es inmediato.
- Malo, porque deja tres copias del dato en tres archivos y el próximo cambio de
  base vuelve a quedar viejo en silencio.

### B — Leer la base de la fuente

- Bueno, porque el rótulo no puede contradecir a la serie que describe.
- Bueno, porque un metadato ausente pasa a ser un fallo ruidoso.
- Malo, porque agrega una dependencia de `metadata=full` en la llamada.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_impacto_social.md`, caso 17.
- [[0225-el-supermercado-deja-de-validar-el-indice-y-pasa-a-integrarlo]] define
  el componente.
- [[0220-la-ficha-se-ata-al-colector-y-al-adr]] es la familia de la que este
  problema forma parte: prosa que describe un dato que ya cambió.
