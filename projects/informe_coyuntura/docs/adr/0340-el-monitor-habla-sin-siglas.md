---
madr: 4
id: '0340'
estado: 'aceptado'
fecha: 2026-09-24
cinturon: 'transversal'
archivos: ['config.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/macro.py', 'scripts/gestion.py', 'scripts/politica.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/charts.ts', 'web/src/components/IndicadorModal.astro', 'web/src/components/CinturonCard.astro', 'web/src/components/Evolucion.astro', 'web/src/components/DimensionesEvolucion.astro', 'web/src/pages/[slug].astro', 'web/src/pages/metodologia/index.astro', 'web/src/lib/fichas.ts', 'web/src/pages/metodologia/[id].astro', 'data/politica/cobertura_judicial_movimientos.json', 'tests/test_siglas_publicas.py', 'tests/test_la_ficha_no_se_queda_atras.py']
relacionado: ['0190', '0311']
ambito: 'Presentación · cómo se nombran los índices, los organismos y las estadísticas en toda la web, fichas metodológicas incluidas'
origen: 'Pedido de Luis (equipo CiGob), septiembre de 2026: «sacar todas las siglas y acrónimos innecesarios» del Monitor. Juan fijó las tres reglas de abajo.'
---

# ADR-0340 — El Monitor habla sin siglas

## Contexto y planteo del problema

ADR-0190 fijó las siglas públicas de los cuatro índices (ITCM, ITCP, ITCIS,
ITCG) y ADR-0311 sacó las siglas internas de los rótulos de las cards. El resto
de la web siguió hablando en siglas: en producción, la página de impacto social
nombraba «ITCIS» 29 veces y la de macro «ITCM» 28, y la prosa de cada cinturón
mezclaba INDEC, EPU, BCRA, IPC, UTDT y códigos de planilla (SDDS, A3500, IMIG)
sin decir nunca qué son. Un lector que no es del equipo no tiene cómo saber que
«ITCP» es el índice del cinturón político, ni que «EPU» es un índice de
incertidumbre de política.

## Factores de decisión

- El Monitor se lee fuera del equipo: la sigla de un índice propio no le dice
  nada a quien no la inventó.
- La sigla sigue haciendo falta como identificador interno (BigQuery, claves
  del snapshot, manuales), pero eso no obliga a mostrarla: un identificador
  vive en los datos, no en el texto que se lee.
- Una sigla de organismo o estadística es legítima si se la presenta: el
  problema no es que exista, es que aparezca sin su nombre.
- Los rótulos cortos de las cards ya se limpiaron en ADR-0311; alargarlos
  rompe la grilla.

## Opciones consideradas

1. Glosario de siglas al pie de cada página.
2. Reemplazar las siglas de los índices por su nombre y presentar las demás la
   primera vez que aparecen en cada bloque de texto.
3. Sacar todas las siglas, incluidas las de organismos.

## Decisión

**Opción 2**, con tres reglas:

1. **Los índices se nombran en llano**: «índice macroeconómico» (ITCM),
   «índice político» (ITCP), «índice de impacto social» (ITCIS), «índice de
   gestión» (ITCG). `config.NOMBRES_PUBLICOS` y `nombre_publico()` los dan a
   `publicar.py`; `datos.ts::indiceDe` los declara en `corto`/`Corto`, y el modal
   en su `INDICE_CFG`. La sigla queda como identificador: la matriz de validación
   cruzada conserva `indice` (la usan la web y `bigquery_export.py`) y suma
   `nombre`, que es lo que se lee. **La regla vale también para las fichas
   metodológicas** (`fichas.ts` y `metodologia/[id].astro`): ver la corrección
   del 5-oct-2026 abajo.
2. **Las siglas técnicas internas salen del texto visible**: referencias
   «ADR-XXXX», el formato «CSV» (el botón dice «Descargar los datos
   (planilla)»), y códigos de planilla o de sistema (SDDS, A3500, IMIG, RON,
   CDF/MS, DEX+DIM, GTFS-RT, B100) que se reescriben en llano, también en las
   citas de fuente cuando eran jerga pura. En el historial de cambios de
   cada ficha, el número de ADR se guarda en el campo `adr` de la entrada: la
   página no lo muestra y la trazabilidad no se pierde.
3. **Organismos y estadísticas se presentan**: en cada bloque de prosa (una
   descripción, una leyenda de fórmula, una nota metodológica, un texto de
   `publicar.py`) la primera mención lleva el nombre completo con la sigla entre
   paréntesis, y después puede ir la sigla. Si la sigla no se repite, alcanza con
   el nombre. LLA, PJ y CABA quedan como están. Los rótulos de las cards
   (`LABELS`) no se tocan (ADR-0311).

### Consecuencias

- Las siglas de los índices quedan en cero en todas las páginas fuera de las
  fichas, incluidos los datos embebidos de los modales. Medido sobre el HTML
  construido, sin `<script>` ni `<style>`: portada 31 → 20 siglas en
  mayúscula, macro 93 → 51, política 72 → 34, impacto social 87 → 41, gestión
  46 → 35, metodología 159 → 98. Lo que queda son las citas de fuente (la
  sección «Fuentes» y los chips de organismo del diccionario), los rótulos de
  cards, LLA/PJ/CABA, CIGOB como nombre del marco, y siglas ya presentadas en su
  bloque.
- Las citas de fuente que escriben los colectores (`macro.py`, `gestion.py`,
  `politica.py`) cambian en el código pero llegan a la web con la próxima
  corrida nocturna; lo mismo el texto de los pares acoplados a propósito, que
  sale de `validacion_externa.py`. Hasta entonces el snapshot conserva la
  versión anterior.
- Quedan fuera, a propósito: `output/informe.md` (material de ingesta), los
  avisos de Slack, los comentarios de código y las claves internas.
- Un texto que un colector copia de un archivo cargado a mano es la cita de la
  fuente, no un rótulo del Monitor. Igual se escribe en llano: las notas de
  conciliación de cargos judiciales decían «los CSV» de datos.jus.gob.ar y
  desde el 5-oct-2026 dicen «las planillas».

### Corrección del 5-oct-2026: las fichas no tenían por qué quedar afuera

La versión del 24-sep exceptuaba a las fichas metodológicas con un único
argumento: que la ficha documenta el índice como objeto técnico y que la sigla
es su identificador estable. Ese argumento justifica guardar la sigla en los
datos, no mostrarla al lector, y ninguna de las tres opciones consideradas
explicaba por qué las fichas debían quedar fuera de la regla. Las fichas son
públicas (`/metodologia/…`) y son justamente donde entra quien quiere entender
el índice: el pedido de Luis aplicaba ahí igual que en el resto. Antes de la
corrección, las 84 páginas de metodología mostraban 137 siglas de índices,
194 referencias «ADR-XXXX» y 11 «CSV». Ya existía, además, una decisión
editorial anterior (06-jul-2026, comentada al tope de `fichas.ts`) que decía
que las fichas públicas no muestran números de ADR, y esta excepción la
contradecía.

Lo que se cambió:

- `fichas.ts`: los índices se nombran en llano; las entradas del historial que
  empezaban con «ADR-XXXX:» o lo citaban en el texto pasan el número al campo
  `adr` (95 números distintos, ninguno perdido), y las menciones en la prosa
  se reescriben con la fecha de la decisión o se quitan cuando sólo remitían
  al ADR. «CSV» pasa a «planilla».
- `metodologia/[id].astro`: los títulos, chips y oraciones que armaban la sigla
  desde el código («Puntaje en el ITCM», «Cómo entra al ITCM») usan el nombre
  llano de `indiceDe`.
- `tests/test_siglas_publicas.py` deja de exceptuar a las fichas (probado
  insertando una sigla: falla), y `test_la_ficha_no_se_queda_atras.py` acepta
  el campo `adr` como registro del ADR.

Medido sobre el HTML construido el 5-oct-2026: cero siglas de índices y cero
«ADR-XXXX» en las 84 páginas de metodología. Quedaban tres «CSV» en la de
cobertura judicial, que vienen del snapshot de la corrida anterior y se van con
la próxima.

### Confirmación

`tests/test_siglas_publicas.py` suma cuatro guardas: ningún archivo de display
—fichas incluidas desde el 5-oct-2026— muestra la sigla de un índice, un
«ADR-XXXX» o «CSV» fuera de comentarios; el snapshot tampoco (salvo la clave de la matriz
cruzada y las citas de archivos de fuente); la matriz trae `nombre`; y los tres
lugares que declaran el nombre llano coinciden. Las dos primeras se probaron
rompiéndolas. La suite completa, `gate_calidad.py`, `npm run build` y
`tsc --noEmit` en verde.

## Pros y contras de las opciones

### Opción 1 — Glosario al pie

- Bueno, porque no toca la prosa.
- Malo, porque obliga al lector a ir y volver, y las siglas de los índices
  propios siguen sin decir qué miden.

### Opción 2 — Nombre llano para los índices y presentación de las demás

- Bueno, porque cada párrafo se entiende solo y la sigla sigue existiendo como
  identificador en los datos.
- Malo, porque algunos párrafos quedan más largos.

### Opción 3 — Sin ninguna sigla

- Bueno, porque es la regla más simple.
- Malo, porque «INDEC» o «IPC» son de uso corriente y reemplazarlas siempre por
  el nombre completo vuelve ilegibles los textos que las repiten.

## Más información

Continúa [[0311-el-titular-sin-escala-y-los-rotulos-sin-siglas-internas]] (los
rótulos de las cards). Las siglas de [[0190-renombrar-los-indices]] quedan
como identificadores internos, sin mostrarse en ninguna página.
