---
madr: 4
id: '0231'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'vida'
indicadores: [mora_familias, carga_servicio_deuda_hogares]
archivos: ['scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/publicar.py', 'scripts/gate_calidad.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
relacionado: ['0045', '0067', '0108', '0109', '0154']
ambito: 'ITCIS · dimensión de vulnerabilidad financiera'
origen: 'Barrido de dimensiones sostenidas por un solo indicador'
---

# ADR-0231 — La carga de deuda anticipa la mora

## Contexto y planteo del problema

Desde [[0154-endeudamiento-e-indice-lider-salen-del-itvc]], vulnerabilidad
financiera dependía sólo de `mora_familias`. La mora es una señal directa, pero
tardía: observa el incumplimiento cuando ya ocurrió. El BCRA publica en el
Informe de Estabilidad Financiera una estimación mensual de la carga del
servicio de deuda de las familias sobre la masa salarial registrada (CDF/MS),
con historia desde abril de 2012.

En el corte de abril de 2026 la carga es **24,076%**, contra **10,193%** en el
promedio del cuarto trimestre de 2023. Rebaseada e invertida da **42,3**. La
correlación con la mora es +0,883 en niveles, pero sólo +0,182 en primeras
diferencias sobre 31 meses comunes: comparten el deterioro general sin repetir
el movimiento mensual.

## Factores de decisión

- **Una dimensión sostenida por una sola observación renormaliza todo su peso
  sobre ella.** Si esa fuente falla un mes, el 10% del índice se apoya en un
  carry-forward sin que nada lo señale.
- **La mora llega tarde por construcción**: mide el incumplimiento una vez
  ocurrido. Una dimensión que se llama «vulnerabilidad» debería ver también la
  presión previa al daño.
- **El candidato no puede repetir a la mora.** Comparten el deterioro del
  período, así que el criterio es el movimiento mensual, no el nivel.
- **El reparto tiene que fijarse antes de mirar el efecto**, o la ponderación
  se elige por el número que produce.

## Opciones consideradas

1. Sumar la carga del servicio de deuda del BCRA al 30%.
2. Sumarla al 50%, tratando las dos señales como equivalentes.
3. Devolver `endeudamiento_familiar`, que salió en ADR-0154.
4. Dejar la dimensión con un solo componente.

## Decisión

Se incorpora `carga_servicio_deuda_hogares` con **30%** de vulnerabilidad y la
mora conserva **70%**. El peso nominal de la dimensión permanece en 10%.

El reparto se fijó antes de mirar el efecto: la mora es directa, se publica
mensualmente y confirma daño materializado; la carga es una estimación que
anticipa presión de pagos y cuyos puntos mensuales se liberan en lotes
semestrales. Por esa diferencia de inmediatez no entran 50/50.

Los dos componentes se invierten contra el cuarto trimestre de 2023: más mora o
más salario comprometido implica peor capacidad de pago. La planilla se busca
por el título de la hoja y el rótulo `CDF / MS`, no por una posición fija.

### Consecuencias

- **La dimensión pasa de 17,2 a 24,7** y sigue marcada como crítica. El
  componente nuevo entra en 42,3 con 3% efectivo del índice; la mora baja de
  10% a 7% efectivo y sigue aportando −5,80 puntos.
- **El ITCIS pasa de 89,3 a 90,0** y la tensión de 7,1 a 7,0. El cinturón
  queda con 19 componentes y los 19 puntúan.
- **El movimiento del índice es hacia arriba y hay que decirlo**: diluir el
  componente más extremo del cinturón mejora el número aunque nada del mundo
  haya cambiado. Se acepta porque el reparto se fijó antes de medirlo y porque
  la dimensión seguía apoyada en una sola observación — pero un lector que
  compare contra ayer tiene que poder leer que 0,7 puntos son de método.
- **La carga discrimina**: recorre de 112,0 a 42,3 durante el mandato y no toca
  el techo de winsorización en ninguno de sus 29 meses. No agrega una constante.
- El dato de fondo es fuerte por sí solo: el servicio de deuda de los hogares
  pasó de **10,19% a 24,08% de la masa salarial registrada** — más que se
  duplicó en dos años y medio.

### Confirmación

`tests/test_segundas_patas.py` cuida que la dimensión no vuelva a quedar con un
solo componente, que el reparto siga siendo 70/30, que la polaridad siga
invertida y que la planilla se busque por rótulo y no por posición.

## Más información

- Vulnerabilidad deja de renormalizar todo su 10% sobre una única observación.
- No vuelve `endeudamiento_familiar`: el stock de crédito sigue sin distinguir
  acceso sano de fragilidad y permanece fuera del índice.
## Pros y contras de las opciones

**1. Carga del BCRA al 30%.** A favor: anticipa la presión de pago en vez de
confirmarla, tiene 169 meses de historia desde 2012, y su correlación con la
mora en primeras diferencias es de sólo +0,182 — no repite el movimiento
mensual. En contra: es una estimación y no una medición, y sus puntos mensuales
se liberan en lotes semestrales, así que la card arrastra rezago.

**2. Al 50%.** A favor: más simple de justificar. En contra: iguala una
medición directa y mensual con una estimación de publicación semestral; la
diferencia de inmediatez es real y el reparto debería reflejarla.

**3. Devolver `endeudamiento_familiar`.** A favor: ya existía el colector. En
contra: salió por un motivo que sigue vigente — el stock de crédito no
distingue acceso sano de fragilidad, y leía el crecimiento de la deuda real
como mayor acceso.

**4. Dejarla con un componente.** A favor: cero trabajo. En contra: es
exactamente el problema — el 10% del índice colgando de una sola observación.

- La card declara el mes del dato y tolera hasta 300 días de rezago porque la
  frecuencia interna es mensual pero la publicación es semestral.
- Si falta una de las dos series, el motor renormaliza temporalmente sobre la
  otra; si faltan ambas, recién entonces falta la dimensión completa.
