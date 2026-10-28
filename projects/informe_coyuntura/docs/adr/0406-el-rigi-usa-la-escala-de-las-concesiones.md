---
madr: 4
id: '0406'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [rigi_inversiones]
archivos: ['scripts/itcg.py', 'scripts/procedencia_anclas.py', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'tests/test_itcg.py', 'tests/test_gestion_adr0405_0407.py']
relacionado: ['0011', '0105', '0121', '0361', '0366', '0405', '0407']
ambito: 'ITCG · dimensión Privatizaciones e inversión · escala de `rigi_inversiones`'
origen: 'Revisión del 28-oct-2026, a pedido de Juan, de las escalas del cinturón de gestión calibradas sobre el propio mandato.'
---

# ADR-0406 — El RIGI usa la escala de las concesiones

## Contexto y planteo del problema

`rigi_inversiones` mide la inversión aprobada sobre la cartera del régimen
(aprobada + en evaluación, [[0011]]). Su escala (10 → 10 · 17,5 → 40 · 32,5 → 65 ·
50 → 85 · 60 → 100) se había fijado mirando el 22,1 % de junio de 2026, y
`procedencia_anclas.py` la declaraba así: una convención calibrada sobre el dato.

Las otras dos patas de la dimensión, concesiones y privatizaciones, son también
medidores de avance 0-100 y usan una escala común (cortes 15/35/55/75).

Además, casi todo lo que se presenta al régimen termina aprobado: el porcentaje no
separa proyectos buenos de rechazados, mide sobre todo cuánto tarda la aprobación.

## Factores de decisión

- Una escala que no se haya puesto mirando el dato.
- Medidores de avance de la misma dimensión con la misma vara.
- Que la ficha diga qué mide de verdad el porcentaje.

## Opciones consideradas

- **Escala de concesiones y privatizaciones, declarada como convención (elegida).**
- Lineal 0 → 10 · 100 → 100.
- Mantener la escala de junio.

## Decisión

`rigi_inversiones` toma exactamente las bandas de `concesiones_infraestructura`
(anclas 15 → 10 · 25 → 40 · 45 → 65 · 65 → 85 · 75 → 100). En `procedencia_anclas.py`
sigue como `convencion`, ahora con la glosa de que no se calibró sobre el dato. La
ficha y la descripción agregan que, como casi todo lo presentado termina aprobado, el
porcentaje mide sobre todo la demora en aprobar.

### Consecuencias

- Con el 36,4 % de octubre de 2026 el puntaje pasa de 69,5 a 54,2; sola, la escala baja
  el ITCG de 80,6 a 79,7.
- El ejemplo de `tests/test_itcg.py` (22,1 %) pasa de 47,7 a 31,3, la dimensión de 58,1
  a 51,6 y el ITCG del ejemplo de 75,4 a 74,4.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_itcg.py` exige que las bandas del RIGI sean las de concesiones;
`tests/test_gestion_adr0405_0407.py` lo cruza con la procedencia declarada.

## Pros y contras de las opciones

- Escala común: misma vara que la dimensión y sin calibrar contra el dato; sigue siendo
  convención.
- Lineal: más simple, pero distinta de sus vecinas sin una razón.
- Escala de junio: la que la auditoría marca como circular.

## Más información

[[0405]] y [[0407]] son las otras dos decisiones de la misma revisión.
