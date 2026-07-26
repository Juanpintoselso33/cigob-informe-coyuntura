# ADR-0131 — SAIJ es automatizable, contar no: el protocolo de codificación

| | |
|---|---|
| **Estado** | Aceptado (define el procedimiento; ningún indicador entra al índice todavía) |
| **Ámbito** | ITCP · bloque judicial y bloque económico · 8 indicadores pendientes |
| **Fecha** | 2026-07-25 |
| **Complementa** | ADR-0126 (dimensión judicial, primer indicador) |
| **Origen** | Aporte externo sobre el cinturón político (doc 260724), recomendación 1 |

## Qué se verificó

El aporte marcaba **Veto de Constitucionalidad** como automatización **Alta**:
*"SAIJ — buscador de jurisprudencia. Motor de búsqueda con metadatos
consultable; tratar como evento, no serie continua"*.

**La parte de infraestructura es correcta y quedó comprobada.** El endpoint
`https://www.saij.gob.ar/busqueda` devuelve JSON, acepta sintaxis de campo
(`texto:`, `fecha-rango:[AAAAMMDD TO AAAAMMDD]`), facetas por tipo de documento
y paginación. No hace falta scrapear HTML.

| consulta | resultados |
|---|---|
| `texto:inconstitucionalidad` (jurisprudencia) | 21.560 |
| `texto:"declara la inconstitucionalidad"` | 643 |
| `texto:"inconstitucionalidad del decreto"` | 122 |
| ídem + `fecha-rango:[20231210 TO 20261231]` | **14** |

## Por qué el indicador NO entra al índice

Se leyeron los 14. **La mayoría no es el fenómeno.**

| sumario | ¿es un veto de constitucionalidad al Ejecutivo nacional? |
|---|---|
| Acción declarativa contra el DNU "Bases para la reconstrucción de la economía" | **sí** |
| Confirmación de sentencia, personal militar, DNU | **sí** |
| "Recurso de inconstitucionalidad, recurso de queja, pagaré, intereses moratorios" | no — remedio procesal provincial |
| "Recurso de inconstitucionalidad, Superior Tribunal de Justicia, subrogancia del juez" | no — cuestión provincial interna |
| "AFIP DGI" | no |
| "Declaración de inconstitucionalidad, honorarios" | no — arancel profesional |

El problema de fondo: **"recurso de inconstitucionalidad" es un remedio
procesal de los códigos provinciales y no tiene nada que ver con declarar
inconstitucional una norma del Ejecutivo nacional.** La búsqueda de texto no
distingue las dos cosas, y en este universo la segunda acepción domina.

### Es la cuarta vez, y conviene decirlo así

| ADR | qué contaba de más |
|---|---|
| 0068 | "fondo de cese laboral" traía el régimen homónimo de la construcción |
| 0091 | `veto_quorum` contaba como fracaso de quórum las informativas del art. 71 CN |
| 0096 | "deroga" matcheaba considerandos donde la norma relata lo que derogó *otra* |
| **0131** | **"inconstitucionalidad" trae el recurso procesal provincial** |

**Una búsqueda de texto completo sobre una base legal cuenta lo que no es, salvo
que alguien lea los resultados.** Ya no es un accidente: es el comportamiento
esperable, y el diseño tiene que asumirlo desde el principio.

## Primera pasada de codificación: dos hallazgos que cambian el diseño

Se bajó el sumario completo de los 14 casos y se los clasificó uno por uno.
Dos cosas aparecieron que no se veían desde el conteo.

### El conteo se movería en la dirección equivocada

La consulta devuelve **casos donde el Ejecutivo GANÓ**, mezclados con los que
perdió:

| caso | qué pasó realmente | ¿es un veto? |
|---|---|---|
| DNU 70/23, acción declarativa (dic-2023) | **rechazada** por falta de legitimación | **no — la norma sobrevivió** |
| DNU 669/2019, declarado inconstitucional de oficio por la Cámara del Trabajo | la Corte **revocó** esa declaración | **no — y además es de otro gobierno** |
| Decreto 6754/43, tacha de inconstitucionalidad | **extemporánea**, rechazada | no — decreto de 1943 |
| Decreto 6754/43, mismo planteo | **improcedente** | no |
| DNU 70/23, amparo de afiliado a prepaga | busca la declaración | candidato |
| Decreto 759/2025, amparo del Consejo Interuniversitario | busca la declaración | candidato |

**Contar los 14 como "vetos de constitucionalidad" habría sumado como golpes al
Gobierno tres casos en los que el Gobierno ganó y dos sobre un decreto de 1943.**
Un indicador así se movería al revés: más litigios ganados subirían la tensión.

La distinción que hay que codificar no es "¿aparece la palabra?" sino
**"¿el tribunal declaró la inconstitucionalidad, o rechazó el planteo?"** —y esa
lectura no la hace una expresión regular.

### SAIJ tiene un tesauro controlado, y es mejor filtro que el texto

Cada documento trae `descriptores` con rutas jerárquicas de vocabulario
controlado:

```
Derecho constitucional/control de constitucionalidad/inconstitucionalidad/
    declaración de inconstitucionalidad/acción de inconstitucionalidad
Derecho administrativo/acto administrativo/acto administrativo de alcance
    general/reglamentos/decreto de necesidad y urgencia
Derecho procesal/recursos/improcedencia del recurso
```

**La rama del tesauro separa el control de constitucionalidad del remedio
procesal mucho mejor que el texto libre.** La consulta definitiva debe filtrar
por descriptor, no por frase, y el registro debe guardar la ruta como evidencia
de por qué el caso entró.

Los documentos traen además `jurisdiccion` (NACIONAL / FEDERAL / LOCAL) y
`tipo-tribunal`, que permiten excluir lo provincial sin leerlo.

## Decisión: el protocolo

Ningún indicador del bloque judicial o económico entra al índice sin cumplir
estos cinco puntos. No es burocracia — es lo que separa un indicador auditable
de un número que depende de quién armó el informe ese mes.

**1. Universo declarado y consulta fija.** La consulta se escribe en el código,
no se ajusta mes a mes. Cambiarla es un cambio de metodología con ADR propio,
como cualquier recalibración de bandas.

**2. Reglas de inclusión explícitas.** Para el veto de constitucionalidad, las
que surgieron de leer los 14 casos:
- **el tribunal DECLARA la inconstitucionalidad.** Un planteo rechazado, una
  acción sin legitimación o una declaración revocada por instancia superior
  **no cuentan** — en esos casos la norma sobrevivió y el Ejecutivo ganó;
- la norma impugnada es **nacional**, **del Poder Ejecutivo** y **de este
  mandato**: se excluye por fecha de la norma, no de la sentencia (apareció un
  decreto de 1943 y un DNU de 2019);
- **filtro por descriptor del tesauro**, no por frase: la rama
  `control de constitucionalidad/declaración de inconstitucionalidad` es el
  universo; `Derecho procesal/recursos/...` queda afuera;
- se descarta lo provincial por el campo `jurisdiccion`;
- se cuenta por **norma impugnada, no por sentencia**: tres fallos contra el
  mismo DNU son un veto, no tres;
- **la instancia importa**: una declaración de primera instancia apelada no es
  lo mismo que una firme. Se registra el estado y se decide editorialmente si
  se cuenta al declararse o al quedar firme.

**3. Doble codificación con chequeo de concordancia.** Dos personas clasifican
el mismo universo por separado y se mide el acuerdo (Cohen's kappa o
Krippendorff's alpha). **Por debajo de 0,70 las reglas no sirven y hay que
reescribirlas, no promediar.** Los desacuerdos se resuelven en una tercera
lectura y el criterio se agrega a las reglas.

**4. Registro versionado, no conteo opaco.** El resultado vive en un archivo
como `privatizaciones_fechas.json` o `gabinete_salidas.json`: cada caso con su
identificador de SAIJ, su fecha, la norma impugnada y la decisión de
clasificación. **Publicable y discutible caso por caso.**

**5. Detección automática, clasificación humana.** Exactamente el patrón de
ADR-0129: la consulta corre sola y marca casos nuevos como pendientes; la
clasificación la hace una persona. Automatizar el paso 2 sería reemplazar un
criterio publicado por una regla escondida en una expresión regular.

## Primera pasada hecha: `veto_constitucionalidad_codificacion.json`

La pasada 1 está completa sobre el universo de 17 documentos y versionada en
`data/politica/veto_constitucionalidad_codificacion.json`, caso por caso con su
motivo. **Falta la pasada 2 y la medición de concordancia.**

| | |
|---|---|
| incluir | **1** |
| dudoso (hay que leer el fallo) | 3 |
| excluir | 13 |

**El único caso claro** es la Resolución 3132/2024 del Ministerio de Salud, que
un tribunal federal declaró reglamentación irrazonable de la ley 27.350 por
exigir diplomatura para prescribir cannabis medicinal.

### Tres hallazgos estructurales de la codificación

**1. El universo tiene duplicados.** Los casos 16 y 17 son el mismo sumario
repetido, y 4, 8 y 10 son tres sumarios del **mismo expediente** (CELS contra el
decreto 193/24). Contar documentos habría inflado esos expedientes ~2,4 veces.
La regla de contar por norma impugnada no es un refinamiento: es indispensable.

**2. Seis de los 17 son derrotas de quien impugna, no del Gobierno.** Rechazos
expresos de acciones contra el DNU 70/2023 y el decreto 193/24. Un conteo crudo
los habría sumado como vetos al Ejecutivo.

**3. Filtrar por fecha de sentencia no alcanza.** Aparecen impugnaciones al
decreto 6754/**1943**, al DNU 756/**2018** y al DNU 669/**2019** porque la
sentencia cae en la ventana. **Hay que filtrar por la fecha de la NORMA.**

### La decisión de codificación que la pasada 2 tiene que resolver

En el único caso incluido el tribunal habla de **"reglamentación irrazonable"**,
no de inconstitucionalidad. ¿Cuenta? Es la elección más consecuente del set: con
el criterio amplio el indicador captura el control de legalidad completo; con el
estricto, se queda casi sin casos. **No la resuelve un codificador solo, y es
exactamente para eso que el protocolo pide dos.**

## Qué habilita esto

Los **ocho indicadores pendientes** —cinco judiciales y tres del bloque
económico— comparten el mismo cuello de botella. Con el protocolo definido,
cada uno necesita sólo su consulta y sus reglas de inclusión:

| indicador | fuente verificada | qué falta |
|---|---|---|
| Veto de Constitucionalidad | **SAIJ, comprobada acá** | reglas + doble codificación |
| Bloqueo Cautelar | CSJN/Cámaras (sin API) | scraper + reglas |
| Éxito Corporativo | ídem | scraper + listado de razones sociales |
| Velocidad de Resolución | ídem | scraper + definición de "causa sensible" |
| Parálisis de Denuncias | actas PDF del Consejo | parser + reglas |
| Apoyo Público | RSS de cámaras empresarias | scraper + esquema de postura |
| Agenda Común | HCDN/Senado vs. propuestas | atribución causa-efecto |
| Judicialización | CSJN/Cámaras | comparte scraper con Bloqueo Cautelar |

El aporte externo ya señala que **Bloqueo Cautelar y Judicialización comparten
el universo de causas** y conviene construir una sola infraestructura. Se
coincide, con la salvedad de este ADR: **primero el protocolo, después el
scraper.** Un scraper que produce datos que no se pueden clasificar no produce
nada.

## Lo que este ADR NO hace

- **No incorpora ningún indicador.** El bloque judicial sigue con uno solo
  (`cobertura_judicial`, ADR-0126) y el económico con uno solo
  (`brecha_obra_publica`, ADR-0088).
- **No escribe las reglas de inclusión de cada indicador**, sólo exige que
  existan y fija el estándar de concordancia.
- **No resuelve** que la doble codificación necesita dos personas. Es un costo
  real del diseño y no hay forma de automatizarlo sin perder lo que lo hace
  auditable.

## Anexo: la consulta que quedó verificada

```
GET https://www.saij.gob.ar/busqueda
  r = (texto:"inconstitucionalidad del decreto"
       AND fecha-rango:[20231210 TO 20261231])
  f = Total|Tipo de Documento/Jurisprudencia
  o = 0 · p = 30
```

Devuelve JSON con `searchResults.documentResultList`; cada documento trae su
`uuid`, su `friendly-url` y un `documentAbstract` con el sumario. El conteo
total sale de `categoriesResultList` → faceta `Total` → `facetHits`.

Queda escrito para que quien retome el punto no vuelva a averiguar si SAIJ se
puede consultar: **se puede, y ese nunca fue el problema.**
