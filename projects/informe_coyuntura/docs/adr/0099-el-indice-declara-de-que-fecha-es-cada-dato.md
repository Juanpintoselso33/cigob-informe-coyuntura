# ADR-0099 — El índice declara de qué fecha es cada dato

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITCM · ITCG · ITCP · card pública "Fechas de los datos" · `publicar._vintages` |
| **Fecha** | 2026-07-20 |
| **Origen** | Auditoría externa del cinturón de gestión (doc 1), punto 3.3 |

## El planteo

> "Los cinco indicadores tienen rezagos distintos (…) Cada ficha lo aclara
> individualmente, pero como el ITCG combina estos valores en un mismo puntaje
> mensual, conviene que el informe deje explícito —no sólo en las fichas
> técnicas sino en la presentación del índice agregado— que **el «mes» del ITCG
> es en rigor un mosaico de vintages de datos distintos**, para que no se lea
> como si todos los componentes describieran el mismo momento del país."

Su recomendación operativa: señalar el rango, "por ejemplo «incluye datos de
mayo a julio de 2026 según el indicador»".

## El rango real es más ancho que el del ejemplo

La auditoría revisó cinco indicadores y vio un rango de dos meses. Sobre los
quince del índice, el rango es de **201 días**:

| | |
|---|---|
| dato más reciente | 20 de julio de 2026 |
| dato más antiguo | **31 de diciembre de 2025** |
| antigüedad media, ponderada por peso | 1,5 meses |

Los tres que arrastran el promedio:

| indicador | fecha | antigüedad |
|---|---|---|
| orden público (piquetes) | 31-dic-2025 | **6,6 meses** |
| libertad de opción en salud | 01-mar-2026 | 4,6 meses |
| litigiosidad laboral | 01-abr-2026 | 3,6 meses |

El caso de piquetes no es demora de publicación sino que **su fuente dejó de
actualizarse**: el protocolo fue anulado judicialmente el 29-dic-2025 y está en
apelación, de modo que su último dato queda congelado en esa fecha. La card lo
expone sin necesidad de que nadie se acuerde de contarlo.

Aplicado a los otros índices:

| índice | rango | antigüedad media |
|---|---|---|
| ITCG | 201 días | 1,5 meses |
| ITCM | 90 días | **2,1 meses** |
| ITCP | 61 días | 0,3 meses |

El ITCG tiene el mosaico más ancho, pero es el **ITCM** el que tiene la
antigüedad media más alta — un dato que ninguna de las dos auditorías miró,
porque cada una revisó su propio cinturón.

## Decisión

Se publica una card, **"Fechas de los datos"**, en los tres índices por bandas.
Muestra la antigüedad media ponderada, el rango entre el dato más nuevo y el
más viejo, y los componentes que superan el trimestre.

**No se declara nada a mano.** El cálculo sale de `fecha_dato`, que cada card ya
trae, ponderado por `peso_efectivo`. Es deliberado: un diccionario paralelo se
desactualiza en silencio, y ése fue el modo de falla de ADR-0082 (la lista de
componentes del ITCM), ADR-0089 (la del ITCP, que había divergido sin que nadie
lo notara) y el que ADR-0092 y ADR-0094 tuvieron que cubrir con tests. Acá no
hace falta test: no hay nada que se pueda desincronizar.

### Distinta del rezago de ADR-0092

Son dos preguntas que conviene no confundir:

- **ADR-0092 (rezago)**: dónde cae el centroide de la *ventana* de cada
  indicador. Un promedio móvil de doce meses describe la situación de hace seis
  aunque su último dato sea de ayer.
- **Este ADR (vintages)**: de qué fecha es el *dato*. Un indicador puede tener
  el dato de ayer y describir el año pasado, o al revés.

El ITCP tiene hoy las dos cards y muestran cosas distintas: 5,8 meses de rezago
de ventana contra 0,3 meses de antigüedad de dato. Es el índice más fresco en
datos y el más retrospectivo en ventanas.

## Detalles de implementación

- Las fechas se emiten **en prosa** ("31 de diciembre de 2025"), no en formato
  ISO: el texto es público y el resto del informe no usa fechas técnicas.
- Una fecha posterior a hoy no es un dato del futuro sino una ventana rotulada
  por su mes de cierre —la encuesta del ISAC pregunta por los tres meses
  siguientes—, así que la antigüedad se acota en cero.
- La card no se emite con menos de tres componentes fechados.

## Limitaciones

- **`fecha_dato` significa cosas distintas según el indicador**: para unos es el
  día del scrapeo, para otros el mes al que corresponde el dato de la fuente.
  La card mide lo que cada ficha declara, y la heterogeneidad de ese campo es
  una deuda anterior a este ADR.
- El ITVC queda afuera: su estructura base-100 no expone los componentes en el
  mismo formato.
- **Medir el mosaico no lo corrige.** Un índice mensual que combina datos de
  siete meses distintos sigue siendo eso; lo que cambia es que ahora lo dice.
