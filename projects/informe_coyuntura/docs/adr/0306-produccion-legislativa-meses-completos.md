---
madr: 4
id: '0306'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indice: 'ITCP'
indicadores: [produccion_legislativa]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts']
corrige: ['0168']
corregido_por: ['0308']
---

# ADR-0306 — Producción legislativa: doce meses completos y leyes distintas

> Actualización: [ADR-0308](0308-sesiones-y-sanciones-fuera-del-catalogo.md) reemplaza las fechas de sesiones de CKAN por el índice oficial y agrega cinco sanciones de agosto omitidas en el catálogo.

## Contexto y planteo del problema

El código etiquetaba cada mes con el conteo al primer día, incluyendo ambos
extremos, mientras la ficha declaraba una ventana que terminaba en ese mes.
Además publicaba el mes en curso. La ficha dibujaba puntos 30, 42 y 60 donde el
motor usa los puntos medios 27,5, 42,5 y 62.

El recurso HCDN consultado el 8 de septiembre contiene 1.340 filas, incluyendo
19 de 2026 y tres números de ley duplicados. Por tanto, 1.340 / 18 no es el
promedio de leyes distintas de 2008-2025: son 1.318 / 18 = 73,22.

## Decisión

- Contar leyes distintas en doce meses calendarios completos, con inicio
  inclusivo y final exclusivo en el primer día del mes siguiente. Excluir el
  mes en curso. La fecha mensual conserva la convención YYYY-MM-01.
- Validar número y fecha; rechazar fechas futuras o leyes con fechas en
  distintos meses. Las dos fechas de la ley 27083 pertenecen a diciembre de
  2014 y no alteran el conteo mensual ni anual; no se decide cuál día es correcto.
- Conservar las bandas de diseño, incluido el umbral 74, y corregir su
  justificación: referencia histórica aproximada, no igualdad con el promedio.
- Alinear el gráfico metodológico con los puntos reales del motor.
- Mostrar la última sanción registrada y explicar que una consulta exitosa
  no acredita la exhaustividad del catálogo. No confundir último evento con
  fecha de cobertura ni eliminar automáticamente meses sin sanciones.

Las leyes 27748 (14-ago-2024) y 27774 (1-oct-2024), ausentes de CKAN, se incorporan desde un registro complementario con sus originales del Boletín Oficial. La unión por número evita duplicarlas cuando el catálogo las incorpore. Con esos complementos, la referencia asciende a 1.320 leyes de 2008-2025 / 18 = 73,33. La revisión del registro es manual y no se renueva por consultar CKAN.

## Más información

### Validación y límites

Pruebas de bordes mensuales, duplicados y entradas inválidas en
`tests/test_produccion_calendario.py`. El cotejo API/CSV y el impacto histórico
se conservan en la auditoría del 8 de septiembre. La conciliación exhaustiva
con otro inventario de sanciones sigue pendiente; estas correcciones no la
dan por terminada. La cantidad de leyes tampoco mide su importancia, su
origen ni su cumplimiento.
