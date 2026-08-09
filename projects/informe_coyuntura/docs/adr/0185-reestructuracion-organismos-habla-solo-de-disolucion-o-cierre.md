---
madr: 4
id: '0185'
estado: 'aceptado'
nota_estado: 'la precisión de etiquetas y la revisión del denominador están cerradas (ago-2026); el hallazgo sobre la calidad del numerador queda declarado y sin resolver, para una tarea aparte'
fecha: 2026-08-09
cinturon: 'gestion'
indicadores: [reestructuracion_organismos]
continuado_por: ['0188']
ambito: 'ITCG · `reestructuracion_organismos` · etiquetas públicas, denominador y calidad del numerador'
origen: 'Revisión de fichas de Gestión por CIGOB (ronda de agosto de 2026): "HAY QUE CAMBIAR Y PRECISAR QUE MEDIMOS, Y HABLAR SOLO DE DISOLUCION O CIERRE. lo de reestructuración, fusión o transformación es difuso, y no puede levantarse o registrarse, había que ir caso por caso."'
---

# ADR-0185 — `reestructuracion_organismos` habla solo de disolución o cierre

## Contexto y planteo del problema

CIGOB revisó las 15 fichas del cinturón Gestión. Sobre `reestructuracion_organismos`
señaló que el proyecto tenía que **precisar qué mide** y **hablar solo de
disolución o cierre**: fusión, transformación y centralización son conceptos
difusos que no se pueden relevar de forma sistemática, sólo caso por caso.

Verificado antes de tocar nada: el CÁLCULO ya media solo eso. `gestion.py`
consulta InfoLeg con `texto="disolucion"` desde el primer commit que
automatizó el indicador (`43ff990`, may-2026) y nunca sumó una búsqueda
separada por "fusión". El defecto no estaba en el número — estaba en el
RÓTULO, que prometía más de lo que el número mide:

- `detalle_txt` decía `"{count} actos de disolución/fusión desde dic-2023"`.
- La descripción pública (`web/src/lib/descripciones.ts`) decía que los
  organismos *"se disolvieron, fusionaron o centralizaron"*.
- La ficha (`web/src/lib/fichas.ts`) hablaba de *"disolución o
  reestructuración"*.
- Los comentarios de `itcg.py` y `procedencia_anclas.py` decían "plan de
  disoluciones/fusiones".

## Factores de decisión

- El cálculo (búsqueda InfoLeg, conteo, banda) no tenía que cambiar: ya medía
  lo que CIGOB pide. Cambiar el cálculo sin que hiciera falta sería resolver
  un problema que no existía y arriesgar el que sí existe.
- Todo texto orientado al lector (card, ficha, descripción, fórmula) tenía que
  alinearse con lo que el cálculo mide de verdad, no al revés.
- La clave técnica `reestructuracion_organismos` está referenciada en código,
  tests y series históricas acumuladas en `data/historico/` — renombrarla
  rompería la continuidad de la serie sin ningún beneficio, ya que el nombre
  interno no es lo que el lector ve.
- El denominador `ORGANISMOS_PLAN_TOTAL = 45` plantea una pregunta aparte que
  no se puede resolver solo con edición de texto: ver la sección dedicada
  más abajo.

## Opciones consideradas

- **Cambiar el cálculo** (agregar detección de fusiones, o restringir el
  conteo con un filtro más estricto que "disolucion") — descartada: el
  cálculo ya es correcto para lo que CIGOB pide; tocarlo sin necesidad
  introduce riesgo de romper la serie histórica sin corregir nada real.
- **Renombrar la clave técnica** a algo como `disolucion_organismos` —
  descartada: rompería 1.300+ referencias cruzadas verificadas en este
  proyecto (código, tests, series, ADRs) por un cambio que es solo de
  redacción pública; la clave interna no es lo que el lector ve.
- **Alinear todo el texto orientado al lector con lo que el cálculo mide, y
  declarar la pregunta sobre el denominador sin resolverla por decreto** —
  elegida.

## Decisión

Se reescribió cada string visible para el lector, reemplazando "fusión",
"reestructuración" o "centralización" por "disolución o cierre":

| Archivo | Antes | Ahora |
|---|---|---|
| `scripts/gestion.py` (`detalle_txt`) | "actos de disolución/fusión" | "actos de disolución o cierre de organismos" |
| `web/src/lib/descripciones.ts` (`que`) | "se disolvieron, fusionaron o centralizaron" | "se disolvieron o cerraron" |
| `web/src/lib/descripciones.ts` (`aporta`) | genérico | explicita que NO cuenta fusiones/transformaciones/reorganizaciones, "difíciles de verificar caso por caso" |
| `web/src/lib/fichas.ts` (`transformaciones`, `limitaciones`) | "disolución o reestructuración" | "disolución o cierre"; se agrega la razón (pedido de CIGOB) |
| `web/src/lib/formulas.ts` (latex + leyenda) | "disolución/reestructuración" | "disolución o cierre"; leyenda aclara "no cuenta fusiones ni transformaciones" |
| `scripts/itcg.py` (comentarios de banda) | "plan de disoluciones/fusiones" | "plan de disoluciones o cierres" |
| `scripts/procedencia_anclas.py` | "plan de disoluciones/fusiones" | "plan de disoluciones o cierres" |

La clave técnica `reestructuracion_organismos` **no se renombra**: sigue
siendo el identificador interno en código, tests y series históricas. Lo que
cambia es únicamente lo que el lector ve.

### El 45 (denominador): revisado caso por caso, agosto de 2026

CIGOB no preguntó por el denominador, pero la instrucción de precisar
qué se mide obliga a revisarlo: si el "plan completo" (`ORGANISMOS_PLAN_TOTAL
= 45`) se calibró contra un universo más amplio que disolución/cierre, la
etiqueta ya no describe la vara contra la que se compara. Esta sección
reemplaza a la pregunta abierta que dejó la primera versión de este ADR:
se hizo la búsqueda que faltaba, caso por caso, siguiendo el orden de
anclas de ADR-0105.

**Cómo se calibró el 45 originalmente.** El commit que lo introdujo
(`43ff990`, 23-may-2026) describe el indicador, ANTES de automatizarlo, como
*"Conteo de decretos de disolución/fusión de organismos en el Boletín
Oficial"*, y dice literalmente *"18 docs = 40% validado con estimación
manual; 45 docs = 100%"* — hablando de "disolución/fusión", no de
disoluciones a secas. La búsqueda en InfoLeg, en cambio, siempre fue solo
`texto="disolucion"`: nunca hubo una segunda búsqueda por "fusión" que se
sumara al conteo. El 45 se fijó, con toda evidencia disponible, contra un
universo más amplio que el que la etiqueta describe desde ago-2026.

#### Búsqueda de una ancla mejor (orden de ADR-0105)

**1) Referencia externa.** Se buscó un plan oficial con una cifra propia de
organismos a disolver/cerrar:

- **Ley 27.742 ("Ley Bases", BO 8-jul-2024), Título II Cap. I** (arts. 2-6):
  la norma habilitante de toda esta reforma. Delega en el Poder Ejecutivo la
  facultad de reorganizar, disolver, fusionar, transformar o transferir
  organismos de la administración central y descentralizada, por el plazo de
  un año. El texto **no fija ninguna cantidad objetivo**: sólo declara una
  lista NEGATIVA de organismos excluidos de la disolución (CONICET, ANLIS,
  ANMAT, INPI, INCAA, ENACOM, ARN, CONAE, CNEA, CONEAU, CNV, INCUCAI, UIF,
  INTA, INTI, BNDG, APN, SENASA, entre otros) y deja todo lo demás a
  discreción del Poder Ejecutivo. No hay cifra de "organismos a disolver" en
  la ley.
- **Ministerio de Desregulación y Transformación del Estado**
  (`argentina.gob.ar/desregulacion` e `.../informes-de-empleo-publico`,
  consultados ago-2026): publican contadores de NORMAS de desregulación (636
  acumuladas a may-2026) y de dotación de personal, pero ningún contador ni
  meta de "estructuras" o "organismos" eliminados — la sección "Disminución
  de personal y estructuras del Estado desde Dic23" enlaza a informes de
  empleo público sin una cifra propia de organismos.
- **Prensa**: La Nación (24-jul-2024) reportó, citando fuentes oficiales,
  que "el Gobierno evalúa disolver alrededor de 60 organismos públicos" — la
  única cifra encontrada que habla específicamente de DISOLVER (no de
  fusionar ni transformar). El propio Ministerio, además, difundió en
  conferencia de prensa (jul-2025, recogido por Infobae y La Nación) un
  listado numerado de ~101 medidas tomadas en el año de facultades
  delegadas, clasificadas por tipo (disolución/eliminación, transformación,
  fusión/unificación, privatización, desregulación).
- **Por qué ninguna de las dos sirve como ancla**: (a) el "~60" es una
  evaluación interna reportada por un medio, no un documento oficial con
  cifra propia, y es de jul-2024 — dos años antes de esta revisión, con el
  plan todavía "evaluándose"; en abr-2026 el Gobierno anunció que reenviaría
  al Congreso una reforma para "recuperar por vía legislativa" eliminaciones
  y fusiones que habían caído por el rechazo de los decretos delegados (ver
  más abajo), es decir que el universo sigue abierto, no se estabilizó en
  una cifra; (b) el listado de ~101 medidas es un conteo de lo YA HECHO a
  jul-2025, no una meta, y mezcla categorías sin declarar un subtotal
  oficial de "disolución pura" — reconstruirlo a mano da unas 30 medidas de
  "disolución/eliminación" sobre 101, pero esa reconstrucción es mía, no del
  Ministerio; (c) sobre todo, **las dos cifras cuentan ORGANISMOS, y el
  indicador cuenta NORMAS de InfoLeg** — una sola norma puede disolver más
  de un organismo (confirmado al leer los 18 casos: ver más abajo), así que
  usar una cifra de organismos como denominador de un numerador de
  documentos mezclaría unidades sin decirlo. Ninguna referencia externa es
  viable.
- **Valor con significado propio.** No hay un 0%, 100% o umbral
  institucional natural para "cuántos organismos cerrar": ni "toda la
  administración pública" ni "cero organismos" son metas que el propio
  proceso reivindique. Se descarta.
- **Historia del propio indicador anterior a dic-2023.** Se buscó algún
  antecedente de una meta o un ritmo de disolución de organismos en
  gestiones previas para anclar contra un rango histórico. No se encontró
  ninguno: una reforma de esta escala, con seguimiento numérico público, no
  tiene antecedente comparable en el registro reciente. No hay serie previa
  de la que extrapolar. Se descarta.
- **Convención calibrada.** Con 1-3 descartadas, ADR-0105 exige declarar una
  convención y decir por qué. El 45 de mayo-2026 sigue siendo la única
  cifra disponible con algún trabajo manual detrás, aunque calibrada para
  el universo amplio. Reemplazarlo por el "~60" sin resolver el problema de
  unidades sería cambiar una convención por otra igual de arbitraria, con
  apariencia de fuente externa que no tiene.

**Sensibilidad probada** (mismo cálculo, mismo conteo de 18 normas, sólo
cambia el denominador, contra el cache de `output/cache/gestion.json` del
9-ago-2026): a 45 el ITCG da **78,7** (banda "moderadamente aflojado"); a 60
(el candidato descartado) da 77,9, misma banda; a 30 (si el universo fuera
sólo la reconstrucción a mano de "disolución pura" del listado oficial de
jul-2025) da 80,1 y **cruza a la banda "aflojado"**. Que dos candidatos
igual de débiles empujen a bandas distintas es la evidencia más concreta de
que adivinar acá sería arbitrario, no una mejora.

**Decisión: el 45 no cambia.** Es una convención calibrada, declarada como
tal (ADR-0105, opción 4), y sigue siendo la mejor disponible tras agotar las
tres anteriores. Esta vez la búsqueda de 1-3 quedó documentada —lo que
ADR-0105 exige aunque falle— y no es un supuesto que cierra el tema por
comodidad.

#### Lectura caso por caso de los 18 actos (lo que pidió CIGOB)

Se reprodujo la búsqueda de InfoLeg mes a mes (mismo patrón que
`_infoleg_buscar_mes`, usado ya para `desregulacion_normativa`) para poder
leer los 18 documentos, no sólo contarlos, y se buscó específicamente el
riesgo que motivó la revisión: ¿alguno instrumenta una FUSIÓN como
"disolución sin liquidación" del organismo absorbido?

**Ese riesgo no se confirmó.** En los dos documentos donde aparecen ambas
palabras, se refieren a cosas distintas: la Resolución General IGJ 15/2024
habla en abstracto de la disolución y fusión de sociedades y asociaciones
civiles (derecho privado, ni un caso concreto); el Decreto 192/2026 dispone
la disolución del Centro Nacional de Investigaciones Nutricionales y, por
un artículo aparte, fusiona otros dos institutos — la fusión no entra al
conteo, como corresponde. Ninguna de las 18 normas usa "disolución" como
eufemismo de una fusión real.

De los 18: **11 son cierres genuinos y vigentes** de organismos o fondos
públicos —el Instituto Argentino del Transporte, el INADI, el Programa de
Promoción del Microcrédito, la Subsecretaría de Puertos y Vías Navegables,
tres fondos fiduciarios en un solo decreto (6/2025), el Fondo de
Infraestructura de Seguridad Aeroportuaria, el FFTEF, cinco organismos de
Cultura en un solo decreto (346/2025: Institutos Browniano/Newberiano/
Belgraniano, Instituto Perón y su comisión de homenaje), dos fondos más en
otro decreto (312/2025: FISU y el de promoción científica), el IOSFA
(DNU 88/2026) y el Centro Nacional de Investigaciones Nutricionales— y
confirman, de paso, que una norma puede cerrar más de un organismo (esos 11
documentos cierran unos 18 organismos, no 11): el numerador cuenta normas,
no organismos, la misma unidad con la que se calibró el 45 originalmente.

Los otros 7 son un hallazgo, no un ajuste que se haya hecho — ver la
sección siguiente.

#### Hallazgo adicional: la calidad del numerador (declarado, no resuelto acá)

La lectura caso por caso encontró un problema distinto del denominador, en
el otro lado de la cuenta:

- **3 documentos no son cierres de organismos públicos del Estado
  nacional** (falsos positivos o fuera de alcance): la Resolución General
  IGJ 15/2024 regula trámites de disolución de sociedades y asociaciones
  civiles (derecho privado); la Disposición ANMAT 2491/2026 prohíbe
  productos de limpieza de la marca "Agranel", uno de ellos llamado "Cloro
  Granulado Disolución Rápida" (coincidencia léxica con un producto
  químico); la Resolución 1056/2025 de la Superintendencia de Servicios de
  Salud disuelve la Obra Social del Personal de la Industria Botonera, una
  obra social sindical privada regulada por el Estado, no un organismo de
  la Administración Pública Nacional.
- **4 documentos son consecuencia de los Decretos 461/2025 y 462/2025**
  (disolución de la Dirección Nacional de Vialidad, la Agencia Nacional de
  Seguridad Vial, la Comisión Nacional del Tránsito y la Seguridad Vial, el
  INAFCI, y transformación del INTI/INTA/INV), **rechazados por Diputados
  el 6-ago-2025 y por el Senado el 21-ago-2025** — ambos decretos delegados
  quedaron sin efecto. Las tres resoluciones de personal derivadas de esos
  decretos que caen dentro de los 18 (1217/2025, 1044/2025 y 1240/2025)
  fueron expresamente abrogadas por la Resolución 1343/2025 del Ministerio
  de Economía (BO 12-sep-2025). InfoLeg sigue indexando el texto de estas
  normas porque se publicaron, aunque hoy no rijan.

En total, 7 de los 18 documentos (39%) son ruido o corresponden a actos hoy
sin efecto — un problema de calidad del numerador, no del denominador, y
que además va en sentido contrario al que motivó esta revisión: si algo,
infla el conteo actual, no lo subestima. **No se corrige en este ADR**: la
tarea que lo originó era sobre el denominador, y tocar la búsqueda de
InfoLeg (para excluir por tipo de entidad o verificar vigencia legislativa)
es un cambio de cálculo con su propio riesgo, que merece su propia revisión
y sus propios tests — el mismo criterio con el que este ADR no tocó el
cálculo para el problema de etiquetas. Queda declarado para que alguien lo
retome.

### Consecuencias

- El indicador no cambia su valor publicado: mismo cálculo, mismo conteo,
  misma banda, mismo denominador (45). Ningún número que ya estaba en el
  snapshot se mueve.
- La pregunta sobre el denominador, que la primera versión de este ADR dejó
  declarada y abierta, se cierra con una búsqueda exhaustiva (ago-2026):
  ninguna referencia externa, valor propio o historia previa sobrevive al
  escrutinio, así que el 45 se mantiene como convención calibrada,
  explícitamente declarada — no una cifra corregida, pero tampoco ya una
  pregunta pendiente.
- La lectura caso por caso de los 18 actos, que sí era lo que CIGOB pidió,
  encontró que el riesgo temido (fusión disfrazada de disolución) no ocurre,
  pero destapó un problema distinto y no resuelto: 7 de los 18 documentos
  son ruido o corresponden a decretos que el Congreso rechazó. Queda
  declarado como hallazgo separado, sin acción en este ADR.

### Confirmación

`python -m pytest tests/ -k reestructuracion` y la suite completa de
`test_itcg.py`/`test_procedencia_anclas.py` verifican que el cálculo no
cambió (banda idéntica, denominador idéntico) mientras el texto público sí lo
hizo. La búsqueda del denominador y la lectura de los 18 actos (ago-2026) se
hicieron por fuera de la suite, contra InfoLeg en vivo y fuentes públicas —
no hay un test automatizado que las reproduzca; el rastro queda en este ADR.

## Pros y contras de las opciones

**Cambiar el cálculo para agregar "fusión" como concepto separado**

- Bueno: cerraría del todo la brecha entre "lo que se afirma medir" y "lo que
  se mide", si existiera una fuente confiable para fusiones.
- Malo: CIGOB señaló exactamente que fusión/transformación/centralización
  **no tienen** una fuente que se pueda relevar de forma sistemática — es la
  premisa de la observación, no algo que este ADR pueda resolver.

**Alinear el texto con el cálculo existente (elegida)**

- Bueno: cero riesgo sobre la serie histórica y el cálculo, que ya eran
  correctos.
- Bueno: dispara la revisión honesta del denominador, que estaba fuera del
  radar hasta que se puso a prueba la precisión de la etiqueta. Esa revisión
  (ago-2026) no cambió el 45, pero lo dejó documentado en vez de sólo
  declarado.
- Malo: la revisión también destapó un problema de calidad del numerador
  (7 de 18 documentos son ruido o normas hoy sin efecto) que este ADR no
  resuelve — queda para una tarea aparte.

## Más información

### Por qué la clave técnica no se toca

`reestructuracion_organismos` aparece en `INDICADORES_ESPERADOS`,
`BANDAS_ITCG`, `DIMENSIONES_ITCG`, la serie histórica en
`data/historico/indicadores.json`, y decenas de asserts de test. Ninguna de
esas referencias es visible para el lector del informe: son identificadores
internos. Renombrar la clave sería un costo real (romper la continuidad de
la serie, forzar una migración de datos) por un beneficio nulo, porque el
problema que CIGOB señaló nunca estuvo en el nombre interno.
