---
madr: 4
id: '0349'
estado: 'aceptado'
fecha: 2026-10-08
cinturon: 'transversal'
archivos: ['web/src/pages/metodologia/index.astro', 'web/src/components/SemaforoLeyenda.astro', 'tests/test_marco_conceptual.py']
supersede_parcialmente: ['0199']
relacionado: ['0200', '0337']
ambito: 'Capa textual del informe — el marco conceptual en /metodologia'
origen: 'Pedido de Juan, 8-oct-2026: el texto del marco validado por LB y MJ, cargado por Luis Babino desde claude.ai (#60 y #61). Las pruebas del marco quedaron en rojo y la corrida nocturna estaba en riesgo.'
---

# ADR-0349 — El texto del marco conceptual: versión validada del 8-oct-2026

## Contexto y planteo del problema

ADR-0199 dejó el marco conceptual en `/metodologia` y fijó el párrafo de la
Fundación **palabra por palabra**, con una guarda
(`tests/test_marco_conceptual.py`): cambiarlo exige un ADR, no una poda de
prosa. El 8-oct-2026 Luis Babino reemplazó el texto del marco por la versión
validada por LB y MJ (pedido de Juan; PR #60 y #61, por el conector de
claude.ai). Ese camino mergea aunque haya pruebas en rojo, así que el cambio
entró y dejó tres pruebas fallando:

- `test_el_parrafo_original_sigue_publicado`: el párrafo cambió dos palabras.
  «La gobernabilidad…» pasó a «la gobernabilidad…» porque ahora sigue a «En
  nuestro marco conceptual,», y «sistematiza el mapa de tensiones» pasó a
  «intenta sistematizar el mapa de tensiones». El resto sigue igual.
- `test_la_escala_sigue_explicada_en_metodologia`: el título «Qué dicen los
  colores» pasó a «Qué nos dicen los colores». La explicación de los colores y
  de sus cortes sigue en la página.
- `test_no_hardcodea_ningun_corte_conocido`: un comentario CSS de
  `SemaforoLeyenda.astro` decía «8-oct-2026», y la guarda tomó el `8` por uno de
  los cortes del semáforo. Era un falso positivo.

Las tres pruebas también son la compuerta G4-G5 de la corrida nocturna: con
`main` así, la corrida de esa noche no publicaba.

## Factores de decisión

- El cambio es una decisión editorial de la Fundación, validada por dos
  personas: no se revierte porque una guarda lo encuentre distinto.
- La guarda tiene que seguir vigilando lo que le importa a ADR-0199: que el
  marco siga publicado y que la escala siga explicada.
- Que la corrida nocturna no se corte por un texto.

## Opciones consideradas

1. Actualizar la guarda al texto nuevo y registrar el cambio en este ADR.
2. Volver al texto anterior.
3. Sacar la guarda.

## Decisión

**Opción 1.** Este ADR supersede parcialmente a ADR-0199 sólo en la redacción
del párrafo:

- `FRAGMENTOS_DEL_PARRAFO_ORIGINAL` pasa a «la gobernabilidad de un proyecto de
  gobierno…» (minúscula) y «sistematizar el mapa de tensiones de la Argentina
  actual». Los otros cinco fragmentos no cambian y siguen vigilando el párrafo
  palabra por palabra.
- La guarda de la escala acepta «Qué dicen los colores» y «Qué nos dicen los
  colores», y sigue exigiendo que la página llame a `coloresEnIndice(` (los
  cortes salen de los datos, no del texto).
- El comentario de `SemaforoLeyenda.astro` deja de llevar la fecha con el
  número `8`.

### Consecuencias

- Vuelven a pasar `tests/test_marco_conceptual.py` y
  `tests/test_web_semaforo.py`, y la corrida nocturna no se corta.
- Cada cambio futuro de redacción del párrafo vuelve a necesitar su ADR: la
  guarda no se aflojó, se puso al día.
- Queda a la vista un hueco de proceso: el camino de texto de claude.ai
  publica con pruebas rojas. Es una decisión vigente (6-oct-2026), pero este
  episodio costó una noche de riesgo. Ver el ADR de los avisos de cambios.

### Confirmación

`pytest tests/test_marco_conceptual.py tests/test_web_semaforo.py` pasa. Se
comprobó rompiendo a propósito una de las palabras nuevas: la guarda falla.

## Pros y contras de las opciones

### Opción 1 — Actualizar la guarda
- Bien: respeta la decisión editorial y mantiene la vigilancia.
- Mal: hay que acordarse de hacerlo en el mismo cambio.

### Opción 2 — Volver al texto anterior
- Bien: ninguna prueba cambia.
- Mal: descarta un texto validado por dos personas.

### Opción 3 — Sacar la guarda
- Bien: no vuelve a frenar nada.
- Mal: reabre el hueco que ADR-0199 cerró (un sitio sin marco conceptual).

## Más información

ADR-0199 (marco conceptual en `/metodologia`), ADR-0200 (el bloque de la
portada), ADR-0337 (la tensión se lee por color).
