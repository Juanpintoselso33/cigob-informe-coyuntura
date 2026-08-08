---
madr: 4
id: '0183'
estado: 'propuesto'
nota_estado: 'Registrado sin aplicar: ningún archivo de scoring cambió. Espera aprobación o baja de CIGOB.'
fecha: 2026-08-08
cinturon: 'politica'
indice: 'itcp'
relacionado: ['0048']
ambito: 'Rediseño del ITCP propuesto por el documento CIGOB de agosto de 2026 · 6 dimensiones, 11 indicadores, umbrales en unidad propia'
origen: 'Documento CIGOB "indicadores y semaforos" (2026-08-05/08), entregado junto con las fichas del semáforo de Gestión'
---

# ADR-0183 — Rediseño del cinturón político según el documento de agosto: registrado, no aplicado

## Contexto y planteo del problema

El documento CIGOB *"indicadores y semáforos"* llegó en el mismo lote que las
fichas del semáforo de Gestión (ADR-0181), pero no es lo mismo: además de
proponer colores, **propone otro ITCP**. Lista 6 dimensiones y 11 indicadores,
cada uno con sus umbrales en unidad propia.

Eso lo pone en otra categoría. El semáforo es una capa de lectura que no mueve
ningún número; este documento **cambia el índice**: qué se mide, con qué peso y
en qué dimensión. Mezclar las dos cosas en la misma entrega significaría que el
día que el ITCP cambie de valor nadie pueda decir si fue por el rediseño o por
el color.

Al traducir el documento contra `scripts/itcp.py` aparecieron tres clases de
discrepancia que hay que resolver **antes** de poder aplicarlo, y que no se
pueden resolver por cuenta propia porque son decisiones editoriales de CIGOB,
no defectos de implementación.

## Factores de decisión

- El ITCP tiene hoy **7 dimensiones y 18 indicadores que puntúan** (más 7
  tablas de bandas que se conservan como referencia histórica: 25 en total).
  Cualquier propuesta de 11 indicadores es también una propuesta de **sacar**
  cosas, aunque no lo diga.
- El documento no declara qué pasa con lo que no menciona. El silencio no es
  una decisión: hay que preguntarlo.
- Un rediseño del índice **no puede bloquear el semáforo**, que es presentación
  y ya está listo.
- Los umbrales que propone el documento tienen defectos formales concretos —
  huecos sin color, ejes mezclados— y resolverlos "con criterio propio" sería
  inventar la parametrizacion de CIGOB en su nombre.
- Reabrir la cohesión por cámara **revierte ADR-0048**, que fue a su vez una
  revisión editorial pedida por CIGOB. Volver atrás sobre una decisión de
  CIGOB requiere que lo pida CIGOB.

## Opciones consideradas

- **Aplicar el documento tal cual** — descartada: tiene cinco defectos de
  umbral sin resolver y borraría en silencio ~35% del peso del índice.
- **Aplicar la parte que mapea limpio y dejar el resto** — descartada: un
  índice mitad viejo y mitad nuevo no es interpretable, y "los diez que
  mapean" no son un recorte que nadie haya decidido.
- **Registrar la propuesta sin aplicarla** — elegida.

## Decisión

**Este ADR registra el rediseño y no lo implementa.** `scripts/itcp.py` no
cambia: ni indicadores, ni dimensiones, ni pesos, ni bandas. El objetivo es que
CIGOB pueda aprobarlo o bajarlo con el efecto ya calculado a la vista, sin que
la decisión bloquee la entrega del semáforo.

Lo que hay que resolver, en tres bloques:

**1. Un indicador que no existe.** *"Postura de los Sindicatos"* no tiene
contraparte en el ITCP. Implementarlo requiere dos cosas que hoy no están: una
**fuente** con cobertura nacional y frecuencia mensual, y el **sistema de
puntajes por tipo de acción** que el documento esboza (una acción sindical no
pesa lo mismo según sea un comunicado, una medida de fuerza sectorial o un paro
general). Ninguna de las dos se resuelve escribiendo una tabla de bandas.

**2. Ocho indicadores que hoy puntúan y el documento no menciona.** Suman
**34,7% del peso del ITCP**:

| Indicador | Dimensión | Peso en su dimensión | Peso en el ITCP |
|---|---|---|---|
| `conflictividad_nacional` | conflicto social (0,10) | 1,00 | 10,0% |
| `iaf_transferencias` | alianzas territoriales (0,19) | 0,40 | 7,6% |
| `produccion_legislativa` | poder legislativo (0,21) | 0,15 | 3,2% |
| `veto_quorum` | poder legislativo | 0,13 | 2,7% |
| `desafios_legislativos` | poder legislativo | 0,13 | 2,7% |
| `bloqueo_sostenido` | poder legislativo | 0,12 | 2,5% |
| `velocidad_resolucion` | poder judicial (0,15) | 0,20 | 3,0% |
| `paralisis_denuncias` | poder judicial | 0,20 | 3,0% |

La dimensión **conflicto social desaparecería entera** (el documento tiene 6
dimensiones, el ITCP tiene 7). Sacarlos puede ser exactamente lo que CIGOB
quiere —acotar el índice, como ya hizo ADR-0048— pero tiene que ser una
decisión, no una omisión.

**3. Los diez que sí mapean.** Salen de restar los ocho de arriba a los
dieciocho que puntúan hoy, y son: `ratio_dnu`, `eficacia_legislativa`,
`alineamiento_senadores_prov`, `adhesion_reformas_provincial`,
`cohesion_bloque`, `votometro_ventaja_lla`, `cobertura_judicial`,
`judicializacion`, `brecha_obra_publica` y `apoyo_empresario`. Mapean como
indicador; **sus umbrales son otra discusión** (ver "Más información").

**Y un punto que no es negociable sin revisar ADR-0048.** El documento propone
volver a la cohesión **por cámara**. ADR-0048 fusionó Diputados y Senado en un
compuesto bicameral (Rice de Diputados 65% + Senado 35%), con anclas
recalibradas contra la serie del compuesto porque las de Diputados sola no
servían: el Senado es un cuerpo chico donde un disidente mueve el promedio, y
le mete al compuesto un rango tres veces más ancho. Separarlas otra vez no es
sólo cambiar un indicador por dos: invalida esa calibración y revierte una
decisión editorial que pidió el propio CIGOB en julio.

### Consecuencias

- El semáforo (ADR-0181/0182) se entrega sin esperar esta discusión, y se
  aplica al ITCP **tal como está hoy**.
- Si CIGOB aprueba el rediseño, hay que resolver primero los cinco defectos de
  umbral de abajo y decidir explícitamente sobre los ocho indicadores y sobre
  ADR-0048. Recién después se puede estimar el efecto sobre el valor del ITCP.
- Si CIGOB lo baja, este ADR pasa a `rechazado` y queda como registro de por
  qué — que es más útil que no tener nada, porque la propuesta va a volver.
- Mientras tanto, los umbrales de color del ITCP son los que calcula
  `umbrales_en_unidad` desde `BANDAS_ITCP` (ADR-0182), no los del documento.

### Confirmación

No hay nada implementado que confirmar, y eso es el punto: la confirmación de
que este ADR se respetó es que **`scripts/itcp.py` no aparece en el diff** de la
entrega del semáforo, y que el valor del ITCP (66,9 al 2026-08-08) es idéntico
antes y después — lo comprueba `TestNoMovioNingunNumero` en
`tests/test_publicar_semaforo.py`.

## Pros y contras de las opciones

**Aplicar el documento tal cual**

- Bueno: entrega lo que CIGOB pidió, sin intermediarios ni interpretación.
- Malo: cinco de sus tramos de umbral son inaplicables como están (huecos sin
  color, dos ejes en una escala, condiciones compuestas).
- Malo: borra 34,7% del peso del índice sin que nadie haya decidido borrarlo.
- Malo: revierte ADR-0048 por efecto colateral.

**Aplicar sólo la parte que mapea limpio**

- Bueno: avanza algo, sin tocar lo dudoso.
- Malo: el resultado no es ni el índice actual ni el propuesto, y nadie puede
  interpretar su valor.
- Malo: consolida como decisión un recorte que es un artefacto de qué mapeó y
  qué no.

**Registrar sin aplicar** — elegida

- Bueno: el semáforo sale hoy; el rediseño se discute con la aritmética a la
  vista.
- Bueno: deja los cinco defectos anotados en el mismo lugar donde se va a tomar
  la decisión, en vez de resolverlos en silencio.
- Malo: la propuesta queda sin efecto hasta que alguien la mire; un ADR
  `propuesto` que nadie lee es una decisión postergada indefinidamente.
- Malo: no calcula el efecto sobre el valor del ITCP, porque no se puede
  calcular hasta resolver los defectos.

## Más información

### Los cinco defectos de los umbrales del documento

No son objeciones de estilo: son tramos que no se pueden traducir a código sin
elegir por CIGOB.

1. **Cohesión del bloque — hueco entre 90 y 99,9%.** El documento define verde
   como "100%" y amarillo como "75% a 89,9%". El tramo **90–99,9% no tiene
   color**, y no es un rincón: la serie reconstruida del compuesto bicameral
   (31 puntos, dic-2023 → jun-2026) tiene media 97,6 y rango 90,3–100,0. El
   hueco es, literalmente, donde vive el indicador.
2. **Ratio DNU/leyes — hueco por encima de 3,0.** Naranja llega hasta 3,0 y
   rojo se define como *"producción legislativa cero"*, que **no es un punto
   del mismo eje**: con leyes = 0 la ratio es infinita, no un valor comparable.
   El tramo **mayor a 3,0 se queda sin color** y el rojo mide otra cosa.
3. **Designación de jueces — dos ejes en una escala.** Verde y amarillo se
   definen por **% de vacantes cubiertas**; rojo, por **% de pliegos aprobados
   en el Senado**. Son dos variables distintas: un valor puede estar en verde
   por una y en rojo por la otra al mismo tiempo.
4. **Votómetro — tramos compuestos.** Los cortes son condiciones de tres
   variables a la vez (% propio, brecha con el segundo y posición), no un único
   eje. El indicador vigente (`votometro_ventaja_lla`) mide una sola cosa: la
   ventaja en puntos porcentuales sobre el PJ. Traducir lo propuesto exige
   decidir qué pasa cuando las tres condiciones no coinciden.
5. **"Postura Pública de las Cámaras Empresarias" aparece dos veces.** Los dos
   tienen el mismo título y distinto contenido: el segundo es, por lo que
   describe, la **brecha de expectativas de obra pública vs privada**
   (`brecha_obra_publica`), no el apoyo empresario (`apoyo_empresario`). Es
   casi con seguridad un error de redacción del documento, pero mientras no se
   corrija son dos indicadores con un nombre.

### Por qué esto no se resolvió por cuenta propia

Cada uno de los cinco tiene una salida "razonable" —extender verde hasta 90,
mover el rojo del DNU a otro eje, quedarse con el % de vacantes— y ninguna es
neutral: todas cambian el puntaje de un indicador publicado. Elegirlas sin
preguntar sería exactamente lo que ADR-0045 prohíbe en su versión de
calibración: mover la vara y que el número mejore por eso.

### Sobre la trazabilidad de este ADR

El documento fuente es un `.docx` de CIGOB que **no está versionado en el
repo**, así que lo de acá se apoya en la verificación hecha al traducirlo
(recogida en `docs/superpowers/specs/2026-08-08-semaforo-cuatro-colores-design.md`,
§7.2 y §7.3) más lo que se puede comprobar contra el código. Los pesos, la lista
de los ocho no mencionados, el 34,7% y los diez que mapean **sí** son
reproducibles hoy desde `itcp.DIMENSIONES_ITCP`. Los nombres exactos de las 6
dimensiones que propone el documento no se transcriben acá para no fijar como
cita algo que no se puede verificar contra el archivo.
