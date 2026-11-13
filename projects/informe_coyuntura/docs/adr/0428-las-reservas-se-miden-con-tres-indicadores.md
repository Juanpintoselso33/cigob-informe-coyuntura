---
madr: 4
id: '0428'
estado: 'aceptado'
nota_estado: 'El reparto de pesos (un tercio de 0,0544 cada uno) es provisorio, a confirmar con la dirección.'
fecha: 2026-11-13
cinturon: 'macro'
indice: 'ITCM'
indicadores: [reservas_bcra, reservas_brutas, meta_reservas_fmi]
archivos: ['scripts/macro.py', 'scripts/itcm.py', 'scripts/meta_reservas_fmi.py', 'data/macro/metas_reservas_fmi.json', 'scripts/descargar_series.py', 'scripts/publicar.py', 'scripts/procedencia_anclas.py', 'config.py', 'web/src/lib/fichas.ts', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/charts.ts', 'tests/test_reservas_tres_indicadores.py']
modifica: ['0005', '0286', '0287', '0409']
relacionado: ['0084', '0105', '0120', '0193', '0404', '0421', '0427']
ambito: 'ITCM · dimensión Estabilidad monetaria-inflacionaria · reservas brutas, reservas netas y meta de reservas del FMI'
origen: 'Reunión de la dirección (Luis Babino) del 13-nov-2026: el cinturón macro tiene que medir las reservas con tres indicadores — brutas, netas como las publican las consultoras y cumplimiento de la meta del FMI.'
---

# ADR-0428 — Las reservas se miden con tres indicadores

## Contexto y planteo del problema

Hasta hoy el índice macroeconómico leía las reservas con una sola tarjeta,
`reservas_bcra` («Reservas netas»), con la fórmula CIGOB de [[0005]] y [[0286]]:
netas estrictas de la planilla SDDS más los depósitos del Tesoro en dólares más el
valor absoluto del tramo de II.1 de más de tres meses a un año. Con septiembre de
2026 daba 10.725 millones de dólares, cerca de la medición convencional que mostró
el propio BCRA y muy lejos de las que publica el mercado.

En la reunión del 13-nov-2026 la dirección pidió tres lecturas:

1. **Reservas brutas**, el número que el BCRA publica todos los días.
2. **Reservas netas** con la definición de las consultoras (EcoGo, Econviews, 1816,
   PPI): brutas menos encajes, swaps y pases.
3. **Cumplimiento de la meta de reservas acordada con el FMI**.

La definición de las consultoras es exactamente `netas_sdds_estricto`, que el
colector ya parseaba: I.A + II.1 + II.2 + II.3 de la planilla SDDS. Septiembre de
2026: 46.092 − 16.754 − 19.384 − 2.488 = **7.465** millones. El II.1 (−16.754)
coincide con los encajes de la API del BCRA (variable 1243: 16.729).

## Factores de decisión

- Medir lo que el nombre dice ([[0217]], [[0218]]): «reservas netas» tiene que ser
  la definición con que se discute en público.
- Cortes de la historia previa al mandato donde haya historia ([[0404]], [[0105]]).
- Los cortes de color decididos en la unidad del indicador se anclan a
  `parametrica.PUNTAJES_DE_CORTE` ([[0427]]), no a números escritos a mano.
- No mover el resto del índice: el peso de las netas (0,0544) se reparte.
- Comprar dólares no es acumular reservas netas: la meta del FMI mide lo segundo.

## Opciones consideradas

**Reservas netas**
- **Medición estricta SDDS en la tarjeta y en toda la serie, con los componentes
  CIGOB en el snapshot (elegida).**
- Mostrar las dos mediciones en la tarjeta y puntuar la CIGOB: dos números para una
  misma tarjeta, y el que puntúa no es el que pidió la dirección.
- Tarjeta nueva para la estricta y dejar la CIGOB: dos tarjetas de «netas» que
  difieren en 3.000 millones sin que el lector sepa por qué.

**Escala de las netas**
- **Conservar las anclas conceptuales en torno al cero (elegida).**
- Recalibrar con el método de [[0404]]: no hay historia previa. El BCRA borra las
  planillas anteriores a jun-2024 (`temp1123` y `temp0524` dan 404, verificado el
  13-nov-2026) y no están en Wayback.
- Recalibrar sobre jun-2024 a hoy: circular ([[0105]]).

**Reservas brutas**
- **Media y uno y dos desvíos de dic-2017 a nov-2023, último dato del mes (elegida).**
- Promedio mensual de datos diarios: ninguno de los saldos del BCRA del colector lo
  usa (préstamos, depósitos y agregados se toman a fin de mes, `_bcra_fin_de_mes`) y
  la planilla SDDS, con la que se cruzan, es a cierre de mes.
- Ventana ene-2004 a nov-2023: en dólares corrientes 2004 no se compara con 2026; la
  ventana de 2017 es la que usó [[0421]] para el compuesto IVA + cheque.
- Medir en meses de importaciones ([[0084]]): es otro indicador.

**Meta del FMI**
- **Avance contra la meta prorrateada al mes, estimado con las netas estrictas
  (elegida).**
- Avance contra la meta entera: enero sale rojo por construcción.
- Esperar el dato oficial: sale una vez por revisión, con meses de demora.
- Compras del BCRA contra el escenario de compras: mide comprar, no acumular.

## Decisión

### 1. Reservas brutas (`reservas_brutas`, nuevo, puntúa)

API de estadísticas monetarias del BCRA v4.0, variable 1, millones de dólares. La
tarjeta lleva el último dato diario; la serie, el último dato de cada mes (el mes en
curso lleva el último publicado, así que coincide con la tarjeta).

Historia previa: 72 cierres de mes de dic-2017 a nov-2023, media **45.373,1** y
desvío muestral **11.374,9** (`itcm.MEDIA_RESERVAS_BRUTAS`,
`itcm.DESVIO_RESERVAS_BRUTAS`, congelados). Cortes en la media y en uno y dos desvíos,
con los puntajes de tramo del crédito privado ([[0404]]):

| Millones de USD | Puntaje del tramo |
|---|---|
| > 68.123 | 100 |
| 56.748 – 68.123 | 85 |
| 45.373 – 56.748 | 65 |
| 33.998 – 45.373 | 45 |
| 22.623 – 33.998 | 25 |
| ≤ 22.623 | 10 |

Anclas (puntos medios): 22.623 → 10 · 28.310,5 → 25 · 39.685,5 → 45 · 51.060,5 → 65 ·
62.435,5 → 85 · 68.123 → 100. Las brutas no tienen un cero con significado: el centro
es la media. `procedencia_anclas`: `historia_larga`.

### 2. Reservas netas (`reservas_bcra`, cambia el valor)

El valor pasa a `netas_sdds_estricto` = I.A + II.1 + II.2 + II.3, en la tarjeta y en
toda la serie de `output/series/macro.csv`, con la misma fórmula para todos los meses.
Los componentes quedan en el snapshot: brutas, los tres drenajes, depósitos del Tesoro,
el tramo de II.1 y `estimacion_cigob` (la fórmula anterior). El Tesoro deja de ser
insumo del valor: si el balance no está, se publica la estricta y los componentes
CIGOB quedan en `None` (el criterio de [[0287]] —no sustituir un insumo faltante por
otra fórmula— sigue valiendo para la planilla SDDS).

Las anclas no cambian (>20.000 → 100, 15-20 mil → 85, 10-15 mil → 70, 5-10 mil → 50,
0-5 mil → 30, ≤0 → 10). Fundamento: el método de [[0404]] necesita historia previa y no
la hay; calibrar sobre el mandato sería circular. Y el cero de la escala ([[0120]],
«el BCRA ni acumula ni quema reservas propias») significa eso recién con la medición
estricta: con el Tesoro sumado, la tarjeta podía estar en positivo con el BCRA en
posición vendida.

### 3. Cumplimiento de la meta de reservas del FMI (`meta_reservas_fmi`, nuevo, puntúa)

Metas en `data/macro/metas_reservas_fmi.json`, validadas por
`meta_reservas_fmi.cargar_metas` (base, fecha de la meta, acumulación, tipo, fuente y
revisión obligatorios; ventanas sin superponerse):

| Base | Fecha de la meta | Acumulación | Tipo | En el memorando técnico |
|---|---|---|---|---|
| 31-dic-2025 | 31-dic-2026 | +8.000 M | criterio de desempeño | −12,1 → −4,1 mil M desde fin de 2024 |
| 31-dic-2026 | 30-jun-2027 | +4.500 M | indicativa | −4,1 → +0,4 mil M desde fin de 2024 |

Fuente: informe del staff de la segunda revisión del Servicio Ampliado (mayo de 2026),
MEFP ¶19. El campo opcional `oficial` ({acumulacion, fuente}) se carga a mano cuando
el FMI publica el resultado de una fecha de prueba y reemplaza a la estimación en el
mes de esa fecha.

El FMI no publica la RIN mensual, así que se estima con la variación de las netas
estrictas SDDS desde la base. Valor = avance contra la meta prorrateada al mes:

    avance = (netas(mes) − netas(base)) / (meta × meses transcurridos / meses de la meta) × 100

Septiembre de 2026: (7.465 − (−2.712)) / (8.000 × 9/12) = 10.177 / 6.000 = **169,6 %**.
Cotejo externo de la variación: Banco Galicia, «metodología FMI», +9.968 millones a
~2-nov-2026 (La Nación, 2-nov-2026). Netas estrictas 2026 (ene a sep): −4.313, −2.888,
−2.337, −3.445, −1.605, −1.704, 5.820, 7.745, 7.465; dic-2024 −11.006; jun-2025 −18.

Cortes de color en la unidad del indicador, anclados al semáforo:

| % de la meta prorrateada | Puntaje | Color |
|---|---|---|
| 0 | 10 | rojo (piso) |
| 50 | `PUNTAJES_DE_CORTE[2]` = 25 | borde naranja/rojo |
| 75 | `PUNTAJES_DE_CORTE[1]` = 50 | borde amarillo/naranja |
| 100 | `PUNTAJES_DE_CORTE[0]` = 75 | borde verde/amarillo |
| 150 | 100 | techo |

Verde ≥ 100 %, amarillo 75-100, naranja 50-75, rojo < 50. El piso (no acumular nada) y
el techo (sobrecumplir por la mitad) son decisión propia. `procedencia_anclas`:
`externa` (la meta es del programa; los escalones de 25 puntos, propios).

La serie arranca en ene-2026, el primer mes con meta cargada.

### 4. Pesos

Las tres se reparten en partes iguales el 0,0544 que pesaban las netas:
0,0544 / 3 ≈ 0,01813 (1,81 % del índice) cada una, dentro de «Estabilidad
monetaria-inflacionaria», que sigue pesando 0,3144. IPC (0,156), expectativas (0,052)
y desequilibrio monetario (0,052) no cambian. El ancla de [[0193]] —el desequilibrio
pesa como las reservas— se lee ahora contra las tres juntas. **Reparto provisorio, a
confirmar con la dirección.**

### 5. Frescura (`config.MAX_DIAS`)

- `reservas_bcra` y `meta_reservas_fmi`: **70 días**. Medido con la fecha de
  modificación de las nueve planillas SDDS de ene a sep de 2026: salen entre 20 y 23
  días después del cierre (temp0126 el 23-feb, temp0926 el 23-oct). El último punto
  llega a ~54 días la víspera de la planilla siguiente; un mes salteado lo lleva a ~85.
- `reservas_brutas`: **20 días**. El 13-nov-2026 el último dato de la API era del
  5-nov (8 días corridos de rezago del dato provisorio).

### 6. Lo que no se hace

Las compras del BCRA del año (variable 78) contra el escenario base de 10.000 millones
no van en la explicación de la tarjeta de la meta: la regla del proyecto es que un dato
que no puntúa no se guarda en la descripción de otra tarjeta. Si la dirección lo
quiere ver, tiene que ser una tarjeta propia que puntúe o quedar afuera.

### Consecuencias

- Con los datos de la corrida del 13-nov-2026 (netas a sep-2026, brutas al 5-nov),
  mismo código y mismos datos para el resto:

  | Indicador | Valor | Puntaje | Color | Peso en el índice |
  |---|---|---|---|---|
  | Reservas brutas | 49.586 M (5-nov-2026) | 62,4 | amarillo | 0,0181 |
  | Reservas netas | 7.465 M (sep-2026; antes 10.725) | 49,9 (antes 62,9) | naranja (antes amarillo) | 0,0181 (antes 0,0544) |
  | Meta del FMI | 169,6 % (10.177 / 6.000) | 100 | verde | 0,0181 |

  Estabilidad monetaria-inflacionaria pasa de 48,7 a 50,0 y el ITCM de 51,9 a 52,3
  (tensión 4,8 en los dos casos). Sólo el cambio de medición de las netas, sin las
  dos tarjetas nuevas, lo habría bajado a ~51,2: las tres juntas promedian 70,8
  contra 62,9 de la tarjeta vieja.
- La serie de la meta, ene a sep de 2026: −240,1 · −13,2 · 18,8 · −27,5 · 33,2 · 25,2 ·
  182,8 · 196,1 · 169,6 %. Los primeros meses son muy volátiles porque el denominador
  es chico (667 millones en enero) y los pagos de deuda de enero bajan las netas.
  Junio sale rojo (25,2 %) aunque el FMI informó sobrecumplimiento en junio: la
  estimación con la planilla y la RIN del programa no coinciden, y el prorrateo lineal
  no sigue el calendario de la meta. Lo dice la ficha.
- Las netas quedan 0,1 puntos debajo del borde amarillo/naranja (7.465 contra 7.500,
  el ancla de 50): un mes de acumulación las pasa de color sin que cambie nada más.
- Es método: llega a la edición mensual y al archivo ([[0359]]).
- La ficha del índice declara una tercera excepción a la serie desde el inicio del
  mandato: la meta arranca en ene-2026.
- `validacion_externa` reconstruye el ITCM con las dos series nuevas.

### Confirmación

`tests/test_reservas_tres_indicadores.py`: la tabla de metas y su validación, la meta
vigente por mes, el prorrateo, el avance de sep-2026 (169,6 %), que el oficial gana en
la fecha de prueba, los cortes de color en sus bordes (100/99,5 · 75/74,5 · 50/49,5),
que los cortes caen en `PUNTAJES_DE_CORTE`, los cortes de las brutas desde la media y
el desvío congelados, que la tarjeta y la serie de netas son la estricta y el reparto
de pesos. `tests/test_itcm.py` y `tests/test_itcm_dimensiones_externo_fiscal.py` fijan
los pesos efectivos; `tests/test_macro_reservas.py`, que el Tesoro ya no es insumo.

## Pros y contras de las opciones

- Estricta en la tarjeta: es el número del debate público y el que usa el mercado;
  la caída de 10.725 a 7.465 en septiembre es método, no dato, y queda en la ficha.
- Anclas sin recalibrar: sin circularidad, pero la escala sigue siendo conceptual y la
  revisión en meses de importaciones ([[0084]]) sigue pendiente.
- Meta estimada con la planilla: mensual y automática, pero la RIN del memorando
  técnico tiene otra definición (tipos de cambio del programa, crédito neto del FMI,
  otros pasivos) y la variación puede diferir en cientos o miles de millones. El
  resultado oficial sale en cada revisión: para jun-2026 el FMI informó un
  sobrecumplimiento de ~4.000 millones en el acuerdo técnico del 27-oct-2026.
- Prorrateo lineal: evita el rojo de enero, pero la acumulación real se concentra en la
  cosecha y los pagos de deuda en enero y julio.

## Más información

- Meta de jun-2027: la +4.500 sobre dic-2026 supone que dic-2026 cierra justo en su
  meta (−4,1 → +0,4 en el memorando técnico). Si dic-2026 sobrecumple, el memorando
  exige menos en el tramo siguiente; la tabla mide el tramo, no el acumulado.
- BCRA, comunicado del 15-dic-2025: escenario base de compras de 10.000 millones en
  2026, ampliable a 17.000.
