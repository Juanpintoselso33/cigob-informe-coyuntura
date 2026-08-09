---
madr: 4
id: '0184'
estado: 'aceptado'
fecha: 2026-08-09
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/parametrica.py', 'scripts/publicar.py', 'web/src/components/IndicadorModal.astro']
continua: ['0182']
ambito: 'Semáforo de 4 colores · la dimensión también publica tensión y "por qué"'
origen: 'Revisión de coherencia de la UI de agosto de 2026: el modal de dimensión pintaba un color y nunca lo explicaba, mismo hueco que el modal de indicador ya había cerrado'
---

# ADR-0184 — La dimensión también dice de qué color es y por qué

## Contexto y planteo del problema

Cuando `_semaforos()` se escribió por primera vez (ADR-0181/0182), a cada
indicador se le adjuntó el bloque completo —`color`, `tension`, `por_que`,
y `umbrales`/`unidad` cuando corresponde— vía `_semaforo_de()`. A los
**índices y dimensiones** se les adjuntó, en cambio, un diccionario literal
aparte que sólo llenaba `color`; `tension`, `por_que`, `umbrales` y `unidad`
quedaban en `null` los cuatro. Eso no fue una decisión: fue que nadie extendió
a índices y dimensiones el mismo camino que ya existía para indicadores.
`umbrales`/`unidad` en `null` sí es correcto para ambos (no hay unidad cruda
en un puntaje que ya vive en la escala del semáforo), pero `tension` y
`por_que` en `null` no tenía ninguna razón: el color de una dimensión **ya**
sale de una tensión real calculada internamente: sólo no se publicaba.

La asimetría se volvió visible cuando el modal de indicador —`IndicadorModal.astro`,
el mismo componente que también renderiza la ficha de dimensión al abrirla desde
`.cg-dim--clickable`— empezó a nombrar su color en palabras y a dar la razón.
Abrir un indicador explica el color; abrir una dimensión, en el mismo modal,
seguía pintando un punto de color sin decir por qué. Cerrar esa brecha llevó a
la pregunta de dónde hacerlo: en la plantilla (cliente) o en la fuente
(`publicar.py`).

## Factores de decisión

- Construir la explicación en el cliente habría obligado a re-derivar los
  cortes en TypeScript. `tests/test_web_semaforo.py::test_ningun_ts_deriva_el_color_de_un_numero`
  existe exactamente para prohibir eso —ninguna línea de `web/src/lib/*.ts`
  puede nombrar un color de semáforo al lado de una comparación numérica—, y
  es la continuación directa de lo que ADR-0181 ya decidió: "el cálculo del
  color sale del cliente... ahora lo lee".
- La convención de borde **se invierte** entre espacio-tensión y
  espacio-puntaje: `color_de_tension` corta con `tensión <= tope`, y la
  tensión es una función *decreciente* del puntaje. El borde que queda
  "inclusive" del lado de tensión baja es el lado de puntaje **alto** —
  exactamente al revés de cómo se leen las bandas de valor del motor.
  Reimplementar esa cuenta una segunda vez en el cliente es una trampa de
  borde a ciegas, no una duplicación inocua.
- El puntaje de una dimensión ya está expresado en la escala propia del
  semáforo —0-100 para ITCM/ITCG/ITCP, el índice base-100 del ITVC para vida
  cotidiana—, así que no hay ninguna unidad cruda en la que armar una tabla de
  tramos. Esto es el mismo argumento de ADR-0182 para los indicadores sin
  ancla, aplicado a un nivel distinto: lo que hay que explicar acá no es "en
  qué unidad cambia el color" (no existe esa unidad) sino "a qué tensión
  equivale este puntaje".
- Re-derivar a mano una fórmula que ya existe como función es, literalmente,
  cómo ADR-0182 perdió el acotamiento a `[0, 10]` en seis tensiones de
  indicadores del ITVC. Cualquier cómputo de tensión para una dimensión tiene
  que reusar `itvc.tension_de_itvc()` (que ya clampea), no reescribir la
  fórmula lineal en el lugar nuevo.
- El bloque `semaforo` del **índice** (el nivel superior de ITCM/ITCG/ITCP/ITVC,
  no sus dimensiones) no tiene, hoy, ningún modal que lo lea. Completarlo
  igual sería trabajo especulativo sin nada que lo consuma ni forma de
  verificar que sirve para algo.

## Opciones consideradas

- **A — Construir la explicación en el cliente**, leyendo puntaje/tensión ya
  presentes en otros campos del snapshot y armando la prosa en Astro/TS —
  descartada.
- **B — Reusar `_semaforo_de()`/`_por_que()` tal cual para dimensiones** —
  descartada: `_por_que()` necesita una lista de tramos (`umbrales`) para
  redactar "a X del corte más cercano", y las dimensiones no tienen —ni deben
  tener, por el punto de arriba— esa tabla.
- **C — Extraer `tension_de_puntaje()` de `color_de_puntaje()`, reusar
  `itvc.tension_de_itvc()` para el caso base-100, y agregar una función nueva
  `_por_que_dimension()`** — elegida.

## Decisión

`parametrica.tension_de_puntaje(puntaje)` se extrae de adentro de
`color_de_puntaje()`, que pasa a llamarla en vez de repetir la cuenta:

```python
def tension_de_puntaje(puntaje: float) -> float:
    return (100.0 - float(puntaje)) / 10.0

def color_de_puntaje(puntaje: float) -> str:
    return color_de_tension(tension_de_puntaje(puntaje))
```

`publicar._semaforos()` usa esa misma función —o `itvc.tension_de_itvc()`
cuando la dimensión es base-100— para calcular la tensión de cada dimensión,
y una función nueva, `_por_que_dimension(puntaje, tension, base100)`, arma la
frase:

> "El puntaje de la dimensión, 67,1/100, equivale a una tensión de 3,3/10 en
> la escala del informe." (`estabilidad_monetaria`, ITCM)
>
> "El índice de la dimensión, 82,7, equivale a una tensión de..." (dimensión
> base-100 del ITVC)

El **color** de la dimensión sigue saliendo, igual que antes, de la tensión
**cruda sin acotar** (vía `color_de_indice_base100`/`color_de_puntaje`) — eso
no cambia. Lo nuevo es que la **tensión publicada** en el bloque `semaforo` sí
se acota a `[0, 10]` reusando `itvc.tension_de_itvc()`, exactamente la misma
separación color-crudo/tensión-acotada que ADR-0182 ya documentó para
indicadores.

`umbrales` y `unidad` siguen en `null` para dimensiones, a propósito: el
puntaje de una dimensión ya es la escala del semáforo, no hay unidad propia
en la que construir una tabla, y la leyenda —presente en todas las páginas
desde donde se abre este modal— ya explica los cortes.

**El bloque `semaforo` del índice queda exactamente como estaba**:
`tension: null`, `por_que: null`, sólo `color`. No es la misma omisión que
esta decisión cierra —hoy no hay ningún modal que muestre ese nivel—, así que
completarlo no es una extensión implícita de este ADR: es una decisión nueva,
el día que exista un consumidor.

### Consecuencias

- Toda dimensión nombra ahora su color en el mismo modal que ya lo hacía para
  indicadores; la asimetría visible que motivó este ADR queda cerrada para
  dimensiones.
- **El bug del clamp reapareció exactamente donde ADR-0182 avisó que podía
  reaparecer, esta vez en una dimensión.** `vulnerabilidad` (ITVC), puntaje
  17,2 en base-100, da tensión cruda **21,6** con la fórmula
  `5 − (17,2−100) × 0,2` — verificado a mano y contra el snapshot publicado.
  `itvc.tension_de_itvc()` la acota a **10,0**, y ese es el valor que
  efectivamente se publica: `web/src/data/informe.json`, dimensión
  `vulnerabilidad` del ITVC, `{"tension": 10.0, "color": "rojo", ...}`.
- **Sin test dedicado que lo cubra si vuelve a pasar.** El caso análogo de
  indicadores (ADR-0182) sí tiene guardia: `tests/test_publicar_semaforo.py::TestTensionEnDominio`
  falla si alguna tensión publicada de un *indicador* sale de `[0, 10]`. Esa
  clase itera `_indicadores(informe)` exclusivamente y no toca
  `dim["semaforo"]["tension"]`. Hoy el valor publicado es correcto porque
  `itvc.tension_de_itvc()` clampea puertas adentro, pero si alguien
  reintrodujera la fórmula lineal sin acotar directamente en la rama de
  dimensiones de `_semaforos()`, nada en la suite lo detectaría. Queda
  declarado como pendiente, no como hallazgo resuelto — es la misma clase de
  gap que ADR-0182 dejó anotada para el caso de indicadores, repetida acá
  porque el fix nuevo no vino acompañado de su propio test de dominio.
- El bloque `semaforo` del índice (ITCM/ITCG/ITCP/ITVC en su nivel superior)
  sigue publicando `tension: null` y `por_que: null` — comprobado en el
  snapshot vigente. Queda declarado, no perdido de vista.

### Confirmación

- `git show 270f92f -- scripts/parametrica.py scripts/publicar.py`: la
  extracción de `tension_de_puntaje()`, la función nueva
  `_por_que_dimension()`, y que el cambio en `_semaforos()` sólo toca la
  rama de dimensiones — la rama de índice queda textualmente igual.
- Snapshot vigente (`web/src/data/informe.json`, regenerado en `0e7050e`):
  dimensión `estabilidad_monetaria` del ITCM (puntaje 67,1) publica
  `"por_que": "El puntaje de la dimensión, 67,1/100, equivale a una tensión de 3,3/10 en la escala del informe."`
  y `"tension": 3.3`; dimensión `vulnerabilidad` del ITVC (puntaje 17,2)
  publica `"tension": 10.0` (acotada) con `"color": "rojo"`.
- Los cuatro bloques de índice (`itcm`, `itcg`, `itcp`, `itvc`) del mismo
  snapshot siguen publicando `"tension": null, "por_que": null`, sólo
  `"color"` — confirma que el alcance de este ADR es la dimensión, no el
  índice.
- `tests/test_publicar_semaforo.py::TestCobertura::test_los_indices_y_sus_dimensiones_tienen_color`
  sigue en verde (existía desde antes; sólo comprueba `color`, no `tension`
  ni `por_que`, así que no es evidencia de cobertura sobre lo que agrega este
  ADR). Ninguno de los tres archivos de test de semáforo
  (`test_semaforo.py`, `test_publicar_semaforo.py`, `test_web_semaforo.py`)
  cambió en el commit que trae esta decisión.

## Pros y contras de las opciones

**A — Construir la explicación en el cliente**

- Bueno: no toca `publicar.py`; el cambio queda contenido en la web.
- Malo: obliga a re-derivar los cortes en TypeScript, que es justo lo que
  `test_ningun_ts_deriva_el_color_de_un_numero` prohíbe.
- Malo: la convención de borde se invierte entre espacio-tensión y
  espacio-puntaje; reimplementarla en el cliente es una trampa de borde a
  ciegas.

**B — Reusar `_semaforo_de()`/`_por_que()` sin cambios**

- Bueno: cero código nuevo.
- Malo: `_por_que()` necesita una tabla de tramos que las dimensiones no
  tienen ni deben tener.

**C — Extraer `tension_de_puntaje()`, reusar `itvc.tension_de_itvc()`, agregar
`_por_que_dimension()`** — elegida

- Bueno: una sola función de conversión puntaje→tensión, compartida ahora por
  `color_de_puntaje()` y `_semaforos()`.
- Bueno: reusa el clamp que ya existe en vez de rederivarlo, cerrando para
  dimensiones el mismo riesgo que ADR-0182 dejó escrito para indicadores.
- Malo: agrega una segunda función de "por qué" (`_por_que_dimension`, al
  lado de `_por_que`) — dos redacciones distintas para el mismo concepto,
  según el nivel.
- Malo: no vino acompañada de un test de dominio para la tensión de
  dimensiones, a diferencia del caso de indicadores.

## Más información

### Por qué el índice queda afuera, y por qué no es el mismo hueco

El bloque `semaforo` del índice nació con la misma forma incompleta que el de
la dimensión —sólo `color`— y por el mismo motivo: nadie lo extendió. La
diferencia es que la dimensión adquirió un consumidor (el modal compartido,
al abrirse desde una card de dimensión) y el índice, hasta hoy, no. Completar
el índice ahora sería escribir una frase que nada renderiza y que nadie puede
confirmar visualmente — el mismo tipo de trabajo no verificable que este
proyecto evita en otros lugares. El día que exista un modal de índice, la
extensión es mecánica (mismo patrón que esta decisión, aplicado a
`bloque[indice_key]` en vez de a `indice.get("dimensiones")`), pero es una
decisión nueva, con su propio disparador.

### La segunda vez que se pierde el clamp

ADR-0182 ya lo dijo con toda claridad: "Volver a derivar un número que ya
tiene función es la manera de producir un defecto que no se ve." La primera
vez fue con indicadores del ITVC (seis tensiones fuera de `[0, 10]`, ningún
color afectado, detectado por revisión y no por test). Esta es la segunda:
misma fórmula, mismo tipo de re-derivación a mano, ahora en una dimensión. Se
evitó reusando la función existente en vez de escribir la cuenta de nuevo —
pero, como en la primera vez, se evitó por revisión durante la implementación,
no porque un test lo hubiera obligado. La sección de Consecuencias de más
arriba deja escrito que ese test todavía no existe para el nivel de
dimensión.
