---
madr: 4
id: '0303'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [conflictividad_nacional, protestas_caba]
archivos: ['scripts/acled_calendario.py', 'scripts/politica.py', 'scripts/gestion.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'tests/test_acled_calendario.py']
ambito: 'Corte semanal, referencia mensual y caché de conflictividad'
---

# ADR-0303 — La semana ACLED empieza el sábado

[ACLED define `week`](https://acleddata.com/use-access/how-use-acleds-aggregated-data)
como el sábado inicial de una semana sábado–viernes. El monitor lo trataba
como fecha final. El archivo cuya última semana empieza el 29 de agosto de
2026 alcanza el 4 de septiembre: descartaba indebidamente el grupo de agosto.

Un módulo compartido calcula el viernes final, comprueba que la semana ya
cerró y decide qué grupos mensuales están completos. Tarjeta nacional,
historia nacional y contexto de CABA usan la misma regla. Se exige calendario
consecutivo, conteos enteros no negativos y los doce meses de la base 2023.
El corte de la descarga se toma de todo el archivo, no de la última protesta
de Argentina: una semana sin eventos no implica falta de cobertura.

Se conserva la agregación por mes de inicio de la semana, pero se explicita su
significado. Las semanas que cruzan mes o año no se reparten: no son totales
exactos por fecha diaria del evento. Tanto la base como la ventana usan esa
convención. La alternativa de medir meses calendario con microdatos queda
como mejora metodológica separada; no se inventa un reparto diario uniforme.

La descarga autenticada cotejada al 8 de septiembre reproduce 2.605 eventos en
los grupos de la base 2023 y 1.977 en septiembre de 2025–agosto de 2026:
−24,1%. Para CABA: base 240, acumulado 280, +16,7%; es contexto, no cortes de
calle ni indicador puntuante de gestión.

Si falla la descarga, la tarjeta conservada se marca desactualizada y mantiene
el sello del archivo. El colector político no vuelve a sellarla ni la cuenta
como fresca. La antigüedad del corte semanal y el fallo de consulta son hechos
distintos. Se regeneran tarjetas, historia y contrastes afectados.
