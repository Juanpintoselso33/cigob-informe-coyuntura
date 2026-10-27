---
madr: 4
id: '0390'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [conflictividad_nacional]
parametros: ['BANDAS_ITCP["conflictividad_nacional"]']
archivos: ['scripts/itcp.py', 'scripts/procedencia_anclas.py', 'tests/test_itcp.py', 'web/src/lib/fichas.ts']
modifica: ['0052']
relacionado: ['0052', '0388', '0359']
ambito: 'ITCP · dimensión de conflicto social · escala de la conflictividad nacional (ACLED)'
origen: 'Revisión del cinturón político de Luis Babino (26-oct-2026), punto 5: las anclas de conflictividad parecen calibradas sobre el propio mandato. Diagnóstico del 27-oct y decisión de Juan del mismo día: cambiarlas.'
---

# ADR-0390 — Conflictividad con cortes de la historia previa

## Contexto y planteo del problema

`conflictividad_nacional` ([[0052-conflictividad-nacional-acled]]) mide la variación de
los eventos de protesta y disturbios de ACLED en todo el país, en doce meses, contra el
total de 2023. Sus cortes eran **−32 · −29 · −26 · −15 %**, puestos en los huecos de los
30 puntos del propio mandato (dic-2023 a may-2026), y `procedencia_anclas` los
clasificaba como `convencion`.

La escala ordenaba al gobierno contra sí mismo y, mirada contra la historia, jugaba en su
contra. El mandato tiene muchos menos eventos por mes que 2020-2023 (145-157 contra
217-250), pero con esos cortes **las 36 ventanas de 12 meses de 2020-12 a 2023-11 habrían
puntuado 10**. Con −27,2 % en septiembre de 2026, el componente daba 63,9.

## Factores de decisión

- Que la escala no salga del período que se evalúa (la misma regla que
  [[0388-jornadas-no-trabajadas-con-escala-que-se-mueve]]).
- ACLED es confiable para la Argentina sólo desde 2020: la historia previa es corta.
- Que el indicador siga moviéndose dentro del mandato.

## Opciones consideradas

- **Uno y dos desvíos de la variación previa: −30 · −15 · +15 · +30 % (elegida).**
- Percentiles 5/25/50/75 de las ventanas de 2020-2023 (−1,2 · 1,7 · 9,6 · 17,4 %).
- Dejar los cortes y declarar la circularidad en la ficha.

## Decisión

Los cortes pasan a **−30 · −15 · +15 · +30 %**. La variación interanual de las ventanas de
12 meses de 2020-2023 (24 casos, 2021-12 a 2023-11) tiene un desvío de **14,7 puntos**:
±15 es un desvío y ±30 son dos. La banda del medio es «un año normal» según esa historia.
El origen pasa a `historia_larga`.

### Consecuencias

- Con el snapshot del 27-oct-2026, el componente pasa de **63,9 a 94,4**, el conflicto
  social de 73,1 a 91,4 y el índice político de 73,1 a 75,0 (con ADR-0388 aplicado).
- En el mandato el componente va de 62 a 100, con 10 meses en 100. La suba de
  abril-mayo de 2026 se lee como una baja de 100 a ~85, no como una caída a 43.
- La historia previa son cuatro años con la pandemia adentro. Además, una caída de
  eventos registrados puede ser de cobertura de prensa: la de 2024 coincide con el
  balance oficial de bloqueos, 2025-2026 no se contrastó. Las dos cosas van en la ficha.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_itcp.py::test_banda_conflictividad_nacional` fija los cortes y los puntajes
en el mínimo del mandato, el dato vigente, el nivel de 2023 y los extremos.

## Pros y contras de las opciones

- Desvíos previos: externa al mandato y sin saturar; descansa en cuatro años de historia.
- Percentiles previos: misma regla que las jornadas, pero satura: 31 de 34 meses del
  mandato darían 100, porque todo el mandato está debajo de toda la historia previa.
- Declararlo: no cambia números, pero deja la escala circular.
