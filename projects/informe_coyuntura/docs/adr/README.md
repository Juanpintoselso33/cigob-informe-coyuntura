# Architecture Decision Records (ADRs) — Informe de Coyuntura

Registro de las **decisiones de diseño y metodología** del proyecto. Cada ADR
documenta una decisión, su contexto, las opciones que se consideraron (incluidas
las descartadas, para no volver a investigarlas) y sus consecuencias.

## ¿Buscás qué rige hoy?

Este registro responde **por qué** se decidió cada cosa y **cuándo**: son 165
documentos y no se leen de corrido. Para saber qué mide cada cinturón hoy —con
qué pesos, con qué anclas y qué decisiones siguen abiertas— están los
**[manuales metodológicos](../manuales/README.md)**, que se generan de este
registro y del código que corre.

## Formato

Los ADR siguen **MADR v4** en castellano. Cada archivo abre con frontmatter YAML
legible por máquina y sigue con este esqueleto de secciones:

    ## Contexto y planteo del problema
    ## Factores de decisión          (opcional)
    ## Opciones consideradas
    ## Decisión
    ### Consecuencias
    ### Confirmación                 (el test o gate que la comprueba)
    ## Pros y contras de las opciones (opcional)
    ## Más información               (precedentes, limitaciones, lo demás)

En el frontmatter, `estado` usa un vocabulario cerrado —`aceptado`,
`rechazado`, `superado`, `parcial`, `propuesto`— y el matiz va en
`nota_estado`. **Los identificadores de ADR van siempre entre comillas**
(`id: '0012'`, `relacionado: ['0036']`): sin comillas, YAML 1.1 los lee como
octal y la referencia cambia de destino en silencio.

Los números de ADR son identificadores estables: se citan más de 1.300 veces
desde `scripts/`, `tests/`, la web y artefactos generados. **No se renumeran.**

## Herramientas

    python scripts/adr_coherencia.py    # cierra relaciones y regenera este índice
    python -m pytest tests/test_adr_format.py

`adr_coherencia.py` escribe el reverso de cada relación —si 0061 supersede a
0050, 0050 declara `superado_por: ['0061']`— y regenera el índice de abajo.
El índice **no se edita a mano**; el test comprueba que coincida con los
archivos.

Los ADR son inmutables en su decisión: si se revierte, se crea un ADR nuevo que
*supersede* al anterior, no se reescribe el viejo.

## Índice

> Generado por `scripts/adr_coherencia.py` a partir del frontmatter de
> cada ADR. No editar a mano: `tests/test_adr_format.py` comprueba que
> esta tabla coincida con los archivos.

### Macro (ITCM)

| # | Decisión | Indicadores | Estado |
|---|---|---|---|
| [0002](0002-rem-equivalente-mensual.md) | El REM se puntúa por su equivalente mensual (raíz-12), no por nivel absoluto | `rem_ipc_12m` | vigente |
| [0003](0003-recaudacion-interanual-real.md) | La recaudación se mide en variación interanual REAL (deflactada) | `recaudacion` | vigente |
| [0004](0004-financiamiento-indice-capacidad-prestable.md) | La dimensión de financiamiento usa el Índice de Capacidad Prestable (IdC) | `idc` | superado por [0028](0028-idc-z-scores.md) |
| [0005](0005-reservas-netas-a-secas.md) | Reservas: netas "a secas" calculadas de la planilla SDDS + Tesoro + Bopreal | `reservas_bcra` | vigente |
| [0008](0008-tcrm-itcrm-bcra.md) | El TCRM usa el ITCRM oficial del BCRA, no la serie discontinuada de INDEC |  | vigente |
| [0009](0009-idm-y-tcrm-en-el-itcm.md) | Índice de Desequilibrio Monetario (real-real i.a.) y el TCRM como 5ª dimensión del ITCM |  | vigente |
| [0010](0010-capitulo-inversion-iai-icip.md) | Capítulo Inversión: IAI (físico) e ICIP (digital) como 6ª dimensión del ITCM | `iai`, `icip` | vigente |
| [0022](0022-credito-real-y-contexto-oculto.md) | Crédito privado real al ITCM; los monetarios nominales quedan ocultos |  | vigente |
| [0027](0027-auditoria-idc-rediseno.md) | Auditoría adversarial del IdC: hallazgos y opciones de rediseño | `idc` | vigente |
| [0028](0028-idc-z-scores.md) | IdC rediseñado: z-scores de nivel contra la propia historia | `idc` | vigente |
| [0029](0029-recaudacion-promedio-movil-3m.md) | Recaudación real: promedio móvil de 3 meses sobre IPC cerrado | `recaudacion` | vigente |
| [0053](0053-transparencia-y-agregados-monetarios-idm.md) | Transparencia y agregados monetarios del IDM | `idm` | vigente |
| [0054](0054-dolarizacion-depositos-itcm.md) | Dolarización de depósitos como indicador del ITCM |  | superado por [0055](0055-presion-dolarizacion-carteras-itcm.md) |
| [0055](0055-presion-dolarizacion-carteras-itcm.md) | Presión de dolarización de carteras sensible al régimen cambiario |  | vigente |
| [0056](0056-suavizado-ajuste-automatico-saldo-comercial.md) | Suavizado del ajuste automático de saldo comercial por composición expo/impo | `saldo_comercial_12m` | vigente |
| [0057](0057-canal-informal-cripto-presion-dolarizacion.md) | Canal informal (dólar cripto) en la presión de dolarización | `presion_dolarizacion` | vigente |
| [0071](0071-costo-financiamiento-tesoro.md) | costo_financiamiento_tesoro: el precio del financiamiento soberano entra al ITCM | `costo_financiamiento_tesoro` | vigente |
| [0072](0072-resultado-primario-dimension-fiscal.md) | resultado_primario: la dimensión fiscal pasa a medir resultado, no ingresos | `resultado_primario`, `recaudacion` | vigente |
| [0073](0073-tcrm-regla-anti-salto.md) | Regla anti-salto para el TCRM: **RECHAZADA** | `tcrm` | rechazado |
| [0074](0074-rebalanceo-idc-credito.md) | El crédito otorgado deja de pesar un tercio de la capacidad de prestar | `idc`, `credito_privado` | vigente |
| [0075](0075-redundancia-interna-itcm.md) | Se publica cuánta información distinta aporta cada componente del ITCM |  | vigente |
| [0076](0076-ipi-segunda-senal-actividad.md) | La dimensión de actividad deja de colgar de un único dato | `ipi_manufacturero`, `emae_ia` | vigente |
| [0077](0077-ipc-nucleo-serie-acompanante.md) | El IPC general se lee junto al núcleo | `ipc_total`, `ipc_nucleo` | vigente |
| [0078](0078-error-compartido-del-deflactor.md) | El error del deflactor deja de tratarse como independiente |  | vigente |
| [0079](0079-peso-del-ipi-en-actividad.md) | El IPI baja de 35% a 20%: es respaldo, no medida principal | `ipi_manufacturero`, `emae_ia` | vigente |
| [0080](0080-cuenta-corriente-contexto-saldo-comercial.md) | La cuenta corriente acompaña al saldo comercial, y el texto público se corrige | `saldo_comercial_12m`, `cuenta_corriente` | vigente |
| [0083](0083-presion-dolarizacion-maximo.md) | La presión de dolarización pasa a ser el máximo de sus dos canales | `presion_dolarizacion` | vigente |
| [0084](0084-reservas-en-meses-de-importaciones.md) | Reservas en meses de importaciones: **RECHAZADO**, con la condición para revisarlo | `reservas_bcra` | rechazado |
| [0106](0106-linea-de-base-diciembre-2023.md) | El ITCM publica su punto de partida |  | vigente |
| [0120](0120-el-itcm-declara-el-origen-de-sus-bandas.md) | El ITCM declara el origen de sus bandas, y baja del 83% al 38% de circularidad |  | vigente |
| [0122](0122-riesgo-sistemico-del-deflactor-ipc.md) | El riesgo sistémico del deflactor IPC, declarado en la metodología | `ipc_total` | vigente |
| [0124](0124-la-actividad-se-mide-tambien-en-amplitud.md) | La actividad se mide también en amplitud: entra la difusión sectorial del EMAE | `emae_difusion`, `actividad` | vigente |
| [0127](0127-la-recaudacion-mide-la-base-imponible-no-la-caja.md) | La recaudación mide la base imponible, no la caja: pasa a DGI | `recaudacion`, `resultado_primario` | vigente |
| [0152](0152-la-recaudacion-mide-nivel-no-variacion.md) | La recaudación pasa a medir NIVEL, y suma los impuestos provinciales |  | vigente |
| [0158](0158-validacion-del-itcm-por-puntos-de-giro.md) | El ITCM se valida por puntos de giro, no sólo por correlación |  | vigente |

### Política (ITCP)

| # | Decisión | Indicadores | Estado |
|---|---|---|---|
| [0012](0012-reconstruccion-series-historicas.md) | Reconstrucción de series históricas para indicadores sin histórico (backfill) |  | vigente |
| [0036](0036-itcp-parametrica-politica.md) | ITCP: el cinturón de política se puntúa con la paramétrica de 5 dimensiones (decisión editorial, sin doc CIGOB) |  | vigente |
| [0037](0037-cohesion-bloque-scraping-bloqueado-antibot.md) | cohesion_bloque: scraping directo implementado y correcto, pero bloqueado en producción por detección de bots de HCDN | `indice_rice`, `es_bloque_lla`, `fetch_cohesion_bloque` | superado por [0040](0040-cohesion-bloque-diputados-desbloqueo-pdf.md) |
| [0038](0038-alineamiento-senadores-recalibracion-bandas.md) | alineamiento_senadores_prov: recalibración de anclas ITCP con backfill mensual real | `fetch_alineamiento_senadores_actas_anio`, `fetch_alineamiento_senadores_prov_mensual` | vigente |
| [0039](0039-cohesion-bloque-senado-recalibracion-bandas.md) | cohesion_bloque_senado: recalibración de anclas ITCP con backfill mensual real | `fetch_cohesion_bloque_senado_actas_anio`, `fetch_cohesion_bloque_senado_mensual` | vigente |
| [0040](0040-cohesion-bloque-diputados-desbloqueo-pdf.md) | cohesion_bloque (Diputados): desbloqueado vía endpoint PDF directo, sin evadir el anti-bot de la SPA | `fetch_cohesion_bloque_diputados_actas_anio`, `fetch_cohesion_bloque` | vigente |
| [0041](0041-cohesion-bloque-diputados-cache-permanente-y-serie-mensual.md) | cohesion_bloque (Diputados): caché permanente por acta y serie mensual real | `fetch_cohesion_bloque_diputados_actas_anio`, `fetch_cohesion_bloque`, `fetch_cohesion_bloque_diputados_mensual` | vigente |
| [0042](0042-cohesion-bloque-diputados-recalibracion-bandas.md) | cohesion_bloque (Diputados): recalibración de bandas ITCP con backfill mensual real |  | vigente |
| [0043](0043-protestas-caba-recalibracion-bandas.md) | protestas_caba: recalibración de bandas ITCP con la serie ACLED ya existente |  | vigente |
| [0044](0044-adhesion-reformas-provincial-serie-mensual.md) | adhesion_reformas_provincial: serie mensual real vía investigación manual de fechas provinciales | `fetch_adhesion_reformas_provincial_serie`, `adhesion_reformas_provincial` | vigente |
| [0045](0045-comisiones-caidas-recalibracion-bandas.md) | comisiones_caidas: recalibración de bandas ITCP (saturación en espejo) |  | vigente |
| [0046](0046-derrotas-legislativas-itcp.md) | `derrotas_legislativas`: nuevo indicador del ITCP (vetos insistidos + decretos rechazados, fusionados) | `fetch_derrotas_legislativas`, `fetch_derrotas_legislativas_mensual` | vigente |
| [0047](0047-rotacion-gabinete-itcp.md) | rotacion_gabinete: la rotación ministerial entra al ITCP (pata ejecutiva de cohesión interna) | `fetch_rotacion_gabinete`, `cohesion_interna`, `fetch_rotacion_gabinete_serie` | vigente |
| [0048](0048-revision-editorial-cinturon-politica.md) | Revisión editorial del cinturón política: rotación y protestas a contexto, cohesión fusionada en un compuesto bicameral |  | vigente |
| [0050](0050-eficacia-legislativa-recalibracion-bandas.md) | `eficacia_legislativa`: recalibración de bandas contra la serie real (truncamiento estructural de la ventana única) |  | superado por [0061](0061-eficacia-legislativa-cohorte-madura.md) |
| [0052](0052-conflictividad-nacional-acled.md) | Conflicto social del ITCP: `conflictividad_nacional` (ACLED país entero) reemplaza a `movilizacion_cepa` |  | vigente |
| [0058](0058-ratio-dnu-ventana-movil-12m.md) | ratio_dnu: ventana móvil de 365 días (reemplaza al acumulado del año calendario) | `ratio_dnu`, `poder_legislativo` | vigente |
| [0059](0059-ratio-dnu-no-recalibrar-anclas.md) | ratio_dnu: se revierte la recalibración de anclas de ADR-0058 | `ratio_dnu` | vigente |
| [0060](0060-generar-informe-recalcula-indices-desde-crudo.md) | generar_informe.py recalcula ITCM/ITCG/ITCP desde los valores crudos, no confía en el caché del colector |  | vigente |
| [0061](0061-eficacia-legislativa-cohorte-madura.md) | eficacia_legislativa: cohorte madura en vez de ventana compartida, anclas contra benchmark histórico externo | `eficacia_legislativa`, `poder_legislativo` | vigente |
| [0062](0062-eficacia-legislativa-fuente-leyes-sancionadas.md) | eficacia_legislativa: numerador desde leyes-sancionadas (la sanción del Senado era invisible) y denominador sin comunicaciones administrativas | `eficacia_legislativa` | superado por [0061](0061-eficacia-legislativa-cohorte-madura.md) |
| [0063](0063-eficacia-legislativa-expedientes-jgm.md) | eficacia_legislativa: los expedientes JGM (Jefatura de Gabinete) son del Ejecutivo — el Presupuesto era invisible | `eficacia_legislativa` | vigente |
| [0064](0064-comisiones-caidas-contexto-oculto.md) | comisiones_caidas sale del ITCP a seguimiento interno (fuente ciega a las sanciones del Senado) | `poder_legislativo` | vigente |
| [0065](0065-iaf-transferencias-deflactor-promedio.md) | iaf_transferencias: deflactor promedio anual (el dic-dic subdeflactaba sumas anuales) | `iaf_transferencias` | vigente |
| [0066](0066-iaf-transferencias-solo-provincias.md) | iaf_transferencias: el CSV RON incluye la porción del Tesoro Nacional y la ANSES — se filtra a provincias | `iaf_transferencias` | vigente |
| [0069](0069-bloqueo-sostenido-indicador.md) | bloqueo_sostenido: la cara ganada del pulso legislativo entra al ITCP | `bloqueo_sostenido` | vigente |
| [0070](0070-eficacia-mascara-era-validacion.md) | máscara de era para eficacia_legislativa en la reconstrucción del ITCP | `eficacia_legislativa` | vigente |
| [0082](0082-un-solo-camino-al-puntaje.md) | Un solo camino del valor crudo al puntaje |  | vigente |
| [0085](0085-redundancia-en-los-tres-indices.md) | La redundancia interna se mide en los tres índices, y en cambios además de niveles |  | vigente |
| [0088](0088-dimension-sector-privado.md) | El ITCP incorpora una dimensión de sector privado | `sector_privado`, `brecha_obra_publica` | vigente |
| [0089](0089-desafios-en-lugar-de-derrotas.md) | Desafíos legislativos en lugar de derrotas legislativas | `poder_legislativo`, `desafios_legislativos`, `derrotas_legislativas` | vigente |
| [0090](0090-que-pregunta-responde-el-ratio-dnu.md) | Qué pregunta responde el ratio DNU (y por qué no se agrega "éxito por decreto") | `ratio_dnu` | vigente |
| [0091](0091-veto-quorum-contaba-mal-el-fracaso.md) | El indicador de quórum contaba mal el fracaso | `veto_quorum` | vigente |
| [0092](0092-el-informe-declara-su-propio-rezago.md) | El informe declara de cuándo es la foto que muestra |  | vigente |
| [0093](0093-la-dimension-federal-dice-que-no-mide.md) | La dimensión federal declara lo que no mide | `alianzas_territoriales`, `alineamiento_senadores_prov`, `iaf_transferencias` | vigente |
| [0094](0094-lectura-por-partes-del-itcp.md) | El ITCP se puede leer por partes: tensión, capacidad y recursos |  | vigente |
| [0095](0095-la-brecha-cambia-de-signo-segun-el-gobierno.md) | La brecha de obra pública cambia de signo según el gobierno | `brecha_obra_publica` | vigente |
| [0099](0099-el-indice-declara-de-que-fecha-es-cada-dato.md) | El índice declara de qué fecha es cada dato |  | vigente |
| [0117](0117-deriva-en-los-otros-indices.md) | Los otros tres índices: sólo el ITCG tenía deriva |  | vigente |
| [0121](0121-itcg-e-itcp-declaran-el-origen-de-sus-bandas.md) | El ITCG y el ITCP declaran el origen de sus bandas; los tres convergen en ~40% |  | vigente |
| [0126](0126-el-itcp-abre-la-dimension-poder-judicial.md) | El ITCP abre la dimensión del Poder Judicial | `poder_judicial`, `cobertura_judicial` | vigente |
| [0131](0131-protocolo-de-codificacion-para-el-bloque-judicial.md) | SAIJ es automatizable, contar no: el protocolo de codificación |  | vigente |
| [0132](0132-conflictividad-nacional-de-donde-viene-y-sobre-que-actua.md) | Conflictividad nacional: de dónde viene y sobre qué actúa | `conflictividad_nacional`, `conflicto_social` | vigente |
| [0134](0134-paralisis-de-denuncias-la-fuente-sirve-y-el-dato-contradice-la-hipotesis.md) | Parálisis de denuncias: la fuente sirve, y el dato contradice la hipótesis |  | vigente |
| [0135](0135-cautelares-judicializacion-si-bloqueo-no.md) | Cautelares: judicialización sí, bloqueo cautelar no |  | vigente |
| [0136](0136-apoyo-publico-de-camaras-el-problema-es-a-quien-le-hablan.md) | Apoyo público de las cámaras: el problema es a quién le hablan | `sector_privado` | vigente |
| [0137](0137-agenda-comun-el-cociente-se-mueve-por-el-denominador.md) | Agenda común: el cociente se mueve por el denominador | `poder_legislativo` | vigente |
| [0138](0138-exito-corporativo-y-velocidad-el-sumario-no-tiene-los-campos.md) | Éxito corporativo y velocidad: el sumario no tiene los campos |  | vigente |
| [0139](0139-correccion-tres-imposibles-que-no-lo-eran.md) | Corrección: tres "imposibles" que no lo eran | `sector_privado` | vigente |
| [0140](0140-el-dato-existe-y-esta-mejor-modelado-de-lo-que-suponiamos.md) | El dato existe y está mejor modelado de lo que suponíamos |  | vigente |
| [0141](0141-detector-de-novedades-judiciales-de-la-csjn.md) | Detector de novedades judiciales de la CSJN |  | vigente |
| [0144](0144-el-piloto-de-concursos-corrobora-cobertura-judicial.md) | El piloto de concursos corrobora la cobertura judicial | `cobertura_judicial` | vigente |
| [0145](0145-apoyo-empresario-la-fuente-sirve-la-metrica-no.md) | Apoyo empresario: la fuente sirve, la métrica no | `sector_privado`, `apoyo_empresario` | vigente |
| [0146](0146-reglamentacion-irrazonable-si-cuenta.md) | «Reglamentación irrazonable» sí cuenta como veto de constitucionalidad |  | vigente |
| [0147](0147-el-universo-de-un-caso-era-un-artefacto.md) | El universo de un caso era un artefacto de la consulta |  | vigente |
| [0148](0148-apoyo-empresario-con-uia-la-metrica-funciona.md) | Apoyo empresario: con UIA, la métrica funciona | `sector_privado`, `apoyo_empresario` | vigente |
| [0149](0149-detector-de-postura-empresaria.md) | Detector de postura empresaria | `sector_privado`, `apoyo_empresario` | vigente |
| [0150](0150-apoyo-empresario-entra-al-itcp.md) | Apoyo empresario entra al ITCP, y el bug que lo encontró | `sector_privado`, `apoyo_empresario` | vigente |
| [0151](0151-el-corpus-estaba-truncado-y-la-codificacion-se-rehace.md) | El corpus estaba truncado: `apoyo_empresario` se recodifica entero | `sector_privado`, `apoyo_empresario` | vigente |
| [0159](0159-validacion-por-panel-para-los-socioeconomicos.md) | Validación por panel para los compuestos socioeconómicos |  | vigente |
| [0161](0161-el-contraste-externo-es-un-factor-comun-no-una-variable.md) | El contraste externo es un factor común, no una variable suelta |  | vigente |
| [0166](0166-regla-de-orientacion-para-indicadores-de-control.md) | La orientación de un indicador sale de la pregunta que responde |  | vigente |

### Gestión (ITCG)

| # | Decisión | Indicadores | Estado |
|---|---|---|---|
| [0006](0006-brecha-cambiaria-ccl-mayorista.md) | La brecha cambiaria (cepo_mulc) se mide CCL/mayorista, no CCL/oficial-minorista | `cepo_mulc` | vigente |
| [0011](0011-rigi-plataforma-oficial.md) | El RIGI se mide desde la plataforma oficial (inversión aprobada/pipeline), no por conteo de normas |  | vigente |
| [0013](0013-itcg-parametrica-gestion.md) | ITCG: el cinturón de gestión se puntúa con la paramétrica de 5 dimensiones (doc 260702) |  | superado por [0021](0021-interpolacion-y-apertura-sin-brecha.md) |
| [0014](0014-piquetes-poller-gtfs-rt.md) | Piquetes: poller GTFS-RT acumulativo (el registro de cortes del GCBA está muerto) |  | vigente |
| [0015](0015-tdps-presupuesto-abierto.md) | TDPS: la asistencia directa se verifica contra la ejecución presupuestaria (API Presupuesto Abierto) |  | vigente |
| [0016](0016-concesiones-contratar-salud-sss.md) | Concesiones vía CONTRAT.AR + opción en salud vía padrones SSS (últimos manuales automatizados) |  | vigente |
| [0017](0017-protestas-acled.md) | Protestas en CABA vía ACLED (contexto): la protesta no bajó, los cortes sí |  | superado por [0051](0051-gestion-contexto-oculto.md) |
| [0019](0019-revision-metodologica-parametricas.md) | Revisión metodológica de las tres paramétricas (ITCM · ITCG · ITVC) |  | parcial |
| [0021](0021-interpolacion-y-apertura-sin-brecha.md) | Puntaje interpolado en ITCM/ITCG y apertura comercial sin brecha | `apertura_comercial` | vigente |
| [0023](0023-litigiosidad-al-itcg.md) | Litigiosidad SRT al ITCG; protestas y alertas siguen de contexto |  | vigente |
| [0025](0025-protocolo-diagnostico-politico.md) | Protocolo antipiquetes automatizado con Diagnóstico Político (y corrección 55 → 74,2) | `protocolo_antipiquetes` | vigente |
| [0026](0026-irpc-mensual-gdelt.md) | Mensualización del IRPC: forma GDELT calibrada a anclajes DP |  | rechazado |
| [0031](0031-validacion-cruzada-tercer-pilar.md) | Tercer pilar de robustez: validación cruzada (matriz discriminante) |  | vigente |
| [0051](0051-gestion-contexto-oculto.md) | Gestión: las cards de contexto salen del tablero (regla pareja en los 5 cinturones) |  | vigente |
| [0068](0068-fal-regimen-ley-27802.md) | fal_modernizacion_laboral: la consulta al BO contaba el régimen de la construcción — se re-apunta al FAL de la Ley 27.802 | `fal_modernizacion_laboral` | vigente |
| [0086](0086-serie-y-banda-tienen-que-medir-lo-mismo.md) | La serie de un indicador tiene que medir lo mismo que puntúa su banda | `rigi_inversiones`, `validacion_externa` | vigente |
| [0087](0087-preadjudicado-no-es-adjudicado.md) | "Preadjudicado" contiene "Adjudicado" | `concesiones_infraestructura` | vigente |
| [0096](0096-desregulacion-cuenta-normas-no-menciones.md) | Desregulación: contar normas derogadas, no menciones de una palabra | `desregulacion_normativa` | vigente |
| [0097](0097-que-universo-mide-la-dotacion-del-estado.md) | Qué universo mide la dotación del Estado | `reduccion_estado` | vigente |
| [0098](0098-fal-en-tres-etapas.md) | El FAL se mide en tres etapas: construcción, vigencia y adopción | `fal_modernizacion_laboral` | vigente |
| [0100](0100-promesa-cumplida-no-es-contexto.md) | Una promesa cumplida no es un indicador de contexto | `asistencia_directa`, `social_orden`, `cumplido` | vigente |
| [0101](0101-privatizaciones-publica-la-norma-de-cada-etapa.md) | Privatizaciones publica la norma que respalda cada etapa | `privatizaciones` | vigente |
| [0102](0102-rigi-denominador-movil.md) | El RIGI avisa cuando su porcentaje baja por el denominador | `rigi_inversiones` | vigente |
| [0125](0125-la-desregulacion-pasa-a-la-fuente-oficial.md) | La desregulación pasa a medirse con la fuente oficial | `desregulacion_normativa` | vigente |
| [0128](0128-fuerzas-en-la-dotacion-y-peso-del-fal.md) | Las fuerzas están en la dotación, y el FAL baja a la mitad de su dimensión | `reduccion_estado`, `reforma_laboral` | vigente |
| [0129](0129-detector-de-novedades-de-privatizaciones.md) | Privatizaciones: se automatiza la detección, no la clasificación | `privatizaciones` | vigente |
| [0142](0142-el-fal-mide-sus-dos-actos-fundamentales.md) | El FAL mide sus dos actos fundamentales | `fal_modernizacion_laboral` | vigente |
| [0143](0143-la-desregulacion-se-mide-en-articulos.md) | La desregulación se mide en artículos, no en normas | `desregulacion_normativa` | vigente |
| [0164](0164-familia-del-itcg-la-respuesta-del-capital-privado.md) | Familia del ITCG: la respuesta del capital privado |  | vigente |

### Vida cotidiana (ITVC)

| # | Decisión | Indicadores | Estado |
|---|---|---|---|
| [0018](0018-itvc-parametrica-vida-cotidiana.md) | ITVC-B100: paramétrica base 100 del cinturón de Vida Cotidiana |  | vigente |
| [0024](0024-motos-movil-12m-estacionalidad.md) | Motos por acumulado móvil de 12 meses (auditoría de estacionalidad) |  | vigente |
| [0032](0032-inseguridad-ivi-mensual.md) | Inseguridad: del SNIC anual al IVI mensual (LICIP-UTDT) | `inseguridad` | vigente |
| [0033](0033-itvc-doble-conteo-y-winsorizacion.md) | ITVC: doble conteo salario/comida eliminado y winsorización asimétrica | `ipc_alimentos` | vigente |
| [0034](0034-sentimiento-digital-puntuable.md) | Sentimiento digital: de contexto a componente del ITVC | `sentimiento_digital` | vigente |
| [0067](0067-mora-familias-indicador-propio.md) | la mora de las familias sale del compuesto de endeudamiento y puntúa como indicador propio del ITVC | `endeudamiento_familiar`, `mora_familias` | vigente |
| [0107](0107-vintages-del-itvc.md) | El cinturón de vida cotidiana declara de cuándo es cada dato |  | vigente |
| [0108](0108-redundancia-interna-del-itvc.md) | La redundancia interna se mide también en el ITVC |  | vigente |
| [0109](0109-saturacion-de-la-escala-de-tension.md) | Saturación de la escala de tensión: verificada, no requiere cambio |  | vigente |
| [0110](0110-percepcion-seguridad-y-consumo.md) | La dimensión se llama por lo que tiene adentro | `confianza` | vigente |
| [0111](0111-alquiler-real-entra-al-itvc.md) | El costo del alquiler entra al cinturón; pobreza y expectativas no | `precios`, `alquiler_real`, `itvc_alquiler` | vigente |
| [0112](0112-el-cinturon-mira-hacia-adelante.md) | El cinturón incorpora su primera medida prospectiva | `empleo`, `indice_lider`, `itvc_lider` | vigente |
| [0113](0113-nowcast-de-pobreza.md) | La pobreza se publica, con la única fuente mensual que existe | `pobreza_nowcast`, `utdt_nowcast_pobreza` | vigente |
| [0114](0114-pobreza-oficial-acompana-al-nowcast.md) | La pobreza oficial acompaña al nowcast en el mismo gráfico | `pobreza_nowcast`, `pobreza_indec` | vigente |
| [0115](0115-reorganizacion-de-la-dimension-de-percepcion.md) | La dimensión de percepción se parte en tres | `ingresos`, `percepcion`, `seguridad` | vigente |
| [0116](0116-la-robustez-del-itvc-estaba-vieja.md) | La sección de robustez del ITVC estaba vieja, y ahora avisa |  | vigente |
| [0118](0118-el-indice-y-la-tension-son-dos-escalas.md) | El índice y la tensión son dos escalas, y ahora se dice dónde |  | vigente |
| [0119](0119-pendientes-de-baja-prioridad-vida.md) | Los tres pendientes de baja prioridad del cinturón de vida | `consumo_carne` | vigente |
| [0123](0123-el-itvc-entra-al-registro-de-circularidad.md) | El ITVC entra al registro de circularidad (0%, y por qué) |  | vigente |
| [0130](0130-la-dimension-empleo-pasa-a-medir-empleo.md) | La dimensión de empleo pasa a medir empleo | `empleo_registrado`, `empleo` | vigente |
| [0153](0153-pobreza-entra-al-itvc-y-no-hay-cards-de-contexto.md) | La pobreza entra al ITVC, y la categoría «card de contexto» queda cerrada |  | vigente |
| [0154](0154-endeudamiento-e-indice-lider-salen-del-itvc.md) | Endeudamiento e Índice Líder salen del ITVC; el líder pasa a validar el ITCM |  | vigente |
| [0155](0155-el-ancla-del-itvc-pasa-a-ser-el-consumo-medido.md) | El ancla de validación del ITVC pasa a ser el consumo medido |  | vigente |
| [0160](0160-la-dispersion-del-itvc-se-publica-junto-al-neto.md) | La dispersión del ITVC se publica junto al neto |  | vigente |
| [0163](0163-el-itvc-se-contrasta-contra-volumenes-fisicos-del-hogar.md) | El ITVC se contrasta contra volúmenes físicos consumidos por los hogares |  | vigente |

### Espíritu de época

| # | Decisión | Indicadores | Estado |
|---|---|---|---|
| [0035](0035-indice-expectativa-futuro-emigracion.md) | Índice de intención migratoria: 4º indicador de espíritu_epoca |  | vigente |
| [0049](0049-espiritu-epoca-solo-intencion-migratoria.md) | Espíritu de época: la intención migratoria queda como único indicador del cinturón |  | vigente |

### Transversal

| # | Decisión | Indicadores | Estado |
|---|---|---|---|
| [0001](0001-datos-calculados-no-hardcodeados.md) | Todos los indicadores se calculan de datos oficiales; nunca valores hardcodeados |  | vigente |
| [0007](0007-fichas-explican-concepto-no-fuente.md) | Las fichas de indicador explican QUÉ MIDE, no de dónde sale el dato |  | vigente |
| [0020](0020-flag-dimension-critica.md) | Flag de dimensión crítica: la compensabilidad se señaliza, no se corrige |  | vigente |
| [0030](0030-borde-irregular-mes-comun.md) | Borde irregular: mes común puntuado + dato fresco provisorio |  | vigente |
| [0081](0081-revision-de-bandas.md) | Las recalibraciones no se calendarizan: se detectan |  | vigente |
| [0103](0103-procedencia-de-las-anclas.md) | Cada ancla declara de dónde sale, y el sesgo se vuelve contable |  | vigente |
| [0104](0104-el-out-of-sample-no-resuelve-la-circularidad.md) | El out-of-sample no puede resolver la circularidad, y por qué |  | vigente |
| [0105](0105-regla-de-anclas-nuevas.md) | Regla para las anclas nuevas, con trinquete |  | vigente |
| [0133](0133-una-fuente-demorada-no-tira-abajo-el-pipeline.md) | Una fuente demorada no puede tirar abajo el pipeline |  | vigente |
| [0156](0156-el-texto-publico-no-afirma-el-estado-de-hoy.md) | El texto público no afirma el estado de hoy |  | vigente |
| [0157](0157-guard-de-anclas-de-banda.md) | Guard de anclas de banda, y un mapeo público que estaba mal |  | vigente |
| [0162](0162-aporte-del-indice-por-encima-de-la-tendencia.md) | Aporte del índice por encima de la tendencia (regresión) |  | vigente |
| [0165](0165-una-oracion-por-card-el-desarrollo-aparte.md) | Una oración por card, el desarrollo a un click |  | vigente |
