# Pendientes de datos y roadmap de indicadores

> Doc vivo de seguimiento. Registra qué indicadores faltan automatizar, qué datos
> están bloqueados o son de pago, qué se acumula a la espera de histórico, y el
> índice de decisiones (ADRs). **No** es metodología del informe (eso vive en
> `docs/archivo/cinturon_*.md`, diseño original ya archivado): es la lista de trabajo pendiente.
>
> **Última actualización:** 2026-10-10 (§1 y §8 rehechos; §3 a §7 siguen de junio).

---

## 1. Fuentes flojas y sus alternativas (barrido del 10-oct-2026)

Barrido de los **67 indicadores publicados** (snapshot del 10-oct: 60 automáticos, 5
semiautomáticos, 2 manuales), cruzado con dos registros de las corridas nocturnas:

- **BigQuery**: 46 corridas `cron` de los últimos 60 días, contando cuántas noches cada
  card quedó `desactualizado`.
- **Logs de GitHub Actions**: 33 corridas programadas desde el 11-ago, contando cada
  `Usando cache` / `Usando fallback` / `[COTEJO_MANUAL]`.

Vida cotidiana y macro no tienen ninguna card con caídas repetidas: sus rezagos (EPH
trimestral, SNIC anual, IVI con ~3 meses) son de la fuente, no del colector. SAIJ (28 de
33 noches bloqueado) y Google Trends fallan seguido, pero **ya no alimentan ninguna card
publicada** (`judicializacion` y `sentimiento_digital` salieron del tablero).

### Resumen: qué hacer con cada una

| Indicador | Cinturón | Síntoma medido | Causa real | Qué conviene |
|---|---|---|---|---|
| `desafios_legislativos` | Política | Desactualizado 32/46 noches | **Desde el 31-jul ninguna corrida de GitHub lee `votaciones.hcdn.gob.ar`**; sólo se refresca con corridas manuales desde la Mac. Bloqueo por IP: hipótesis, el walk de actas no loguea el código HTTP | Detectar *si hubo* desafío con el índice de sesiones de `hcdn.gob.ar` (llega desde CI) y resolver *cómo terminó* con Senado + InfoLeg. Mínimo ya: loguear el HTTP del walk. **Ojo 15-oct**: sesión especial por el DNU 70/2023 |
| `cobertura_judicial` | Política | Desactualizado 25/46, cotejo manual | Regla `desactualizado = fecha_corte < hoy` + CSV del ministerio «eventuales» (padrón al 5-jun) | Detector de decretos en InfoLeg (ya integrado) para el paso manual; contraste con el mapa de concursos del Consejo; tolerancia de días en la regla |
| `apoyo_empresario` | Política | Desactualizado 16/29, cotejo casi diario | Cada comunicado nuevo de la UIA frena la serie hasta que alguien lo codifica | Primera codificación automática con el manual vigente (LLM, marcada provisoria, auditoría humana). Ampliar a CRA sólo después de medir cuántas notas pasan el filtro |
| `concesiones_infraestructura` | Gestión | Desactualizado 16/46; CONTRAT.AR con timeout 15/33 noches | El colector tira el indicador si CONTRAT.AR no responde, aunque las 4 etapas ya están fechadas por resolución del Boletín | Invertir el orden: store fechado + Boletín como fuente, CONTRAT.AR como detector no fatal |
| `adhesion_reformas_provincial` | Política | Cache 5/33 noches | Re-verifica cada noche dos leyes ya publicadas (Santa Fe, CABA); si el Boletín de CABA no responde (timeout de 30 s hoy) anula las 18 jurisdicciones | Guardar la verificación hecha y no repetirla cada noche; una falla avisa, no anula |
| `iaf_transferencias` | Política | **Resuelto (ADR-0353)**: 12 meses móviles, dato a ago-2026 (−1,8 % real) | Era: el colector sólo aceptaba años completos | Ya no; las bandas no se tocan (misma escala) |
| `produccion_legislativa` | Política | Cache 3/33 noches | Una fila del CKAN sin número de ley aborta el indicador entero | Excluir la fila con aviso; cruzar con InfoLeg |
| `protocolo_antipiquetes` | Gestión | Dato al 2025-12-31 | Diagnóstico Político anual, y su sitio hoy da «Account Suspended» | ACLED Research (cortes en CABA por notas, base 2023 real, ~12 meses de rezago) — cambio de método, lleva ADR |
| `privatizaciones` | Gestión | Manual, revisión al 8-sep | No hay fuente con la etapa por empresa | Detector de CONTRAT.AR UOC 504/2 (ATEP) + hechos relevantes de CNV; la etapa sigue manual |
| `velocidad_resolucion` | Política | Manual, dato 2025 | Anuario de la Corte, anual | Nada que arreglar; sumar el semestre es decisión de método |
| `inseguridad` (IVI) | Vida | Cotejo ocasional, dato a jul-2026 | La UTDT sube los PDF en tandas (~3 meses) | Leer el último mes del HTML del LICIP; fijar `MAX_DIAS` al rezago real |
| `libertad_opcion_salud` | Gestión | 5xx ocasionales | CDN de argentina.gob.ar; cadencia bimestral de la SSS | Reintentos con espera y bajar la URL ya conocida; no hay otra fuente |
| `fal_modernizacion_laboral` | Gestión | Semiautomático, fresco | Normas y estado judicial a mano | Detector de normas en InfoLeg; lo judicial seguirá manual (captcha del PJN) |

**Lo común**: en seis de las trece la fuente funciona y lo que falla es el colector
(anula el indicador ante una falla que no cambia el dato, o descarta datos que ya
tiene). Ninguna de esas seis necesita una fuente nueva.

### Alternativas relevadas, indicador por indicador

Todas las encontradas, incluidas las descartadas con su motivo. «Hasta» es la fecha
del último dato verificada el 10-oct-2026, no la que declara la fuente.

#### `desafios_legislativos`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| Índice de sesiones y versiones taquigráficas de HCDN (`hcdn.gob.ar/sesiones/`) | Sesiones con temario + PDF; HTML | Convocatoria del 21-oct-2026 | Llega desde CI (`veto_quorum` lo lee cada noche) | Sin voto nominal; hay que escribir el parser |
| Votaciones nominales HCDN (`votaciones.hcdn.gob.ar`, la actual) | Actas en PDF | Cache al 9-sep | La mejor calidad | No llega desde CI desde el 31-jul |
| CKAN HCDN `votaciones_nominales` | CSV/JSON | 2019-2020 | API abierta | **Descartada**: congelada |
| CKAN HCDN `resultado-proyectos` | Resultado por expediente | 26-ago-2026 | Llega desde CI | **Descartada** como principal: muy escasa (13 filas ago-oct 2025) |
| Senado, actas de votación | Scraping | Al día | Ya integrada | Sólo media Cámara |
| Datos abiertos del Senado | JSON/Excel | 24-sep-2026 | JSON directo | **Descartada**: no tiene votaciones ni leyes |
| InfoLeg, página de vetos | HTML | Dto. 652/2025 | Lista oficial | Sólo vetos, no insistencias |
| HCDN DIP, «Leyes insistidas 1983-2025» | PDF | 29-oct-2025 | Oficial, sirve de auditoría | Un año atrasado |
| Como_voto (rquiroga7, GitHub) | JSON | 27-ago-2026 | Gratis | Más atrasado que el cache propio, sin licencia, falla en silencio (ADR-0037) |
| DeQuéSeTrata | Web armada en el navegador | No verificado | Puede tener votaciones recientes | Privado, sin API |
| nahuelhds/votaciones-ar-datasets · datar.info | CSV | 2019 · 2015 | — | **Descartadas**: abandonadas |
| Chequeado / Parlamentario / Directorio Legislativo | Notas | — | Contraste | **Descartadas**: no son datos |
| Correr el walk de Diputados fuera de GitHub (Mac/torre) | Las mismas actas | Diario | Mantiene la mejor fuente | Infraestructura propia y máquina prendida |

#### `cobertura_judicial`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| Padrón de magistrados (datos.jus.gob.ar, el actual) | Cargos, vacantes; CSV | Foto del 5-jun | Único censo con denominador | Sale cada varios meses |
| Designaciones / renuncias (datos.jus.gob.ar, el actual) | CSV | 11-sep | Oficial | Un mes de atraso |
| **InfoLeg** (búsqueda en vivo y base mensual) | Decretos de nombramiento y renuncia | Boletín al 30-sep | Automatiza el paso manual; ya integrado | Falta clasificar alta, promoción y traslado |
| Primera sección del Boletín Oficial | HTML/PDF diario | Al día | Primaria | Más cruda que InfoLeg |
| **Mapa de concursos del Consejo de la Magistratura** | CSV: ternas, mensajes al Senado, designaciones | 28-sep (act. 2-oct) | Fresco, embudo completo | Sin renuncias ni vacantes sin concurso: contraste, no denominador |
| Senado, acuerdos con el Poder Judicial | Formulario HTML | No verificado | Captura el paso del Senado | Acuerdo ≠ designación |
| Tablero Tableau de Justicia Abierta | Gráficos | 8-jun | — | **Descartado**: mismos datos que el padrón |
| Traslados de jueces (datos.jus.gob.ar) | CSV | 2022 | — | **Descartado**: muerto |
| ACIJ · indicadores.ar · Infobae · Chequeado | Informes y notas | ago-2026 / mar-2026 | Contraste | **Descartados**: no son datasets o no se actualizan |

#### `velocidad_resolucion`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| Anuario estadístico de la CSJN (el actual) | PDF | 2025 | Oficial | Anual |
| Informe del 1er semestre 2026 de la CSJN (Tableau) | Ingresados y resueltos del semestre | 30-jun-2026 | Un punto cada seis meses | La feria de enero rompe la comparación; la imagen de «resueltos» sale vacía |
| Imágenes estáticas de Tableau por hoja | PNG | 2014-2025 | Reproducible | Exige chequeo aritmético |
| sjconsulta (novedades de fallos) | JSON con cookie | Al día | Diario | **Descartado**: sólo resueltos; el buscador completo tiene CAPTCHA |
| Página de sentencias de la CSJN | — | — | — | **Descartada**: HTTP 500 |
| Estadísticas del Consejo de la Magistratura | PDF | feb-2026 | — | **Descartada**: tribunales inferiores, no la Corte |
| CIJ | Noticias | Al día | — | **Descartado**: sin conteos |

#### `produccion_legislativa`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| CKAN HCDN `leyes-sancionadas` (el actual) | API datastore | Sanción del 24-sep (27.828) | La más fresca | Publica filas sin número |
| Base InfoLeg (datos.jus.gob.ar) | ZIP mensual de 257 MB | Boletín al 30-sep | Contraste independiente | ~3 semanas de atraso (sólo ley publicada) |
| Búsqueda en vivo de InfoLeg | HTML, ya usada | Al día | Llega desde CI | Mismo atraso de publicación |
| CKAN HCDN `leyes-promulgadas` | API | feb-2020 | — | **Descartado**: congelado |
| CKAN HCDN `resultado-proyectos` | API | 26-ago | Contraste posible | Escaso |
| HCDN DIP, leyes de la presidencia Milei | PDF | 28-feb-2026 | Buena auditoría | Siete meses atrasado |
| Datos abiertos del Senado | — | — | — | **Descartado**: no exporta leyes |
| Directorio Legislativo / Parlamentario / Chequeado | Notas | — | — | **Descartados**: no son datos |

#### `apoyo_empresario`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| UIA, comunicados (la actual) | HTML | 5-oct-2026 | Mide lo que dice el rótulo | Codificación manual; una cámara |
| AEA, prensa | PDF | 31-mar-2026 | Ya codificada | **Fuera** (ADR-0334): dejó de publicar |
| CRA, Confederaciones Rurales | HTML, robots permite | Vigente oct-2026 | Cubre el agro | Mucha agenda; parte de la postura va al Congreso o a provincias |
| CONINAGRO | API WordPress | 7-oct-2026 | Fácil de bajar | Pocas posturas sobre el Ejecutivo |
| Grupo de los Seis | Sólo por prensa | feb-2026 | Voz del establishment | Sin repositorio |
| SRA | — | — | — | **Descartada**: robots.txt `Disallow: /` (verificado hoy; ADR-0088 decía lo contrario) |
| CAC, CAME, ADEBA, CAMARCO, COPAL, AmCham | — | — | — | **Descartadas** (ADR-0148): no publican postura, feed muerto o login |
| ICE de LIDE Argentina | PDF trimestral, puntúa la gestión nacional | 2º trim. 2026 | Única encuesta que pregunta por la gestión | Sin archivo de serie ni metodología publicada |
| Vistage, confianza empresaria | PDF trimestral | 2º trim. 2026 | Serie desde 2006 | Mide confianza en los negocios, no postura |
| INDEC, ICE industria | PDF mensual | may-2026 | Oficial | **Descartado** (ADR-0088): clima macro |
| Encuesta de expectativas IDEA · Encuesta del Coloquio | Anual | 2026 | Grandes empresas | Un punto por año |
| Polimetría «Decisores» | Confidencial | jun-2026 | Pertinente | **Descartada**: no es pública |
| GDELT DOC API | JSON | No verificado (límite de pedidos) | Automático | Mide la cobertura de prensa, no lo que dice la cámara; ADR-0026 ya lo rechazó |
| Codificación automática con LLM (no es fuente) | Pipeline | — | Saca la traba; los dos codificadores actuales ya son IA (95 % y 94 % de coincidencia) | Publicar como provisorio y declararlo; clave de API en CI |

#### `adhesion_reformas_provincial`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| MAGyP, provincias adheridas (la actual) | Tabla HTML, 16 provincias | Responde hoy | Estable y rápida | Faltan Santa Fe y CABA; le pone a Tucumán la ley de Santa Cruz (3912) |
| Portal RIGI del Min. Economía | Google Sheet público | 23 proyectos | Abierto | **Descartado**: lista proyectos, no adhesiones |
| Boletín Oficial de CABA (el actual para CABA) | HTML | Timeout hoy | Primaria | Es el host que se cae |
| elDial (espejo de la Ley 6949) | HTML | 28-may-2026 | Segundo host | Privado, puede tener muro |
| SAIJ, legislación provincial | HTML/API | — | Todas las provincias | **Descartado** para CI: bloquea a los runners |
| Boletines de las 6 provincias que faltan | HTML/PDF | No verificado | Ahí aparece primero una adhesión | Seis scrapers para un evento raro |
| Alerta de prensa («adhiere al RIGI») | RSS | — | Barato | Sólo avisa |

#### `iaf_transferencias`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| Hacienda, consolidada mensual (la actual) | XLSX | **sep-2026** | Ya se baja | Nombre de archivo cambiante (resuelto) |
| Hacienda, distribución diaria | XLS, una hoja por provincia | 9-oct-2026 | Casi en tiempo real | Formato complejo |
| OPC, RON a provincias | PDF mensual | ago-2026 | Cotejo oficial | Elaboración, no dato primario |
| OPC, informe trimestral de transferencias | PDF | mar-2026 | Incluye discrecionales | Trimestral |
| Politikon Chaco · IARAF · Fundación Encuentro | Informes mensuales | jul/ago-2026 | Cotejos independientes | Privados |
| API Series de Tiempo (`372.9_GTOS_CORR_017_0_M_51_61`) | JSON | ago-2026 | API estable | Otro universo: no incluye coparticipación |
| Presupuesto Abierto | API con token (ya en `.env`) | Al día | Desagrega discrecionales | No cubre la coparticipación |
| CEPA | PDF | 1er bim. 2026 | Contexto | Irregular |

#### `inseguridad` (IVI)

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| IVI en PDF (la actual) | PDF | jul-2026 | Única mensual nacional con lo no denunciado | Rezago de 2-3 meses |
| IVI en el HTML del LICIP | Texto del último mes | jul-2026 | Evita parsear el PDF | Sólo el último mes |
| Notas de prensa de la UTDT | HTML | 2022 | Texto plano | No sale todos los meses |
| SNIC, base mensual por departamento | CSV | 2025 | Oficial; ya usado | Sólo denuncias, un año tarde |
| Encuesta Nacional de Victimización (INDEC) | Microdatos | 2017 | Muestra enorme | **Descartada**: sin continuidad |
| Encuesta de Victimización de CABA | PDF anual | 2022 | Oficial | **Descartada**: discontinuada |
| Mapa del Delito CABA | CSV anual | dic-2025 | Detallado | Sólo CABA y denuncias |
| Observatorio de Seguridad Pública de Santa Fe | PDF mensual | ago-2026 | Mensual | Una provincia, sólo homicidios |
| ODSA-UCA · Latinobarómetro · LAPOP | Informes / microdatos | No verificado | Series largas | Anuales o bienales |

#### `concesiones_infraestructura`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| Boletín Oficial / InfoLeg (hoy respaldo) | Resoluciones de adjudicación | Res. 1379/2026 (24-ago) | Es el acto jurídico; las 4 etapas ya están | No descubre etapas nuevas |
| Página oficial de la RFC | Km por tramo | Vigente | Estable | No dice el estado |
| CONTRAT.AR (el actual) | Estado de cada proceso | Al día desde una IP residencial (0,18 s) | Estructurado | Timeout desde los runners 15/33 noches (bloqueo por IP: hipótesis) |
| Datos abiertos CONTRAT.AR (CKAN) | CSV | may-2023 | Formato limpio | **Descartado**: congelado |
| «Contratar (histórico)» | XLSX | sep-2019 | — | **Descartado** |
| Secretaría de Obras Públicas | Avisos | Al día | Detector | No es serie |
| Prensa (Infobae, TN) | Notas | 6-oct-2026 | Avisa la Etapa IV (26 tramos identificados, TN 23-sep) | No son actos jurídicos |
| COMPR.AR | — | — | — | **Descartado**: las concesiones de obra no pasan por ahí |

#### `privatizaciones`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| **CONTRAT.AR, UOC 504/2 (ATEP)** | Estado de cada proceso de venta | 10-oct: Comahue adjudicado, CITELEC con contrato, Intercargo desierto, AySA preadjudicado | Estructurado, oficial, ya hay código | No están Belgrano Cargas, Nucleoeléctrica, YCRT ni SOFSE; mismos timeouts |
| Boletín Oficial / InfoLeg (el actual) | Decretos y resoluciones | Al día | Acto primario | No trae la etapa |
| CNV, hechos relevantes | Tabla HTML | 9-oct-2026 | Fechó el cierre de Transener | Sólo empresas que cotizan; ventana corta |
| Página de la ATEP | Lista de empresas | Vigente | Oficial | **Descartada**: no trae estado |
| Secretaría de Obras Públicas | Avisos (Res. 1722/2026, AySA) | Al día | Detector | Sólo lo último |
| Comisión Bicameral de Privatizaciones | Exposiciones | 23-sep | Institucional | No estructurada; URL sin verificar |
| Mapas de Infobae / TN · bplaw · Cronista | Notas | sep-2026 a ago-2025 | Cotejo | Periodísticos, sin conciliar o viejos |

#### `protocolo_antipiquetes`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| **ACLED, eventos (Research, cuenta UBA)** | Cortes en CABA por notas, mensual | oct-2025 | Base 2023 real; automático; ya en el repo (`acled_cortes.json`: 55 → 26 → 17, −69 % vs −74 % de DP) | ~12 meses de rezago; universo chico |
| ACLED, agregado semanal (Open) | Protestas por semana y provincia | 26-sep-2026 | Al día | No tiene subtipo «corte» |
| PIMSA (CONICET) | PDF semestral con «Corte» | 1er sem. 2025 | Académico | Nacional, 5+ meses de rezago |
| FLACSO, Observatorio de Políticas Públicas | PDF anual | dic-2025 | Metodología explícita | Dos diarios; sin cortes de CABA |
| Huella del Sur | Conflictos mensuales | jul-2026 | Reciente | Nacional, sesgo laboral, fuente militante |
| Monitor de Respuestas Represivas · CPM / Amnistía | Informes | 2025 | — | **Descartados**: miden represión, no cortes |
| Observatorio de conflictividad de Mar del Plata | Web | Tiempo real | Automático | **Descartado**: sólo General Pueyrredón |
| Nueva Mayoría · Ministerio de Seguridad | — | — | — | **Descartados**: sin conteos públicos |
| API de tránsito del GCBA (`/transito/v1/cortes`) | — | — | — | **Descartada**: HTTP 500 desde 2026 (ADR-0014) |
| GTFS-RT de alertas (monitoreo propio) | API | 0 alertas en 101 días | Propio | Hoy no capta nada: revisar el filtro |
| Diagnóstico Político (la actual) | Anclajes anuales | 2025 | Es la definición de la Res. 943/23 | Sitio suspendido; el detector va a fallar siempre |

#### `libertad_opcion_salud`

| Fuente | Qué da / acceso | Hasta | Pros | Contras |
|---|---|---|---|---|
| Planillas de la SSS en argentina.gob.ar (la actual) | XLSX | jun-2026 (publicado el 14-ago) | Única oficial con este detalle | 5xx ocasionales de la CDN |
| Sitio viejo de la SSS | — | — | — | **Descartado**: 503 |
| datos.gob.ar, usuarios de prepagas · padrón de obras sociales | CSV | 2018 · 2019 | API CKAN | **Descartados**: congelados |
| Contador de opciones de cambio | — | — | — | **Descartado**: caído (ADR-0016) |
| Resoluciones de la SSS en el Boletín | HTML | Al día | — | Cuenta entidades, no personas |

#### `fal_modernizacion_laboral`

Seguirá semiautomático. Las normas se pueden detectar en InfoLeg (como el detector de
privatizaciones); el estado judicial no tiene fuente estructurada (la consulta del PJN
tiene captcha). Como respaldo de CNV se probó la API de CAFCI: **403**, descartada.

---

## 3. Fuentes bloqueadas / por conseguir

Datos que **no existen como serie automatizable** hoy (investigados a fondo).

| Dato | Para | Por qué está bloqueado | ADR |
|---|---|---|---|
| **Patentamientos comerciales** (camiones + utilitarios) | IAI (inversión física) | DNRPA solo expone el **mes corriente** a nivel registro; el agregado histórico solo trae "Automotores" total. → resuelto por acumulación (§4). | [0010](adr/0010-capitulo-inversion-iai-icip.md) |
| **Hardware hi-tech** (NCM 8471/8517/8542: servers, telecom, circuitos integrados) | ICIP (inversión digital) | El NCM oficial en datos.gob.ar es **solo a 2 dígitos** (capítulo, demasiado amplio) y **~16 meses viejo**. Las posiciones a 8 dígitos solo viven en microdata bulk de Aduana, sin serie. | [0010](adr/0010-capitulo-inversion-iai-icip.md) |
| **Bienes de capital importados por CANTIDAD** | IAI | El índice de cantidad (limpio de precios) es **trimestral**; hoy el IAI usa el valor mensual en USD (`74.3_IIBCA`). Caveat menor. | — |
| Votaciones nominales Diputados (LLA) | `cohesion_bloque` | CKAN congelado en 2019 (ver §1). | — |

---

## 4. Acumulaciones en curso (se completan con el tiempo)

Cuando la fuente no da histórico, se **acumula mes a mes** en un JSON versionado.

| Store | Indicador | Estado | Serie i.a. lista |
|---|---|---|---|
| `data/macro/patentamientos_comerciales.json` | `iai` (3er componente) | Arrancó **2026-05** (12.652 comerciales/mes). `macro.actualizar_patentamientos_comerciales()` upserta un mes por corrida. | **~mediados de 2027** (a los 13 meses). Ahí el IAI pasa de 65/35 a 55/30/15 automáticamente. |

---

## 5. Data de pago / suscripción (evaluación pendiente)

Atajos comerciales que resolverían algún bloqueo, a sopesar costo/beneficio.

| Servicio | Resolvería | Notas |
|---|---|---|
| **SIOMAA** (ACARA) | Patentamientos comerciales **ya** (sin esperar la acumulación a 2027) | Producto comercial con login/paywall. Decisión: por ahora se acumula gratis vía DNRPA (§4). |
| Microdata Aduana por NCM 8 dígitos | Hardware hi-tech del ICIP | No es "pago" pero requiere un pipeline de extracción/normalización de archivos bulk; sin serie limpia. Proyecto aparte si se prioriza. |

---

## 6. Mejoras metodológicas pendientes

Cosas que funcionan pero podrían afinarse.

- **`mortalidad_pymes` (Vida):** hoy usa **% m/m de la serie IPI original**, dominada por estacionalidad (feb→mar puede dar +21% m/m espurio). **Cambiar a i.a. o serie desestacionalizada** con nuevas anclas.
- **Divergencia de score de Vida:** el colector (`vida_cotidiana.py`/`generar_informe.py`) escribe el score legacy de 3 indicadores; `publicar.py` lo **sobrescribe** con el promedio de aportes en el snapshot. Pendiente opcional: portar el scoring al colector para eliminar la divergencia.
- **IAI / ICIP volatilidad:** las series i.a. de inversión son ruidosas (±30-180% en 2024-25). Las bandas ya clampean, pero si el score mensual salta mucho, evaluar **media móvil 3m** de los componentes antes de componer.
- **ICIP — `servicios_tech`:** hoy usa solo "Pago de servicios de informática" (`185.1`). Se podría sumar "uso de propiedad intelectual" (licencias) si se valida que no mete ruido.

---

## 7. Índice de decisiones (ADRs)

Las decisiones de diseño/metodología viven en [`docs/adr/`](adr/README.md). Resumen:

| # | Decisión |
|---|---|
| [0001](adr/0001-datos-calculados-no-hardcodeados.md) | Todo calculado de datos oficiales; nunca hardcodeado. |
| [0002](adr/0002-rem-equivalente-mensual.md) | REM por equivalente mensual (raíz-12). |
| [0003](adr/0003-recaudacion-interanual-real.md) | Recaudación en variación i.a. real. |
| [0004](adr/0004-financiamiento-indice-capacidad-prestable.md) | Financiamiento usa el Índice de Capacidad Prestable (IdC). |
| [0005](adr/0005-reservas-netas-a-secas.md) | Reservas netas "a secas" (SDDS + Tesoro + Bopreal). |
| [0006](adr/0006-brecha-cambiaria-ccl-mayorista.md) | Brecha cambiaria CCL/mayorista. |
| [0007](adr/0007-fichas-explican-concepto-no-fuente.md) | Las fichas explican qué mide, no de dónde sale. |
| [0008](adr/0008-tcrm-itcrm-bcra.md) | TCRM via ITCRM oficial del BCRA. |
| [0009](adr/0009-idm-y-tcrm-en-el-itcm.md) | IDM (real-real i.a.) + TCRM como 5ª dimensión. |
| [0010](adr/0010-capitulo-inversion-iai-icip.md) | Capítulo Inversión: IAI + ICIP (6ª dimensión); patentamientos por acumulación. |

---

## 8. Snapshot de cobertura (2026-10-10)

| Cinturón | Indicadores | Automáticos | Semiautomáticos | Manuales | Tensión |
|---|---|---|---|---|---|
| Macro | 16 | 16 | 0 | 0 | 3,8 |
| Política | 16 | 12 | 3 (`apoyo_empresario`, `desafios_legislativos`, `cobertura_judicial`) | 1 (`velocidad_resolucion`) | 2,6 |
| Impacto social | 22 | 22 | 0 | 0 | 6,3 |
| Gestión | 13 | 10 | 2 (`fal_modernizacion_laboral`, `protocolo_antipiquetes`) | 1 (`privatizaciones`) | 2,0 |
