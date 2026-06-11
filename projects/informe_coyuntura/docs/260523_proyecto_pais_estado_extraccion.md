# Proyecto País — Estado de extracción de indicadores

**Fecha:** 23 de mayo de 2026
**Documento base:** *Proyecto País: Indicadores en trabajo* (20 de mayo de 2026)
**Objeto:** documentar, para cada indicador enunciado en el documento base, su estado de implementación, la fuente real utilizada y, en los casos donde no fue posible automatizar, la razón técnica.

> **Actualización (10 de junio de 2026):** dos documentos institucionales nuevos cambiaron la metodología.
> 1. *Fórmula Paramétrica — Cinturón de la Macroeconomía* (`260602 Parametrica Macro.docx`): el cinturón macro pasó a puntuarse con el **ITCM** (índice 0–100, 4 dimensiones ponderadas, 7 de los 11 indicadores; los otros 4 quedan como contexto). Detalle en `docs/cinturon_macro.md`.
> 2. *Marco Conceptual del Informe de Coyuntura* (`260606 MARCO CONCEPTUAL lINFORME DE COYUNTURA.docx`): se amplió de 4 a **5 cinturones** con **Espíritu de Época** (colector `scripts/espiritu_epoca.py`, 3 proxies v1: ICC UTDT, sentimiento digital, clima electoral del Votómetro). Detalle en `docs/cinturon_espiritu_epoca.md`.
>
> Los pesos del score global son **por fase del mandato** (`config.py`, según la ponderación temporal del Marco Conceptual): fase temprana (primeros 4 años) 20% parejo para los cinco; consolidación 25/25/20/15/15. Las tablas de este documento describen el estado a mayo de 2026 y siguen siendo válidas para fuentes y extracción.

---

## Resumen

| Cinturón | Indicadores del documento base | Automáticos | Carga manual | Sin fuente disponible |
|---|---|---|---|---|
| Vida Cotidiana | 14 + 1 manual | 14 | 1 | 0 |
| Macroeconomía | 11 | 11 | 0 | 0 |
| Política | 10 | 4 | 0 | 6 |
| Gestión | 12 | 6 | 4 | 2 |
| **Total** | **47** | **35** | **5** | **8** |

Cobertura efectiva: 40 de 47 indicadores producen datos (35 automáticos + 5 con carga manual periódica). Los 7 restantes se documentan al pie de cada cinturón con la razón técnica de la limitación.

Adicionalmente, se incorporaron 5 indicadores no listados en el documento base pero relevantes para la lectura de coyuntura: brecha LLA−PJ del Votómetro, sesiones fracasadas por falta de quórum, comisiones caídas post-dictamen, patentamiento de motos, y brecha CCL/oficial.

---

## 1. Cinturón de la Vida Cotidiana

Orquestador: `scripts/vida_cotidiana/main.py`. Ocho fuentes activas, aproximadamente 32 datapoints por ejecución. Última corrida: 23 de mayo de 2026, todas las fuentes operativas.

### Indicadores activos

| Indicador | Fuente / proxy | Frecuencia | Estado | Último dato |
|---|---|---|---|---|
| Brecha salario real vs. CBT | INDEC, RIPTE + CBT (datos.gob.ar) | Mensual | Automático | 3.82 canastas, marzo 2026 |
| IPC alimentos | INDEC, serie 146.3 | Mensual | Automático | +3.35% m/m, marzo 2026 |
| Endeudamiento familiar | BCRA API v4.0 (tarjeta, personales, hipotecarios, consumo) | Diaria | Automático | $129.334 millones, mayo 2026 |
| Peso de tarifas | INDEC, IPC vivienda + IPC regulados | Mensual | Automático | +3.71% / +5.08%, marzo 2026 |
| Consumo de carne vacuna | CICCRA, parsing de PDF mensual | Mensual | Automático | abril 2026 |
| Informalidad laboral | INDEC, asalariados sin descuento | Anual | Automático | 36.75%, enero 2026 |
| Mortalidad de PyMEs | INDEC, IPI manufacturero + EMAE (proxy) | Mensual | Automático | febrero 2026 |
| Despacho de cemento e hierro | INDEC, ISAC + acero crudo | Mensual | Automático | 143.5 / 731.6, febrero 2026 |
| Pluriempleo | INDEC EPH, subocupación demandante (proxy) | Trimestral | Automático | 7.8%, octubre 2025 |
| Inseguridad urbana | SNIC + datos abiertos CABA | Anual | Automático | 2.501.057 hechos, 2024 |
| ICC Confianza del Consumidor | UTDT, scraping XLS | Mensual | Automático | 40.5, mayo 2026 |
| Sentimiento digital | Google Trends vía pytrends (4 términos) | Tiempo real | Automático | inflación 1.8, precios 9.2 |
| Apatía electoral | Votómetro CIGOB (implementado en cinturón Política como `votometro_ventaja_lla`) | Continua | Automático | +13.3 pp LLA−PJ |
| Espera en salud pública | DEIS / CKAN (solo enumera datasets disponibles) | Variable | Automático parcial | 3 datasets identificados |

### Indicador de carga manual

| Indicador | Razón de carga manual |
|---|---|
| Deserción escolar | Sin serie mensual disponible. Ministerio de Educación publica datos con rezago anual; carga manual en cada actualización ministerial. |

### Indicador adicional implementado

| Indicador | Fuente | Comentario |
|---|---|---|
| Patentamiento de motos | CAFAM | Proxy de consumo discrecional. 51.124 unidades en mayo 2026. |

### Observación técnica

El script puente `scripts/vida_cotidiana.py` —que integra con el orquestador global del informe— solo expone tres indicadores legacy (`ipc_total`, `desocupacion`, `icc_utdt`). El dashboard agregado del informe debe migrarse a leer del output `scripts/vida_cotidiana/data/vida_cotidiana_*.json` para acceder a los 14 indicadores.

---

## 2. Cinturón de la Macroeconomía

Script: `scripts/macro.py`. Once de once indicadores activos. Score actual: 2.1 (estable). Última corrida: 23 de mayo de 2026, todos los indicadores frescos.

### Indicadores activos

| Indicador | Qué mide | Fuente | Último valor |
|---|---|---|---|
| IPC total | Inflación mensual nacional | INDEC, serie 148.3 | 3.38% m/m |
| Reservas BCRA | Reservas internacionales brutas | BCRA API v4.0, variable 1 | 46.585 millones USD |
| Tasa BADLAR | Costo del dinero para depósitos mayoristas | BCRA API v4.0, variable 7 | 22.0% anual |
| EMAE (variación interanual) | Actividad económica adelantada | INDEC, serie 143.3 | +1.88% i.a. |
| Saldo comercial 12 meses | Balance exportaciones-importaciones acumulado | INDEC, serie 164.3 | +17.125 millones USD |
| Recaudación tributaria | Variación mensual recaudación total | INDEC/AFIP, serie 172.3 | −0.99% var. m |
| TCRM | Tipo de cambio real multilateral | INDEC, serie 116.3 (base 2010=100) | 79.77 |
| Expectativas inflación (REM) | Proyección del mercado a 12 meses | BCRA API v4.0, variable 29 | 24.2% anual |
| Préstamos privados | Variación crédito bancario al sector privado | BCRA API v4.0, variable 26 | +2.13% var. m |
| Base monetaria | Variación billetes + reservas bancarias | BCRA API v4.0, variable 15 | +0.7% var. m |
| Tipo de cambio mayorista | Variación tipo de cambio oficial referencia | BCRA API v4.0, variable 5 | −0.27% var. m |

### Indicadores no implementados del documento base

El documento base listó 8 indicadores adicionales bajo "Perspectiva Matusiana en diseño". Estado actual:

| Indicador | Estado | Comentario |
|---|---|---|
| Tasa de desempleo / subocupación | Disponible | Ya se extrae en cinturón Vida Cotidiana (EPH INDEC). Pendiente: exponerlo también en Macro. |
| Pobreza por ingresos (proxy) | Disponible | Construible con CBT, CBA y RIPTE, todos ya extraídos en Vida Cotidiana. |
| Brecha cambiaria | Disponible | Ya implementado como `cepo_mulc` en Gestión (brecha CCL/oficial, dolarapi.com). |
| Resultado fiscal financiero | No implementado | Fuente disponible: Ministerio de Economía, informe mensual de ejecución presupuestaria (PDF). Requiere parser de PDF. |
| Riesgo país (EMBI+) | No implementado | Fuente disponible: serie EMBI+ Argentina vía datos.gob.ar o scraping de Ámbito Financiero. |
| Deuda pública bruta / PBI | No implementado | Fuente disponible: Ministerio de Economía, Oficina de Crédito Público (publicación trimestral). |
| Utilización de capacidad instalada | No implementado | Fuente disponible: INDEC, serie UCI mensual. Pendiente identificación de serie en datos.gob.ar. |
| Formación bruta de capital fijo | No implementado | Fuente disponible: INDEC Cuentas Nacionales trimestrales. |

Las 5 incorporaciones pendientes son técnicamente viables. Las 3 disponibles requieren únicamente exponerlas en el output de macro.

---

## 3. Cinturón de la Política

Script: `scripts/politica.py`. Siete indicadores automáticos y dos con carga manual. Score actual: 4.7 (en tensión). Última corrida: 23 de mayo de 2026, 8 de 9 indicadores frescos (CEPA cayó por error 404 en URL del informe).

### Mapeo de los 10 indicadores propuestos en el documento base

| Indicador del documento base | Estado | Implementación |
|---|---|---|
| Tasa de Eficacia Parlamentaria (TEP) | Automático | `eficacia_legislativa`. Fuente: datos.hcdn.gob.ar (CKAN, proyectos PE vs. sanciones, ventana 12 meses). Valor: 4.8% (1 de 21 proyectos). |
| Ratio DNU | Automático | `ratio_dnu`. Fuente: InfoLeg, sesión POST con conteo de DNUs y leyes del año corriente. Valor: 3.14 (22 DNU / 7 leyes). |
| Índice de Armonía Federal (IAF) | Automático | `iaf_transferencias`. Fuente: Hacienda, CSV serie RON. Mide variación real interanual de transferencias federales. Valor: +1.8% real. |
| Índice de Tensión Social (ITS) | Automático | `movilizacion_cepa`. Fuente: scraping de informes de centrocepa.com.ar. Valor: 46.0. |
| Tasa de Judicialización de la Gestión | No implementable | No existe fuente estructurada de medidas cautelares contra el Ejecutivo. CSJN no publica dataset abierto; juzgados federales requieren scraping caso por caso. Requiere desarrollo separado de scraper jurisprudencial. |
| Control de Agenda (vida media de crisis vía Google Trends) | No implementado | Fuente disponible: pytrends, ya utilizada en cinturón Vida Cotidiana. Requiere definir lista de eventos a trackear y ventana de medición. |
| Tasa de Compromiso RIGI/RIMI provincial-sindical | No implementable | Requiere parseo cualitativo de declaraciones provinciales y sindicales sin formato común. No hay registro oficial de adhesiones. |
| Impacto del Clima Internacional | No implementado | Construible con calendario electoral regional + variación de spreads soberanos (EMBI Latam). Requiere diseño metodológico. |
| Tensión Estructural Discursiva | No implementable | Requiere NLP sobre redes sociales de diputados. Fuera del alcance del proyecto. |
| Independencia del Banco Central | No aplica | Indicador cualitativo sin proxy cuantitativo objetivo. |

### Indicadores adicionales implementados

Se agregaron tres indicadores no listados en el documento base que refuerzan la dimensión legislativa del cinturón:

| Indicador | Fuente | Valor |
|---|---|---|
| `votometro_ventaja_lla` | Votómetro CIGOB, parsing del HTML | +13.3 pp (LLA 41.8 / PJ 28.5, n=11 encuestas) |
| `veto_quorum` | datos.hcdn.gob.ar (CKAN, `REUNION_TIPO` con substring "Fracasada") | 0.0% (0 de 2 sesiones período 144) |
| `comisiones_caidas` | datos.hcdn.gob.ar (CKAN, dictámenes OD vs. sanciones) | 99.6% (519 de 521 sin sanción) |

### Indicadores con carga manual

| Indicador | Razón |
|---|---|
| `cohesion_bloque` | Las votaciones nominales en CKAN HCDN están congeladas en el período 137 (2019). La composición actual del bloque LLA (95 diputados) está disponible pero sin `PERSONA_ID` que mapee a votos históricos. Requeriría headless browser sobre hcdn.gob.ar/votaciones o acuerdo institucional con HCDN. |
| `gobernadores_alineamiento` | Sin fuente pública estructurada. Construible con NLP sobre cobertura periodística (La Nación Data, Infobae) pero requiere proyecto separado. |

---

## 4. Cinturón de Gestión

Script: `scripts/gestion.py`. Doce de doce indicadores con dato (6 automáticos + 4 carga manual + 2 sin fuente). Score actual: 5.9 (en tensión). Última corrida: 23 de mayo de 2026, automáticos frescos 6 de 6.

### Mapeo de los 12 indicadores del documento base

| Eje del documento base | Implementación | Fuente | Estado | Avance |
|---|---|---|---|---|
| Desmantelamiento del cepo | `cepo_mulc` | dolarapi.com, brecha CCL/oficial | Automático | 78.4% (brecha 4.32%) |
| Reducción del Estado | `reduccion_estado` | datos.gob.ar, serie 324.1 (puestos de trabajo sector público) | Automático | 2.7% (variación −0.8%) |
| Reestructuración de organismos | `reestructuracion_organismos` | InfoLeg, sesión POST con `texto="disolucion"` desde diciembre 2023 | Automático | 40.0% (18 normas) |
| Inversiones (RIGI / Super RIGI) | `rigi_inversiones` | InfoLeg, sesión POST con `tipoNorma=3 texto="VPU"` desde julio 2024 | Automático | 28.0% (28 resoluciones VPU) |
| Desregulación normativa | `desregulacion_normativa` | InfoLeg, sesión POST con `texto="deroga"` desde diciembre 2023 | Automático | 55.0% (55 normas) |
| Apertura comercial | `apertura_comercial` | datos.gob.ar, serie 163.3 (importaciones totales, proxy) | Automático | 100.0% (+42.4% i.a.) |
| Concesiones de infraestructura | `concesiones_infraestructura` | manuales.json | Carga manual | 35% |
| Asistencia directa | `asistencia_directa` | manuales.json | Carga manual | 35% |
| Modernización laboral (FAL) | `fal_modernizacion_laboral` | manuales.json | Carga manual | 10% (FAL entra en operación H2 2026) |
| Protocolo antipiquetes | `protocolo_antipiquetes` | manuales.json | Carga manual | 55% |
| Privatizaciones | `privatizaciones` | manuales.json | Sin fuente disponible | 15% |
| Libertad de opción en salud | `libertad_opcion_salud` | manuales.json | Sin fuente disponible | 40% |

### Cálculo del avance

Cada indicador expresa un porcentaje 0–100 que representa el grado de ejecución de la reforma. La conversión a score de tensión es `score = 10 × (1 − avance/100)`: a mayor avance, menor tensión. El score del cinturón es el promedio de los doce.

### Resolución del bloqueo del RIGI

El indicador RIGI se desbloqueó en esta versión del documento. La investigación recorrió las siguientes vías:

| Vía | Resultado |
|---|---|
| Portal oficial argentina.gob.ar/economia/industria/rigi | Devuelve 404. URL cambió sin redirección. |
| Datasets RIGI en CKAN datos.gob.ar | Cero packages. |
| Wikipedia "Régimen de Incentivo para Grandes Inversiones" | Página existe pero última edición de octubre 2025, desactualizada. |
| API JSON Boletín Oficial | Endpoints retornan HTML, no JSON parseable. |
| ComprAR (pliegos de compras del Estado) | ASP.NET con `__VIEWSTATE`, scraping frágil. |
| InfoLeg con `texto="RIGI"` (cualquier tipo de norma) | 93 normas mezcladas. El buscador de InfoLeg realiza búsqueda OR sobre tokens, no permite aislar resoluciones de aprobación. |
| InfoLeg con `texto="adhesion RIGI"` | 164 normas. Confirma que el OR-search infla resultados. |
| InfoLeg con `tipoNorma=3 texto="VPU"` desde julio 2024 | 28 normas. Solución adoptada. |

El término "VPU" (Vehículo de Proyecto Único) es vocabulario técnico exclusivo de la Ley 27.742, presente únicamente en resoluciones de aprobación e implementación del régimen. Calibración: 28 resoluciones VPU corresponden a 16 proyectos aprobados (aproximadamente 1.7 resoluciones por proyecto), equivalente a 28.0% de avance. Este valor coincide con el dato manual de mayo 2026 publicado por El Cronista (28.7%, calculado sobre USD 27.210 millones aprobados sobre USD 94.965 millones totales).

### Indicadores sin fuente disponible

#### `libertad_opcion_salud` (Superintendencia de Servicios de Salud)

Vías intentadas:

| Vía | Resultado |
|---|---|
| Scraping directo sssalud.gob.ar | Devuelve mensaje "No se reportan datos". El sitio implementa fingerprinting de cliente en backend (endpoint `/fwb/first_submit.df`). |
| Playwright (browser real) | Mismo resultado: "No se reportan datos". El bloqueo es a nivel servidor, no de renderizado JS. |
| Datasets datos.gob.ar (Padrón Obras Sociales Nacionales, Financiamiento) | Datasets existen pero los CSV están congelados con `last_modified` 2018-2019. |
| Memorias y publicaciones de SSS | Páginas HTML estáticas, sin estadísticas estructuradas de traspasos post-diciembre 2023. |

**Conclusión:** sin alternativa pública. Carga manual trimestral desde reportes oficiales de SSS cuando se publiquen.

#### `privatizaciones` (transferencia efectiva de acciones)

Vías intentadas:

| Vía | Resultado |
|---|---|
| API Boletín Oficial | Endpoints `lookup/sections` y `lookup/dependencies` retornan HTML, no JSON. |
| ComprAR (pliegos publicados) | ASP.NET con `__VIEWSTATE`, búsquedas requieren mantener sesión y simular formularios complejos. |
| InfoLeg `tipoNorma=2 texto="Aerolíneas"` (Decreto) | 1 norma. Insuficiente como serie. |
| InfoLeg `tipoNorma=3 texto="privatizacion"` (Resolución) | 9 normas, pero OR-search ambiguo: contar normas no equivale a transferencia efectiva de acciones. |
| InfoLeg `tipoNorma=2 texto="transferencia acciones"` (Decreto) | 367 normas. Falso positivo masivo por OR-search. |

**Conclusión:** sin proxy confiable. Carga manual mensual desde anuncios oficiales del Ministerio de Economía.

### Indicadores con carga manual no bloqueados

| Indicador | Fuente potencial | Vía de automatización futura |
|---|---|---|
| Concesiones de infraestructura | Vialidad Nacional, ORSNA — informes PDF trimestrales | Parser de PDF (similar al usado en CICCRA) |
| Asistencia directa | ANSES portal transparencia | Pendiente apertura de API pública por ANSES |
| Modernización laboral (FAL) | MTEySS, ARCA, ANSES | Implementable cuando FAL entre en operación (H2 2026) |
| Protocolo antipiquetes | Ministerio de Seguridad | Requeriría acuerdo institucional o relevamiento propio |

---

## Apéndice — Patrones técnicos consolidados

### Sesión POST en InfoLeg

Patrón compartido entre `politica.py` (`fetch_ratio_dnu`) y `gestion.py` (`fetch_desregulacion_normativa`, `fetch_reestructuracion_organismos`, `fetch_rigi_inversiones`). Requiere:

1. `GET` a la home de InfoLeg para obtener el `jsessionid`.
2. Extraer la URL de acción del formulario con regex sobre el HTML.
3. `POST` con `tipoNorma`, `texto`, rango de fechas, manteniendo la sesión.
4. Parsear el conteo con regex `r"Encontradas?[:\s]+(\d+)"`.

**Limitación clave:** el campo `texto` realiza búsqueda OR sobre tokens, no búsqueda exacta. Para aislar normas específicas debe usarse vocabulario técnico exclusivo del régimen buscado (caso "VPU" para RIGI).

### CKAN HCDN

Patrón en `politica.py` para `eficacia_legislativa`, `veto_quorum` y `comisiones_caidas`. Limitaciones documentadas:

- El parámetro `q=` realiza búsqueda full-text por tokens, no substring (`q="HCDN144"` no matchea `HCDN144R02`).
- Filtros por campo exacto con caracteres acentuados fallan por encoding. Filtrar siempre del lado Python con `.lower()`.
- El campo `dictámenes.EXPEDIENTE` permite join directo con `movimientos.PROYECTO_ID`.
- El número de período legislativo se calcula como `144 + (año_actual − 2026)`.

### datos.gob.ar series API

Patrón estándar: `https://apis.datos.gob.ar/series/api/series/` con parámetros `ids`, `format=json`, `limit`, `sort=desc`. Ocho series INDEC en uso distribuidas en macro, gestión y vida cotidiana.

### BCRA API v4.0

Requiere `verify=False` + `urllib3.disable_warnings()` por configuración SSL del servidor. Los datos vienen en orden descendente: `detalle[0]` es siempre el dato más reciente.
