---
madr: 4
id: '0297'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [cobertura_judicial]
archivos: ['scripts/politica.py', 'web/src/lib/fichas.ts']
ambito: 'Universo de movimientos judiciales'
---

# ADR-0297 — Cobertura excluye Corte Suprema y renovaciones

El padrón de jueces federales y nacionales inferiores se reconstruía con
registros que también incluían designaciones y renuncias de la Corte Suprema.
Además, las renovaciones por cinco años entraban como vacantes cubiertas.
Ambos tratamientos alteran el numerador sin un cambio equivalente en el stock.

Se excluyen movimientos identificados como Corte Suprema y las renovaciones
corroboradas: 876/2024, 875/2024, 736/2025, 367/2026, 615/2026, 645/2026 y
853/2026. El filtro se comparte en tarjeta e historia mediante
`_jus_es_movimiento_del_universo` y `cobertura_judicial_serie`.
No se infiere automáticamente que cualquier nuevo nombramiento sea un alta.

Fuentes de las renovaciones históricas:
- https://www.boletinoficial.gob.ar/detalleAviso/primera/315056/20241003
- https://www.boletinoficial.gob.ar/detalleAviso/primera/315055/1
- https://www.boletinoficial.gob.ar/detalleAviso/primera/332799/20251014

Las cuatro de 2026 están documentadas en los cotejos originales de esta
auditoría. La fecha del CSV de Tyden tampoco coincide con la vigencia del
artículo 1: usa la fecha del decreto, mientras la renovación empieza el
4 de noviembre. Su exclusión evita trasladar ese error al stock.

La conciliación de normas posteriores, promociones y bajas se integra en
ADR-0298. Conserva límites explícitos de juras, habilitaciones y exhaustividad
de bajas; no se presenta como certificación integral del stock.
