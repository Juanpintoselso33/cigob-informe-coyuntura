---
madr: 4
id: '0313'
estado: 'rechazado'
nota_estado: 'Rechazado el filtro por convocante: la fuente no identifica quién convoca cada sesión. El cálculo de `veto_quorum` no cambia (sigue ADR-0308).'
fecha: 2026-09-15
cinturon: 'politica'
indice: 'ITCP'
indicadores: [veto_quorum]
relacionado: ['0091', '0308']
ambito: 'ITCP · `veto_quorum` · fuente HCDN'
origen: 'Juan (Slack, 15-sep): "Sesiones caídas, que solo cuenten las sesiones caídas PROPUESTAS por el oficialismo"'
---

# ADR-0313 — El quórum caído no se puede filtrar por quién convocó: la fuente no lo dice

## Contexto y planteo del problema

El pedido: que `veto_quorum` cuente sólo las sesiones caídas por falta de
quórum que fueron **convocadas por el oficialismo** — hoy el denominador
incluye toda sesión ordinaria, extraordinaria o especial convocada para tratar
temas, sin distinguir quién la convocó (`_sesiones_desde_indice()`,
`_veto_quorum_tasa_12m()`, `fetch_veto_quorum()` en `scripts/politica.py`).

Antes de tocar el cálculo, la pregunta empírica: **¿la fuente permite saber
quién convocó cada sesión?** Se buscó en las cuatro superficies que el
colector y sus vecinos ya tocan.

## Opciones consideradas

- **Filtrar el denominador por convocante, leyéndolo de la fuente** — no
  aplicable: el campo no existe en ninguna de las cuatro fuentes revisadas
  (ver abajo).
- **Aproximar el convocante por una heurística de nombre de bloque** (p. ej.
  "si el primer firmante del expediente pertenece a LLA") — descartada sin
  implementar: el proyecto tiene una regla dura contra medir con una proxy lo
  que el nombre del indicador no mide, y una heurística de autoría de
  expediente no es "quién convocó la sesión" — una sesión especial reúne
  varios expedientes de distintos bloques bajo un solo temario (ver evidencia
  del 23-jun-2026 abajo), así que no hay un "convocante" único derivable por
  expediente.
- **No tocar el cálculo y documentar el hueco** — elegida.

## Decisión

**No se modifica `fetch_veto_quorum()` ni `_sesiones_desde_indice()`.** El
universo de sesiones caídas sigue siendo el de ADR-0308 (todas las
convocadas para tratar temas, sin distinguir convocante). Cambiar el cálculo
sin el dato sería copiar un rezago del pedido en vez de medirlo — la regla de
método de este repo es la inversa.

### Evidencia: las cuatro superficies que se revisaron, y qué tienen

1. **Índice de sesiones** (`https://www.hcdn.gob.ar/sesiones/`, lo que lee
   `_sesiones_desde_indice()`): cada fila es un `<a>` con el tipo y la fecha
   en el texto del enlace — p. ej. *"6° Reunión - 5° Sesión Ordinaria Especial
   - (26/08/2026)"*, *"4° Reunión - Expresiones en Minoría - (23/06/2026)"*.
   Sin bloque ni convocante en ningún lado del título.
2. **Página de detalle de una reunión** (`sesion.html?id=…`): tres pestañas —
   Asistencia, Diario de Sesiones, Temario. Se inspeccionó por completo el
   HTML de la reunión 4 (23/06/2026, en minoría): sin una sola mención a
   "convoc", "bloque" (fuera del menú de navegación) ni "solicit" con
   contenido relevante.
3. **El temario de esa misma reunión** (PDF embebido en la página, decodificado
   y leído entero): lista seis expedientes, todos pedidos de informes o mociones
   de censura contra el Jefe de Gabinete (Adorni) — es decir, una sesión que
   por su propio contenido es un pedido **opositor**, no oficialista. El
   temario no declara bloque ni autor por expediente, y una sesión especial
   puede mezclar expedientes de distintos bloques bajo un temario único: no
   hay "el convocante" de la sesión, en el sentido de un solo actor.
4. **El dataset CKAN subyacente** (`sesiones`, resource
   `4ac70a51-a82d-428b-966a-0a203dd0a7e3`, el mismo que dio origen al criterio
   de ADR-0091): los campos son `REUNION_NO`, `REUNION_TIPO`, `SESION_NO`,
   `REUNION_INICIO`, `REUNION_FIN`, `SESION_CAMARA`, `PERIODO_ID`. Ningún
   campo de convocante ni de bloque.

El dataset `proyectos-parlamentarios` (que sí usan `fetch_eficacia_legislativa`
y otros) tiene un campo `AUTOR` (nombre de un diputado) por expediente — pero
es autoría de un **proyecto**, no convocatoria de una **sesión**, y napear
nombre de diputado → bloque → oficialismo/oposición es exactamente la
heurística que se descartó arriba.

### Qué haría falta para poder hacerlo

Un registro que documente el pedido formal de sesión especial (art. 35/37 del
reglamento de Diputados: firmas de un tercio del cuerpo) con la identidad de
los firmantes o del bloque peticionante. No se encontró ese registro
publicado ni en CKAN ni en el sitio de sesiones. Si existiera en otra fuente
(el Diario de Sesiones en su versión taquigráfica completa, más allá del
temario, podría nombrar quién pidió la palabra para fundar la convocatoria),
haría falta parsear la versión taquigráfica completa de cada sesión — un
trabajo de una escala distinta al de este ticket, y sin garantía de que el
dato esté ahí de forma estructurada.

## Más información

### La objeción del equipo, sin actuar sobre ella

El comentario del equipo en el doc de ajuste de indicadores (sección
POLÍTICA) señala que "Sesiones caídas por falta de quórum" es un indicador de
relevancia dudosa frente a "Producción legislativa" y "Eficacia parlamentaria"
— junto con "Normas desafiadas" y "Bloqueo sostenido en el recinto", hacen
más al preciosismo del análisis legislativo que a información significativa
sobre el pulso del gobierno. Queda registrado acá como contexto para que Juan
lo resuelva; no es una decisión de este ADR sacar o fusionar un indicador.
