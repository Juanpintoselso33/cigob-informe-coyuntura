---
madr: 4
id: '0293'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [iai]
archivos: ['scripts/macro.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts']
ambito: 'Consistencia temporal del índice de inversión'
---

# ADR-0293 — IAI comparte la composición mensual

La tarjeta preveía incorporar patentamientos comerciales al acumular trece
meses, pero el historial mantenía ISAC y bienes de capital importados en 65/35.
Además, la tarjeta tomaba el último patentamiento disponible, aunque fuera de
otro mes. La discrepancia todavía no afectaba el snapshot: sólo hay tres
meses de patentamientos acumulados al realizar esta auditoría.

Se comparte una función de composición por mes entre tarjeta e historia.
La participación de patentamientos exige trece observaciones acumuladas
hasta el mes de referencia y valores en ese mes y doce meses antes.
Si no se cumple, se conserva ISAC/BK 65/35. Si se cumple, se aplica 55/30/15
y se identifica DNRPA en la tarjeta. No se usan meses futuros para activar
retrospectivamente el componente ni se mezclan fechas.

Tres regresiones verifican coincidencia tarjeta/historia con el tercer
componente, ausencia del mes común y ausencia de suficiente historia en el
pasado. El cambio no modifica los valores actualmente publicados.
