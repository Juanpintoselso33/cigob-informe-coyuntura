# Diputados: columnas y totales nominales corregidos

El parser perdía filas cuando los nombres de bloques largos dejaban menos
de 15 puntos entre bloque y provincia. Ahora infiere los inicios de
columna a partir de las filas bien separadas de cada página y ubica las
palabras por posición horizontal. Conserva los filtros de voto válido y
campos presentes; no incluye al presidente sin votar.

Se releyeron los 29 PDFs nuevos ya capturados. Sus 256 nombres únicos
por acta y sus totales por tipo de voto coinciden con los encabezados
oficiales, extraídos independientemente con `pdftotext -layout`. El Rice
de LLA no cambia en ninguna de las 29 actas. No fue necesario descargar
nuevamente los documentos.

El fixture real 5959 también tenía el defecto: su encabezado dice 131
afirmativos, 107 negativos, 2 abstenciones y 16 ausentes; el test esperaba
252 filas y 103 negativos, reproduciendo la omisión. Se corrigió a 256 y
107, y se agregaron comprobaciones de nombres únicos y campos de bloques
largos. Las suites dirigidas de cohesión y series: 148 aprobadas (1,87 s).

[Evidencia nominal y totales](cotejo-diputados-parser-corregido.json).
La consolidación productiva está pendiente del chequeo de eventos de
bloqueo/desafíos, para regenerar conjuntamente las salidas afectadas.

Integración posterior completada: [tarjetas y eventos actualizados](diputados-integracion-actual.md).
