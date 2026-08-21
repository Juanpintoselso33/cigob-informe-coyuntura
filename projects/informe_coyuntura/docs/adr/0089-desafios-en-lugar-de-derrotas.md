---
madr: 4
id: '0089'
estado: 'aceptado'
fecha: 2026-07-19
cinturon: 'politica'
indicadores: [poder_legislativo, desafios_legislativos, derrotas_legislativas]
modifica: ['0069']
relacionado: ['0172', '0230']
ambito: 'ITCP · dimensión `poder_legislativo` · `desafios_legislativos` · `derrotas_legislativas`'
origen: 'Auditoría externa del cinturón político, prioridad 3'
---

# ADR-0089 — Desafíos legislativos en lugar de derrotas legislativas

| **Modifica** | ADR-0069 (entrada de `bloqueo_sostenido` y pesos internos) |

## Contexto y planteo del problema

La auditoría señaló que `derrotas_legislativas` y `bloqueo_sostenido` comparten
el registro de eventos y el universo de normas desafiadas, y que tenerlos como
dos indicadores del 20% cada uno le daba a un mismo conjunto de eventos ~12% del
ITCP.

Es correcto, y la medición lo confirma con holgura: **r = −0,984** sobre los
valores crudos. Más concreto todavía: **desde marzo de 2025 los dos arrojan mes
a mes el mismo número** —16 lecturas consecutivas en que las derrotas igualan
exactamente a las normas caídas que forman el denominador del bloqueo.

### Lo que NO es (corrección de una hipótesis propia)

Durante el análisis se afirmó que la relación era una **identidad algebraica**,
`derrotas = desafíos × (1 − tasa)`, a partir de que el N implícito daba entero
exacto en los meses inspeccionados. **Era falso.** La identidad no cierra en 12
de los 28 meses, todos de 2024, y la inspección había mirado sólo la cola de la
serie: en sep-2024 el N implícito daba 6,0 —redondo y convincente— cuando los
desafíos reales eran 3.

La divergencia tiene una causa real: los dos cuentan la caída distinto.

- Para **derrotas**, que una cámara rechace un decreto ya es una derrota política.
- Para **bloqueo**, la norma cae recién cuando la rechaza la **segunda** cámara
  (ley 26.122, art. 24).

El DNU 70/2023 es el caso testigo: el Ejecutivo perdió la votación en el Senado
**y conservó la norma**. Ambas lecturas son correctas; lo que ocurrió es que en
el régimen posterior convergieron.

Se deja registrado porque es el mismo error que ADR-0086 documentó doce horas
antes: un mecanismo plausible, bien argumentado, que encaja con los números
visibles y es falso. La redundancia era real; la explicación, no.

## Opciones consideradas

- **`desafios_legislativos`** — elegida: cuántas normas propias del Ejecutivo fueron llevadas a votación en el recinto en los últimos 12 meses, gane o pierda.
- **`derrotas_legislativas`** — sale del índice.

## Decisión

`derrotas_legislativas` sale del índice y entra **`desafios_legislativos`**:
cuántas normas propias del Ejecutivo fueron llevadas a votación en el recinto en
los últimos 12 meses, gane o pierda.

El par pasa a ser **(desafíos, tasa de bloqueo)**, que es la descomposición del
fenómeno en sus dos preguntas:

- **cuánto lo confrontan** — el Congreso decide dar la pelea N veces;
- **cuánto aguanta** — de esas N, sostiene una proporción.

Eso cubre los dos flancos que el índice debe atender a la vez: tensión externa y
capacidad propia. El par anterior respondía dos veces la misma.

Las derrotas se siguen relevando y quedan **a la vista como dato** dentro de la
card de bloqueo (`caidas_12m`); lo que sale es su puntaje propio.

### Pesos

| indicador | antes | ahora |
|---|---|---|
| eficacia_legislativa | 0,25 | **0,32** |
| ratio_dnu | 0,20 | **0,23** |
| veto_quorum | 0,15 | 0,15 |
| desafios_legislativos | (derrotas 0,20) | **0,15** |
| bloqueo_sostenido | 0,20 | **0,15** |

El par acoplado baja de **0,40 a 0,30** combinado. El peso liberado va a las dos
medidas más abarcativas. **`veto_quorum` no sube**: su 0% actual dice más sobre
cuántas sesiones se convocaron que sobre ausencia de conflicto, y la propia
auditoría lo advierte.

### Cuánto mejora, medido con honestidad

| par | r valores crudos | **r puntajes** | r puntajes, cambios |
|---|---|---|---|
| viejo (derrotas × bloqueo) | −0,984 | 0,937 | — |
| nuevo (desafíos × bloqueo) | −0,828 | **0,918** | **0,411** |

Sobre los valores crudos la mejora es grande. **Sobre los puntajes —que es lo
que efectivamente se promedia dentro del índice— pasa de 0,937 a 0,918: casi
nada.** Las bandas comprimen, porque ambos indicadores están cerca de su piso y
recorren los mismos tramos.

Conviene decirlo sin adornos: **lo que reduce el doble conteo es la baja de peso
combinado, no el cambio de indicador.** El cambio de indicador vale por claridad
conceptual —el par ahora responde dos preguntas— y no debe presentarse como una
corrección estadística.

En primeras diferencias el par queda en **0,411**: sigue acoplado, pero la mayor
parte del 0,918 de niveles es tendencia compartida. Queda declarado en
`ACOPLADOS_POR_DISENO` con ese motivo escrito.

### Consecuencias

- ITCP: 12 indicadores en la matriz, 43 pares, \|r\| medio 0,384 en niveles y
  **0,208 en cambios** (2,3% de pares altos).
- `desafios_legislativos` entra a `G3_EXCEPCIONES` por la misma asimetría de
  anclaje declarada de sus dos hermanos: la card ancla la ventana al mes en
  curso y la serie al último mes cerrado. Hoy difieren en 1 porque la ley 27.790
  —desafiada el 10-jul-2025— salió de la ventana de la card el 1 de julio.
- Apareció un par nuevo entre dimensiones, `bloqueo_sostenido ×
  brecha_obra_publica`, con −0,82 en niveles. **En cambios queda en −0,16**: es
  tendencia compartida, no co-movimiento. No requiere acción — y es precisamente
  el caso que la medición sobre primeras diferencias de ADR-0085 existe para
  distinguir.

## Más información

### Limitaciones

- La ventana tiene entre 4 y 13 eventos. **Ninguna descomposición de un conjunto
  tan chico queda estadísticamente independiente**, y este ADR no pretende
  haberlo logrado.
- El indicador cuenta el acto de desafiar, no su importancia: una norma central
  y una menor pesan igual.
- `derrotas_legislativas` conserva su banda en `BANDAS_ITCP` como referencia
  histórica, igual que `comisiones_caidas` y `gobernadores_alineamiento`.

### Un hallazgo colateral: la lista escrita a mano del ITCP

Al regenerar la matriz apareció que seguía publicando **11 indicadores y el par
viejo**. La causa: `validacion_externa.ITCP_SERIES` era una **lista escrita a
mano** que ya había divergido del índice —nombraba a `derrotas_legislativas` y
no incluía a los dos indicadores nuevos.

Es exactamente el bug que ADR-0082 fue a erradicar en el ITCM; el ITCP se había
quedado con su versión. Ahora se **deriva de `itcp.DIMENSIONES_ITCP`** y no
puede divergir.

Vale como recordatorio: ADR-0082 arregló *una instancia* del patrón y declaró el
principio, pero no barrió el resto del archivo buscando las otras. La instancia
sobreviviente esperó tres días y volvió a fallar igual.
