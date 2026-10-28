---
madr: 4
id: '0394'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [pobreza_nowcast, pobreza_indec]
archivos: ['scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'tests/test_pobreza_indec_fechado.py']
modifica: ['0114', '0153']
relacionado: ['0114', '0153', '0393']
ambito: 'ITCIS · dimensión Ingresos · `pobreza_nowcast` y la serie `pobreza_indec`'
origen: 'Verificación del 28-oct-2026: la serie oficial de pobreza estaba fechada seis meses tarde y la base del componente tomaba el semestre equivocado.'
---

# ADR-0394 — La pobreza del INDEC se fecha al inicio de su semestre

## Contexto y planteo del problema

La API de series de tiempo fecha cada semestre en el primer día del mes siguiente a su
cierre: el 54,0 % del primer semestre de 2003 viene como 2003-07-01, el 31,6 % del
primer semestre de 2025 como 2025-07-01 y el 41,7 % del segundo semestre de 2023 como
2024-01-01. `fetch_pobreza_indec_serie` copiaba esa fecha tal cual, así que todos los
puntos quedaban seis meses corridos. La base de `itvc_pobreza` tomaba `2023-07-01`
creyendo que era el segundo semestre de 2023 y era el primero (40,1 % en vez de 41,7 %).

## Decisión

Cada valor queda fechado al inicio de SU semestre: primer semestre → AAAA-01-01, segundo
→ AAAA-07-01. La base de `itvc_pobreza` es el segundo semestre de 2023 (`2023-07-01`),
41,7 %.

### Consecuencias

- El componente de pobreza pasa de unos 128,1 a unos 133,2 (la base sube 40,1 → 41,7).
- El gráfico de la tarjeta muestra la oficial en el semestre que mide.
- El contraste con el nowcast, que estaba hecho contra semestres equivocados, se
  recalcula con el semestre móvil que cierra en junio o diciembre: 1S-2025 0,0 puntos,
  2S-2025 +2,4 y 1S-2026 −0,7 (nowcast menos INDEC). El error máximo sobre la base es
  5,8 %. Los textos de [[0114]] y [[0153]] que citaban otros semestres no se reescriben;
  vale lo de acá y la ficha.
- Es dato y método: llega al diario con la próxima corrida y a la edición mensual con
  el rearmado.

### Confirmación

`tests/test_pobreza_indec_fechado.py`.

## Pros y contras de las opciones

- Corregir en el origen: todo consumidor de la serie queda bien sin parches.
- Corregir sólo la base: dejaba el gráfico de la tarjeta seis meses corrido.
