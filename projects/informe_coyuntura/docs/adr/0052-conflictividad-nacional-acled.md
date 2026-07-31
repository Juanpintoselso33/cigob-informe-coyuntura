---
madr: 4
id: '0052'
estado: 'aceptado'
fecha: 2026-07-11
cinturon: 'politica'
archivos: ['scripts/gestion.py', 'scripts/politica.py', 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'web/src/lib/*', 'tests/*']
relacionado: ['0058', '0059']
complementado_por: ['0132']
ambito: '`scripts/gestion.py` · `scripts/politica.py` · `scripts/itcp.py` · `scripts/descargar_series.py` · `scripts/validacion_externa.py` · `web/src/lib/*` · `tests/*`'
---

# ADR-0052 — Conflicto social del ITCP: `conflictividad_nacional` (ACLED país entero) reemplaza a `movilizacion_cepa`

| **Precedente directo** | ADR-0048 (revisión editorial: `protestas_caba` fuera del cinturón, la dimensión quedó en CEPA sola), ADR-0017 (infraestructura ACLED), ADR-0022/0048 (patrón contexto oculto), ADR-0042 (criterio "nace discriminando") |

## Contexto y planteo del problema

Tras ADR-0048 la dimensión conflicto_social (15% del ITCP) quedó sostenida
por un único indicador, `movilizacion_cepa`, con dos defectos verificados en
vivo el 2026-07-11:

1. **Sin backfill posible.** CEPA publica informes de conflictividad recién
   desde fines de 2025 (escaneo en vivo de 40 páginas de
   centrocepa.com.ar/informes, 2026-07-08: ~4 informes, 2 usables). Era el
   único indicador puntuante del ITCP sin serie desde dic-2023 (2 puntos:
   abr-2026 y jun-2026), y la dimensión no existía hacia atrás en la
   reconstrucción de la validación externa.
2. **Fórmula no comparable mes a mes.** La cifra es un acumulado de
   conflictos "desde inicios del año" normalizado por un máximo arbitrario
   (200) y extraído por regex de la prosa del informe: crece mecánicamente
   con el calendario y se resetea en enero — la "tensión social" desaparece
   todos los veranos por construcción.

Fuentes alternativas investigadas y descartadas para la ventana dic-2023+:
la serie mensual oficial de conflictos laborales (Secretaría de Trabajo)
termina en mar-2023 y sus informes trimestrales se discontinuaron en 2020
(manifest `srt_conflictividad_urls.json`, verificado contra la spreadsheet
canónica); GDELT quedó cerrado por precedente (ADR-0026, throttling); la
API por evento de ACLED (filtro laboral/sindical por actor) devuelve 403 en
el nivel Open de la cuenta UBA. Las gacetillas mensuales de la Secretaría
de Trabajo (existen al menos hasta jun-2025) quedan anotadas como posible
pata futura — notas de prensa con encuadre oficial, sin archivo estructurado
confirmado.

## Opciones consideradas

- **Disolver la dimensión** (lectura amplia de ADR-0048, redistribuir el 15%):
  descartada — el ITCP quedaría con 4 de las 5 dimensiones Matus del marco
  publicado a un mes del lanzamiento, y el índice subiría por tercera vez en
  la semana (72,9 → 77,2 → 79,5) removiendo una dimensión que mide tensión
  real. Sigue siendo el candidato si CIGOB formaliza el encuadre "solo
  parlamentario".
- **Arreglar CEPA en vez de reemplazarlo**: no hay arreglo — el defecto es
  de la fuente (sin historia publicada) y de la métrica (acumulado YTD).
- **Anclas 2/4/6/8 alternativas (−33/−30/−25/−15 u otras)**: la variante
  elegida es la única con todos los cortes en huecos reales de la
  distribución; otras partían el clúster central por ruido.
- **Filtrar solo conflicto laboral/sindical en ACLED** (actor = gremios):
  imposible hoy — requiere la API por evento, bloqueada en nivel Open (403).
  Condición de reapertura: upgrade de la cuenta académica.

## Decisión

### `conflictividad_nacional`: eventos ACLED de TODO el país

% de variación de los eventos de protesta y disturbios (Protests+Riots) de
ACLED en las 24 jurisdicciones, acumulados en 12 meses completos, contra el
total 2023 (2.605 eventos — la base del mandato). Menor = mejor. `valor` ES
la variación (a diferencia de `protestas_caba`, que exponía el conteo crudo
y necesitaba un caso especial de scoring). El mes final del archivo se
excluye si está parcial (corte semanal + rezago de carga).

Misma descarga que ya hace el pipeline para la card de protestas de gestión
(agregado semanal LatAm, sesión académica UBA): el store
`data/gestion/protestas_caba.json` pasa a guardar también la serie
`mensual_nacional`, con memo por proceso para no bajar el XLSX (~8 MB) más
de una vez por corrida. Sin cachés nuevos que agregar al cron.

**No es reponer lo que sacó la revisión editorial**: ADR-0048 retiró la
medición de protesta *en CABA* (9% de los eventos del país) manteniendo la
dimensión conflicto social con la pata de CEPA. Esto reemplaza esa pata por
una operacionalización nacional del mismo constructo que el editor conservó.
Queda marcado para la próxima revisión editorial CIGOB con este argumento.

### Anclas calibradas contra la serie real y verificadas contra prensa

Serie reconstruida: 30 puntos (dic-2023→may-2026, rango −34,2 a +2,7,
mediana −27,8). Anclas **−32/−29/−26/−15** (números redondos ≈ quintiles):

`(−∞,−32]→100 · (−32,−29]→85 · (−29,−26]→65 · (−26,−15]→40 · (−15,∞)→10`

Distribución 5/7/8/4/6 — las cinco bandas pobladas, cada corte en un hueco
real de los datos (criterio ADR-0042, nace discriminando). La historia que
cuenta la serie se verificó contra la cronología de prensa antes de decidir:

- **2024**: caída fuerte (−27,7% en dic-24 ≈ el −27% del balance oficial de
  bloqueos del Ministerio de Seguridad; marchas CABA −56% según GCBA).
- **2025**: meseta baja, con el pico de feb-2025 (255 eventos) coincidiendo
  con la ola de movilizaciones de jubilados documentada por CELS
  (29-ene, 19/26-feb, 5/12-mar) y el paro general del 10-abr-2025.
- **2026**: reaceleración feb→may (210/216/251/279 eventos — máximos
  sostenidos desde 2023): 4° paro general 19-feb (reforma laboral, adhesión
  >90%, 255 vuelos cancelados), paro nacional docente 2-mar, marchas del
  30-abr, conflicto universitario/científico de mayo. El propio CEPA
  (informe feb-2026) reporta la misma dirección: 717 casos ene-24→feb-26 y
  "crece el conflicto social y gremial".

### Límites declarados (ficha y ADR)

- **Cobertura ACLED pre-2020 NO confiable** (2019 promedia 102 eventos/mes
  vs 240 de 2020 — expansión de cobertura, no menor conflictividad): no se
  usa ni para calibrar ni para el gráfico público, que arranca en dic-2023.
- La base 2023 es fija y envejece (mismo criterio declarado que ITVC-B100);
  además su 2° semestre fue atípicamente calmo (período electoral), lo que
  hace la base algo baja — sesgo en dirección conservadora.
- Cuenta eventos, no asistentes: frecuencia del conflicto, no masividad.
- La estacionalidad del calendario de protestas (dic-ene bajos, mar/sep
  altos) queda absorbida por la ventana de 12 meses.

### `movilizacion_cepa` a seguimiento interno

Sale del índice Y del tablero (`INDICADORES_CONTEXTO` → `POLITICA_OCULTOS`,
patrón ADR-0022/0048); el scraper y su serie siguen corriendo como contraste
del indicador nacional. Su ficha se retira de /metodologia (los ocultos no
tienen ficha — precedente rotación/badlar); banda de referencia en
`BANDAS_ITCP`. **No se borra nada.**

### Consecuencias

- Con los valores del 11-jul: `conflictividad_nacional` = −21,4% (2.048
  eventos en 12m a may-2026 vs 2.605 en 2023) → puntaje interpolado 43,2;
  la dimensión conflicto_social baja de 64,4 (CEPA) a 43,2 — **el reemplazo
  es más conservador que el statu quo**: captura la reaceleración de
  protesta 2026 que CEPA no ve. ITCP 77,2 → **74,0** (tensión 2,6), banda
  sin cambio. Es el efecto de medir mejor, no un error. El Monte Carlo
  pasa a señalar a `conflictividad_nacional` como componente dominante
  (sin él, el índice sube a 79,5): la dimensión que antes casi no existía
  ahora es la que más mueve el resultado — coherente con que hoy es la
  segunda más tensa del cinturón después de poder legislativo.
- La reconstrucción histórica de la validación externa gana una pata mensual
  completa desde dic-2023 (la dimensión conflicto social antes no existía
  hacia atrás); el r ITCP↔EPU se recalcula en la misma corrida scoped.
- 11 indicadores siguen puntuando; los ocultos pasan de 2 a 3
  (`rotacion_gabinete`, `protestas_caba`, `movilizacion_cepa`).
- El store de gestión suma la clave `mensual_nacional` (aditiva — la card de
  protestas CABA de gestión no cambia).
- Tests: banda nueva pineada (`test_banda_conflictividad_nacional`),
  composición de la dimensión pineada
  (`test_conflicto_social_es_conflictividad_nacional`), reconciliación de
  publicar actualizada (movilizacion_cepa AUSENTE del snapshot).
- Pendiente declarado: mostrar el cambio al editor CIGOB en la próxima
  revisión editorial del cinturón (riesgo de lectura "volvieron las
  protestas" — el argumento de respuesta está en la sección Decisión).
