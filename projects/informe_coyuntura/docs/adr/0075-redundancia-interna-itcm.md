---
madr: 4
id: '0075'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'macro'
archivos: ['scripts/validacion_externa.py', 'scripts/publicar.py']
relacionado: ['0019', '0021', '0031', '0078']
ambito: 'Cinturón macro · ITCM · validación · `scripts/validacion_externa.py` · `scripts/publicar.py` · página del cinturón'
origen: 'Auditoría de consistencia del cinturón macro (17-jul-2026), sección IV.3'
---

# ADR-0075 — Se publica cuánta información distinta aporta cada componente del ITCM

## Contexto y planteo del problema

La auditoría pidió medir y publicar la **correlación entre los componentes del
propio índice**, por el riesgo de prociclicidad: si actividad, recaudación,
crédito y capacidad de fondeo se mueven todos con el mismo ciclo, promediarlos
no produce quince lecturas independientes sino una sola repetida quince veces,
y el índice transmite una falsa sensación de convergencia.

**Se verificó primero si ya estaba cubierto y no lo estaba.** Existe una matriz
de validación cruzada (ADR-0031), pero cruza **los cuatro índices contra
anclas externas** —riesgo país, Merval, ICC, EPU—. Es una pregunta distinta:
aquélla mide si el índice acierta, ésta mide si sus partes dicen cosas
distintas.

## Opciones consideradas

- **Correlacionar los puntajes mensuales** — elegida: el puntaje es lo que efectivamente se promedia dentro del índice, así que es ahí donde dos indicadores acoplados terminan contando dos veces el mismo ciclo.
- **Correlacionar los valores crudos** — descartada por lo anterior.
- **Reponderar por este hallazgo** — no se hace: no se cambia ninguna ponderación a partir del resultado.

## Decisión

Se agrega `matriz_redundancia_itcm()` a la validación y un bloque público
"Consistencia interna" en la página del cinturón.

### Sobre qué se correlaciona

Sobre los **puntajes** mensuales, no sobre los valores crudos. El puntaje es lo
que efectivamente se promedia dentro del índice, así que es ahí donde dos
indicadores acoplados terminan contando dos veces el mismo ciclo. Un par con
|r| alto y en **dimensiones distintas** es el caso que preocupa: el índice cree
estar midiendo dos cosas y mide una.

La construcción de los valores mes a mes se extrajo a `_valores_itcm_por_mes()`,
compartida con la reconstrucción histórica del índice, para que las dos no
puedan divergir en qué componentes miran — el modo exacto en que ya se había
colado un error antes (lista de componentes escrita a mano).

### Consecuencias

Trece componentes con serie histórica, **78 pares**:

| medida | valor |
|---|---|
| correlación media entre pares (\|r\|) | **0,502** |
| pares con \|r\| ≥ 0,7 | **26%** (20 pares) |
| de ésos, en dimensiones distintas | **17** |
| pares con \|r\| < 0,3 | **27%** |

Los más acoplados:

| par | r | |
|---|---|---|
| IPC × expectativas de inflación (REM) | +0,935 | misma dimensión |
| crédito privado × capacidad prestable | +0,912 | misma dimensión |
| capacidad prestable × expectativas de inflación | +0,911 | **dimensiones distintas** |
| capacidad prestable × IPC | +0,910 | **dimensiones distintas** |
| saldo comercial × tipo de cambio real | −0,908 | **dimensiones distintas** |

- El bloque se publica en la página del cinturón macro, con los números, los
  pares concretos y la salvedad muestral por delante.
- No se cambia ninguna ponderación por este hallazgo. Reponderar contra
  correlaciones estimadas sobre un único episodio macroeconómico sería
  sobreajustar a un período que no se repite.
- El tipo del snapshot quedó genérico: extender la medición a los otros tres
  índices no requiere cambios de estructura.

## Más información

### Precedentes directos

ADR-0019 (validación externa) · ADR-0031 (matriz de validación cruzada) · ADR-0021 (puntaje interpolado)

### Limitaciones

- n = 29-31 meses según el par. Con esa muestra, las correlaciones tienen
  intervalos de confianza amplios y no se publican como estimaciones precisas.
- Correlación de Pearson sobre niveles de puntaje: no distingue asociación
  contemporánea de tendencia común, que es justamente la ambigüedad del
  período.
- El IAI y el ICIP no tienen serie histórica y quedan fuera de la matriz, igual
  que en la reconstrucción del índice.

### Interpretación

El hallazgo **no se publica como defecto de construcción**, porque la evidencia
no alcanza para afirmarlo. El período disponible son treinta y un meses de un
**único programa de estabilización**, en el que la desinflación, la recuperación
de la actividad y la consolidación fiscal avanzaron simultáneamente. En esa
ventana, que los indicadores co-muevan refleja sobre todo el proceso
macroeconómico. Distinguir "el índice cuenta dos veces lo mismo" de "el país
atravesó un proceso con una dirección dominante" exigiría un período que
incluya al menos un ciclo con signos divergentes, y no existe todavía.

Que la dispersión sea real —un 27% de pares prácticamente independientes junto
al 26% muy acoplado— es evidencia en contra de la lectura extrema de que el
índice mide una sola cosa.

Lo que **sí** se afirma sin reservas es la consecuencia para el lector: cuando
varias dimensiones coinciden en el diagnóstico, eso no debe leerse como varias
confirmaciones independientes del mismo resultado. Esa advertencia va en el
texto público.
