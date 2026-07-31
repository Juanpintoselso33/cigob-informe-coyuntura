---
madr: 4
id: '0079'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'macro'
indicadores: [ipi_manufacturero, emae_ia]
ambito: 'Cinturón macro · ITCM · dimensión Actividad económica · `ipi_manufacturero` · `emae_ia`'
origen: 'Revisión adversarial externa (18-jul-2026)'
---

# ADR-0079 — El IPI baja de 35% a 20%: es respaldo, no medida principal

| **Enmienda a** | ADR-0076 (alta del IPI, mismo día) |
| **Precedentes** | ADR-0045 (no recalibrar anclas cuando el rango bajo es desempeño real) · ADR-0075 (redundancia interna) |

## Contexto y planteo del problema

ADR-0076 incorporó el IPI manufacturero a la dimensión de actividad con **35%**,
para resolver que el 11% del índice colgara de un único dato. La revisión
externa objetó tres cosas, y las tres resultaron ciertas al verificarlas.

### 1. El EMAE ya contiene a la industria

No es una fuente nueva sino una segunda medición de algo que el agregado ya
incluye (~17% del EMAE). Con el reparto 65/35, la exposición total de la
dimensión a manufactura pasaba a **46%**: una dimensión llamada "actividad
económica" quedaba, casi a la mitad, en un solo sector.

### 2. El peso se había elegido por el efecto buscado

La justificación textual de ADR-0076 era que el 35% era *"peso suficiente para
que la segunda señal se note cuando diverge"*. Eso es elegir el peso a partir
del resultado que se quiere ver, no de la importancia del componente.

### 3. Hay un arrastre estructural que no se había medido

Es el hallazgo nuevo de esta revisión. Con **las mismas bandas**, un mes
**mediano** de cada indicador puntúa:

| | mediana histórica | puntaje |
|---|---|---|
| EMAE | +2,9% i.a. | **70,9** |
| IPI | −1,1% i.a. | **39,4** |

**31 puntos de brecha estructural**, porque la industria argentina rindió peor
que la actividad agregada durante todo el período disponible. El IPI al 35% no
sólo agregaba una segunda lectura: **arrastraba la dimensión hacia abajo de
forma permanente**, unos 11 puntos.

## Opciones consideradas

- **Bajar el peso del IPI de 35% a 20%**, tratándolo como respaldo y no como medida principal — elegida.
- **Recalibrar las anclas del IPI** para que un mes típico puntúe cerca de la mitad — descartada por criterio establecido en ADR-0045: las anclas se recalibran cuando el techo o el piso son matemáticamente inalcanzables, nunca cuando el rango observado es desempeño real.

## Decisión

**El IPI baja a 20% de la dimensión; el EMAE sube a 80%.**

### Por qué no se tocan las bandas

La respuesta intuitiva al arrastre estructural sería recalibrar las anclas del
IPI para que un mes típico puntúe cerca de la mitad. **Se descarta por criterio
establecido (ADR-0045)**: las anclas se recalibran cuando el techo o el piso son
matemáticamente inalcanzables, nunca cuando el rango observado es desempeño
real. Acá es desempeño real —la industria efectivamente creció menos que el
conjunto— y cerrar la brecha blanquearía la señal que el indicador viene a dar.

**El arrastre se compensa con el peso, no con las anclas.** Es la corrección
que preserva la información.

### Por qué 20% y no cero

El barrido de pesos contra la validación externa es inequívoco y va en contra
del indicador:

| peso IPI | r vs riesgo país | exposición a manufactura |
|---|---|---|
| 0% | **−0,775** | 17% |
| 15% | −0,768 | 29% |
| **20%** | **−0,767** | **34%** |
| 35% (anterior) | −0,764 | 46% |
| 50% | −0,760 | 58% |

El deterioro es **monótono**: no existe un peso donde el IPI mejore la
validación externa. Se declara y se pondera —no se esconde, como sí hizo la
versión original de ADR-0076— pero no se toma como criterio único, precisamente
porque la auditoría señaló que ese estadístico se había usado de forma
asimétrica (como prueba cuando subía, como ruido cuando bajaba).

Se conserva el indicador porque **la fragilidad que motivó su alta es real y no
la mide el r**: si el EMAE falta un mes o se revisa fuerte, la dimensión sigue
teniendo lectura. Ese es riesgo **operativo**, y el IPI sí lo cubre.

El 20% sale de un criterio explícito: **la exposición total a manufactura no
debe superar aproximadamente el doble de su peso natural en la economía**
(17% → 34%). Es el máximo defendible para un componente cuya función es
respaldo.

### Consecuencias

- Dimensión de actividad **53,5 → 56,8**. **ITCM 61,8 → 62,2**, sin cambio de
  banda.
- Correlación con el riesgo país **−0,764 → −0,767** (recupera parte de lo
  perdido; sigue por debajo del −0,775 sin IPI).
- Exposición a manufactura de la dimensión: **46% → 34%**.

### Tres afirmaciones de ADR-0076 corregidas

1. **La ganancia de frescura vale un tercio de lo declarado.** El IPI publica un
   mes antes que el EMAE, pero se promedia a tres meses, y un promedio móvil de
   (t, t−1, t−2) tiene su centro de masa en **t−1**. El IPI de may-2026 informa,
   en el neto, sobre abr-2026 — el mismo mes del EMAE.
2. **La comparación de rangos que justificaba las bandas estaba viciada.**
   Medía el EMAE sobre sesenta meses con rebote post-COVID contra treinta del
   IPI, y el IPI ya suavizado contra el EMAE sin suavizar. En ventana comparable
   el EMAE da 16,1 pp y el IPI 26,0: la industria oscila 1,6× más.
3. **"Reduce el riesgo de fuente única" es parcialmente falso.** El EMAE ya
   contiene a la industria y ambos los publica el INDEC: un cambio de
   metodología del organismo los movería juntos. Reduce el riesgo operativo, no
   el de organismo.

Las tres quedaron corregidas en ADR-0076, en la ficha metodológica pública y en
los comentarios del código.

## Más información

### Limitaciones

- El 20% surge de un criterio defendible (no más del doble de la exposición
  natural), no de una optimización. Un criterio distinto daría 15% o 25%; el
  orden de magnitud es el mismo.
- El arrastre estructural **sigue existiendo** al 20%, sólo que amortiguado.
  Está declarado en la ficha pública para que un lector no interprete el puntaje
  bajo del IPI como deterioro reciente.
- Si la industria dejara de rendir por debajo del agregado de forma sostenida,
  la brecha de 31 puntos se cerraría sola y este peso convendría revisarlo.
