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
| `ipc_alimentos` · `peso_tarifas` · `mortalidad_pymes` | Variación m/m % reconstruida de la serie índice INDEC (146.3 / 148.3 / 453.1) con `fetch_indec_var_mensual` | 47 c/u |
| `iaf_transferencias` | Variación real i.a. anual (RON Hacienda) deflactada por el **IPC dic-dic oficial de INDEC** (se de-hardcodeó `IPC_ANUAL`, corrigió la card 1,8% → 7,0%) | 9 (anual) |
| `desregulacion_normativa` · `reestructuracion_organismos` | Conteo acumulado de normas InfoLeg ("deroga"/"disolucion") reconsultado a fin de cada mes | 31 / 24 |
| `icc_utdt` (vida + espíritu) | Todas las filas del XLS oficial UTDT (no solo la última), acotado a los últimos 60 meses | 60 |
| `sentimiento_digital` (vida + espíritu) | Serie diaria de Google Trends en la **misma ventana 'today 3-m'** que el live (Trends es relativo al período → ventana más larga re-normaliza; se acota a 3m para no cambiar el valor) | ~90 (diaria) |

> El "último punto = valor live" se verificó indicador por indicador. La variación m/m y
> el conteo InfoLeg corren en cada pipeline (`descargar_series` está en el CI), con
> degradación elegante a la acumulación hacia adelante si la fuente falla.

---

## 🟡 Media factibilidad — próximas
| Indicador | Cinturón | Fuente | Método / fricción |
|---|---|---|---|
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
1. ✅ Votómetro, 3 de Vida (m/m), `iaf_transferencias`, 2 de InfoLeg, `icc_utdt`, `sentimiento_digital` — **todo el 🟢 + Trends/UTDT** (hecho).
2. CKAN política (`eficacia_legislativa`, `veto_quorum`, `comisiones_caidas`) + EPH trimestral (`informalidad`, `pluriempleo`) + `endeudamiento_familiar` (BCRA ya tiene la serie).
3. datos.gob.ar de gestión (`reduccion_estado`, `apertura_comercial`) + scraping CEPA.

Las bloqueadas seguirán acumulando hacia adelante; no se pierde dato.
