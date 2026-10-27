---
madr: 4
id: '0388'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [jornadas_individuales_no_trabajadas_12m]
parametros: ['BANDAS_ITCP["jornadas_individuales_no_trabajadas_12m"]']
archivos: ['scripts/itcp.py', 'scripts/procedencia_anclas.py', 'tests/test_itcp.py', 'web/src/lib/fichas.ts']
modifica: ['0232']
relacionado: ['0359', '0232', '0295', '0081', '0103']
ambito: 'ITCP · dimensión de conflicto social · escala de las jornadas no trabajadas'
origen: 'Revisión del cinturón político de Luis Babino (26-oct-2026): un cuarto del peso del índice está clavado en 100, jornadas incluida. Decisión de Juan del 27-oct-2026: ajustar la escala para que el indicador se mueva.'
---

# ADR-0388 — Jornadas no trabajadas con una escala que se mueve

## Contexto y planteo del problema

`jornadas_individuales_no_trabajadas_12m` (ADR-0232) suma doce meses de jornadas
no trabajadas por paros, de la Secretaría de Trabajo (cuadro C1). Sus cortes eran
**5,0 · 6,5 · 8,0 · 10,0 millones**, puestos sobre los años calendario 2006-2022.
Todo lo que quedaba por debajo de 5 millones daba 100, y la gestión vive ahí:
**16 de sus 32 ventanas** (dic-2023 a jul-2026) y 9 de las últimas 12 marcaron 100.
El dato vigente, 4.820.775 jornadas a julio de 2026, también. ADR-0232 ya lo había
declarado como limitación. Luis lo puso entre los cuatro indicadores que «sólo
pueden empeorar», y Juan resolvió ajustar la escala.

La escala vieja no venía del propio mandato: los cortes eran externos. El problema
era otro. Cortar sobre 17 promedios anuales deja el primer corte en un valor que
la historia previa rara vez alcanzó por debajo: el 15% de las ventanas
pre-mandato (32 de 204) ya caía en 100. El tramo bajo de la escala, que es donde
está la gestión, no tenía resolución.

## Factores de decisión

- **No calibrar con el período que se evalúa** (ADR-0103): los cortes salen sólo
  de la historia anterior a diciembre de 2023.
- **ADR-0081 sólo admite recalibrar un extremo inalcanzable**, y este no lo es: el
  piso (≥ 10 millones) se tocó en 2014 y entre 2016 y 2018. Correr cortes porque
  la gestión quedó pegada al techo es justo lo que esa regla prohíbe. Por eso
  acá no se mueve el techo hacia donde está la gestión: se cambia la regla con la
  que se eligen los cortes, y se aplica sólo a datos previos.
- **Usar las ventanas que el indicador publica**, no promedios anuales: el
  indicador es un acumulado móvil de 12 meses, y su distribución es la de esas
  ventanas.
- **Un paro general tiene que poder notarse**, en la medida en que la fuente lo
  registre (ver «Más información»).

## Opciones consideradas

1. Cortes en los percentiles 5, 25, 50 y 75 de las 204 ventanas móviles de 12
   meses anteriores al mandato (dic-2006 a nov-2023).
2. Dejar la escala de ADR-0232 (aplicar ADR-0081 al pie de la letra).
3. Sacar el indicador del índice y pasarlo a contexto mientras siga en 100.
4. Recalibrar sobre el rango observado de la gestión.

## Decisión

Opción 1. Los cortes nuevos, con su origen:

| Corte | Valor | Origen (ventanas dic-2006 a nov-2023) |
|---|---|---|
| 100 / 85 | 4,0 millones | percentil 5 (3,99): el 5% más calmo, la pandemia |
| 85 / 65 | 5,9 millones | percentil 25 (5,90) |
| 65 / 40 | 7,6 millones | percentil 50 (7,63) |
| 40 / 10 | 9,1 millones | percentil 75 (9,11) |

Las ventanas pre-mandato quedan repartidas 11 / 39 / 51 / 52 / 51 entre las cinco
bandas. El motor interpola entre las anclas (4,0 → 100 · 4,95 → 85 · 6,75 → 65 ·
8,35 → 40 · 9,1 → 10), así que el puntaje es continuo. La serie mensual se
calculó con la planilla oficial «datos a julio de 2026», cuadro C1, columna total
de jornadas de paro, con la misma suma de 12 meses calendario del colector
(ADR-0295). Las anclas son estadísticas de la historia previa, no conceptuales.
La procedencia sigue siendo `historia_larga` y no cambia el techo de circularidad.

### Consecuencias

- **Componente: 100 → 87,0** con el dato de julio de 2026 (4.820.775 jornadas).
- **Dimensión de conflicto social: 78,3 → 73,1** (ACLED sigue en 63,9 con 60%).
- **Índice político: 73,6 → 73,1**, con el resto del snapshot del 27-oct-2026 fijo.
- Durante el mandato el componente pasa de un rango 78,5-100 (16 meses en 100) a
  **70,7-97,0**, sin ningún mes en 100. El máximo es feb-2026 (4,19 millones),
  el mínimo oct/dic-2024 (6,24 millones).
- **Sensibilidad** sobre el dato vigente: 200.000 jornadas más lo bajan de 87,0 a
  84,2; 500.000, a 80,9; un millón, a 75,3. Con la escala vieja, las mismas
  sumas daban 99,6, 93,6 y 84,1.
- La serie histórica del índice y los meses ya publicados se recalculan con la
  escala nueva (ADR-0359): es un cambio de método y mueve también el archivo.

### Confirmación

`tests/test_itcp.py::test_banda_jornadas_individuales_no_trabajadas` fija los
cuatro cortes y ubica años de la historia previa en cada banda.
`test_jornadas_ya_no_satura_en_el_nivel_de_la_gestion` comprueba que el dato de
julio de 2026 da 87, que medio millón de jornadas más lo mueve al menos 5 puntos y
que el 100 sigue siendo alcanzable. `tests/test_fichas_bandas.py` cruza los cortes
de la ficha contra el motor.

## Pros y contras de las opciones

**1. Percentiles de las ventanas pre-mandato.** A favor: regla explícita y
reproducible, sólo con datos previos, y con resolución en el tramo bajo. En
contra: es la tercera escala del indicador en dos meses, y el 25% más conflictivo
de 2006-2023 (2014, 2016-2018) queda todo en 10.

**2. Escala de ADR-0232.** A favor: respeta ADR-0081 literalmente. En contra: el
40% de una dimensión sigue en 100 sin moverse, y su techo estaba en un valor que
el 15% de la historia previa ya superaba por abajo.

**3. Pasar a contexto.** A favor: no hay que decidir anclas. En contra: la
dimensión vuelve a tener un solo componente, que es lo que ADR-0232 vino a
corregir.

**4. Rango de la gestión.** A favor: máxima discriminación. En contra: circular.
Es lo que Luis sospecha de las anclas de conflictividad, y lo que ADR-0103 pide
vigilar.

## Más información

- **Lo que ninguna escala arregla: la fuente casi no registra los paros generales.**
  En los cuatro meses con paro general de la CGT del mandato, las jornadas del mes
  comparadas con la mediana de ese mismo mes en 2006-2023 (sin contar meses con
  paro general) dan: enero de 2024 +27.000, mayo de 2024 +453.000, abril de 2025
  −462.000 y febrero de 2026 −26.000. Antes del mandato, los paros generales
  dejaban entre −168.000 y +1.038.000 (mediana cercana a +170.000; los mayores,
  abril de 2017 y septiembre de 2018). Un paro general con millones de adherentes
  daría millones de jornadas si se contara entero, así que la estadística
  oficial lo registra, cuando lo hace, sólo en parte. La metodología publicada no
  dice si los excluye. Con la escala nueva, un paro que la fuente registre como
  medio millón de jornadas se nota (unos 6 puntos del componente); uno que no
  registre, no se nota con ninguna escala. Si se quiere que el paro general
  pese por sí mismo, eso es otro indicador (un conteo de paros generales
  convocados), no otra escala.
- Las fechas de los paros generales son las de la cronología de prensa (CGT:
  20-nov-2012, 10-abr-2014, 28-ago-2014, 31-mar-2015, 9-jun-2015, 6-abr-2017,
  18-dic-2017, 25-jun-2018, 25-sep-2018, 29-may-2019, 24-ene-2024, 9-may-2024,
  abril de 2025, 19-feb-2026).
- Sigue en pie la limitación de ADR-0232: se usa el nivel absoluto, sin
  normalizar por asalariados.
