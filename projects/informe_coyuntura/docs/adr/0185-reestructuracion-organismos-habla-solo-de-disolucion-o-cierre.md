---
madr: 4
id: '0185'
estado: 'parcial'
fecha: 2026-08-09
cinturon: 'gestion'
indicadores: [reestructuracion_organismos]
ambito: 'ITCG · `reestructuracion_organismos` · etiquetas públicas y pregunta abierta sobre el denominador'
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

### Pregunta abierta sobre el 45 (denominador)

CIGOB no preguntó por el denominador, pero la instrucción de precisar
qué se mide obliga a revisarlo: si el "plan completo" (`ORGANISMOS_PLAN_TOTAL
= 45`) se calibró contra un universo más amplio que disolución/cierre, la
etiqueta ya no describe la vara contra la que se compara.

**Evidencia, leyendo la historia real (no supuesta):**

El commit que introdujo el 45 (`43ff990`, 23-may-2026) describe el indicador,
ANTES de automatizarlo, como *"Conteo de decretos de disolución/fusión de
organismos en el Boletín Oficial"*, y el mensaje de commit dice literalmente:

> "18 docs = 40% validado con estimación manual; 45 docs = 100%"

hablando de esos "actos de disolución/fusión" — no de disoluciones a secas.
La estimación manual que fijó el 45 se hizo, con toda evidencia disponible,
contra la lectura AMPLIA que CIGOB ahora pide dejar de usar. La búsqueda en
InfoLeg, en cambio, siempre fue solo `texto="disolucion"` — nunca hubo una
segunda búsqueda por "fusión" que se sume al conteo.

**Conclusión:** si el 45 se calibró para el universo amplio, angostar la
etiqueta sin tocar el denominador deja el indicador midiendo disoluciones
contra una vara que se fijó pensando en más cosas que disoluciones. Eso
podría estar SUBESTIMANDO el avance real (el "plan completo" cuenta cosas
que "disolucion" no captura, así que el mismo esfuerzo de gobierno rinde un
% más bajo del que debería).

**Por qué no se corrige el 45 en este ADR:** no existe una nueva estimación
manual de cuántas disoluciones o cierres, exclusivamente, componen el plan
completo. Cambiar 45 por otro número sin ese trabajo sería reemplazar una
convención declarada por otra sin evidencia — el mismo error que este
proyecto evita en otros indicadores (ver la disciplina de "no aproximar con
un factor inventado" documentada junto a `fetch_gasto_funcionamiento()` en
`scripts/gestion.py`, a raíz de otra observación de la misma ronda de CIGOB).
Además hay una razón que atenúa el
problema sin resolverlo: en el derecho administrativo argentino la fusión por
absorción de un organismo suele instrumentarse jurídicamente como la
disolución del organismo absorbido ("disuélvase... e incorpórase a..."), así
que una parte de lo que la estimación de mayo contaba como "fusión" bien
puede aparecer en el texto de la norma con la palabra "disolución" y ya estar
adentro del conteo actual. No hay forma de saber qué proporción sin releer
los 18 casos originales uno por uno.

**Recomendación:** antes de la próxima recalibración de este indicador,
alguien con acceso al archivo de normas debería re-hacer la estimación
manual restringida a disolución/cierre puro (sin fusiones ni
transformaciones) para fijar un plan completo consistente con la etiqueta
nueva. Hasta entonces, el 45 queda como está, con esta limitación declarada
en la ficha (`web/src/lib/fichas.ts`, bloque `limitaciones`) y en el código
(`scripts/gestion.py`, comentario junto a `ORGANISMOS_PLAN_TOTAL`).

### Consecuencias

- El indicador no cambia su valor publicado: mismo cálculo, mismo conteo,
  misma banda. Ningún número que ya estaba en el snapshot se mueve.
- El estado de este ADR es `parcial`: la parte de precisión de etiquetas está
  cerrada; la pregunta sobre el denominador queda declarada y abierta,
  explícitamente, para que alguien la retome con la evidencia que falta.

### Confirmación

`python -m pytest tests/ -k reestructuracion` y la suite completa de
`test_itcg.py`/`test_procedencia_anclas.py` verifican que el cálculo no
cambió (banda idéntica, denominador idéntico) mientras el texto público sí lo
hizo.

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
  radar hasta que se puso a prueba la precisión de la etiqueta.
- Malo: no resuelve la pregunta sobre el 45 — la deja declarada, no cerrada.

## Más información

### Por qué la clave técnica no se toca

`reestructuracion_organismos` aparece en `INDICADORES_ESPERADOS`,
`BANDAS_ITCG`, `DIMENSIONES_ITCG`, la serie histórica en
`data/historico/indicadores.json`, y decenas de asserts de test. Ninguna de
esas referencias es visible para el lector del informe: son identificadores
internos. Renombrar la clave sería un costo real (romper la continuidad de
la serie, forzar una migración de datos) por un beneficio nulo, porque el
problema que CIGOB señaló nunca estuvo en el nombre interno.
