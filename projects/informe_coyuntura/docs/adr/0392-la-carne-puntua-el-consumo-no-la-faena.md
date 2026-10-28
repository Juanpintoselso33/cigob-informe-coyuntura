---
madr: 4
id: '0392'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [consumo_carne_vacuna, consumo_carnes_total, consumo_carnes_otras]
archivos: ['scripts/vida_cotidiana/collectors/consumo_carnes.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'scripts/gate_calidad.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'web/src/lib/descripciones.ts', 'tests/test_carne_compuesto.py']
modifica: ['0217']
relacionado: ['0217', '0322', '0339', '0373']
ambito: 'ITCIS · dimensión Consumo · de qué serie salen el titular y el puntaje de las carnes'
origen: 'Revisión de Luis Babino (26-oct-2026): la carne «es consumo per cápita». Preparando la reunión del 28-oct se verificó que el titular era consumo pero el puntaje seguía la faena; decisión de Juan del 28-oct: «lo que tiene que puntuar es el consumo».'
---

# ADR-0392 — La carne puntúa el consumo, no la faena

## Contexto y planteo del problema

Desde [[0217-puntua-el-acceso-total-a-proteina-no-la-vacuna]] las dos tarjetas de carne
mostraban un dato y puntuaban otro. El titular era el consumo aparente por habitante del
tablero de la Secretaría de Agricultura (SAGYP); el color y el aporte al índice salían de
la faena del INDEC por habitante, rebaseada a fines de 2023. La razón era de datos: el
tablero es una foto del mes que se pisa en cada edición y no tiene historia hasta el
4T-2023.

La faena es producción y no descuenta exportaciones. Con la exportación vacuna en alza,
la faena por habitante cae menos que el consumo: en agosto de 2026 el componente vacuno
daba 88,5 con la faena y da 86,4 con el consumo.

## Factores de decisión

- El número que se ve tiene que ser el que puntúa.
- La base del índice es el 4T-2023 para todos los componentes.
- Una sola fuente y un solo método para las tres carnes.

## Opciones consideradas

- **Series mensuales de SAGYP por carne (elegida).** Cada área publica su consumo
  aparente por habitante, promedio móvil de 12 meses, mes a mes: vacuna en los
  «Principales indicadores del sector bovino» (desde ene-2024 en la edición vigente),
  aviar en los «Indicadores de oferta y demanda» (desde 2016) y porcina en la «Evolución
  mensual de los indicadores» (desde 2017). Las tres usan la población 2022-2040 del
  INDEC y su suma reproduce el tablero: julio de 2026, 46,74 + 20,14 + 47,01 contra
  46,75 + 20,13 + 47,06.
- Acumular el tablero mes a mes hasta tener historia: no llega nunca al 4T-2023.
- Seguir con la faena y aclararlo mejor en la tarjeta: deja el problema de fondo.

## Decisión

Titular y puntaje salen de las series mensuales de SAGYP. La tarjeta muestra el último
mes con las tres carnes y la variación interanual de cada una; el índice es ese mismo
dato rebaseado a 100 = promedio del 4T-2023. Lo leído se acumula en
`data/vida/consumo_carnes_sagyp.json`: un mes revisado se pisa y uno que la edición ya no
trae se conserva.

**El 4T-2023 de la vacuna**, que la edición vigente no trae, queda fijo en el código
(`ANCLA_VACUNA_4T2023`):

- diciembre = 52,72 kg, el anual oficial de 2023 con la población del censo 2022 (tablero
  de consumo 2025; con la población anterior era 52,24);
- octubre = 53,80 y noviembre = 53,94, despejados de la identidad del promedio móvil
  M(t) − M(t−1) = (x(t) − x(t−12))/12 con los mensuales de 2024 y los de nov/dic-2022 de
  la edición de agosto de 2023, llevados a la población nueva con el cociente medio entre
  las dos ediciones en feb-jul de 2023 (1,052; entre 1,044 y 1,062).

Con el cociente en cualquiera de los dos extremos, la base se mueve ±0,04 kg sobre 53,49.

### Consecuencias

- Septiembre de 2026: vacuna 45,81 kg (−9,8 % interanual), total 113,60 kg (−2,7 %).
  Índice: vacuna 85,6, total 97,1. Con la faena eran 88,5 y 94,0 (agosto): la vacuna
  baja y el total sube, porque el consumo de cerdo creció más que su faena.
- El titular avanza dos meses: el tablero estaba en julio y las series en septiembre.
- La tarjeta y la serie siguen en `G3_EXCEPCIONES`: es el mismo dato en dos unidades
  (kilos e índice), ya no dos fuentes.
- Se borran la reconstrucción por faena, `FAENA_TONELADAS` y la población urbana de
  `descargar_series.py`.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_carne_compuesto.py` prueba los tres lectores contra recortes de las fuentes,
que el índice salga de esas series y no del INDEC, y que la base del 4T-2023 dé 53,49 kg
para la vacuna.

## Pros y contras de las opciones

- Series de SAGYP: mismo dato arriba y abajo, y es consumo. Dos meses de 2023 de la
  vacuna son reconstruidos, con error acotado.
- Acumular el tablero: sin reconstrucción, pero sin base.
- Faena: serie larga y oficial, pero mide otra cosa.
