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
| `informalidad` · `pluriempleo` | Tasa INDEC EPH ×100 (`fetch_indec_x100`): 52.1 (anual) y 47.2 (trimestral) | 22 / 40 |
| `endeudamiento_familiar` | Stock nominal de crédito de consumo (BCRA personales 114 + tarjeta 115) en billones = headline (la var real i.a. que puntúa va en el box de score) | 43 |
| `reduccion_estado` · `apertura_comercial` | datos.gob.ar: empleo público vs baseline ≤2024-01 (trim.) e importaciones i.a. (mens.) | 8 / 36 |
| `ratio_dnu` | DNUs/leyes en ventana móvil de 365 días, recalculada al fin de cada mes (InfoLeg; ADR-0058 reemplazó el acumulado anual) | 32 (mensual) |
| `brecha_salario_cbt` | RIPTE / Canasta Básica Total, alineado por mes (el live mezcla meses → último 3,86 vs card 3,79, inmaterial) | 59 |

> El "último punto = valor live" se verificó indicador por indicador. Todo corre en cada
> pipeline (`descargar_series` está en el CI), con degradación elegante a la acumulación
> hacia adelante si la fuente falla.

---

## 🟡 Media factibilidad — restantes (bajo rinde / scraping)
| Indicador | Cinturón | Fuente | Por qué quedó |
|---|---|---|---|
| `eficacia_legislativa` | Política | CKAN HCDN | Ventana móvil 12m recomputable, pero valor bajo (~4%) y reconstrucción CKAN compleja (gotchas). |
| `veto_quorum`, `comisiones_caidas` | Política | CKAN HCDN | **Estructuralmente planos** (0% y ~98%): la serie sería una línea casi constante → poco valor. |
| `movilizacion_cepa` | Política | centrocepa.com.ar | Scraping de informes mensuales históricos; el scraper live además está frágil. |
| `consumo_carne` | Vida | CICCRA / IPCVA | Scraping de informes mensuales; falta fuente histórica estable. |
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

## Estado
**17 indicadores con serie reconstruida** (🟢 completo + casi todo el 🟡). Lo que queda es
de bajo rinde: CKAN `veto_quorum`/`comisiones_caidas` son planos, `eficacia_legislativa`
es complejo y bajo, y `movilizacion_cepa`/`consumo_carne` requieren scraping frágil. Las
🔴 siguen acumulando hacia adelante; no se pierde dato.
