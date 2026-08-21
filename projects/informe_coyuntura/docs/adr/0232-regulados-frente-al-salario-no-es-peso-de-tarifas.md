---
madr: 4
id: '0232'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'vida'
indicadores: [peso_tarifas]
archivos: ['scripts/vida_cotidiana/collectors/iiep_tarifas.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
modifica: ['0012', '0018']
relacionado: ['0033', '0109', '0182']
ambito: 'Canasta efectiva de servicios sobre ingreso · anclas internacionales de asequibilidad · reemplazo de IPC Regulados/RIPTE'
origen: 'Revisión editorial del rojo 10/10: el indicador afirmaba medir tarifas pero puntuaba un agregado de precios contra una base subsidiada'
---

# ADR-0232 — La canasta de servicios puntúa contra asequibilidad, no contra 2023

## Contexto y planteo del problema

La card **«Peso de tarifas (regulados)»** mostraba 2,13% mensual de julio de
2026 y aparecía roja (10/10) por otro número: 72,4 base 100 en junio, cociente
entre IPC Regulados y RIPTE contra el 4T-2023.

Ese cálculo no sostenía lo que afirmaban el nombre, la fórmula y el color:

- IPC Regulados incluye rubros ajenos a las facturas de servicios públicos,
  entre ellos salud, educación, telefonía, combustibles y cigarrillos;
- dividir dos índices no calcula qué proporción del ingreso paga un hogar;
- el 4T-2023 estaba afectado por congelamientos y subsidios. Alejarse de ese
  precio prueba un ajuste, pero no que la carga haya cruzado un límite de
  asequibilidad.

La corrección no puede consistir en dejar la card como contexto. ADR-0153 y
ADR-0216 fijan la regla editorial: **o integra el índice, o no es card**.

## Factores de decisión

### Variable argentina

La fuente pasa al **Observatorio de Tarifas y Subsidios del IIEP
(UBA-CONICET)**. Su Canasta de Servicios Públicos del AMBA suma electricidad,
gas natural, agua potable y transporte público para un hogar representativo y
la publica como porcentaje de un salario RIPTE. En agosto de 2026 la canasta
es $289.622 y equivale a 14,5% del salario estimado.

Fuente argentina:
[Reporte de Tarifas y Subsidios, agosto de 2026](https://economicas.uba.ar/iiep/reporte-de-tarifas-y-subsidios-agosto-2026/).

### Referencia internacional comparable

No se usa el promedio de costos de vivienda de la OCDE: incluye alquiler,
hipoteca, mantenimiento, impuestos y servicios, y por eso no tiene el mismo
numerador.

Se usan referencias por los mismos componentes, expresadas como porcentaje
del ingreso:

- el Banco Mundial ubica una canasta de **agua y energía** dentro de un rango
  indicativo de asequibilidad de **10–15%** del presupuesto familiar; el mismo
  documento contrasta ese rango con hogares de Buenos Aires y Uruguay;
- ONU-Hábitat recomienda que el **transporte público** no supere **5%** del
  ingreso neto del hogar.

Fuentes: [Banco Mundial, *Uruguay — Public Services Modernization Technical
Assistance Project*, pp. 84–86](https://documents1.worldbank.org/curated/en/760271468781746830/pdf/multi0page.pdf)
y [ONU-Hábitat, metadatos del indicador ODS 11.2.1,
p. 12](https://unhabitat.org/sites/default/files/2022/08/sdg_indicator_metadata-11.2.1.pdf).

No se suman los límites. Hacerlo permitiría que transporte por encima de 5%
quedara compensado por energía por debajo de 10%, o al revés. El IIEP publica
qué proporción de su canasta es transporte, de modo que ambos grupos pueden
compararse por separado. No es un promedio de precios extranjeros trasladado
a pesos: son dos varas de asequibilidad en la misma unidad que el dato argentino.

## Decisión

`peso_tarifas` conserva su lugar en presión de precios: 45% interno, equivalente
a 11,25% del ITCIS. La card muestra la carga observada y la serie
`itvc_tarifas` la lleva a la escala común del índice:

```text
T_agua_energía = clip[0,10](2 × (porcentaje_agua_energía − 10))
T_transporte   = clip[0,10](2 × (porcentaje_transporte − 5))
T              = máximo(T_agua_energía, T_transporte)
índice         = 125 − 5 × T
```

Así, agua+energía marca tensión 0/5/10 en 10/12,5/15% del ingreso y transporte
en 5/7,5/10%. La winsorización general del ITCIS sigue acotando el índice por
arriba en 140.

En agosto de 2026, transporte representa 43% de la canasta: 6,2% del salario.
Agua+energía representa el 57% restante: 8,3%. El primer grupo supera
moderadamente su referencia de 5% y el segundo queda debajo de 10%; la mayor
señal produce índice 112,6 y tensión equivalente 2,5/10, verde. El ajuste no se
pinta como crisis, pero el transporte tampoco queda escondido en el total.

## Más información

### Consecuencias verificables

- Desaparecen del indicador el IPC Regulados y la base 4T-2023.
- Titular, gráfico y score usan la misma variable del IIEP; el histórico viejo
  de variaciones mensuales de Regulados no se conserva bajo el nombre nuevo.
- La historia se reconstruye desde cifras textuales de los informes PDF desde
  diciembre de 2025. Los puntos anteriores no se infieren de un gráfico.
- El colector guarda también la variación mensual de la canasta y la cobertura
  de costos, pero ninguna de las dos sustituye la carga sobre el ingreso.
- El perímetro sigue siendo explícito: hogar representativo del AMBA, sin
  subsidios en electricidad y gas, contra un salario registrado promedio.

### Guardas

- `test_no_hay_cards_de_contexto` impide sacar el indicador del score y dejarlo
  visible.
- `test_vida_itvc_reconcilia` exige valor 14,5, índice 112,6, peso efectivo
  11,25% y tensión 2,5.
- `test_tarifas_usa_canasta_real_y_ancla_internacional` impide que vuelvan el
  nombre o la interpretación de IPC Regulados.
- Los tests del colector fijan el parseo de período, carga, participación del
  transporte, variación y cobertura del reporte del IIEP.
