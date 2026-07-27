# ADR-0146 — «Reglamentación irrazonable» sí cuenta como veto de constitucionalidad

- **Estado**: Aceptado
- **Fecha**: 2026-07-26
- **Ámbito**: cinturón político (ITCP) · bloque judicial · regla de codificación
- **Resuelve**: la decisión editorial abierta en ADR-0131, marcada allí como
  «la decisión de codificación más importante del set»

## La pregunta

La primera pasada sobre los 17 documentos del universo dejó **un dudoso**: un
fallo federal de nov-2024 que anula la Resolución 3132/2024 del Ministerio de
Salud —la que exigía diplomatura o maestría para prescribir cannabis medicinal—
por ser una **reglamentación irrazonable** de la ley 27.350.

¿Cuenta como veto de constitucionalidad, o el indicador debe exigir la
declaración expresa de inconstitucionalidad?

No es una pregunta menor: **es el único caso incluido de todo el universo.** Si
no cuenta, el indicador mide cero en treinta y un meses.

## Resolución: sí cuenta

**1. El propio SAIJ lo indexó como control de constitucionalidad.** Los
descriptores del fallo son «Reglamentación de la ley, control de razonabilidad,
facultades reglamentarias, jerarquía de las leyes, cannabis medicinal, derecho a
la salud, **control de constitucionalidad de oficio**, MINISTERIO DE SALUD».

Eso es dirimente por coherencia: toda la lección de ADR-0131 fue **confiar en el
tesauro controlado y no en la búsqueda de texto libre**. Se usó ese criterio para
excluir catorce casos; no se puede ignorar cuando incluye.

**2. Doctrinariamente es control constitucional.** Anular un reglamento por
irrazonable es artículo 28 CN (razonabilidad) más artículo 99 inciso 2, que
prohíbe al Ejecutivo alterar el espíritu de la ley con excepciones
reglamentarias. No es una vía lateral: **es la forma más habitual por la que los
tribunales argentinos invalidan reglamentos del Ejecutivo.** Exigir la fórmula
«declaro la inconstitucionalidad» dejaría afuera el mecanismo principal.

**3. El indicador mide el efecto, no la fórmula.** Lo que interesa es que una
norma del Ejecutivo nacional de este mandato fue invalidada por un tribunal. Qué
artículo invocó el juez para hacerlo es doctrina, no fenómeno.

## La misma regla resuelve el otro caso, en sentido contrario

El segundo pendiente —un fallo de may-2024 sobre el art. 80 LCT donde la
demandada invocó el DNU 70/2023— **se mantiene excluido**, porque sus
descriptores no tienen ninguna rama de control de constitucionalidad: el decreto
aparece como argumento de parte, no como norma cuya validez se resuelve.

**Una sola regla, dos casos, resultados opuestos.** Es la señal de que la regla
discrimina y no es un racional armado para llegar a un resultado.

Universo final de la primera pasada: **1 incluir · 16 excluir · 0 dudosos.**

## Dos hallazgos de la revisión que hay que registrar

**Los sumarios de SAIJ están truncados en el origen.** Los dos casos revisados
cortan a mitad de oración a los ~248 caracteres («…es una reglamentación
irrazonable de la ley nacional 27.350 de Uso…», «El decreto aludido es…»), y el
visor de documento por *friendly-url* devuelve **HTTP 500**. La lectura completa
del fallo **no está disponible por esta vía**. Eso acota lo que el protocolo de
ADR-0131 puede pedirle a un codificador —no se puede «leer el caso» más allá del
sumario— y refuerza que el criterio se apoye en los descriptores.

**El campo `numero-sumario:` es consultable** —`r=(numero-sumario:QG000067)`— y
permite recuperar un caso puntual. La primera pasada **no guardó identificadores**
y hubo que reconstruir el universo entero para volver a dos casos. Ya está
anotado en el registro y los dos casos revisados llevan su número.

## Lo que esto NO resuelve

Sigue abierta la otra decisión: **con un caso en treinta y un meses, ¿el ITCP
puede alojar un indicador de evento** que pasa la mayoría de los meses sin
novedad, o conviene agregarlo con otros del bloque judicial en un compuesto de
presión sobre el Ejecutivo? Esta resolución no la responde — sólo confirma que el
universo es 1 y no 0.

Y sigue pendiente la **segunda pasada con otro codificador** (kappa ≥ 0,70), que
por definición no puede hacer quien escribió ésta.
