# ADR-0116 — La sección de robustez del ITVC estaba vieja, y ahora avisa

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITVC · matriz de redundancia · validación externa · `tests/test_redundancia_itvc.py` |
| **Fecha** | 2026-07-20 |
| **Origen** | Pregunta del usuario: "¿recalculaste todo en la sección de robustez?" |

## El hallazgo

No. Tres altas seguidas —`alquiler_real` (ADR-0111), `indice_lider` (ADR-0112) y
la reorganización de dimensiones (ADR-0115)— se publicaron **sin volver a correr
`validacion_externa.py`**, que es el script que produce la matriz de redundancia
y las correlaciones del cinturón.

El informe publicaba, en su propia sección de robustez:

| | publicado | real |
|---|---|---|
| componentes de la matriz | **14** | 16 |
| pares medidos | 91 | **120** |
| ITVC↔ICC, niveles | **0,554** | 0,525 |
| ITVC↔ICC, diferencias | **0,309** | 0,147 |

La matriz además clasificaba los pares con el mapeo de dimensiones anterior, de
modo que `alquiler_real ↔ ipc_alimentos` figuraba como cruce entre dimensiones
cuando hoy comparten la de precios.

## A quién atribuirlo

Reconstruyendo el estado previo a cada cambio, la correlación en niveles sin
`alquiler_real` ni `indice_lider` da **0,554 exacto**: el número que estaba
publicado. **La deriva viene de ADR-0111, no de la reorganización de hoy** —que
es demostrablemente neutral, su ponderado exacto se mueve 0,0009.

Es decir: el informe mostró una validación vieja durante las tres altas.

## Lo que falla en el proceso, no en el cálculo

`CLAUDE.md` ya dice que hay que correr `validacion_externa.py` cuando se agrega
o cambia un indicador de una paramétrica, y explica por qué con un caso
verificado: en julio, tras tres recalibraciones y dos series nuevas del ITCP, el
r publicado contra el EPU siguió siendo el de la mañana.

**La regla existía y se salteó igual, tres veces seguidas.** Una regla escrita
que depende de acordarse no es una defensa: la primera vez que se olvida, nada
falla y el número viejo se publica como si fuera nuevo.

## Decisión

Además de recalcular todo, se agrega el guard que faltaba:
`test_lo_publicado_cubre_los_componentes_que_hoy_puntuan` compara el número de
componentes de la matriz **publicada en el snapshot** contra los que el índice
pondera hoy, y falla si no coinciden.

Se verificó que dispara: forzando el valor a 14 —el estado stale real— el test
falla con "la matriz publicada mide 14 componentes y el índice tiene 16: falta
correr validacion_externa.py". Un guard que nunca se probó no se sabe si frena.

## Lo que el guard no cubre

Detecta que **faltan componentes**, que es la forma más común de esta falla.
**No detecta una correlación vieja** si el conjunto de componentes no cambió —
por ejemplo tras recalibrar una banda o refrescar una serie. Para eso haría
falta comparar el valor publicado contra un recálculo, que es caro y depende de
datos de red.

Queda declarado como límite: este guard atrapa la desactualización estructural,
no la numérica.

## Números corregidos

| | |
|---|---|
| matriz | 16 componentes · 120 pares · \|r\| medio 0,400 |
| en diferencias | \|r\| medio 0,202 · **ningún par sobre el umbral** |
| ITVC↔ICC | 0,525 niveles · 0,147 diferencias (n=30) |

La lectura de fondo no cambia: en niveles el cinturón muestra acoplamiento y al
destendenciar no queda ninguno sobre el umbral, que es la conclusión que la card
ya publicaba.
