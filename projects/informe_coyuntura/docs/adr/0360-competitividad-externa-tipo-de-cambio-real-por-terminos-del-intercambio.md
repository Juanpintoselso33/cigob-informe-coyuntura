---
madr: 4
id: '0360'
estado: 'propuesto'
fecha: 2026-10-20
cinturon: 'macro'
indice: 'ITCM'
indicadores: [tcrm]
archivos: ['scripts/itcm.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'tests/test_itcm.py']
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

## Decisión

La dimensión pasa a puntuar un compuesto que cruza los dos datos en una
matriz, con el mismo patrón que la liquidez en pesos y presión compradora de
divisas ([[0257-matriz-simetrica]] y scripts/desequilibrio_monetario.py): cada
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
[[0257-matriz-simetrica]], acá el orden de las cruzadas tiene fundamento
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

## Consecuencias

- El compuesto reemplaza a la card del tipo de cambio real (un indicador que
  no puntúa no se publica como card). Los dos componentes se muestran dentro
  del modal, como en la liquidez en pesos.
- El peso de la dimensión no cambia: 11 %.
- Se actualizan la card (datos.ts), la descripción, la fórmula y la ficha;
  la ficha del tipo de cambio real registra el cambio.
- Hay que reescribir los tests que fijan el tipo de cambio como único
  indicador de la dimensión (tests/test_itcm.py y el test de pesos de
  [[0193-peso-del-desequilibrio-monetario]]).

## Limitaciones declaradas

- La ventana de los términos del intercambio es corta: unos 11 trimestres.
  Los cortes pueden ser inestables y se revisan cuando la serie crezca.
- Repetir el último trimestre hace que el componente b se mueva por saltos
  cada tres meses.

## Pendiente para pasar a aceptado

1. Fijar la fuente exacta (INDEC, índices de precios y cantidades del
   comercio exterior, términos del intercambio, base 2004 = 100) y escribir
   el colector contra el archivo real.
2. Calcular y congelar los cortes de b con el dato real.
3. Decidir si la dimensión cambia de nombre: los términos del intercambio
   miden holgura externa más que competitividad en sentido estricto
   («competitividad y condiciones externas»).
