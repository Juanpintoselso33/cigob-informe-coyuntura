---
madr: 4
id: '0305'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'gestion'
indicadores: [fal_modernizacion_laboral]
archivos: ['scripts/gestion.py', 'data/gestion/fal_hitos.json', 'web/src/lib/fichas.ts', 'tests/test_fal_fechas_revision.py']
ambito: 'Fechas y alcance de la verificación del FAL'
---

# ADR-0305 — Consultar CNV no actualiza la revisión judicial

La tarjeta combina consulta automática de fondos CNV y un registro normativo
y judicial curado. La ficha decía «sin rezago» y que las resoluciones no podían
faltar por estar en un archivo local. Esas garantías no se sostienen.

Se estructuran las fechas ya documentadas: revisión normativa 20-jul-2026 y
judicial 21-ago-2026. La tarjeta expone ambas, la consulta CNV y la fecha de
evaluación. Su texto advierte que consultar CNV no renueva las revisiones
manuales. Una fecha ausente, inválida o futura impide producir un nuevo dato;
el proceso aplica su mecanismo habitual de caché.

La fecha de evaluación no se presenta como verificación integral. Se mantienen
valor y pesos; queda pendiente cerrar el expediente judicial y definir una
regla de antigüedad específica de la revisión manual. No se inventa una nueva
fecha de revisión a partir de una búsqueda sin noticias recientes.

Se corrige además la presentación de la litigiosidad SRT como resultado del
FAL: los juicios por riesgos del trabajo corresponden a otro universo y no
identifican el efecto del Fondo. El alcance es consistente con ADR-0285.
