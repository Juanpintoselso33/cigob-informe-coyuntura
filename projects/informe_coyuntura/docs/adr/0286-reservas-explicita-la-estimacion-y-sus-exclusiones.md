---
madr: 4
id: '0286'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [reservas_bcra]
archivos: ['scripts/publicar.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'web/src/lib/descripciones.ts', 'web/src/pages/[slug].astro']
continuado_por: ['0287']
ambito: 'Alcance de la estimación de reservas'
origen: 'Auditoría integral solicitada por Juan'
---

# ADR-0286 — Reservas explicita la estimación y sus exclusiones

## Contexto y planteo del problema

La planilla SDDS de julio de 2026 identifica II.1 por préstamos, valores y
depósitos y desglosa por vencimiento residual. Su tramo de más de tres meses
y hasta un año suma −2.536,78 M USD. No lo identifica como BOPREAL. La asociación
temporal propuesta en ADR-0005 no demuestra identidad ni representa los doce
meses completos. El BCRA identifica los BOPREAL como títulos que emite él mismo.

## Decisión

Corregir ficha, explicación, fórmula visible y detalle de los sumandos: el
resultado es una estimación según la fórmula CIGOB, con exclusiones del diseño.
No llamarlo medida oficial, consenso de mercado ni libre disponibilidad.
Conservar de momento el cálculo, las bandas y los pesos; el campo interno
`bopreal_12m` permanece por compatibilidad y no demuestra la identidad del tramo.

La nota metodológica de la página macro conservaba además versiones anteriores
de recaudación y dolarización y decía otros cuatro cinturones. Se remite a las
fichas actuales y se corrige a otros tres, evitando una segunda descripción
estática del catálogo.

## Más información

La auditoría de reservas sigue abierta: conciliar los vencimientos por instrumento
y revisar el respaldo que usa otra fórmula. No se consideran resueltos por cambiar
el lenguaje. La elección de qué obligaciones excluir y de cómo medir liquidez
debe quedar diferenciada de la corrección de etiquetas.

Fuente: https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/temp0726.pdf
