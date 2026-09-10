---
madr: 4
id: '0290'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'transversal'
archivos: ['scripts/generar_informe.py']
ambito: 'Coherencia entre índice y tarjeta'
---

# ADR-0290 — El recálculo anota los aportes de las tarjetas

## Contexto y planteo del problema

El informe recalculaba los índices con el motor vigente, pero conservaba los
metadatos de cada tarjeta tal como estaban en el caché. Un valor actualizado
sin anotar, o un cambio de bandas o pesos, podía dejar su pertenencia y aporte
ausentes u obsoletos mientras el índice agregado sí lo incorporaba.

## Decisión

Tras recalcular ITCM, ITCG o ITCP, ejecutar el anotador del mismo cinturón con
ese resultado. Se conserva el tratamiento posterior de suspendidos. ITCIS
mantiene su anotación durante la publicación, donde se calcula desde series.
El censo de auditoría compara pertenencia, puntaje y peso de cada tarjeta
con el componente efectivamente agregado.

## Más información

No se alteran pesos ni bandas. Los controles incluyen tarjetas con metadatos
deliberadamente obsoletos para verificar que el nuevo cálculo los reemplaza.
