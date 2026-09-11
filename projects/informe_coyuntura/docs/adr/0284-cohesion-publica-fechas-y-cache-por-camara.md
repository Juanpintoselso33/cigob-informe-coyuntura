---
madr: 4
id: '0284'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [cohesion_bloque, alineamiento_senadores_prov]
archivos: ['scripts/publicar.py', 'web/src/lib/fichas.ts']
ambito: 'Presentación de actualización parcial y conservación de datos'
origen: 'Auditoría integral solicitada por Juan'
---

# ADR-0284 — Cohesión publica fechas y caché por cámara

## Contexto y planteo del problema

La fecha del compuesto es la última acta más reciente de cualquiera de las
cámaras. El desglose mostraba pesos y cantidades, pero no las fechas ni el
estado de caché por cámara. Podía parecer enteramente actualizado aunque una
parte proviniera de una consulta anterior.

## Decisión

Mostrar en el valor utilizado la fecha de última acta y condición de caché de
cada cámara. Si sólo una aporta, explicitar que su peso se renormaliza al 100%.
Conservar la fórmula, el valor y el criterio de actualización del compuesto.
Corregir las fichas de cohesión y alineamiento: la conservación del promedio
anterior ante fallos o receso no equivale a un recálculo con observaciones nuevas.

## Más información

El cotejo del 8 de septiembre conserva el componente de Diputados mientras
Senado responde. La salvedad no se elimina porque el valor coincida en 100%.
