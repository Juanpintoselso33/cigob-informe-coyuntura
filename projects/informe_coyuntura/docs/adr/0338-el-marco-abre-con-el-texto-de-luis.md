---
madr: 4
id: '0338'
estado: 'aceptado'
fecha: 2026-09-24
cinturon: 'transversal'
archivos: ['web/src/pages/metodologia/index.astro', 'tests/test_marco_conceptual.py']
supersede: ['0326']
relacionado: ['0199', '0337']
ambito: 'Sección «El marco» de `/metodologia` — orden del texto y explicación de los colores'
origen: 'Revisión de Luis del 23-sep-2026: «se cambió pero está mal encuadrado, hay que explicar además el tema de los colores». Juan eligió que el texto de Luis abra el marco y explicar qué significa cada color y de dónde sale.'
---

# ADR-0338 — El marco abre con el texto de Luis y explica los colores

## Contexto y planteo del problema

El apunte del 15-sep pedía «cambiar el texto del marco por el proporcionado por
Luis». ADR-0326 lo sumó al final de la sección, como tramo propio, y descartó
explícitamente cambiar la apertura. Luis lo leyó como mal encuadrado. Además, el
marco seguía explicando la tensión como «escala de 0 a 10», que desde ADR-0337
la web ya no muestra: lo que el lector ve son colores, y nada decía qué
significa cada uno.

## Factores de decisión

- El pedido original era de apertura, no de apéndice.
- La definición del informe (ADR-0199) y el barbarismo siguen haciendo falta: el
  resto del sitio usa esas nociones.
- Un ejemplo sobre el propio método tiene que ser verificable en el repo.

## Opciones consideradas

1. Dejar el texto de Luis al final (ADR-0326).
2. Reemplazar el marco entero por el texto de Luis.
3. Que el texto de Luis abra el marco y después vengan qué mide el informe, qué
   dicen los colores y el barbarismo.

## Decisión

**Opción 3.** El marco se titula «Reducir sin simplificar» y abre con la síntesis
de Luis y su distinción entre reduccionismo y simplificación con método, con sus
ejemplos (la matriz del desequilibrio monetario y las fichas con limitaciones e
historial). Siguen «Qué mide el informe» —la definición de ADR-0199, palabra por
palabra, y los cuatro cinturones—, «Qué dicen los colores» —qué significa cada
tramo y sus cortes en la escala del puntaje, derivados de `semaforo_cortes` con
`coloresEnIndice()`— y «Por qué los cuatro juntos» (barbarismo).

Del documento de Luis no se publican las partes internas del equipo (vocabulario
para posteos, cómo usar el documento) ni el ejemplo de «no fusionar tipo de cambio
con saldo comercial», que no es una decisión que el informe haya tomado
(ADR-0326).

### Consecuencias

- `tests/test_marco_conceptual.py` deja de exigir «0 a 10» y exige los cuatro
  colores y la explicación de sus cortes.
- El párrafo sobre el cinturón de espíritu de época sale del marco: es historia
  del tablero, y está en ADR-0205.

### Confirmación

`tests/test_marco_conceptual.py` y el build.
