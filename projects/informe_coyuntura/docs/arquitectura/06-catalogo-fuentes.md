# 06 — Catálogo de fuentes por indicador

El mapa de daños: cuando una fuente cambie o se caiga, acá está qué toca,
cómo llega y qué lo amortigua. Credenciales: solo donde se indica.

> **La fuente de cada indicador la declara su ficha, no esta tabla.** Desde
> ADR-0220 la ficha (`output/fichas/*.md`, publicada en `/metodologia/<id>`)
> es el único lugar que se verifica contra el colector, y
> `tests/test_la_ficha_no_se_queda_atras.py` falla si divergen. Esta página
> es el mapa de daños por familia de fuente; ante una diferencia manda la
> ficha. Revisión de este mapa: 8 de septiembre de 2026. El censo de todos los
> componentes activos está en `docs/auditorias/2026-09-08/indicadores.csv`.

## Macro

| Indicador | Fuente / vía | Frec. y rezago | Notas de resiliencia / ADRs |
|---|---|---|---|
| `ipc_total` | INDEC vía apis.datos.gob.ar (148.3 nivel → % m/m) | mensual, ~2 sem | — |
| `reservas_bcra` | BCRA planilla SDDS + balance consolidado; netas con `data/macro/reservas_netas_pasivos.json` | diaria/mensual | fecha ISO del dato en ficha |
| `idc` | BCRA: BADLAR (v.7), depósitos privados (v.100), préstamos | mensual (mes IPC cerrado) | z-scores vs historia 2017→ (ADR-0028); memo anti rate-limit |
| `emae_ia` | INDEC vía datos.gob.ar | mensual, ~8 sem | validado al decimal vs INDEC |
| `saldo_comercial_12m` | cuadro original ICA vigente + API histórica | mensual, mes siguiente | suma móvil de doce meses consecutivos; composición compara 24 meses; store conserva el cuadro validado (ADR-0275) |
| `recaudacion` | Sec. Hacienda vía datos.gob.ar | mensual, días | media móvil 3m del i.a. real sobre meses con IPC cerrado (ADR-0029); fresco provisorio en detalle |
| `tcrm` | BCRA planilla ITCRM (xlsx) | diaria | + bilaterales Brasil/EEUU/China para el comparado |
| `rem_ipc_12m` | BCRA REM (API monetarias) | mensual | — |
| `desequilibrio_monetario` | BCRA + IPC; matriz monetaria | mensual | reemplaza presión de dolarización; tensión invertida para agregar al ITCM |
| `iai` | INDEC ISAC + ICA bienes de capital | mensual | mes común (ADR-0030), BK provisorio declarado |
| `resultado_primario` | Secretaría de Hacienda | mensual | resultado acumulado 12m sobre ingresos |
| `costo_financiamiento_tesoro` | licitaciones del Tesoro y referencias monetarias | por licitación | ver composición y ventanas en ficha |
| `emae_difusion` | componentes sectoriales del EMAE (INDEC) | mensual | amplitud de la recuperación |
| `ipi_manufacturero` | INDEC IPI manufacturero | mensual | promedio móvil 3m de variaciones interanuales |
| `credito_privado` | BCRA préstamos privados (v.26) + IPC | mensual | nivel a mes cerrado, diario provisorio |

Ocultos (insumos, ADR-0022): base monetaria, depósitos, préstamos nominales, circulante.
IDM e ICIP fueron retirados del índice en agosto; sus referencias históricas no
describen componentes vigentes.

## Gestión

| Indicador | Fuente / vía | Credencial | Notas |
|---|---|---|---|
| `cepo_mulc` | dolarapi.com (CCL vs mayorista) | — | brecha % |
| `apertura_comercial` | ARCA (DEX+DIM) + INDEC ICA + BCRA A3500 | — | alícuota efectiva (ADR-0023) |
| `desregulacion_normativa` | informes oficiales de desregulación | — | artículos acumulados; `reestructuracion_organismos` está suspendido |
| `reduccion_estado` | INDEC dotación APN | — | % vs dic-2023 |
| `gasto_funcionamiento` | Sec. Hacienda IMIG/AIF + IPC | — | var. real vs 2023. `masa_salarial` salía de la misma fuente y dejó de puntuar (ADR-0186) |
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

## Vida cotidiana

Familias de fuente: INDEC y datos.gob.ar (precios, ingresos, empleo, consumo y
construcción) · Secretaría de Trabajo (RIPTE) · BCRA (Informe sobre Bancos e
Informe de Estabilidad Financiera) · SRT (empleadores) · SAGYP (carnes) ·
DNRPA (motorización) · UTDT (confianza y victimización) · Google Trends.
El detalle indicador por indicador, incluida la resiliencia ante faltantes,
está en las fichas. Sentimiento digital está suspendido. Para mora familiar,
el anexo bancario vigente es `informe-bancos-anexo.xlsx`: el enlace antiguo
`InfBanc_Anexo.xlsx` devolvía HTTP 200 con mayo mientras el vigente ya contenía
junio (ADR-0272). Respuesta exitosa no demuestra actualidad.

## Política

Familias de fuente del cinturón, que desde ADR-0036 puntúa con la paramétrica
ITCP: Votómetro CIGOB · InfoLeg y Boletín Oficial (`ratio_dnu`) · ACLED
(`conflictividad_nacional`, que reemplazó a la serie CEPA por ADR-0052) ·
Secretaría de Trabajo (jornadas individuales no trabajadas, ADR-0232) · serie
RON oficial (`iaf_transferencias`) · datos.hcdn.gob.ar y actas del Senado
(eficacia legislativa, comisiones, cohesión de bloque) · elaboración CIGOB con
registro datado (`data/politica/manuales.json`). El detalle indicador por
indicador está en las fichas.

Espíritu de época fue un quinto cinturón —`icc_utdt` y `sentimiento_digital`
compartidos con vida, más `clima_electoral`— y salió del tablero por
ADR-0205.

## Fuentes investigadas y descartadas (con evidencia)

| Fuente | Para | Por qué no | Dónde |
|---|---|---|---|
| GDELT DOC API | protestas mensuales | throttling 429 persistente | ADR-0026 (rechazado, condiciones de reapertura) |
| Bases SAT (Min. Seguridad) | inseguridad mensual | tandas anuales con un año de rezago, solo subconjuntos | ADR-0032 |
| Wikipedia pageviews | sentimiento | colapso 6× post-pánico: detector de eventos | ADR-0034 |
| Conference Board style imputation | ragged edge | datos estimados + revisiones retroactivas | ADR-0030 |
