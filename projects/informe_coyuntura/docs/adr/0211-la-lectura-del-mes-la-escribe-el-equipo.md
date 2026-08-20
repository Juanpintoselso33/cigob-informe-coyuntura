---
madr: 4
id: '0211'
estado: 'aceptado'
fecha: 2026-08-20
cinturon: 'transversal'
archivos: ['web/src/components/Bluf.astro', 'web/src/contenido/lectura-del-mes/', 'scripts/gate_calidad.py', 'web/public/dashboard.css']
relacionado: ['0165', '0199']
ambito: 'El bloque "La lectura del mes" de la portada'
origen: 'Devolución de Luis Babino sobre el artifact de agosto: reemplazó la síntesis automática por un párrafo editorial escrito a mano'
---

# ADR-0211 — La lectura del mes la escribe el equipo, y si no la escribió nadie la portada lo dice

## Contexto y planteo del problema

El bloque que abre la portada —"La lectura del mes"— se armaba **solo**, desde
el snapshot: qué cinturones están en rojo, cuál es el más exigido, qué
dimensión aporta más tensión, cuál es el barbarismo dominante. Nunca quedaba
viejo ni vacío, y lo declaraba al pie: *"Síntesis generada automáticamente a
partir del tablero de indicadores"*.

Es correcto y es poco. Una síntesis derivada puede decir **qué** número se
movió, pero no puede decir qué significa ese movimiento para el proyecto de
gobierno que el informe evalúa. La devolución editorial de agosto de 2026 lo
mostró de la forma más directa posible: el editor borró la síntesis y escribió
en su lugar un párrafo que ninguna regla podría haber derivado del tablero —
que la macro cierra y la política no explota, y que el problema del proyecto no
está ni en la gestión ni en la economía sino en la paciencia ciudadana que se
mide en el supermercado.

El problema no es cómo publicar ese párrafo. Es qué pasa el mes siguiente.

**El pipeline publica todas las noches, la lectura editorial es mensual.** Si
el texto se fija en el código, el 1 de septiembre el nocturno amanece
publicando la lectura de agosto bajo el título "Argentina · Septiembre 2026", y
nada falla: `gate_calidad.py` mira estructura, frescura de fuentes e
invariante card-contra-serie, y los tests de reconciliación comparan el
snapshot consigo mismo. **Ninguna de las dos cosas mira la vigencia de la
prosa.** Es la misma clase de agujero que abrió
[[0199-el-marco-conceptual-vuelve-en-metodologia]]: texto publicado que ningún
gate puede evaluar.

## Factores de decisión

- **Lo escrito y lo calculado no se pueden confundir.** La nota al pie actual
  existe para eso, y si desaparece sin reemplazo el lector pierde la única
  señal de qué está leyendo.
- **La portada no puede quedar en blanco.** Sea cual sea el mecanismo, un mes
  sin texto escrito tiene que seguir publicando algo cierto.
- **Un mes sin texto no es una falla de integridad.** El snapshot es correcto;
  lo que falta es trabajo editorial. Bloquear la publicación entera por eso es
  el error que [[0133-una-fuente-demorada-no-tira-abajo-el-pipeline]] ya
  descartó para las fuentes demoradas.
- **La defensa tiene que ser estructural, no una nota en un calendario.** Si la
  única garantía de que el texto se actualice es que alguien se acuerde, el
  fallo va a ocurrir.

## Opciones consideradas

1. **Archivo por período, con fallback a la síntesis automática.**
2. Texto editorial fijo en el componente, sin síntesis automática.
3. Campo `lectura_editorial` en el snapshot, escrito por `publicar.py`.
4. Los dos textos siempre: el editorial arriba y la síntesis abajo.

## Decisión

**Opción 1.** La lectura del mes vive en
`web/src/contenido/lectura-del-mes/AAAA-MM.md`, un archivo por edición
nombrado con el período tal como lo publica el snapshot. `Bluf.astro` lo
levanta con un `import.meta.glob` eager —se resuelve en build, no hay servidor
que pueda ir a buscarlo después— y compara la ruta contra `informe.period`.

- **Con archivo**: se publica ese markdown, firmado *"Lectura editorial del
  equipo CiGob · {mes}"*.
- **Sin archivo**: cae a la síntesis automática, que se conserva **entera**,
  con su nota de origen intacta. El código viejo no se borró: se envolvió.

`gate_calidad.py` suma **G8**, que avisa —sin bloquear— cuando el período
publicado no tiene archivo editorial.

### Consecuencias

- El mes que nadie escriba se publica igual, y dice de dónde sale su texto. La
  portada no puede mentir sobre su propia autoría.
- La firma reemplaza a la nota de "generada automáticamente" sólo cuando hay
  texto escrito. Las dos señales son mutuamente excluyentes por construcción,
  no por disciplina.
- El aviso G8 aparece en cada corrida del mes hasta que se escriba el texto:
  es ruido deliberado y acotado, dirigido al equipo, no al lector.
- El texto es markdown: admite más de un párrafo y negrita, y hereda la
  tipografía del bloque vía `.cg-bluf-editorial`.

### Confirmación

`tests/test_marco_conceptual.py` cubre el marco; para este bloque la
verificación es la del propio mecanismo, y se hace en los dos sentidos: con el
archivo del período presente, la portada publica el texto firmado; moviéndolo
fuera de la carpeta y reconstruyendo, vuelve la síntesis automática con su
nota. Un fallback que no se probó en el sentido que importa no existe.

## Pros y contras de las opciones

**1. Archivo por período con fallback.** A favor: el mes sin texto es
imposible de publicar como si fuera nuevo; el editorial se escribe en markdown
sin tocar código; el mecanismo es invisible en el snapshot, así que no
contamina BigQuery ni el archivo histórico. En contra: el texto vive en el repo
de la web y no en el snapshot, así que una corrida vieja recuperada desde git
no trae la lectura de aquel mes.

**2. Texto fijo en el componente.** A favor: es el cambio más corto. En contra:
convierte una omisión editorial en una publicación falsa, en silencio y todas
las noches. Descartada por eso.

**3. Campo en el snapshot.** A favor: la lectura viajaría con la corrida y
quedaría archivada en BigQuery junto a los números que describe. En contra:
`publicar.py` tendría que leer prosa de algún lado igual —el problema no se
resuelve, se muda—, y una corrección de estilo obligaría a re-correr el
pipeline entero.

**4. Los dos textos siempre.** A favor: no hay que elegir. En contra: duplica
en dos párrafos consecutivos lo que ya dicen el hero y las cards, que es
exactamente el hallazgo de la revisión adversarial del 2026-07-11 que sacó la
línea de score/riesgo de este mismo bloque.

## Más información

- El párrafo de agosto de 2026, primero en usar el mecanismo, es el que
  devolvió el editor sobre el artifact autocontenido.
- [[0165-una-oracion-por-card-el-desarrollo-aparte]] fija el criterio hermano
  para las cards: una oración con el veredicto, el detalle aparte.
