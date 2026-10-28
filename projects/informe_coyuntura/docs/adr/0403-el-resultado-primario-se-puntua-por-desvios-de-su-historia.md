---
madr: 4
id: '0403'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'macro'
indice: 'ITCM'
indicadores: [resultado_primario]
archivos: ['scripts/itcm.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'tests/test_itcm.py', 'tests/test_itcm_anclas_historia.py']
modifica: ['0072']
relacionado: ['0021', '0072', '0105', '0359', '0388', '0390', '0404']
ambito: 'ITCM · dimensión Cuentas fiscales · escala del resultado primario'
origen: 'Revisión del 28-oct-2026, a pedido de Juan, de las escalas del cinturón macro calibradas sobre el propio mandato.'
---

# ADR-0403 — El resultado primario se puntúa por desvíos de su historia

## Contexto y planteo del problema

La escala del resultado primario sobre la recaudación ([[0072]]) iba de −5 a +8 %, con
cortes elegidos mirando diciembre de 2023 (−12,0 %) y el programa estabilizado en
+6/+8 %: una convención calibrada sobre el período que mide. Contra la historia era
muy angosta: con esos cortes, el 67 % de los meses de 2004-2023 habría quedado en el
techo o en el piso. En el mandato, 28 de 33 meses salían verdes.

La historia previa (enero de 2004 a noviembre de 2023, 239 meses de la misma serie de
Hacienda sobre la recaudación total) tiene desvío de 11,878 pp, mediana −1,9 %, máximo
+19,8 % (noviembre de 2004) y mínimo −26,4 % (diciembre de 2020).

Antes de 2015 el resultado primario incluye las rentas del BCRA y del FGS, que inflan
los superávits de 2007-2014. Las series «sin rentas» mensuales de datos.gob.ar vuelven
vacías, así que la historia no se puede limpiar. Desde 2015 la serie coincide con la
del informe mensual que usa el Monitor.

## Factores de decisión

- Sacar el origen circular (regla de anclas nuevas, [[0105]]): cortes de la historia
  previa, como en [[0390]].
- Que el equilibrio fiscal siga siendo el punto medio conceptual.
- Que el método sea lo menos sensible posible a las rentas de antes de 2015.

## Opciones consideradas

- **Equilibrio = 50 y uno y dos desvíos a cada lado (elegida).**
- Percentiles 25/50/75/95 de 2004-2023, como [[0388]] hizo con las jornadas no trabajadas.
- Mínimo histórico → 10, equilibrio → 50, máximo histórico → 100.
- Dejar la escala de [[0072]].

## Decisión

El puntaje sale de cinco anclas explícitas (`ANCLAS_ITCM`), con el desvío de 11,878 pp
redondeado a 11,9:

| Resultado / recaudación | Puntaje |
|---|---|
| −23,8 % (dos desvíos de déficit) | 10 |
| −11,9 % (un desvío de déficit) | 30 |
| 0 (equilibrio) | 50 |
| +11,9 % (un desvío de superávit) | 80 |
| +23,8 % (dos desvíos de superávit) | 100 |

Entre anclas se interpola ([[0021]]). La subida es asimétrica a propósito: el primer
desvío de superávit suma 30 puntos y el primer desvío de déficit resta 20, porque un
déficit sostenido ya es tensión. Los tramos que publica la ficha cortan en las mismas
anclas y llevan el puntaje de su ancla inferior (la convención de los términos del
intercambio).

Las anclas quedan congeladas: no se recalculan con cada dato nuevo.

### Consecuencias

- Con agosto de 2026 (6,02 %), el puntaje pasa de 85,1 a 65,2: un superávit de ese
  tamaño se lee bien, no como óptimo. La dimensión Cuentas fiscales pasa de 75,1 a
  62,7 y el ITCM, junto con [[0404]], de 53,9 a 52,2.
- En el mandato, el puntaje va de 30 a 70 y ningún mes toca un extremo.
- Las rentas del BCRA y del FGS se declaran en la ficha. Sin 2007-2014 el desvío
  sería 13,1 y el puntaje de hoy, 63,8: el método se mueve 1,4 puntos. Los
  percentiles, en cambio, se corrían de 62,9 a 74,9.
- `procedencia_anclas.py` pasa el indicador de `convencion` a `historia_larga`.
- Es método: llega a la edición mensual y al archivo ([[0359]]).

### Confirmación

`tests/test_itcm_anclas_historia.py` fija las cinco anclas, comprueba que salen de
`DESVIO_RESULTADO_PRIMARIO` y que los tramos publicados cortan en ellas;
`tests/test_fichas_bandas.py` cruza la ficha con el motor.

## Pros y contras de las opciones

- Desvíos: no satura, deja el equilibrio en el medio y es la menos sensible a las
  rentas. Contra: baja mucho el puntaje de un superávit que el programa presenta como
  logro.
- Percentiles: más fieles a la distribución, pero dependen mucho del período (12 puntos
  de diferencia según se incluyan o no 2007-2014).
- Mínimo y máximo históricos: da hoy lo mismo que los desvíos, pero un solo mes
  extremo mueve toda la escala.
- La escala de [[0072]]: circular y saturada contra la historia.

## Más información

Datos: series 379.7, 379.8 y 379.9 (resultado primario) y 172.3 (recaudación) de
datos.gob.ar, acumuladas en doce meses.
