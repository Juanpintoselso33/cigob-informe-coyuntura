---
madr: 4
id: '0395'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [protocolo_antipiquetes]
archivos: ['scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'tests/test_serie_piquetes_anio_cerrado.py']
relacionado: ['0025', '0361', '0405']
ambito: 'ITCG · `protocolo_antipiquetes` · serie histórica'
origen: 'Verificación del 28-oct-2026: la serie aplicaba el total de un año desde enero de ese mismo año.'
---

# ADR-0395 — Los piquetes usan el último año cerrado

## Contexto y planteo del problema

La ficha dice «último año cerrado» y que el valor «se arrastra hasta el anclaje
siguiente», pero `fetch_protocolo_serie` aplicaba el total del año Y desde enero de Y,
cuando ese total recién existe al cerrar el año. La historia reconstruida usaba así un
dato que en esos meses nadie conocía. Siniestralidad y juicios, en cambio, fechan al
cierre del período.

## Decisión

Cada mes usa el último año CERRADO antes de él: el dato de 2024 (reducción 52,7 %) entra
en enero de 2025 y el de 2025 (74,2 %) en enero de 2026. La serie arranca en 2025-01:
antes no hay ningún año cerrado posterior a la base 2023, y el único valor posible sería
0 %, la base contra sí misma, que puntuaría «sin mejora» en una historia que nadie midió.

### Consecuencias

- La tarjeta de hoy no cambia (74,2 %, año 2025): sólo cambia la historia.
- Desaparecen los 12 meses de 2024 y se corre un año el escalón de 2025 (antes 52,7
  desde 2024-01, 74,2 desde 2025-01).

### Confirmación

`tests/test_serie_piquetes_anio_cerrado.py`.

## Pros y contras de las opciones

- Año cerrado, serie desde 2025: consistente con la ficha y con siniestralidad.
- Serie desde 2024 con 0 %: conserva la longitud pero inventa un punto.
