---
madr: 4
id: '0368'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'macro'
indice: 'ITCM'
indicadores: [actividad_tributaria]
archivos: ['scripts/itcm.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0329', '0367']
ambito: 'Cinturón macro · ITCM · dimensión actividad e inversión'
origen: 'Revisión de Luis Babino del 26-oct-2026 (punto 1.2) y decisión de Juan del mismo día.'
---

# ADR-0368 — La recaudación de IVA y cheque sale del índice

## Contexto y planteo del problema

`actividad_tributaria` entró en septiembre a pedido de Luis
([[0329-actividad-tributaria-proxy-de-actividad-no-control-fiscal]]), como señal
de la actividad que se publica antes que el EMAE. El propio ADR midió que repite
esa lectura (r = 0,84 con el EMAE) y no la anticipa. En su revisión del 26-oct
Luis pidió sacarla por redundante.

## Factores de decisión

- Una señal que no agrega información sólo duplica el peso de la actividad.
- Lo que no puntúa no se publica como tarjeta.

## Opciones consideradas

- **Sacarla del índice y de las tarjetas (elegida).**
- Mantenerla por llegar antes.

## Decisión

Sale del índice y pasa a los indicadores calculados pero ocultos. Su 8,4 % de la
dimensión vuelve a los otros tres de actividad en proporción: EMAE 42 %,
amplitud 14 %, industria 14 %, inversión física 30 % (el 60/20/20 original sobre
el 70 % de actividad).

### Consecuencias

- Con los datos del 26-oct-2026: actividad e inversión 42,8 → 41,4; índice
  macroeconómico 54,2 → 53,9.
- La parte del índice que depende del IPC baja de 31,3 % a 29,4 %.
- Por ser método, llega a la edición mensual y al archivo.

### Confirmación

`tests/test_itcm.py` y los tests de pesos de fichas corren con la composición
nueva.

## Pros y contras de las opciones

- Sacarla: la dimensión no cuenta dos veces la misma señal; pierde un dato que
  llega un mes antes.
- Mantenerla: sigue la duplicación que el propio ADR-0329 midió.

## Más información

Documento de Luis «Cinturón macroeconómico: revisión antes de publicar»
(26-oct-2026), punto 1.2.
