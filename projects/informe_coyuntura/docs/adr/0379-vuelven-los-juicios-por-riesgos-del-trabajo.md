---
madr: 4
id: '0379'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [litigiosidad_laboral, juicios_trabajo_capital]
archivos: ['scripts/itcg.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
supersede: ['0369']
relacionado: ['0023', '0359', '0365', '0385']
ambito: 'Cinturón de gestión · ITCG · dimensión Reforma laboral'
origen: 'Reunión de Juan con Luis Babino y Marcos del 26-oct-2026 (resumen de acuerdos enviado por Luis) y decisión de Juan del 27-oct.'
---

# ADR-0379 — Vuelven los juicios por riesgos del trabajo

## Contexto y planteo del problema

[[0369-los-juicios-por-riesgos-del-trabajo-salen-de-la-reforma-laboral]] sacó de
Reforma laboral los juicios del sistema de riesgos del trabajo (SRT), a pedido de
la revisión de gestión de Luis: son juicios por accidentes y enfermedades, y la
reforma apunta a los despidos. Esa misma tarde, la reunión con la dirección de
CiGob acordó medir el resultado de la reforma con las dos series de juicios —la
de la Justicia Nacional del Trabajo y la de la SRT—, como también pedía el
documento de Marcos sobre la dimensión.

## Factores de decisión

- Lo acordado en la reunión prevalece sobre la revisión previa.
- La serie de la SRT es la única nacional y mensual; la de la Justicia del Trabajo
  es sólo de la Capital y semestral.

## Opciones consideradas

- **Reponerlos con el 50/25/25 de ADR-0365 (elegida).**
- Mantenerlos afuera.

## Decisión

Reforma laboral vuelve a 50 % Fondo de Asistencia Laboral, 25 % juicios por
riesgos del trabajo y 25 % juicios de la Justicia Nacional del Trabajo.
`litigiosidad_laboral` deja de estar suspendido y vuelve a ser tarjeta. La ficha y
la descripción aclaran que cuenta accidentes y enfermedades, no despidos.

### Consecuencias

- Con los datos del 26-oct-2026: Reforma laboral 47,6 → 53,8 (seguimiento diario);
  en la edición de septiembre, 49,5 → cerca de 54. El índice de gestión sube
  alrededor de un punto.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_juicios_trabajo_capital.py` fija el 50/25/25.

## Pros y contras de las opciones

- Reponerlos: medida nacional y mensual; no mide despidos.
- Afuera: la dimensión mide sólo despidos y otros juicios de la Capital, cada seis meses.
