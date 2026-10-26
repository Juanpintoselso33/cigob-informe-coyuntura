---
madr: 4
id: '0369'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [litigiosidad_laboral, juicios_trabajo_capital]
archivos: ['scripts/itcg.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0023', '0128', '0365']
ambito: 'Cinturón de gestión · ITCG · dimensión Reforma laboral'
origen: 'Revisión de gestión de Luis Babino del 26-oct-2026 (punto 1.1), reenviada por Marcos, y decisión de Juan del mismo día.'
---

# ADR-0369 — Los juicios por riesgos del trabajo salen de la reforma laboral

## Contexto y planteo del problema

Desde [[0023-litigiosidad-al-itcg]] la mitad del resultado de la reforma laboral
la medían los juicios del sistema de riesgos del trabajo (SRT). Son juicios por
accidentes y enfermedades laborales; la reforma apunta a las indemnizaciones por
despido. Su propia descripción admitía que no miden el resultado de la reforma.
[[0365-los-juicios-de-la-justicia-del-trabajo-entran-a-la-reforma-laboral]] sumó
los juicios de la Justicia Nacional del Trabajo, que sí incluyen despidos.

## Factores de decisión

- Un indicador tiene que medir lo que su nombre y su dimensión prometen.
- Mantener la regla de [[0128-fuerzas-en-la-dotacion-y-peso-del-fal]]: mitad
  instrumento, mitad resultado.

## Opciones consideradas

- **Sacar los juicios por riesgos del trabajo (elegida).**
- Mantener el reparto 50/25/25.

## Decisión

`litigiosidad_laboral` pasa a suspendido: se sigue relevando, no puntúa y no se
publica como tarjeta. Reforma laboral queda 50 % Fondo de Asistencia Laboral y
50 % juicios de la Justicia Nacional del Trabajo.

Condición para volver: que la reforma alcance al sistema de riesgos del trabajo,
o una serie nacional de juicios por despido que la complemente.

### Consecuencias

- El resultado de la reforma laboral queda medido sólo en la Capital y por
  semestre, como declara la ficha de los juicios de la Justicia del Trabajo.
- Con los datos del 26-oct-2026 (seguimiento diario): Reforma laboral 53,8 → 47,6
  e índice de gestión 75,1 → 74,1. Los juicios por riesgos del trabajo puntuaban
  bien (+0,1 %) y los de la Capital, mal (+12,4 %).

### Confirmación

`tests/test_juicios_trabajo_capital.py` fija el 50/50.

## Pros y contras de las opciones

- Sacarlos: la dimensión mide lo que dice; pierde la única medida nacional y
  mensual de juicios.
- Mantener: conserva esa medida, que no mide la reforma.
