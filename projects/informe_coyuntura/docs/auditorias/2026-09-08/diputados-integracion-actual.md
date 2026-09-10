# Diputados y eventos: integración vigente

La captura desde el máximo 5995 observado en el listado oficial terminó
sin fallos. Se verificaron 29 PDFs nuevos, corrigiendo las columnas antes
de integrarlos. El componente Diputados tiene ahora 42 actas con señal,
última 27-ago; Senado conserva sus 16 actas verificadas. Rice bicameral
100%, 58 actas y ambas cámaras actualizadas. No cambió el valor de Rice.

Se ejecutaron los colectores de eventos en una copia temporal: InfoLeg,
Senado y clasificación de las actas de Diputados hasta 5995, sin pendientes.
Sólo después del éxito se integraron el registro y las tarjetas. En la
ventana de doce meses calendario octubre-2025 a septiembre-2026 parcial
no hay normas con primer desafío dentro de ella. Desafíos vale 0; bloqueo
queda sin universo, no en 0% ni en el 33,3% conservado de otra ventana.
El motor redistribuye el peso entre los componentes observados.

Las dos derrotas con desenlace dentro de la ventana corresponden a vetos
cuyo primer desafío fue anterior. El conteo de desenlaces y el de primeros
desafíos tienen distinta fecha de referencia; no confundir los universos.
La métrica de desafíos no cuenta cada sesión, protesta o confrontación.

ITCP actual: 71,9 → 73,0; tensión 2,8 → 2,7. Este cambio es una revisión
por actualización de fuente, no un movimiento político ocurrido el día
de la auditoría. Julio histórico sigue 67,9 y agosto 68,2; las series ya
reflejaban el vencimiento de esa cohorte de eventos. Se mantienen 63
indicadores publicados, de los cuales 62 tienen observación para puntuar.

Se corrigió además una diferencia de sensibilidad: `_agregar` omitía el
redondeo por dimensión utilizado por el motor. La base recomputada del
ITCP daba 73,1 frente al publicado 73,0; ahora ambas son 73,0. Se agregó
una regresión contra el motor con componentes faltantes.

[Antes/después y resultados de eventos](integracion-diputados-actual.json).
[Verificación de columnas y totales](diputados-parser-columnas.md).
La captura usó el máximo observado; no modificó el descubridor productivo
ni su tolerancia a huecos. El mayor alcance de una revisión histórica
exhaustiva de cada PDF no se presupone por este cotejo vigente.
