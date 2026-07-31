---
madr: 4
id: '0166'
estado: 'aceptado'
fecha: 2026-07-31
cinturon: 'politica'
indice: 'ITCP'
cierra: ['0134', '0135', '0137', '0139']
relacionado: ['0090', '0094', '0131', '0171']
corregido_por: ['0168']
ambito: 'Cinturón político (ITCP) · regla de orientación para indicadores de control institucional'
origen: 'Al revisar una por una las decisiones editoriales abiertas del cinturón, cuatro resultaron ser la misma'
---

# ADR-0166 — La orientación de un indicador sale de la pregunta que responde

## Contexto y planteo del problema

Cuatro indicadores del cinturón político quedaron construidos, validados y
versionados, pero fuera del índice, **todos por la misma razón**. ADR-0139 lo
dice explícitamente: *"No se incorpora todavía ninguno, por la misma razón que
ADR-0134/0135/0137: falta la decisión editorial de orientación"*.

La ambigüedad, en las palabras de cada uno:

| ADR | Indicador | El problema |
|---|---|---|
| 0134 | parálisis de denuncias | *"No es obvio que más control disciplinario sea mejor ni peor para la capacidad política del gobierno"* |
| 0135 | judicialización | densidad cautelar: ¿más judicialización es más freno o más actividad? |
| 0137 | agenda común | *"su participación en la producción legislativa sube cuando lo que la hace subir es que el Congreso produce menos"* |
| 0139 | velocidad de resolución | mismo bloqueo, declarado por referencia a los tres anteriores |

Los cuatro comparten la forma: **una serie que sube puede leerse como más
fricción institucional o como más actividad del Gobierno**, y ponerle signo sin
resolver eso sería arbitrario — que es justamente lo que ADR-0045 prohíbe hacer
con las anclas, y la prohibición vale igual acá.

## Factores de decisión

- **El repo ya resolvió esta clase de ambigüedad una vez.** ADR-0090 se planteó
  lo mismo para `ratio_dnu` —"un gobierno que gobierna por decreto con éxito
  está, en un sentido literal, avanzando su plan"— y no lo resolvió eligiendo un
  signo, sino **declarando qué pregunta responde el indicador**. Fijada la
  pregunta, el signo dejó de ser opinable.
- **La estructura para ubicarlos ya existe.** ADR-0094 clasifica los indicadores
  del ITCP en tres familias: tensión externa, capacidad propia y recursos. Un
  indicador sin familia declarada es un indicador sin pregunta declarada.
- **El objetivo del cinturón está acotado.** ADR-0048 lo fijó en capacidad de
  gobernar y avanzar la agenda legislativa. La pregunta que responde un
  indicador de control institucional es, dentro de ese objetivo, cuánto lo
  confrontan las otras instituciones — no cuánta actividad tiene el Gobierno.
- No inventar un criterio nuevo cuando hay uno propio y ya aplicado es la misma
  disciplina que ADR-0161 aplicó al contraste externo.

## Opciones consideradas

- **Generalizar la regla de ADR-0090**: cada indicador declara qué pregunta
  responde y el signo sale de ahí — elegida.
- **Que entren como contexto, sin puntuar** (patrón de ADR-0022 y ADR-0051).
- **Que no entren hasta que sus series tengan más recorrido** (el criterio con
  el que ADR-0147 dejó suspendido el veto de constitucionalidad).

## Decisión

### 1. La regla, general para el ITCP

**Ningún indicador entra al índice sin declarar qué pregunta responde.** El
signo no se elige: se deriva de esa pregunta y de la familia de ADR-0094 en la
que cae. Si la pregunta no se puede escribir en una oración, el indicador no
está listo para puntuar — es la misma prueba que ADR-0131 impuso al bloque
judicial, aplicada a la orientación en vez de a la fuente.

### 2. Los cuatro son de tensión externa

Los cuatro responden la misma pregunta —**cuánto lo confrontan las otras
instituciones**— y no *cuánta actividad despliega el Gobierno*. De ahí el signo:
más control activo es menos margen del Ejecutivo, o sea más tensión.

| Indicador | Pregunta que responde | Familia |
|---|---|---|
| parálisis de denuncias | ¿el control disciplinario del Congreso está activo? | `tension` |
| judicialización | ¿cuánto se le frena la agenda por vía judicial? | `tension` |
| agenda común | ¿cuánto de la producción legislativa es del Ejecutivo? | `tension` |
| velocidad de resolución | ¿cuán rápido resuelve el sistema lo que se le plantea? | `tension` |

### 3. `agenda_comun` publica su denominador

La lectura de ADR-0137 —el cociente sube porque el Congreso produce menos— **no
desaparece con la orientación: se publica**. La card muestra el `n` de la
ventana junto al porcentaje, siempre, como ya exige ese ADR. Declarar la
pregunta resuelve el signo, no la ambigüedad de lectura, y esa se resuelve
mostrando el dato.

### Consecuencias

- Se desbloquean cuatro indicadores de tres bloques distintos —judicial,
  legislativo y empresario— con una sola decisión.
- **Esto no los incorpora todavía**: falta implementarlos con el checklist
  completo de indicador nuevo (colector, serie con backfill, bandas, ficha,
  `datos.ts`, `descripciones.ts`, `formulas.ts`, tests). La decisión que faltaba
  era ésta; la construcción es trabajo aparte.
- Queda **una elección dependiente** en ADR-0134: qué medir exactamente. Con la
  orientación fijada en parálisis, el propio ADR-0134 la deriva —*"Si el
  indicador busca parálisis, Disciplina sola es la señal fuerte"*—, así que la
  candidata es sesiones de la comisión de Disciplina, no el promedio de ambas.
  Conviene confirmarlo al implementar, no acá.
- ADR-0147 sigue suspendido y con razón: su bloqueo no era la orientación sino
  no saber cuántos eventos hay.

### Confirmación

`tests/test_web_labels.py` ya exige que todo indicador que puntúa tenga display;
al implementar cada uno, `itcp.FAMILIAS_ITCP` tiene que declarar su familia —el
guard de ADR-0092 falla si un indicador del índice no está en las estructuras
que lo acompañan.

## Más información

### Limitaciones

- La regla fija **cómo** se decide la orientación, no la vuelve automática:
  escribir la pregunta que responde un indicador sigue siendo un acto editorial.
  Lo que elimina es elegir el signo mirando qué resultado da.
- Los cuatro entran como `tension`, lo que refuerza una familia que ADR-0094 ya
  midió como la más alta de las tres. Al implementarlos hay que volver a mirar
  la lectura por partes: si la tensión externa crece sólo porque se agregaron
  indicadores de tensión, eso es composición y no señal.
