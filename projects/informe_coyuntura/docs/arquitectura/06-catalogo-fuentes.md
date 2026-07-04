# 06 — Catálogo de fuentes por indicador

El mapa de daños: cuando una fuente cambie o se caiga, acá está qué toca,
cómo llega y qué lo amortigua. Credenciales: solo donde se indica.
(Los cinturones política y espíritu de época están **pre-barrido**: sus filas
se completarán en detalle cuando pasen por la revisión uno-por-uno.)

## Macro (12 puntuables + 4 nominales ocultos)

| Indicador | Fuente / vía | Frec. y rezago | Notas de resiliencia / ADRs |
|---|---|---|---|
| `ipc_total` | INDEC vía apis.datos.gob.ar (148.3 nivel → % m/m) | mensual, ~2 sem | — |
| `reservas_bcra` | BCRA planilla SDDS + balance consolidado; netas con `data/macro/reservas_netas_pasivos.json` | diaria/mensual | fecha ISO del dato en ficha |
| `idc` | BCRA: BADLAR (v.7), depósitos privados (v.100), préstamos | mensual (mes IPC cerrado) | z-scores vs historia 2017→ (ADR-0028); memo anti rate-limit |
| `emae_ia` | INDEC vía datos.gob.ar | mensual, ~8 sem | validado al decimal vs INDEC |
| `saldo_comercial_12m` | INDEC ICA | mensual, ~4 sem | suma móvil 12m |
| `recaudacion` | Sec. Hacienda vía datos.gob.ar | mensual, días | media móvil 3m del i.a. real sobre meses con IPC cerrado (ADR-0029); fresco provisorio en detalle |
| `tcrm` | BCRA planilla ITCRM (xlsx) | diaria | + bilaterales Brasil/EEUU/China para el comparado |
| `rem_ipc_12m` | BCRA REM (API monetarias) | mensual | — |
| `idm` | BCRA M3 privado + IPC | mensual | brecha i.a. real en pp |
| `iai` | INDEC ISAC + ICA bienes de capital | mensual | mes común (ADR-0030), BK provisorio declarado |
| `icip` | INDEC balanza de servicios + IPI/EIL | mensual | mes común de 3 insumos |
| `credito_privado` | BCRA préstamos privados (v.26) + IPC | mensual | nivel a mes cerrado, diario provisorio |

Ocultos (insumos, ADR-0022): base monetaria, depósitos, préstamos nominales, circulante.

## Gestión (17, todo automatizado — ADR-0025)

| Indicador | Fuente / vía | Credencial | Notas |
|---|---|---|---|
| `cepo_mulc` | dolarapi.com (CCL vs mayorista) | — | brecha % |
| `apertura_comercial` | ARCA (DEX+DIM) + INDEC ICA + BCRA A3500 | — | alícuota efectiva (ADR-0023) |
| `desregulacion_normativa` / `reestructuracion_organismos` | InfoLeg | — | proxy normativo |
| `reduccion_estado` | INDEC dotación APN | — | % vs dic-2023 |
| `gasto_funcionamiento` / `masa_salarial` | Sec. Hacienda IMIG/AIF + IPC | — | var. real vs 2023; candidato a 3m MA (pendiente) |
| `fal_modernizacion_laboral` | CNV (FCI RG 1071/2025) + Boletín Oficial | — | — |
| `litigiosidad_laboral` | SRT serie histórica | — | al índice 70/30 |
| `privatizaciones` | Boletín Oficial + tabla doc CIGOB | — | etapas 0-4 |
| `rigi_inversiones` | plataforma oficial RIGI (MECON) | — | — |
| `concesiones_infraestructura` | CONTRAT.AR (UOC 504) + RFC | — | — |
| `asistencia_directa` | API Presupuesto Abierto (SIDIF) | `PRESUPUESTO_ABIERTO_TOKEN` | TDPS; plan B: ZIPs dgsiaf sin auth; baseline 2023 cacheado |
| `protocolo_antipiquetes` | Diagnóstico Político (monitoreos públicos) | — | store `dp_piquetes.json` |
| `libertad_opcion_salud` | SSS (RNAS/RNEMP) | — | — |
| `alertas_manifestacion` | API Transporte GCBA (serviceAlerts) | `BA_TRANSPORTE_*` | + poll 2×/día (`piquetes-poll.yml`) |
| `protestas_caba` | ACLED (agregado semanal) | `ACLED_*` (cuenta juan@ott.law nivel Open; sonda UBA auto-destrabante en `gestion.py`) | serie completa 2018→ (excepción de ventana) |

## Vida cotidiana (13, todos puntúan — ADR-0034)

| Indicador | Fuente / vía | Frec. | Resiliencia / ADRs |
|---|---|---|---|
| `brecha_salario_cbt` | Sec. Trabajo (RIPTE) + INDEC (CBT) | mensual | mes común; CBT fresca provisoria |
| `ipc_alimentos` | INDEC IPC alimentos | mensual | ITVC: relativo al IPC general (ADR-0033) |
| `peso_tarifas` | INDEC IPC regulados | mensual | relativo al salario |
| `endeudamiento_familiar` | BCRA crédito consumo + Informe sobre Bancos (mora) | mensual | I_EC real×mora; **dimensión crítica** |
| `informalidad` / `pluriempleo` | INDEC EPH (serie 52.2 trimestral) | trimestral | upgrade barrido 2/13 |
| `mortalidad_pymes` | INDEC IPI manufacturero **desestacionalizado** | mensual | card desest (barrido 6/13) |
| `despacho_cemento` | INDEC ISAC desestacionalizado | mensual | — |
| `inseguridad` | **UTDT LICIP — IVI** (PDFs mensuales) | mensual ~1-2m | store `ivi_serie.json`, base declarada ene-2024 (ADR-0032); contraste SNIC anual con store `snic_serie.json` (host frágil) |
| `icc_utdt` | UTDT CIF (xls, requiere `xlrd==1.2`) | mensual | par de validación del ITVC |
| `sentimiento_digital` | Google Trends vía pytrends | mensual (puntaje) + pulso 3m | ventana fija 2021→, store con reemplazo TOTAL (ADR-0034); 429 frecuentes |
| `consumo_carne` | CICCRA (PM-12m) | mensual | store `carne_serie.json` |
| `patentamiento_motos` | CAFAM | mensual, días | móvil 12m (ADR-0024) |

## Política (9, pre-barrido)

Votómetro CIGOB (`votometro_ventaja_lla`, también `clima_electoral` en
espíritu) · InfoLeg (`ratio_dnu`) · CEPA (`movilizacion_cepa`) · serie RON
oficial (`iaf_transferencias`) · datos.hcdn.gob.ar (`eficacia_legislativa`,
`veto_quorum`, `comisiones_caidas`, votaciones para `cohesion_bloque`) ·
elaboración CIGOB con registro datado (`gobernadores_alineamiento`,
`data/politica/manuales.json`).

## Espíritu de época (3, pre-barrido)

Comparte `icc_utdt` y `sentimiento_digital` con vida (⚠️ al cambiar la
semántica de la card se toca este cinturón también) + `clima_electoral`
(Votómetro).

## Fuentes investigadas y descartadas (con evidencia)

| Fuente | Para | Por qué no | Dónde |
|---|---|---|---|
| GDELT DOC API | protestas mensuales | throttling 429 persistente | ADR-0026 (rechazado, condiciones de reapertura) |
| Bases SAT (Min. Seguridad) | inseguridad mensual | tandas anuales con un año de rezago, solo subconjuntos | ADR-0032 |
| Wikipedia pageviews | sentimiento | colapso 6× post-pánico: detector de eventos | ADR-0034 |
| Conference Board style imputation | ragged edge | datos estimados + revisiones retroactivas | ADR-0030 |
