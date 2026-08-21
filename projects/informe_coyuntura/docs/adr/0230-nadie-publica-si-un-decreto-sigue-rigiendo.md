---
madr: 4
id: '0230'
estado: 'rechazado'
nota_estado: '**Rechazado el indicador, versionado el relevamiento**: no se construye `supervivencia_judicial`, y el mapa de fuentes queda en `data/politica/supervivencia_judicial_fuentes.json` para no volver a recorrer el camino.'
fecha: 2026-08-21
cinturon: 'politica'
archivos: ['data/politica/supervivencia_judicial_fuentes.json', 'tests/test_supervivencia_judicial_sin_fuente.py']
relacionado: ['0069', '0089', '0131', '0135', '0140', '0141', '0143', '0147', '0168', '0170']
ambito: 'Bloque judicial · si una norma del Ejecutivo sobrevive el desafío JUDICIAL — indicador propuesto y NO construido'
origen: 'el capítulo laboral del DNU 70/2023 lo frenó la Justicia y no el Congreso, y el informe sólo mide el desafío legislativo'
---

# ADR-0230 — Nadie publica si un decreto sigue rigiendo

`data/politica/supervivencia_judicial_fuentes.json`
- **Relacionados**: [[0069-bloqueo-sostenido-indicador]] y
  [[0089-desafios-en-lugar-de-derrotas]] (la pata legislativa, que sí se mide),
  [[0170-judicializacion-y-paralisis-pasan-a-fuente-viva]] y
  [[0135-cautelares-judicializacion-si-bloqueo-no]] (`judicializacion`, la misma base),
  [[0140-el-dato-existe-y-esta-mejor-modelado-de-lo-que-suponiamos]] y
  [[0141-detector-de-novedades-judiciales-de-la-csjn]] (el mapa de la CSJN),
  [[0131-protocolo-de-codificacion-para-el-bloque-judicial]] y
  [[0147-el-universo-de-un-caso-era-un-artefacto]] (el mismo callejón, por otra
  puerta), [[0143-la-desregulacion-se-mide-en-articulos]] (el candidato natural
  del otro lado del tablero)

## Contexto y planteo del problema

El informe mide si una norma del Ejecutivo sobrevive el desafío **legislativo**
y no mide si sobrevive el **judicial**. `bloqueo_sostenido` (ADR-0069) cuenta
qué porcentaje de las normas desafiadas *en el recinto* sigue en pie, y
`desafios_legislativos` (ADR-0089) cuenta cuántas fueron desafiadas ahí. Las dos
miran el Congreso. `judicializacion` (ADR-0135/0170) mira la Justicia pero mide
**intensidad** —qué proporción de los sumarios de SAIJ menciona una medida
cautelar— sin atarla a qué norma.

El caso que destapa el hueco es concreto y grande. El **capítulo laboral del DNU
70/2023 lo frenó la Justicia, no el Congreso**: el Título IV está suspendido
desde enero de 2024 y nunca rigió, mientras el decreto entero figura entre las
normas que el Congreso no consiguió voltear. La base de Chequeado + elDiarioAR
publicada por FOPEA lo cuantifica: reproducida hoy contra su planilla,
**16 de las 45 filas del DNU 70/2023 tienen impacto NULO (35,6%) contra 4 de 116
(3,4%) en las normas posteriores**. Ese contraste no aparece en ningún
componente de ningún índice.

La pregunta de este ADR es si se puede medir. **La respuesta es que no**, y el
motivo no es el que se esperaba.

## Factores de decisión

- El rezago **se mide, no se copia del documento**: es la regla que este
  cinturón viene cazando y la que decidió el resultado en dos de las fuentes.
- Un indicador tiene que medir **lo que su nombre dice** (ADR-0218, ADR-0217).
  Una fuente que se parece a la buena y mide otra cosa es peor que ninguna.
- El ITCG es hoy una recta contra el calendario —**r(ITCG, calendario) = 0,981,
  r² = 0,962** sobre 31 meses, recalculado para este ADR— y lo que le falta es
  un componente que pueda **bajar**. Un indicador de normas que se caen sería
  exactamente eso, así que valía la pena agotar la búsqueda antes de cerrarla.

## Opciones consideradas

- **No construir el indicador y versionar el relevamiento** — elegida.
- **Construirlo sobre InfoLeg** — descartada: InfoLeg no registra nada judicial.
- **Construirlo sobre el campo `estado` de SAIJ** — descartada, y es la opción
  peligrosa: el campo existe, se llama como haría falta y mide otra cosa.
- **Construirlo contando fallos en la jurisprudencia de SAIJ** — descartada por
  cobertura y por validez, no por redundancia.
- **Construirlo sobre la base de Chequeado + elDiarioAR / FOPEA** — descartada:
  está congelada y su categoría mezcla el freno judicial con la derogación.
- **Publicarlo como indicador de vigencia NORMATIVA con otro nombre** — no se
  decide acá: es otro indicador y merece su propio ADR.

## Decisión

**No se construye el indicador.** Ninguna fuente pública dice, norma por norma,
si una norma del Ejecutivo fue suspendida por cautelar o declarada
inconstitucional. No se toca ningún índice, ningún peso, ninguna banda y ninguna
ficha.

Lo que sí se hace es dejar el relevamiento versionado en
`data/politica/supervivencia_judicial_fuentes.json`, con endpoints, campos,
casos de prueba y mediciones — mismo patrón que ADR-0140 con el mapa de acceso a
la CSJN, y por el mismo motivo: quien retome esto no debería volver a recorrerlo.

### Lo que se midió, fuente por fuente

**InfoLeg no registra nada judicial, y se comprobó contra el caso más grande.**
La ficha del DNU 70/2023 no tiene campo de estado; su texto completo (260.811
bytes) trae tres «Nota Infoleg» y las tres son normativas —Decretos 942/2025,
1120/2024 y 730/2024—, con cero menciones de cautelar, inconstitucionalidad o
CNAT. `verVinculos` lista las 50 normas que lo modifican o complementan y ningún
fallo. En el dataset abierto (`datos.jus.gob.ar`, actualizado al 2026-08-03) las
17 columnas no incluyen ninguna de estado, y de las **2.914 normas del Ejecutivo
posteriores al 10-dic-2023, 200 tienen `observaciones` y ninguna menciona algo
judicial**: 9 declaran abrogación y 6, rechazo del Congreso.

**El campo `estado` de SAIJ es la trampa.** Existe, es gratis, sigue vivo, y su
vocabulario es cerrado: *Vigente de alcance general · Individual, Solo
Modificatoria o Sin Eficacia · Derogada · Vetada · No vigente, ley caduca ·
Refundida, ley caduca*. **Ningún valor judicial.** Consultado hoy, devuelve el
**DNU 70/2023 como «Vigente, de alcance general»**, con el Título IV laboral
servido como derecho en vigor dos años y medio después de que la Justicia lo
frenara. Un indicador construido sobre ese campo mediría vida normativa y se
llamaría supervivencia judicial. Además el campo está flojo donde haría falta:
en la ventana dic-2023 → ago-2026 hay 15.128 registros de legislación y
**8.015 (53%) tienen el campo vacío**, con 29 «Derogada» y 11 «Vetada» en total.

**La jurisprudencia de SAIJ no cubre las normas.** Sobre el universo de los
**113 DNU** dictados entre el 10-dic-2023 y el 31-jul-2026, y con la consulta
más **inclusiva** posible —`texto:"<número>/<año>"`, que sobrecuenta porque
matchea cualquier norma con ese número—, **10 DNU (8,8%) tienen al menos un
documento y la mediana es cero**. De los 24 DNU de 2026, ninguno. El DNU 70/2023
solo se lleva 134 de los ~170 documentos: sacándolo, nueve normas acumulan 33 y
ciento tres no tienen ninguna. Con la consulta exacta `"Decreto N/AAAA"` la
cobertura baja a 4 de 111 (3,6%). Y los DNU son la parte visible: el universo
real son ~2.990 decretos más las resoluciones, así que **8,8% es una cota
superior**.

**El rezago de esa base, medido.** Contando los documentos de jurisprudencia
fechados en cada mes de 2026 contra el promedio del mismo mes de 2024 y 2025
—ya maduros—, un mes de fallos llega al **26% de su volumen final al mes
siguiente y al 65% a los dos meses**, y recién deja de crecer alrededor de los
cinco. `judicializacion` lo tolera porque es un cociente y numerador y
denominador se recortan juntos (ADR-0170); un conteo por norma no cancelaría
nada.

**La CSJN sigue cerrada, y ahora falta algo más que el volumen.** ADR-0140 dejó
mapeado que el buscador completo tiene la casilla «Sentencias que declaran
Inconstitucionalidad» detrás de reCAPTCHA —hoy además con un WAF— y que el
endpoint abierto topea en 10 registros sin paginar. A eso se le suma un hallazgo
nuevo: **de los 21 fallos que el detector de ADR-0141 marcó y acumuló, ninguno
nombra una norma con número** en carátula, título o materia. Aunque el tope de
10 se levantara, el payload no permite atribuir un fallo a una norma. Falta la
clave de cruce, no sólo el volumen. Por eso no se extiende el detector: se probó
sobre lo que ya juntó y no hay nada que extraer.

**La base de terceros existe, es descargable y está congelada.** El Google Sheet
de Chequeado + elDiarioAR / FOPEA responde sin login: 161 filas, y reproduce la
premisa exactamente (35,6% contra 3,4%). Pero sus 123 filas con fecha parseable
van del 20-dic-2023 al 24-abr-2025 y el producto se publicó en dic-2025: el
**rezago ya es de ~16 meses y crece solo**. Su categoría NULO mezcla por
definición metodológica el freno judicial con la modificación normativa
posterior, el hecho judicial vive en prosa —sólo 2 de 161 filas dicen «cautelar»
o «inconstitucional»— y el universo son 161 medidas de desregulación, no las
2.914 normas del Ejecutivo.

### El motivo del rechazo no es la redundancia

Vale distinguirlo porque cambia qué habría que hacer para destrabarlo. El
proxy más cercano que **sí** se puede construir —el % anual de sumarios
Federal+Nacional que mencionan «inconstitucionalidad», misma construcción que
`judicializacion` con otra palabra— **no es redundante**: contra
`judicializacion` da **r = 0,454 en niveles y −0,002 en diferencias**, los dos
holgadamente por debajo del umbral de 0,7 del informe.

Y aun así no entra, porque **cuenta la palabra en cualquier pleito** —privado,
provincial, tributario— y no dice qué norma cayó. Es el mismo error que
ADR-0131 ya había encontrado y ADR-0140 reencuadró: el problema era la búsqueda
de texto, no el concepto. El salto de 1,44 (2025) a 3,47 (2026) de esa serie es
mezcla editorial de la base más el rezago recién medido, no vetos de
constitucionalidad multiplicándose en ocho meses.

O sea: no se descarta por no aportar. Se descarta por no medir lo que su nombre
diría.

### Consecuencias

- El bloque judicial del ITCP sigue con `cobertura_judicial`, `judicializacion`,
  `velocidad_resolucion` y `paralisis_denuncias`, sin cambios. El hueco que este
  ADR abre queda **declarado y sin tapar**, que es preferible a taparlo con el
  campo `estado` de SAIJ.
- El ITCG sigue sin un componente que pueda bajar. Con r = 0,981 contra el
  calendario y **ocho de sus catorce componentes monótonos, que se llevan el
  50,7% del peso** —recontado para este ADR sobre `output/series/gestion.csv`—,
  ése sigue siendo su problema abierto, y este ADR confirma que la salida no
  viene por acá.
- **Nadie debe cablear el campo `estado` de SAIJ ni `observaciones` de InfoLeg a
  un índice como estado judicial.** Es lo que guarda
  `tests/test_supervivencia_judicial_sin_fuente.py`.
- El detector de ADR-0141 no se toca. Sigue siendo el techo de lo automatizable
  en este bloque.

### Confirmación

`tests/test_supervivencia_judicial_sin_fuente.py`, cinco guardas:

1. el relevamiento parsea y todas las fuentes traen veredicto del vocabulario
   cerrado;
2. **ninguna fuente relevada quedó declarada apta** — si alguien pone `sirve`,
   el test cae y obliga a escribir el ADR que revierte éste, en vez de cambiar
   el veredicto en silencio;
3. el relevamiento **no alimenta ningún índice** ni aparece en `itcp.py`,
   `itcg.py`, `itvc.py` o `itcm.py` (misma guarda que ADR-0141);
4. ningún índice declara un indicador con nombre de supervivencia judicial;
5. las cifras que el ADR cita salen del relevamiento y no de la prosa.

## Pros y contras de las opciones

### Construirlo sobre el campo `estado` de SAIJ

El único candidato que habría funcionado mecánicamente: campo poblado,
vocabulario cerrado, cobertura nacional, sin login. Y el peor de todos, porque
falla en silencio: devuelve «Vigente» para la norma cuyo capítulo más importante
la Justicia frenó hace dos años y medio. Ningún gate del proyecto compara un
nombre con su fuente, así que el error habría vivido en la web hasta que alguien
lo leyera. Es literalmente el caso que ADR-0218 dejó escrito.

### Construirlo sobre la base de Chequeado + elDiarioAR / FOPEA

Tentador: es pública, descargable, tiene el juicio experto hecho y reproduce la
premisa del pedido con precisión. Pero es un relevamiento cerrado de un
bootcamp, con corte en abril de 2025 y sin compromiso de continuidad — la clase
de insumo que ADR-0168 y ADR-0170 sacaron del proyecto justamente por eso: un
store curado que no se refresca es un indicador viejo sin que ningún gate lo
note. Y su categoría NULO no separa lo judicial de lo normativo, que es
exactamente la distinción que este indicador tenía que hacer.

### Publicarlo como vigencia normativa con otro nombre

Es constructible hoy —`observaciones` del CSV de InfoLeg trae abrogaciones y los
seis DNU rechazados por ambas cámaras desde dic-2023— y mediría algo real que el
tablero no tiene. No se decide acá porque **no es este indicador**: cambiarle el
nombre al resultado para poder publicar algo es la forma educada de publicar
otra cosa. Si se quiere, va con su propio ADR, su propia ficha y su propia
discusión de a qué índice pertenece.

## Más información

### Dónde iría, si alguna vez se pudiera

Queda argumentado para quien lo retome, porque la respuesta no es obvia y el
trabajo de decidirla ya está hecho.

**Iría al ITCG, no al ITCP.** El ITCP mide capacidad de gobernar frente a
actores de veto, y ahí el fenómeno relevante es la **presión** —cuántos
desafíos, con qué intensidad—, que es lo que ya miden `desafios_legislativos` y
`judicializacion`. Que una norma efectivamente **rija** no es presión sino
resultado: es ejecución, que es lo que el ITCG mide. El paralelo interno lo
confirma: `desregulacion_normativa` cuenta artículos que el Gobierno consiguió
modificar o eliminar y vive en el ITCG; su reverso —artículos que no llegaron a
regir— pertenece al mismo lugar.

Y hay un argumento empírico que no aplica al ITCP: **el ITCG es una recta contra
el calendario (r = 0,981) y el ITCP no lo es (r = −0,01)**. Un indicador que
puede bajar le agrega al ITCG información que hoy no tiene, y al ITCP le
agregaría una más de las que ya tiene.

**Con qué peso.** Entraría en `reformas_economicas` junto a
`desregulacion_normativa`, con `itvc.alta_proporcional()` — la regla escrita de
cesión proporcional, para que los tres previos cedan ×(1−peso) y conserven su
orden relativo sin dejar decimales calculados a mano. El peso queda sin fijar a
propósito: ADR-0045 exige fijarlo antes de ver el efecto, y no hay efecto que
ver mientras no haya serie.

### Lo que este ADR explícitamente NO hace

- **No propone infraestructura para esquivar bloqueos.** El buscador de la CSJN
  tiene reCAPTCHA y WAF, el de causas del PJN tiene CAPTCHA y el `robots.txt`
  del CIJ hace `Disallow` de `/adj/fallos/`. Es el organismo diciendo que el
  acceso es para consumo humano. Se aplica el gate de siempre.
- **No propone cambiar cómo se refresca `judicializacion`.** SAIJ bloquea por IP
  a los runners y la política acordada es refrescarlo a mano; esto no lo toca.
- **No declara que el dato no exista.** Existe: la Secretaría de Jurisprudencia
  de la CSJN calcula el atributo `inconstitucional` y las cautelares están en
  los expedientes. Lo que falta es que alguien lo publique **atado al número de
  la norma**. La diferencia es operativa: es un pedido de acceso a la
  información, no un problema de método.

### Lo que habría que conseguir para desbloquearlo

En orden de qué tan cerca está cada cosa:

1. Que **cualquier** fuente publique la norma impugnada como **campo**, no como
   prosa en la carátula. Sin clave de cruce norma↔fallo no hay indicador, por
   más fallos que se publiquen. Es el hallazgo nuevo de este relevamiento y el
   cuello de botella real.
2. Que la CSJN exponga el buscador de fallos, que es el pedido de acceso a la
   información que ADR-0140 dejó formulado y que sigue siendo pedible porque el
   campo ya existe y el organismo ya lo calcula.
3. Que el **MIDA del CELS** vuelva a estar en línea: conceptualmente es lo que
   haría falta —cruza normas con los amparos que las revirtieron— y hoy el sitio
   devuelve una página de mantenimiento.
