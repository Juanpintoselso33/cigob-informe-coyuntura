---
madr: 4
id: '0378'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [transferencias_no_automaticas, iaf_transferencias]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'scripts/itcp.py', 'scripts/procedencia_anclas.py', 'scripts/validacion_externa.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'tests/test_politica_transferencias_no_automaticas.py']
relacionado: ['0066', '0239', '0353', '0359', '0397']
modificado_por: ['0397']
ambito: 'Cinturón político · ITCP · dimensión Alianzas territoriales'
origen: 'Reunión del 26-oct-2026.'
---

# ADR-0378 — Las transferencias no automáticas reemplazan a las automáticas

## Contexto y planteo del problema

`iaf_transferencias` ([[0066-iaf-transferencias-solo-provincias]],
[[0239-el-deflactor-lo-pondera-el-flujo-no-el-calendario]],
[[0353-armonia-federal-a-doce-meses-moviles]]) mide la variación real de lo que la
Nación gira a las provincias por el reparto automático: coparticipación y fondos de
ley del RON. Eso es lo que a cada provincia le corresponde, no una decisión del
Gobierno, y por lo tanto no dice nada sobre la relación política con los
gobernadores. La reunión del 26-oct-2026 decidió medir sólo lo no automático.

## Factores de decisión

- Un indicador tiene que medir lo que su dimensión promete: alianzas territoriales
  es lo que la Nación pone en juego con las provincias, no lo que debe girarles.
- Fuente oficial, mensual y reproducible.
- Mismo peso (0,40) y misma cuenta (12 meses contra 12, deflactada mes a mes).

## Opciones consideradas

- **Presupuesto Abierto, devengado de transferencias a provincias y municipios
  (elegida).** `POST /api/v1/credito`, `inciso_id = 5`, partidas principales 7
  (corrientes) y 8 (de capital), por mes de impacto. Mensual desde 2022 (el
  ejercicio 2026 llega al mes cerrado); la API se actualizó el 26-oct-2026 con
  septiembre cerrado y octubre parcial. Rezago real: un mes, y lo fija el IPC.
- Sumar los adelantos financieros del Tesoro: **descartada por falta de fuente.**
  Se dictan por decreto individual (p. ej. Decretos 219/2026 y 474/2026) y no
  existen en Presupuesto Abierto ni en una serie mensual consolidada; el inciso 6
  no trae préstamos a provincias.
- Restar el RON automático del gasto total: descartada, la coparticipación no pasa
  por el presupuesto como gasto (se detrae de la recaudación), no hay nada que restar.

## Decisión

Nace `transferencias_no_automaticas` y reemplaza a `iaf_transferencias` en
`alianzas_territoriales` con el mismo 0,40. Es la variación real de los últimos 12
meses cerrados contra los 12 previos, cada flujo a precios de su propio mes. Entra
el devengado de las partidas 7 y 8 del inciso 5 (Aportes del Tesoro Nacional,
transferencias corrientes y de capital por programa). Salen cuatro partidas que
son automáticas por ley o fallo, o financian entes nacionales:

1. coparticipación de la Ciudad de Buenos Aires por la Ley 27.606 y la cautelar
   CSJN 1864/2022 (jurisdicción 91, programa 67), el rubro más grande: 1,0 billones
   en 2025;
2. el Fondo Nacional de Incentivo Docente;
3. las transferencias a cajas previsionales provinciales;
4. el funcionamiento de hospitales nacionales (Garrahan, El Cruce, SAMIC).

Los ATN se identifican por la descripción de la actividad, no por la jurisdicción:
estuvieron en Interior (30) y en 2025 en Jefatura de Gabinete (25).

`iaf_transferencias` pasa a suspendido (se sigue calculando, no puntúa, no es
tarjeta), con las bandas conservadas. Condición para volver: que la dimensión
necesite además una lectura del flujo automático.

Bandas: más giro discrecional se lee como más recurso de negociación puesto en
juego, mismo sentido que `iaf_transferencias`. Cortes −50 / −20 / +5 / +30 puntos
porcentuales. **Es una convención**, fijada mirando el rango observado: las 22
ventanas de la gestión (dic-2024 a sep-2026) van de −85 % a +38 %, porque el giro
discrecional se concentra en pocos meses (diciembre de 2025 llevó la ventana de
−34 % a +32 %). Con los ±10 pp del flujo automático la serie quedaría casi siempre
saturada. Se declara en `procedencia_anclas.py`; el techo de circularidad del ITCP
se evalúa abajo.

### Consecuencias

- Valor a sep-2026: **+6,0 % real** (1,25 billones de pesos en los 12 meses contra
  0,91 los 12 previos, +37,6 % nominal con un deflactor de 29,9 %). La composición de
  los 12 meses: ATN 0,27 · transferencias corrientes 0,81 · de capital 0,16 billones.
- Con los valores del snapshot del 27-oct-2026: el indicador viejo daba −0,6 % y
  73,8 puntos; el nuevo da +6,0 % y 75,8. Alianzas territoriales 77,7 → 78,5 e
  índice político 71,6 → 71,8.
- Montos anuales no automáticos en millones de pesos corrientes: 2022, 574.234;
  2023, 1.389.553; 2024, 635.153; 2025, 1.147.220. Los años electorales (2023) y el
  ajuste de 2024 mueven la serie mucho más que el RON.
- Serie desde dic-2023 (34 puntos); la reconstrucción histórica del ITCP la usa desde
  dic-2024, la primera ventana toda de esta gestión, como hacía con la anterior.
- Es devengado, no caja, y no dice a qué provincia fue cada giro. La lista de
  partidas excluidas es un criterio de CIGOB, y un programa nuevo con otro nombre
  entra hasta que se lo agregue.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_politica_transferencias_no_automaticas.py` (sin red, con filas de la
API como fixture) fija las exclusiones, la deflación mes a mes, la ventana, el mes
en curso fuera y el peso en la dimensión.

## Pros y contras de las opciones

- Presupuesto Abierto: oficial, mensual y con el mismo método que la medida anterior;
  no cubre los adelantos del Tesoro y es devengado.
- Adelantos financieros: serían el instrumento más político, pero no hay serie.
- Restar al RON: imposible, no está en el presupuesto como gasto.
