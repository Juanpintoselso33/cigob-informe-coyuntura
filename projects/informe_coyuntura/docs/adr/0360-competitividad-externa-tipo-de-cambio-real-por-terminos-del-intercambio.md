---
madr: 4
id: '0360'
estado: 'aceptado'
fecha: 2026-10-20
cinturon: 'macro'
indice: 'ITCM'
indicadores: [tcrm, tcr_terminos_intercambio]
archivos: ['scripts/terminos_intercambio.py', 'scripts/itcm.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'tests/test_terminos_intercambio.py', 'tests/test_itcm.py']
relacionado: ['0009', '0073', '0257']
ambito: 'Cinturón macro · ITCM · dimensión competitividad externa'
origen: 'Pedido del 20-oct-2026 en el Proyecto del Monitor: sumar los términos del intercambio al tipo de cambio real multilateral y construir entre los dos un índice de competitividad. Diseño acordado en la misma conversación.'
---

# ADR-0360 — La competitividad externa cruza el tipo de cambio real con los términos del intercambio

## Contexto y planteo del problema

La dimensión competitividad externa pesa 11 % del índice macroeconómico y
depende de un solo dato: el tipo de cambio real multilateral del BCRA
([[0009-idm-y-tcrm-en-el-itcm]]). Dice si el peso está caro o barato, pero no
si ese nivel es sostenible. Un peso apreciado con buenos precios de
exportación no es la misma situación que un peso apreciado con precios en
caída. Los términos del intercambio (precios de exportación sobre precios de
importación, INDEC) aportan esa segunda lectura.

## Opciones consideradas

- Seguir con el tipo de cambio real solo.
- Promediar el tipo de cambio real y los términos del intercambio.
- Cruzarlos en una matriz de cuatro esquinas (elegida): un componente en su
  mejor valor no tapa al otro en el peor, como en
  [[0257-los-dos-componentes-el-mismo-regimen-y-el-mismo-peso]].

## Decisión

La dimensión pasa a puntuar un compuesto que cruza los dos datos en una
matriz, con el mismo patrón que la liquidez en pesos y presión compradora de
divisas ([[0257-los-dos-componentes-el-mismo-regimen-y-el-mismo-peso]] y scripts/desequilibrio_monetario.py): cada
componente se lleva a una posición 0-1 y el puntaje sale de interpolar
bilinealmente entre cuatro esquinas. No se promedian.

| | Términos del intercambio altos (b = 1) | Términos del intercambio bajos (b = 0) |
| --- | --- | --- |
| Peso competitivo (a = 1) | 85 · verde | 50 · amarillo |
| Peso apreciado (a = 0) | 30 · naranja | 10 · rojo |

    puntaje = (1−a)(1−b)·10 + a(1−b)·50 + (1−a)·b·30 + a·b·85

Las esquinas caen en el medio de cada color del Monitor (verde ≥60,
amarillo 40-60, naranja 20-40, rojo <20).

### La matriz es asimétrica, a propósito

Peso competitivo con términos bajos (50) puntúa mejor que peso apreciado con
términos altos (30). Con el peso competitivo el ajuste ya ocurrió y la
posición es defendible aunque los precios no ayuden. Un peso apreciado
sostenido por buenos precios depende de una variable externa y volátil: si
los precios se dan vuelta, no queda colchón. A diferencia de
[[0257-los-dos-componentes-el-mismo-regimen-y-el-mismo-peso]], acá el orden de las cruzadas tiene fundamento
conceptual y se codifica.

### Posición del tipo de cambio real (a)

Sale de los umbrales institucionales que el indicador ya tiene, no de una
ventana estadística: a = 0 con 75 o menos, a = 1 con 110 o más, interpolado
entre las anclas vigentes (a = (puntaje institucional − 10) / 90). Así no
depende del punto de arranque de ninguna ventana —diciembre de 2023 fue el
pico de la devaluación y lo habría vuelto la referencia de «competitivo»— y
respeta la paramétrica de CIGOB.

### Posición de los términos del intercambio (b)

Percentiles 0/25/50/75/100 de la serie desde diciembre de 2023 (el período
que cubre el Monitor) hasta el último trimestre publicado, CONGELADOS como
en desequilibrio_monetario.py: no se recalculan en cada corrida para que el
puntaje de un mes sea reproducible.

### Frecuencia

El INDEC publica el índice por trimestre, con unos dos meses y medio de
rezago. Cada mes usa el último trimestre publicado, sin imputar ni anticipar
con otra serie. La card y la ficha declaran el trimestre de referencia y el
rezago.

### Consecuencias

- El compuesto reemplaza a la card del tipo de cambio real (un indicador que
  no puntúa no se publica como card). Los dos componentes se muestran dentro
  del modal, como en la liquidez en pesos.
- El peso de la dimensión no cambia: 11 %.
- Se actualizan la card (datos.ts), la descripción, la fórmula y la ficha;
  la ficha del tipo de cambio real registra el cambio.
- Hay que reescribir los tests que fijan el tipo de cambio como único
  indicador de la dimensión (tests/test_itcm.py y el test de pesos de
  [[0193-peso-del-desequilibrio-monetario]]).

### Confirmación

`tests/test_terminos_intercambio.py` pinea las cuatro esquinas y su
asimetría, la posición del tipo de cambio real por sus umbrales, los cortes
congelados contra los percentiles de la ventana, que cada mes use el último
trimestre publicado y el valor de septiembre de 2026 (49,8).

## Más información

### Limitaciones declaradas

- La ventana de los términos del intercambio es corta: unos 11 trimestres.
  Los cortes pueden ser inestables y se revisan cuando la serie crezca.
- Repetir el último trimestre hace que el componente b se mueva por saltos
  cada tres meses.

### Implementación (20-oct-2026)

1. **Fuente.** INDEC, índices de precios y cantidades del comercio exterior,
   términos del intercambio, base 2004 = 100, serie trimestral
   `82.2_ITI_2004_T_27` de la API de series de datos.gob.ar (llega a 2T-2026).
   El módulo es `scripts/terminos_intercambio.py`; el compuesto se publica
   como `tcr_terminos_intercambio` y el `tcrm` pasa a
   `itcm.INDICADORES_CONTEXTO`: se sigue bajando y publicando como serie, pero
   no es card. Sus bandas se mudaron a `terminos_intercambio.BANDAS_TCR`,
   porque un indicador de contexto no puede conservar banda viva.
2. **Cortes de b**, congelados, sobre los 11 trimestres 4T-2023 / 2T-2026:
   129,7 · 138,1 · 140,4 · 143,63 · 148,15.
3. **Rezago.** Un trimestre cuenta como publicado desde el tercer mes posterior
   a su cierre (el 2T entra en septiembre). Si los términos del intercambio
   quedan más de 9 meses detrás del mes que puntúa, el compuesto no se publica.
4. **Valor publicado.** El puntaje 0-100 de la matriz; `ANCLAS_ITCM` es la
   identidad. Septiembre de 2026: tipo de cambio real 85,87 (a = 0,44) ×
   términos del intercambio 145,14 del 2T-2026 (b = 0,83) → 49,8, celda
   «apreciado con términos altos». El tipo de cambio real solo daba 49,7.
5. **Circularidad.** La dimensión pasa de un ancla de historia larga (el TCRM,
   1997-2026) a una de convención (b se calibra contra la ventana desde
   dic-2023). La fracción circular del ITCM sube de 27,3% a 38,3% y el techo
   de `procedencia_anclas.py` se sube a 0,39 en este mismo cambio. Se baja si
   los cortes de b se recalibran con la historia desde 2004.

### Pendiente

- Decidir si la dimensión cambia de nombre: los términos del intercambio
  miden holgura externa más que competitividad en sentido estricto
  («competitividad y condiciones externas»). Por ahora conserva el nombre.
