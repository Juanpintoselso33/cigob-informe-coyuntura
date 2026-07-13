# Cinturón Gestión

| Campo | Valor |
|---|---|
| Script | `scripts/gestion.py` |
| Cache | `output/cache/gestion.json` |
| Datos de carga manual | `data/gestion/manuales.json` |
| Peso en score global | 20% |
| Barbarismo de riesgo | gerencial |

## Encuadre

Mide el cumplimiento de reformas del Estado y compromisos de la Administración Pública Nacional iniciados en diciembre de 2023. Cada indicador expresa un avance porcentual sobre el objetivo de la reforma. La conversión a score de tensión es `score = 10 × (1 − avance_pct/100)`: a mayor ejecución, menor tensión. El score del cinturón es el promedio simple de los 12 indicadores.

Umbrales: 0–3 estable, 4–6 en tensión, 7–10 tensionado.

## Indicadores activos

| Indicador | Estado | Fuente | Frecuencia | Avance actual |
|---|---|---|---|---|
| `cepo_mulc` | Automático | dolarapi.com (brecha CCL/oficial) | Diaria | 78.4% (brecha 4.3%) |
| `reduccion_estado` | Automático | datos.gob.ar, serie 324.1 | Trimestral | 2.7% (var −0.8%) |
| `apertura_comercial` | Automático | datos.gob.ar, serie 163.3 (importaciones, proxy) | Mensual | 100% (+42.4% i.a.) |
| `desregulacion_normativa` | Automático | InfoLeg, sesión POST, `texto="deroga"` desde dic-2023 | Mensual | 55% (55 normas) |
| `reestructuracion_organismos` | Automático | InfoLeg, sesión POST, `texto="disolucion"` desde dic-2023 | Mensual | 40% (18 normas) |
| `rigi_inversiones` | Automático | InfoLeg, sesión POST, `tipoNorma=3 texto="VPU"` desde jul-2024 | Mensual | 28% (28 resoluciones) |
| `concesiones_infraestructura` | Carga manual | Vialidad Nacional / ORSNA (informes PDF trimestrales) | Trimestral | 35% |
| `asistencia_directa` | Carga manual | ANSES / MDS (programa Volver al Trabajo) | Mensual | 35% |
| `fal_modernizacion_laboral` | Carga manual | MTEySS (FAL operativo H2-2026) | Mensual | 10% |
| `protocolo_antipiquetes` | Carga manual | Ministerio de Seguridad | Trimestral | 55% |
| `privatizaciones` | Sin fuente disponible | Carga manual desde anuncios oficiales | Mensual | 15% |
| `libertad_opcion_salud` | Sin fuente disponible | Carga manual desde reportes SSS | Trimestral | 40% |

Score actual del cinturón: **5.9 (en tensión)**. Última ejecución: 23 de mayo de 2026, 6 de 6 automáticos frescos, 12 de 12 con dato.

## Detalle por indicador

### `cepo_mulc` — Cepo Corporativo

- Fuente: `GET https://dolarapi.com/v1/dolares`
- Cálculo: `brecha = (CCL_venta − oficial_venta) / oficial_venta × 100`
- Fórmula de avance: `max(0, 100 − brecha × 5)`. Brecha 0% equivale a avance 100%; brecha 20% equivale a avance 0%.
- Interpretación: el cepo minorista se levantó en abril de 2025. Para empresas persiste la restricción cambiaria: giro de dividendos, remesa de utilidades, acceso al MULC para capital. El CCL (contado con liquidación) refleja esta brecha. El dólar blue, en cambio, retornó cerca de cero respecto del oficial y resulta engañoso como proxy.
- Último valor (mayo 2026): CCL=1486.6, oficial=1425, brecha=4.32%, avance=78.4%.

### `reduccion_estado` — Reducción del Estado

- Fuente: `GET https://apis.datos.gob.ar/series/api/series/?ids=324.1_TOTAL_SECTAJO__36&sort=desc&limit=16`
- Serie: "Total sector público puestos trabajo", frecuencia trimestral.
- Cálculo: variación porcentual contra baseline Q4-2023 / Q1-2024. Meta de referencia: −30% equivale a avance 100%.
- Limitación: la serie mide insumo de mano de obra (puede ser índice, no headcount). La variación −0.8% contra Q1-2024 sugiere reducción modesta. Para mayor precisión se debería identificar serie de nómina ONP en datos.gob.ar.
- Último valor (mayo 2026): −0.8% versus 2024-01-01, avance=2.7%.

### `apertura_comercial` — Apertura Comercial

- Fuente: `GET https://apis.datos.gob.ar/series/api/series/?ids=163.3_MTALTAL_0_0_7&sort=desc&limit=14`
- Serie: "Importaciones. Total. Millones USD. Mensual" (INDEC).
- Cálculo: variación interanual. +30% i.a. equivale a avance 100%; flat equivale a avance 50%; −30% i.a. equivale a avance 0%.
- Limitación: proxy imperfecto. Mide recuperación del comercio, no directamente la eliminación de aranceles o trabas no arancelarias.
- Último valor (mayo 2026): +42.4% i.a. (febrero 2025), avance=100% (rebote desde recesión 2024).

### `desregulacion_normativa` — Desregulación Normativa

- Fuente: InfoLeg, búsqueda mediante sesión POST. Requiere GET previo a la home para obtener `jsessionid`, luego POST con `texto="deroga"` y rango dic-2023 a hoy.
- Cálculo: conteo de normas con "deroga" en el texto publicadas desde diciembre 2023. 100 normas equivalen a avance 100% (escala lineal).
- Observación: cada documento cuenta como uno independientemente de cuántos artículos derogue (el DL 70/23 cuenta como una acción aunque contenga cientos de derogaciones).
- Último valor (mayo 2026): 55 normas, avance=55%.

### `reestructuracion_organismos` — Reestructuración de Organismos

- Fuente: InfoLeg, sesión POST con `texto="disolucion"` y rango dic-2023 a hoy.
- Cálculo: conteo de normas con "disolucion" publicadas desde diciembre 2023. 45 normas equivalen a avance 100%.
- Observación: el DNU 70/23 (el mega-decreto de diciembre 2023 que redujo secretarías de 106 a aproximadamente 54) no aparece en la búsqueda de texto libre de InfoLeg porque no está indexado como full-text. Los 18 documentos capturados corresponden a acciones de disolución y fusión posteriores al megadecreto.
- Calibración: 18 actos equivalen a avance 40%, valor validado contra estimación manual previa.
- Último valor (mayo 2026): 18 normas, avance=40%.

### `rigi_inversiones` — Inversiones RIGI

- Fuente: InfoLeg, sesión POST con `tipoNorma=3` (Resolución) + `texto="VPU"` desde 01/07/2024 (entrada en vigencia de la Ley 27.742).
- Cálculo: conteo de resoluciones con "VPU" (Vehículo de Proyecto Único). Fórmula directa: `avance_pct = min(100, count)`.
- Calibración: 28 resoluciones VPU equivalen a aproximadamente 16 proyectos aprobados (USD 27.210 millones, mayo 2026). Ratio de aproximadamente 1.7 resoluciones por proyecto (aprobación más complementarias). Calibrado contra el dato manual publicado por El Cronista y La Nueva en mayo 2026.
- Nota técnica: la búsqueda OR-search del InfoLeg falla con términos genéricos como "RIGI" (devuelve 93 normas mezcladas) o "adhesion" (164 normas). "VPU" es vocabulario técnico exclusivo del régimen y aparece únicamente en resoluciones de aprobación e implementación.
- Último valor (mayo 2026): 28 resoluciones VPU, avance=28.0%.

### `privatizaciones` — Privatizaciones

- Fuente: carga manual desde `data/gestion/manuales.json`.
- Cálculo: porcentaje de empresas privatizadas efectivamente sobre el listado del DL 70/23.
- Estado actual: Aerolíneas y Correo en proceso parlamentario sin transferencia efectiva. Avance estimado 15%.
- Razón del bloqueo técnico: el Boletín Oficial no expone API JSON pública (los endpoints retornan HTML). ComprAR (plataforma de pliegos) es ASP.NET con `__VIEWSTATE` y requiere mantener sesión con formularios complejos. InfoLeg con `tipoNorma=3 texto="privatizacion"` devuelve 9 normas pero el OR-search es ambiguo: contar normas no equivale a transferencia efectiva.
- Política de actualización: carga manual mensual desde anuncios oficiales del Ministerio de Economía.

### `concesiones_infraestructura` — Concesiones de Infraestructura

- Fuente: carga manual desde `data/gestion/manuales.json`.
- Cálculo: porcentaje de corredores viales concesionados sobre el plan total de 9 corredores.
- Estado actual: corredores viales en licitación activa. Avance estimado 35%.
- Vía de automatización futura: parser de PDF sobre informes trimestrales de Vialidad Nacional / ORSNA, similar al utilizado para CICCRA en vida cotidiana.

### `asistencia_directa` — Asistencia Directa

- Fuente: carga manual desde `data/gestion/manuales.json`.
- Cálculo: porcentaje de beneficiarios sociales que cobran directamente sobre el total de beneficiarios.
- Programa de referencia: Volver al Trabajo (ex Potenciar Trabajo), aproximadamente 330.000 beneficiarios iniciales.
- Estado actual: avance estimado 35%.
- Vía de automatización futura: portal de transparencia ANSES, pendiente de apertura de API pública.

### `fal_modernizacion_laboral` — Modernización Laboral (FAL)

- Fuente: carga manual desde `data/gestion/manuales.json`.
- Cálculo: porcentaje de etapas implementadas (ley, reglamentación, operación).
- Estado actual (mayo 2026): FAL aprobado por ley, reglamentación incompleta (ARCA, CNV, ANSES pendiente). Entrada en vigencia postergada a H2-2026. Avance 10%.
- Vía de automatización futura: implementable cuando el FAL entre en operación, vía endpoints de MTEySS, ARCA y ANSES.

### `libertad_opcion_salud` — Libertad de Opción en Salud

- Fuente: carga manual desde `data/gestion/manuales.json`.
- Cálculo: opciones de cambio captadas acumuladas desde diciembre 2023 sobre baseline.
- Estado actual: avance estimado 40%.
- Razón del bloqueo técnico: la Superintendencia de Servicios de Salud usa fingerprinting de cliente en backend (endpoint `/fwb/first_submit.df`); el sitio devuelve "No se reportan datos" incluso con browser real (Playwright). Los datasets de obras sociales en datos.gob.ar están congelados con `last_modified` 2018-2019.
- Política de actualización: carga manual trimestral desde reportes oficiales de SSS.

### `protocolo_antipiquetes` — Protocolo Antipiquetes

- Fuente: carga manual desde `data/gestion/manuales.json`.
- Cálculo: porcentaje de cortes con carril libre garantizado sobre el total de cortes registrados desde diciembre 2023.
- Estado actual: avance estimado 55%.
- Vía de automatización futura: requeriría acuerdo institucional con Ministerio de Seguridad o relevamiento propio.

## Ejecución

```bash
cd projects/informe_coyuntura
python scripts/gestion.py
```

Códigos de salida:

| Código | Significado |
|---|---|
| 0 | Todos los colectores automáticos devolvieron datos frescos |
| 1 | Al menos un colector automático fresco (parcial) |
| 2 | Ningún colector automático fresco |
