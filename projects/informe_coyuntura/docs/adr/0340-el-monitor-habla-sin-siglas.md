---
madr: 4
id: '0340'
estado: 'aceptado'
fecha: 2026-09-24
cinturon: 'transversal'
archivos: ['config.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/macro.py', 'scripts/gestion.py', 'scripts/politica.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/charts.ts', 'web/src/components/IndicadorModal.astro', 'web/src/components/CinturonCard.astro', 'web/src/components/Evolucion.astro', 'web/src/components/DimensionesEvolucion.astro', 'web/src/pages/[slug].astro', 'web/src/pages/metodologia/index.astro', 'tests/test_siglas_publicas.py']
relacionado: ['0190', '0311']
ambito: 'Presentación · cómo se nombran los índices, los organismos y las estadísticas en toda la web salvo las fichas'
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
- La capa metodológica sí necesita la sigla: la ficha documenta el índice como
  objeto técnico y la sigla es su identificador estable (BigQuery, manuales).
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
   `nombre`, que es lo que se lee. **Excepción: las fichas metodológicas**
   (`fichas.ts` y `metodologia/[id].astro`) conservan las siglas.
2. **Las siglas técnicas internas salen del texto visible**: referencias
   «ADR-XXXX», el formato «CSV» (el botón dice «Descargar los datos
   (planilla)»), y códigos de planilla o de sistema (SDDS, A3500, IMIG, RON,
   CDF/MS, DEX+DIM, GTFS-RT, B100) que se reescriben en llano, también en las
   citas de fuente cuando eran jerga pura.
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
- Un texto que un colector copia de un archivo cargado a mano (el conteo de
  cargos judiciales cita «los CSV» de datos.jus.gob.ar) es la cita de la fuente,
  no un rótulo del Monitor, y se deja.

### Confirmación

`tests/test_siglas_publicas.py` suma cuatro guardas: ningún archivo de display
fuera de la capa metodológica muestra la sigla de un índice, un «ADR-XXXX» o
«CSV» fuera de comentarios; el snapshot tampoco (salvo la clave de la matriz
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

- Bueno, porque cada párrafo se entiende solo y la ficha sigue teniendo su
  identificador.
- Malo, porque algunos párrafos quedan más largos.

### Opción 3 — Sin ninguna sigla

- Bueno, porque es la regla más simple.
- Malo, porque «INDEC» o «IPC» son de uso corriente y reemplazarlas siempre por
  el nombre completo vuelve ilegibles los textos que las repiten.

## Más información

Continúa [[0311-el-titular-sin-escala-y-los-rotulos-sin-siglas-internas]] (los
rótulos de las cards) y deja las siglas de
[[0190-renombrar-los-indices]] para la capa metodológica.
