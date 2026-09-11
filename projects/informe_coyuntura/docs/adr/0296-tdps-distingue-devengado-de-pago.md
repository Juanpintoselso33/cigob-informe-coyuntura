---
madr: 4
id: '0296'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'gestion'
indicadores: [asistencia_directa]
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts']
ambito: 'Interpretación de la composición presupuestaria social'
---

# ADR-0296 — TDPS distingue devengado de pago

El colector usa crédito devengado, pero tarjeta, fórmula y descripción hablaban
de pago efectivo sin intermediarios. Además, la descripción sostenía que buena
parte del programa 2023 estaba intermediada, mientras la propia base daba
98,3% en ayudas a personas. Las inferencias excedían los datos.

Se conserva la fórmula 5.1.4/inciso 5, los filtros por actividad y las bandas.
Se describe la TDPS como aproximación presupuestaria a la desintermediación,
con universo Volver al Trabajo y Acompañamiento Social. El resto del inciso
son otras partidas: su existencia no acredita intermediación en el cobro.
Devengado, pagado y cobro efectivo no se confunden. Las claves internas
`directo_musd` e `intermediado_musd` se conservan por compatibilidad; son
millones de pesos y designan 5.1.4 y el resto del inciso, respectivamente.

La API original confirma 434.589,03731808 y 123.471,11114301 millones en 5.1.4
para ambas actividades en 2026. La suma 558.060,14846109 produce 100% del
devengado de transferencias seleccionado. La consulta independiente de
Potenciar Trabajo 2023 confirma 98,312165%, compatible con 98,3% publicado.

Evidencia: `../auditorias/2026-09-08/cotejo-tdps-original.json`.
La documentación de Presupuesto Abierto distingue devengado y pagado:
https://www.presupuestoabierto.gob.ar/api/
