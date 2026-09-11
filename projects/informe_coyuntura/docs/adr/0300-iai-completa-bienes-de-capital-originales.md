---
madr: 4
id: '0300'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [iai]
archivos: ['scripts/bienes_capital.py', 'scripts/macro.py', 'web/src/lib/fichas.ts']
ambito: 'Fuente vigente y ventana mensual de inversión'
---

# ADR-0300 — IAI completa los bienes de capital originales

Actualizar el ISAC no bastaba: la API de bienes de capital seguía en junio,
mientras la planilla oficial del ICA ya incluía julio y el año anterior.
El IAI quedaba detenido en junio por su regla de último mes común.

Se descubre la planilla mensual de importaciones por usos económicos desde
la página oficial del ICA. Se exige la columna exacta Bienes de capital (BK),
millones de USD, años consecutivos, año anterior completo y meses cerrados
consecutivos desde enero. No se toman piezas y accesorios ni acumulados anuales.

La ventana completa del original sustituye los niveles de API, incluidas las
revisiones. Para fechas anteriores a esa ventana se conserva la API histórica.
El límite de observaciones se aplica después de unir las fuentes, sin borrar
la historia anterior. Si falla el original o la API resulta más reciente,
el cálculo no publica una actualización: opera el tratamiento de caché ya
existente. No se retrocede silenciosamente al dato de junio.

Tarjeta e historia usan el mismo adaptador. Permanecen los pesos 65/35 sin
patentamientos comparables y la intersección mensual con ISAC. No se alteran
bandas, ni se convierten importaciones nominales en volumen físico.

Julio se cotejó en dos cuadros oficiales: BK 1167,16911031 millones USD en
2026 y 1265,03060453 en 2025 (−7,73589934%). Con ISAC −4,53982580% da
IAI −5,66%. El original mensual aporta 19 meses: enero-diciembre de 2025 y
enero-julio de 2026; la historia anterior sigue identificada como API.

Evidencia: `docs/auditorias/2026-09-08/cotejo-bienes-capital-original-pendiente.json`.
Pruebas de calendario, universo, unidades, precisión, revisión, preservación
de historia, fuente más nueva discrepante y composición mensual compartida.
