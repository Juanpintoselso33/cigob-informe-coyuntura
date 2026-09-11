# Verificación integrada tras las correcciones

Primera corrida completa: 3.689 aprobadas, cinco fallos y cuatro omisiones. Los fallos expusieron un encabezado ADR fuera del formato, una expresión de la portada que chocaba con la nomenclatura y falta de distinción entre pesos nominales, indicadores publicados y componentes que puntúan.

Se corrigió el ADR-0129, incluida una frase antigua sobre vaciar avisos que contradecía el detector corregido. Se precisó la frase de la portada. Las fichas legislativas rotulan pesos nominales y explican la redistribución ante falta de universo; sus tablas mantienen pesos efectivos. El generador declara por separado publicados y puntuantes. Los tests comprueban que bloqueo sin universo carezca de valor y quede excluido, sin exigirle la composición nominal completa.

Segunda corrida integral: **3.694 aprobadas, cuatro omitidas, cinco avisos de deprecación, 47,53 s**. Las cuatro omisiones comparan una tarjeta de septiembre con reconstrucciones que llegan a julio/agosto; no son pruebas aprobadas. No hubo errores de red en esta corrida. Build 81 páginas correcto. Después se añadió una guarda específica de pesos nominales, comprobada con el archivo de pruebas correspondiente; no se repitió toda la suite por ese test adicional.

Logs: /tmp/cigob-suite-integrada-final.log, /tmp/cigob-suite-integrada-corregida.log, /tmp/cigob-build-composicion.log. Todos los procesos terminaron. No se ejecutaron productores de datos mientras corrían los tests. Las limitaciones de fuentes judiciales y de privatizaciones siguen pendientes: una suite verde no las resuelve.
