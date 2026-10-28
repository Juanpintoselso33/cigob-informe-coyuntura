---
madr: 4
id: '0404'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'macro'
indice: 'ITCM'
indicadores: [iai, credito_privado, saldo_comercial_12m]
archivos: ['scripts/itcm.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'web/src/components/IndicadorModal.astro', 'tests/test_itcm.py', 'tests/test_itcm_anclas_historia.py']
modifica: ['0022', '0056', '0120', '0341']
relacionado: ['0021', '0022', '0056', '0080', '0081', '0105', '0120', '0341', '0359', '0390', '0403']
ambito: 'ITCM · Actividad e inversión, Financiamiento y Sector externo · escalas de inversión física, crédito privado y saldo comercial'
origen: 'Revisión del 28-oct-2026, a pedido de Juan, de las escalas del cinturón macro calibradas sobre el propio mandato.'
---

# ADR-0404 — Inversión, crédito y saldo comercial con cortes de la historia previa

## Contexto y planteo del problema

Tres escalas del índice macroeconómico estaban puestas sobre el período que miden, o
en una unidad que no se compara en el tiempo:

- **Inversión física** (`iai`): bandas de ±2 y ±10 % calibradas a 2024-2026 y corridas
  +0,17 al crecimiento de la población ([[0341]]). 23 de 33 meses del mandato tocaban
  un extremo (11 en 100 y 12 en 10), y contra 2004-2023 dejaba saturado el 62 % de los
  meses.
- **Crédito privado** (`credito_privado`): bandas «calibradas a la remonetización
  2024-2026» ([[0022]]). 19 de 34 meses en un extremo.
- **Saldo comercial** (`saldo_comercial_12m`): cortes en miles de millones de dólares
  redondos ([[0120]]). Siete meses seguidos en el techo, y 14 de 34. En dólares
  corrientes, 15 mil millones no pesan lo mismo con el comercio de 2004 que con el de
  2026: la escala no se compara en el tiempo.

La historia previa, de enero de 2004 a noviembre de 2023 (239 meses):

| Indicador | Medida de dispersión | Valor |
|---|---|---|
| Inversión física (% i.a.) | rango intercuartil / 1,349 | 18,925 |
| Inversión física (% i.a.) | desvío clásico | 26,8 |
| Crédito privado (% i.a. real) | desvío | 14,471 |
| Saldo 12 meses (% del comercio) | desvío | 8,48 |

## Factores de decisión

- Sacar el origen circular ([[0105]]), como [[0390]] y [[0403]].
- Conservar el centro conceptual de cada escala: la población en la inversión, el cero
  en el crédito y el equilibrio en el saldo.
- No estirar la escala para que el mandato deje de saturar si la saturación es real
  ([[0081]]).

## Opciones consideradas

- **Inversión física:** desvíos robustos centrados en la población (elegida); desvíos
  clásicos; percentiles 25/50/75/95 de 2004-2023; dejar la escala.
- **Crédito privado:** centro en 0 y desvíos (elegida); centro en la media histórica y
  desvíos; percentiles; medir el nivel real del stock en lugar de la variación.
- **Saldo comercial:** % del comercio con centro en 0 y desvíos (elegida); % del comercio
  con percentiles; dólares con percentiles; dejar la escala.

## Decisión

**Inversión física.** Cortes en uno y dos desvíos robustos (18,9 y 37,8), centrados en
+0,17: −37,63 · −18,73 · 19,07 · 37,97, con los mismos puntajes de tramo (10 · 35 · 60 ·
80 · 100). Robusto y no clásico porque la cola de rebotes de +100 % o más infla el
desvío y comprime todo el mandato en el medio. La historia es un empalme: ISAC base
2004 hasta 2012 y el vigente desde 2013; en los 34 meses en que se superponen difieren
3,35 pp en promedio. Se declara en la ficha.

**Crédito privado.** Centro en 0 y cortes en uno y dos desvíos: −28,9 · −14,5 · 0 · 14,5 ·
28,9, con los mismos puntajes de tramo (10 · 25 · 45 · 65 · 85 · 100). El mandato está
fuera de todo el rango previo: en 2004-2023 el máximo fue +27,2 % (noviembre de 2006) y
el mínimo −35,7 % (julio de 2019); el mandato llegó a −38,4 % y a +117,8 %. Por eso
sigue tocando los extremos (17 meses), y eso es dato, no defecto de la escala. Se
declara en la ficha. La historia usa un deflactor empalmado (IPC GBA hasta 2006, San
Luis 2007-2012, CABA 2012-2016, INDEC desde entonces).

**Saldo comercial.** Pasa a medirse como **% del comercio**: saldo de doce meses sobre
exportaciones más importaciones de los mismos doce meses. Centro en 0 y cortes en
desvíos (8,48): −17 · −8,5 · 8,5 · 12,7 · 17. Con los puntajes de tramo de siempre y el
techo de 85 de [[0120]], las anclas quedan:

| % del comercio | Puntaje |
|---|---|
| −17 | 10 |
| −12,7 | 30 |
| 0 | 50 |
| 10,6 | 60 |
| 14,8 | 75 |
| 17 | 85 |

El colector publica el % como valor de la tarjeta y deja en el detalle el saldo y el
comercio en millones de dólares. La serie del titular pasa a %, y el saldo en dólares
se publica aparte (`saldo_comercial_12m_usd`) para que el gráfico lo compare con la
cuenta corriente en la misma unidad ([[0080]]).

**Umbral de la regla automática** ([[0056]]): el «superávit relevante» era 5.000
millones de dólares. Se reexpresa en 3 % del comercio: 5.000 millones eran el 3,6 % del
comercio de diciembre de 2023, el 3,2 % del promedio 2022-2023 y el 2,9 % del de agosto de
2026. No es el que decide: la regla exige además un puntaje de banda mayor que 60, y
eso recién pasa por encima del 10,6 %.

Los cortes quedan congelados.

### Consecuencias

Con los valores del snapshot del 28-oct-2026:

| Indicador | Valor | Antes | Después |
|---|---|---|---|
| Inversión física | −1,74 % | 52,0 | 58,3 |
| Crédito privado | −1,2 % | 33,4 | 53,3 |
| Saldo comercial | 15,11 % del comercio (US$ 26.472 M) | 85,0 | 76,2 |

- Actividad e inversión pasa de 41,4 a 43,3; Financiamiento, de 58,4 a 64,5; Sector
  externo, de 61,1 a 59,1. Con [[0403]], el ITCM pasa de 53,9 a 52,2.
- En el mandato, la inversión física satura 3 meses en lugar de 23; el saldo comercial
  ya no toca el techo (de 42 a 76) y el crédito sigue saturando 17 meses.
- `procedencia_anclas.py` pasa los tres a `historia_larga`. Con [[0403]], la parte
  circular del ITCM baja de 32,4 % a 10,7 % y el techo, de 0,33 a 0,11.
- La validación externa lee la serie del saldo en % tal cual: el cociente no se rearma
  desde el saldo mensual en dólares.
- Es método: llega a la edición mensual y al archivo ([[0359]]). La serie del saldo en %
  aparece en la próxima corrida de datos.

### Confirmación

`tests/test_itcm_anclas_historia.py` fija los cortes, comprueba que salen de los
desvíos declarados en `itcm.py` y fija el umbral de la regla en % del comercio;
`tests/test_fichas_bandas.py` cruza las fichas con el motor;
`tests/test_procedencia_anclas.py` vigila el techo de la parte circular.

## Pros y contras de las opciones

- Desvíos robustos (inversión): saturan poco y conservan el centro. Los clásicos no
  saturan nunca pero comprimen el mandato entre 36 y 86; los percentiles castigan el
  estancamiento (la mediana histórica es +6,9 %: crecer 0 daría alrededor de 35).
- Centro en 0 (crédito): referencia conceptual sin circularidad. La media histórica
  mueve el centro a +3 % sin un motivo propio; medir el nivel del stock es otro
  indicador y pediría su propio ADR.
- % del comercio (saldo): comparable en el tiempo y deja de saturar. Contra: el número
  de la tarjeta deja de ser un monto en dólares, que es como lo cuenta la prensa; por
  eso el monto queda en el detalle.

## Más información

Datos: ISAC 32.3 y 33.2, bienes de capital 74.3_IIBCA, exportaciones 74.3_IET e
importaciones 74.3_IIT de datos.gob.ar; préstamos en pesos del BCRA (variable 117).
