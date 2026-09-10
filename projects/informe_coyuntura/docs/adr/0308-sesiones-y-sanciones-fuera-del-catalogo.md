---
madr: 4
id: '0308'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indice: 'ITCP'
indicadores: [veto_quorum, produccion_legislativa]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'data/politica/leyes_sancionadas_complementarias.json']
corrige: ['0091', '0306']
---

# ADR-0308 — Sesiones y sanciones fuera del catálogo

## Contexto y planteo del problema

El índice oficial de sesiones de Diputados registra la reunión del 26 de
agosto de 2026, ausente en CKAN. En 72 reuniones emparejadas, las fechas de
CKAN preceden en dos días a las del índice. Consultar el catálogo con éxito
no demuestra que esté actualizado ni que sus fechas sean correctas.

La versión taquigráfica de esa reunión, concluida el 27 de agosto, consigna
cinco sanciones definitivas que tampoco aparecen en el catálogo de leyes:
Mercosur–Singapur, San Miguel de Tucumán como capital simbólica, las cámaras
federales de Tucumán y Mar del Plata, y Camino de Brochero. El tratado PCT
vuelve al Senado con modificaciones y no integra este complemento.

## Decisión

El indicador de minoría usa las fechas e identidades del índice oficial,
sin aplicar un desplazamiento constante a CKAN. Conserva reuniones distintas
del mismo día y descarta enlaces duplicados. Excluye convocatorias futuras,
citadas no efectuadas, reuniones informativas, preparatorias, asambleas y
homenajes. Un rótulo de convocatoria no efectuada no demuestra falta de quórum.
La ventana conserva doce meses calendario y corta en la fecha real de consulta.

Las cinco sanciones se agregan al registro complementario con expediente,
fuente original y verificación explícita de sanción definitiva. No se inventa
un número de ley. Cuando CKAN incorpore el mismo expediente o proyecto con
número de ley, se cuenta una sola identidad. Identidades contradictorias,
fechas inválidas o un catálogo vacío provocan fallo y preservación de caché.

## Más información

Las fuentes son el [índice de sesiones](https://www.hcdn.gob.ar/sesiones/) y el
[diario de la reunión 6](https://www3.hcdn.gob.ar/dependencias/dtaquigrafos/diarios/periodo-144/diario_202608266.pdf),
páginas impresas 291, 361, 364, 369 y 374. La fecha de inicio de la reunión
no debe confundirse con el día civil de aprobación ni con la publicación de
la ley. La incorporación aumenta el total de los doce meses completos hasta
agosto de 22 a 27. El promedio de referencia 2008–2025 permanece en 73,33.
No cambia ningún peso ni ancla. La cobertura posterior de ambas cámaras
continúa abierta: cinco omisiones verificadas no certifican exhaustividad.

### Cotejo posterior del mismo día

El BAT de Diputados confirma 27.819–27.823 y sus textos consignan fecha de sanción 26-ago. El boletín del Senado del 27-ago, página 18, agrega 27.824 y 27.825; los otros tres tratados pasan a Diputados. Se actualiza el registro a siete omisiones y 29 leyes en la ventana vigente. Los expedientes conservan utilidad como aliases, pero ya se dispone de números verificados para los siete casos. La referencia histórica de 73,33 no cambia.
