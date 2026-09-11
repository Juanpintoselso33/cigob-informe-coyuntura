---
madr: 4
id: '0280'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'gestion'
indicadores: [cepo_mulc]
archivos: ['scripts/gestion.py', 'web/src/lib/fichas.ts', 'tests/test_cepo_fecha_cotizacion.py']
ambito: 'Trazabilidad temporal de la brecha cambiaria'
origen: 'Auditoría integral solicitada por Juan'
---

# ADR-0280 — La brecha conserva la fecha de cotización

## Contexto y planteo del problema

El colector descartaba `fechaActualizacion` de DolarAPI y etiquetaba el dato
con el día de consulta. Una respuesta vieja podía parecer fresca. Además,
la ficha calificaba como inmaterial la diferencia entre spot y promedio
mensual, sin evidencia para generalizarlo.

## Decisión

Conservar precios y marcas de tiempo de CCL y mayorista, convertidas a hora
argentina. El corte es el día de la pata más antigua. Las fechas inválidas o
sin zona horaria y los precios no positivos o no finitos hacen fallar el
colector para que el mecanismo general conserve el cache con su fecha previa.
La fórmula, las bandas y los pesos no cambian.

La ficha distingue cotizaciones intradiarias y promedio mensual sin prometer
una diferencia pequeña. Una brecha baja no prueba desregulación legal.

## Más información

### Consecuencias y validación

Se hace visible el desfase entre ambas cotizaciones y se evita rejuvenecer
observaciones. Los tests cubren cambio de día UTC/Argentina, pata más antigua,
fechas inválidas y precios inválidos. La actualización real se registra con
los valores y las horas devueltos por la fuente.

Fuente: [API pública DolarAPI](https://dolarapi.com/v1/dolares).
