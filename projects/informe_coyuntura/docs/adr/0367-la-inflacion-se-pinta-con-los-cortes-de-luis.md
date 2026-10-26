---
madr: 4
id: '0367'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'macro'
indice: 'ITCM'
indicadores: [ipc_total, rem_ipc_12m]
archivos: ['scripts/itcm.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'tests/test_itcm.py']
relacionado: ['0120', '0366', '0368']
ambito: 'Cinturón macro · ITCM · dimensión estabilidad monetaria'
origen: 'Revisión de Luis Babino del 26-oct-2026 (punto 3.1) y decisión de Juan del mismo día.'
---

# ADR-0367 — La inflación se pinta con los cortes de Luis

## Contexto y planteo del problema

Con las anclas de ADR-0120 (1 % → 100 · 1,5 % → 85 · 2,5 % → 65 · 4 % → 40), el
verde de la inflación mensual llegaba hasta cerca de 2,8 % (≈ 39 % anual). En
octubre de 2026, 1,93 % mensual salía «sin tensión relevante», igual que las
expectativas de 21,1 % anual. El propio código dice que 1 % mensual es la zona de
éxito.

## Factores de decisión

- Que el color diga lo que diría un lector: 26 % anual no es inflación sin tensión.
- Conservar la escala normativa (no anclada a la historia) de ADR-0120.
- Misma vara para la inflación realizada y la esperada.

## Opciones consideradas

- **Cortes de Luis: verde hasta 1 % mensual, amarillo hasta 2 %, naranja hasta 3 %,
  rojo arriba, y el puntaje acompaña (elegida).**
- Dejar las anclas y aclarar que el verde es «dentro del sendero de desinflación».

## Decisión

Las anclas caen sobre los cortes de color del semáforo: 0,5 % mensual o menos →
100 · 1 % → 60 · 2 % → 40 · 3 % → 20 · 3,5 % o más → 10, con interpolación
lineal. Las bandas que las producen son ≤ 0,5 → 100 · 0,5–1,5 → 60 · 1,5–2,5 → 40
· 2,5–3,5 → 20 · > 3,5 → 10. Las expectativas usan la misma escala sobre su
equivalente mensual (raíz 12 de la tasa anual).

### Consecuencias

Con los datos del 26-oct-2026:

- Inflación del mes, 1,93 %: puntaje 76,4 → 41,4, de verde a amarillo.
- Inflación esperada, 21,1 % anual (1,61 % por mes): 82,8 → 47,8, de verde a
  amarillo.
- Estabilidad monetaria: 69,6 → 41,6.
- Índice macroeconómico: 61,5 → 54,2; el cinturón pasa de verde a amarillo.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_itcm.py` fija los cortes nuevos y el ejemplo del índice.

## Pros y contras de las opciones

- Cortes de Luis: el color se lee como lo leería cualquiera; el índice macro
  queda mucho más sensible a la inflación (estabilidad pesa 26 %).
- Dejar y aclarar: no mueve el índice, pero el verde sigue diciendo «sin tensión»
  con 26 % anual.

## Más información

Documento de Luis «Cinturón macroeconómico: revisión antes de publicar»
(26-oct-2026), en `docs/pedidos/texto/`.
