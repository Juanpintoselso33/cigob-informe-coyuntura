---
madr: 4
id: '0398'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'politica'
indice: 'ITCP'
indicadores: [produccion_legislativa]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'tests/test_produccion_calendario.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts']
modifica: ['0168']
relacionado: ['0166', '0168', '0306', '0377', '0359']
ambito: 'ITCP · dimensión Poder legislativo · qué leyes cuenta la producción legislativa'
origen: 'Auditoría del cinturón político del 28-oct-2026; decisión de Juan del mismo día.'
---

# ADR-0398 — La producción legislativa no cuenta las leyes vetadas

## Contexto y planteo del problema

`produccion_legislativa` ([[0168-los-cuatro-indicadores-desbloqueados-entran-al-itcp]],
[[0306-produccion-legislativa-meses-completos]]) cuenta las leyes sancionadas en 12
meses, en la familia de tensión externa ([[0166-regla-de-orientacion-para-indicadores-de-control]]):
más leyes, más puntaje. Su pregunta declarada era «cuánto sanciona el Congreso por su
cuenta».

Con esa pregunta, una ley que el Ejecutivo vetó entera suma como producción. En la
ventana a agosto de 2025 había ocho de esas leyes sobre 40 (financiamiento
universitario dos veces, emergencia en Bahía Blanca, discapacidad, moratoria
previsional, aumento a las jubilaciones, reparto de los ATN y Garrahan):
el componente subía justo cuando el Congreso y el Gobierno estaban más enfrentados, y
esas mismas leyes ya restaban en los vetos insistidos ([[0377-vetos-insistidos-y-decretos-derogados-reemplazan-quorum-y-desafios]]).

## Factores de decisión

- Que la pregunta y el signo sean coherentes con la familia de tensión.
- No contar el mismo desacuerdo dos veces con signos opuestos.
- Usar el registro de vetos que ya alimenta el índice, no una lista aparte.

## Opciones consideradas

- **Excluir las leyes vetadas en su totalidad, con las mismas bandas (elegida).**
- Contar sólo las leyes de origen Ejecutivo, con percentiles de 2008-2023.
- Dejarlo como está.

## Decisión

No cuentan las leyes que el Ejecutivo **vetó en su totalidad**, según
`data/politica/derrotas_legislativas_eventos.json`, aunque el Congreso después haya
insistido con dos tercios: el Gobierno no las aceptó. Los vetos parciales sí cuentan,
porque la ley se promulgó. Sin registro de vetos el colector no publica.

La pregunta pasa a ser **«¿el Congreso sanciona leyes que el Gobierno acepta?»**. Más
leyes es menos tensión; el desacuerdo abierto lo miden los vetos insistidos y los
decretos derogados, en la misma dimensión. Las bandas (umbral de 74) no cambian.

### Consecuencias

- Con el dato de septiembre de 2026 no hay leyes vetadas en la ventana: el valor sigue
  en 31 y el componente en 45,8.
- La historia cambia entre agosto de 2024 y julio de 2026: la ventana a agosto de 2025
  pasa de 40 a 32 leyes y su puntaje de 60,8 a 47,5.
- Un veto que llega después de publicada la ventana saca la ley del conteo y la serie se
  revisa hacia atrás.
- La referencia de 74 leyes por año no descuenta los vetos totales de gobiernos
  anteriores. Va en la ficha.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_produccion_calendario.py` fija que los vetos totales salen (también los
insistidos), que los parciales quedan, que la card informa cuántas excluyó y que sin
registro no publica.

## Pros y contras de las opciones

- Excluir vetadas: corrige el signo sin tocar la escala; el cambio es chico porque los
  vetos totales son pocos.
- Sólo origen Ejecutivo: responde otra pregunta (la agenda propia) y es la que
  [[0137]] descartó porque el numerador apenas se mueve.
- Dejarlo: el componente premia el conflicto que otros dos componentes castigan.
