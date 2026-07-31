---
madr: 4
id: '0084'
estado: 'rechazado'
fecha: 2026-07-18
cinturon: 'macro'
indicadores: [reservas_bcra]
ambito: 'Cinturón macro · ITCM · `reservas_bcra`'
origen: 'Auditoría de consistencia del cinturón macro (17-jul-2026), observación 13 — marcada por la propia auditoría como no urgente'
---

# ADR-0084 — Reservas en meses de importaciones: **RECHAZADO**, con la condición para revisarlo

## Opciones consideradas

- **Dejar las reservas como están** — elegida.
- **Medirlas en meses de importaciones** — **rechazada**; el ADR deja registrada la condición bajo la cual correspondería revisar el rechazo.

## Decisión

### Por qué se rechaza

### 1. La métrica no está definida donde viven los datos

**Trece de los veintitrés meses de serie tienen reservas netas NEGATIVAS.**

| mes | reservas netas | impo. prom. 3m | "meses cubiertos" |
|---|---|---|---|
| 2025-11 | −1.802 | 6.646 | **−0,27** |
| 2026-01 | −2.626 | 5.404 | **−0,49** |
| 2026-03 | −1.719 | 5.446 | **−0,32** |
| 2026-05 | +4.122 | 6.117 | +0,67 |

"Cubrir −0,49 meses de importaciones" no significa nada. La métrica estándar
está pensada para reservas **brutas**, que son siempre positivas; aplicada a las
**netas** —que restan pasivos, y son las que este índice puntúa por decisión
previa: son "el número del mercado"— se rompe en más de la mitad de las
observaciones.

### 2. Donde sí está definida, no agrega información

Sobre los 23 meses, la correlación entre el nivel absoluto y la versión
normalizada por importaciones es **+0,998**.

Las importaciones del período se movieron en un rango estrecho (promedio móvil
de tres meses entre 5.200 y 6.900 millones), así que dividir por ellas es
prácticamente un **reescalado monótono**: no reordena los meses ni cambia qué
tramo de la banda ocupa cada uno. La normalización no aporta discriminación que
el nivel no tenga ya.

## Más información

### Lo que se proponía

Reemplazar las anclas de `reservas_bcra`, hoy en millones de dólares absolutos
(>20.000 → 100 · 15.000-20.000 → 85 · … · <0 → 10), por la métrica
internacional estándar de adecuación: **meses de importaciones cubiertos**, con
el umbral clásico de tres meses.

La preocupación de fondo es legítima: un umbral en dólares absolutos no se
ajusta al tamaño de la economía ni a sus necesidades de importación. Veinte mil
millones significan cosas distintas según cuánto importe el país por mes.

### Cuándo habría que revisarlo

El rechazo es sobre **el período disponible**, no sobre la idea. La objeción de
fondo —que un umbral absoluto envejece si cambia la escala del comercio
exterior— sigue siendo válida hacia adelante.

Corresponde reabrir esta decisión si se cumple alguna de estas dos condiciones:

1. **Las reservas netas dejan de ser negativas de forma sostenida**, con lo que
   la métrica pasa a estar definida en todo el rango relevante.
2. **Las importaciones se apartan de forma persistente del rango en que se
   calibraron las bandas** (5.200-6.900 millones mensuales). Ahí la
   normalización dejaría de ser un reescalado y empezaría a reordenar meses,
   que es cuando aportaría algo.

### Nota sobre un problema vecino, que este cambio no resolvía

El diagnóstico de bandas (ADR-0081) marca `reservas_bcra` como candidata a
revisión por otro motivo: **57% de los meses en el piso y el techo nunca
alcanzado en 23 meses**. Conviene no confundirlo con lo de acá — normalizar por
importaciones **no lo habría arreglado**, porque con r=0,998 los mismos meses
seguirían cayendo en el mismo extremo.

Esa saturación refleja desempeño real (las reservas netas fueron negativas la
mayor parte del período), así que bajo el criterio de ADR-0045 tampoco
corresponde recalibrar. Queda como está, declarado.
