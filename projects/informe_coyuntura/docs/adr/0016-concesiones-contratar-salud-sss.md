# ADR-0016 — Concesiones vía CONTRAT.AR + opción en salud vía padrones SSS (últimos manuales automatizados)

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-02 |
| **Ámbito** | `scripts/gestion.py` · `scripts/descargar_series.py` · web |

## Contexto

Tras los ADR-0013/0014/0015 quedaban tres indicadores manuales en gestión:
`concesiones_infraestructura` (35% estimado), `libertad_opcion_salud` (40%
estimado, SSS bloqueada desde may-2026) y `protocolo_antipiquetes`. Se
verificó con llamadas reales qué fuentes existen hoy para los dos primeros
(el tercero ya tiene su reemplazo acumulándose, ADR-0014).

## Decisión 1 — Concesiones: tasa de adjudicación en KM desde CONTRAT.AR

La Red Federal de Concesiones se licita por **CONTRAT.AR** (UOC 504,
Subsecretaría de Gestión Administrativa de Infraestructura, MEC) y su
búsqueda avanzada **funciona sin login**: sesión + `__VIEWSTATE` + POST
`txtNombrePliego="RED FEDERAL"` → tabla proceso/nombre/apertura/**estado**.
El kilometraje por tramo sale de las 4 tablas (una por etapa) de la página
oficial de la RFC en argentina.gob.ar.

- **Indicador** (doc 260702): `km de etapas adjudicadas / km totales del
  proceso`. Una etapa cuenta cuando su proceso figura **"Adjudicado"**.
  Jul-2026: Etapas I y II-A adjudicadas → **2.614 / 9.091 km = 28,7%**
  (banda 40 — la misma que daba el manual de 35%, sin salto de score).
- Gotchas resueltos: la tabla de la Etapa III usa **punto decimal**
  ('681.92') mientras las demás usan coma es-AR ('682,28'); el estado es la
  **anteúltima** columna (la última es la UOC).
- **Refinamiento pendiente**: II-B y III adjudican por renglones (tramo a
  tramo); hoy cuentan recién al estado final. Las fichas públicas por proceso
  (`VistaPreviaPliegoCiudadano.aspx`) permitirían capturar adjudicaciones
  parciales.
- **Descartado**: los datos abiertos de CONTRAT.AR (CKAN) están congelados en
  mar-2023 (verificado: 482 procesos, máx. 2023-03-16); no existe OCDS de
  obra pública; la búsqueda del Boletín Oficial bloquea la automatización
  (302 a /error/show).

## Decisión 2 — Opción en salud: derivación directa desde los padrones SSS

**Hallazgo nuevo (no existía o no se encontró en may-2026):** la SSS publica
en `argentina.gob.ar/sssalud/estadisticas` XLSX con **URL estable por año**,
actualizados in-place (~2 meses de rezago): beneficiarios por entidad del
RNAS (mensual) y usuarios por entidad de medicina prepaga (RNEMP). Las
prepagas inscriptas como Agentes del Seguro (canal creado por el DNU 70/23)
llevan **código RNAS ≥ 900000**: sus beneficiarios son aportes **derivados
directo, sin triangulación** por obra social.

- **Indicador**: `beneficiarios derivados a prepagas inscriptas (RNAS
  90xxxx) / usuarios totales de prepagas (RNEMP)`. Mar-2026: **2.660.767
  derivados a 59 prepagas / 8.369.312 usuarios = 31,8%** (banda 65 — la
  misma que el manual de 40%). Serie del canal: 12.334 (sep-2024) → 1,97M
  (ene-2025, fin de la triangulación, Res. 3284/2024) → 2,66M (mar-2026).
- Numerador y denominador son oficiales y de la misma fuente; antes de la
  reforma el canal directo no existía (0%).
- **Ruido conocido**: 1-2 obras sociales preexistentes con código 90xxxx
  (ej. 900102, ~11 mil beneficiarios, ~0,4% del numerador) — se acepta.
- **Sigue muerto**: el contador de "opciones de cambio" de sssalud.gob.ar
  (fingerprinting back-end) y el padrón CKAN (congelado en 2019). Ya no
  hacen falta.

## Complementos de la misma tanda

- **Serie mensual real del TDPS** (`descargar_series.fetch_tdps_serie`, API
  Presupuesto Abierto): 39 puntos 2023→2026 (Potenciar ~95-99% → sucesores
  100% desde abr-2024). Reemplaza el salto espurio 35→100 que mostraba el
  histórico acumulado (35 era la estimación manual vieja bajo otra métrica).
- **Purga del histórico acumulado**: se eliminaron los meses pre-jul-2026 de
  los indicadores cuya métrica cambió con el ITCG (cepo_mulc,
  apertura_comercial, asistencia_directa, fal_modernizacion_laboral,
  privatizaciones, concesiones, libertad_opcion_salud) — mezclaban la
  métrica vieja con la nueva en el mismo gráfico.

## Consecuencias

- Gestión queda con **15 colectores automáticos de 16 indicadores**; el único
  manual es `protocolo_antipiquetes` (su reemplazo se acumula solo,
  ADR-0014). El día empezó con 6 de 12.
- Continuidad de score: ambos indicadores caen en la misma banda que sus
  estimaciones manuales (ITCG sin salto por cambio de medición).
- **Riesgos**: CONTRAT.AR es ASP.NET WebForms (rediseño rompería el POST);
  la página RFC ya mudó de URL una vez; los XLSX de la SSS podrían cambiar
  de layout. Todos caen al fallback manual visible como "Carga manual".
