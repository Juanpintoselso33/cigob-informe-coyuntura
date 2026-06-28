# Reconstrucción de series hacia atrás — auditoría y roadmap

> Para los indicadores sin serie histórica real (política, vida, espíritu, avances de
> gestión), ¿se puede reconstruir el pasado desde una fuente oficial? Esta es la
> auditoría: qué indicador, desde qué fuente, con qué método y qué factibilidad.
> Mientras tanto, TODOS acumulan hacia adelante (`data/historico/indicadores.json`),
> así que aunque no se reconstruya, la serie se arma sola mes a mes.
>
> **Última actualización:** 2026-06-30.

## Convención de factibilidad
🟢 alta (dato histórico disponible, método claro) · 🟡 media (requiere fetch/scrape o
cómputo trimestral) · 🔴 bloqueada (no hay dato histórico) · ✅ hecho.

---

## ✅ Hechas
| Indicador | Fuente / método | Puntos |
|---|---|---|
| `rigi_inversiones` | Inversión aprobada acumulada por fecha de sanción del BO ([ADR-0011](adr/0011-rigi-plataforma-oficial.md)) | 12 |
| `votometro_ventaja_lla` · `clima_electoral` | Brecha LLA−PJ ponderada recalculada mes a mes desde `encuestasRaw` (todos los sondeos desde dic-2023) | 31 |

---

## 🟢 Alta factibilidad — próximas
| Indicador | Cinturón | Fuente | Método |
|---|---|---|---|
| `ipc_alimentos` | Vida | INDEC IPC aperturas | Es una serie INDEC directa → agregar a `descargar_series`. |
| `peso_tarifas` | Vida | INDEC IPC regulados | Idem (ya existe el alias `ipc_regulados`; falta bajar la serie). |
| `mortalidad_pymes` | Vida | INDEC IPI nivel general | Serie INDEC; computar la variación usada (ver caveat de estacionalidad en pendientes). |
| `iaf_transferencias` | Política | CSV RON Hacienda | El CSV ya trae el histórico mensual de transferencias → computar la variación real i.a. por mes. |
| `desregulacion_normativa` | Gestión | InfoLeg ("deroga" desde dic-2023) | Conteo ACUMULADO por fecha de norma (mismo patrón que RIGI). |
| `reestructuracion_organismos` | Gestión | InfoLeg ("disolucion") | Conteo acumulado por fecha. |
| `sentimiento_digital` | Vida · Espíritu | Google Trends | Trends devuelve una **serie temporal**; usar el histórico en vez del último punto. |

---

## 🟡 Media factibilidad
| Indicador | Cinturón | Fuente | Método / fricción |
|---|---|---|---|
| `icc_utdt` | Vida · Espíritu | UTDT | UTDT publica el ICC histórico mensual; scrapear la planilla histórica. |
| `informalidad`, `pluriempleo` | Vida | INDEC EPH | Serie **trimestral**; computar el indicador por trimestre. |
| `brecha_salario_cbt` | Vida | INDEC salarios (RIPTE) + CBT | Derivado de dos series con historia. |
| `endeudamiento_familiar` | Vida | BCRA crédito consumo + IPC | `credito_consumo_serie` ya existe → var real i.a. por mes. |
| `ratio_dnu` | Política | InfoLeg | DNUs / leyes por período (acumulado mensual o anual). |
| `eficacia_legislativa`, `veto_quorum`, `comisiones_caidas` | Política | CKAN HCDN | Recomputar la métrica por período legislativo (los gotchas del CKAN ya están documentados). |
| `reduccion_estado` | Gestión | datos.gob.ar empleo público | Serie trimestral; variación vs Q1-2024 por trimestre. |
| `apertura_comercial` | Gestión | datos.gob.ar importaciones | Serie mensual; variación i.a. por mes. |
| `movilizacion_cepa` | Política | centrocepa.com.ar | Scrapear informes mensuales históricos de conflictividad. |
| `consumo_carne` | Vida | CICCRA / IPCVA | Buscar fuente mensual con histórico. |
| `patentamiento_motos` | Vida | CAFAM API | Verificar si la API expone meses anteriores. |

---

## 🔴 Bloqueadas (sin dato histórico)
| Indicador | Por qué |
|---|---|
| `cohesion_bloque` | Votaciones nominales CKAN congeladas en 2019; LLA no existía. |
| `gobernadores_alineamiento` | Sin fuente estructurada (métrica cualitativa). |
| `inseguridad` (SNIC) | Anual y con el parser roto; sin granularidad mensual. |
| `cepo_mulc` | dolarapi solo da el valor actual; la brecha histórica necesitaría otra fuente CCL. |
| Patentamientos comerciales (IAI) | DNRPA no expone histórico → acumulación hacia adelante (ya activa). |
| `privatizaciones`, `concesiones_infraestructura`, `asistencia_directa`, `fal_modernizacion_laboral`, `libertad_opcion_salud`, `protocolo_antipiquetes` | Carga manual / fuentes bloqueadas (ver `pendientes-datos.md`). |

---

## Orden sugerido
1. ✅ Votómetro (hecho).
2. **INDEC directas de Vida** (`ipc_alimentos`, `peso_tarifas`, `mortalidad_pymes`): bajar la serie y mapearla — son el camino más corto.
3. **`iaf_transferencias`** (el CSV ya trae la historia).
4. **InfoLeg acumulado** (`desregulacion_normativa`, `reestructuracion_organismos`): mismo patrón que RIGI.
5. **`sentimiento_digital`** (histórico de Trends) e **`icc_utdt`** (histórico UTDT).
6. CKAN política + EPH trimestral + resto de gestión.

Las bloqueadas seguirán acumulando hacia adelante; no se pierde dato.
