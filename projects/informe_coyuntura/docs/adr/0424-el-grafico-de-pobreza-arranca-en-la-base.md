---
madr: 4
id: '0424'
estado: 'aceptado'
fecha: 2026-11-04
cinturon: 'vida'
indice: 'ITVC'
indicadores: [pobreza_nowcast]
archivos: ['web/src/lib/datos.ts', 'web/src/lib/fichas.ts']
relacionado: ['0114', '0153', '0394']
ambito: 'Impacto social · gráfico de `pobreza_nowcast` (con `pobreza_indec`)'
origen: 'Revisión de Luis del 3-nov-2026 («no está en base a fines de 2023; revisar cómo se empalman las series del INDEC y de la Di Tella»). Juan, 4-nov: es el gráfico de pobreza.'
---

# ADR-0424 — El gráfico de pobreza arranca en la base

## Contexto y planteo del problema

El gráfico de la pobreza superpone la estimación mensual de la Di Tella y la tasa
semestral del INDEC. Para no perder la lectura de la base, [[0114]] dejó la serie del
INDEC completa, desde 2003: era el único gráfico del Monitor que no arrancaba en la base
de fines de 2023. Luis pidió además revisar el empalme de las dos series.

## Factores de decisión

- Todos los gráficos arrancan en la base del mandato.
- La lectura del 2º semestre de 2023 (fechada 2023-07-01, [[0394]]) es la base de la
  pobreza ([[0153]]) y tiene que verse.

## Opciones consideradas

- **La serie del INDEC arranca en el 2º semestre de 2023 (elegida).**
- Recortarla a diciembre de 2023 como el resto: pierde el punto de la base.

## Decisión

En el gráfico, `pobreza_indec` arranca en 2023-07-01. El empalme queda sin ajuste: en
los tres semestres que se solapan, el nowcast (semestre móvil a junio o diciembre) da
31,6 contra 31,6 del INDEC (1S-2025), 30,6 contra 28,2 (2S-2025) y 31,6 contra 32,3
(1S-2026). La diferencia no tiene signo constante, así que no hay un sesgo que corregir;
ya estaba declarada en la ficha y en `fetch_itvc_pobreza`.

### Consecuencias

- No cambia ningún valor ni puntaje.
- Los cortes fijos de la pobreza (pendiente 11) van aparte.

### Confirmación

Build del sitio; el modal de la pobreza muestra el primer punto oficial en el 2º semestre
de 2023.

## Pros y contras de las opciones

- Elegida: el gráfico se lee como el resto y conserva la base.
- Recorte general: más simple, pero el gráfico pierde su referencia.

## Más información

Pendiente 10 de `docs/pendientes-monitor.md`.
