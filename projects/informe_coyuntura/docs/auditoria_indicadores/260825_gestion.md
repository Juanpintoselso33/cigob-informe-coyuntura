# Auditoría externa de indicadores — Gestión

**Fecha de corte:** 25 de agosto de 2026
**Snapshot auditado:** `web/src/data/informe.json`
**Cobertura:** 14 de 14 indicadores publicados

## Criterio

La cifra del tablero se contrastó primero con su definición y sus insumos locales y luego mediante búsqueda web. La fuente oficial que alimenta el colector se usa como control primario, pero no cuenta por sí sola como corroboración independiente. Se considera **confirmado** cuando una fuente externa permite replicar la cifra o los hechos que determinan íntegramente un índice propio; **compatible** cuando confirma tendencia y orden de magnitud pero no el mismo universo o cálculo; **discrepante** cuando existe evidencia contemporánea incompatible; y **no verificable independientemente** cuando no existe un registro externo suficiente.

## Resultado resumido

| # | Indicador | Tablero | Evidencia externa | Veredicto | Confianza | Acción recomendada |
|---:|---|---|---|---|---|---|
| 1 | Brecha cambiaria | 6,0%, 25-08-2026 | CCL $1.600,29 y mayorista $1.510: 5,98% | Confirmado | Alta | Ninguna |
| 2 | Apertura comercial | 6,18%, jun-2026 | Intercambio USD 15.916 M; DEX+DIM $1,427 bn; conversión cercana a USD 0,96–0,98 bn | Compatible | Media | Publicar el tipo de cambio promedio exacto usado |
| 3 | Desregulación normativa | 16.771 artículos, jul-2026 | 719 normas, 2.803 normas afectadas y 16.771 artículos | Confirmado | Alta | Aclarar que es conteo oficial, no impacto económico |
| 4 | Dotación del Estado | -20,36% vs dic-2023, jun-2026 | Centros independientes reportan -20,4% para el agregado comparable | Confirmado | Alta | Afinar el rótulo del universo APN/empresas |
| 5 | Gasto de funcionamiento | -31,37% real vs jun-2023 | CEPA calcula -31,4% con la misma base y período | Confirmado | Alta | Ninguna |
| 6 | Reestructuración de organismos | 24,4% = 11/45 | La prensa confirma el proceso, pero no existe un padrón externo que replique 11 ni la meta de 45 | No verificable independientemente | Media | Publicar las 11 altas y justificar el denominador 45 |
| 7 | Fondo de Asistencia Laboral | 50/100, 25-08-2026 | Ley y decreto dictados; vigencia diferida al 01-11-2026; todavía no opera | Confirmado | Alta | Mostrar el 50 como índice CIGOB, no como “50% implementado” |
| 8 | Litigiosidad laboral | +2,1%, 12m a may-2026 | Serie SRT permite el cálculo; prensa confirma nivel alto, pero suele usar flujo mensual/anual proyectado | Compatible | Media | Enlazar descarga y publicar las 24 sumas mensuales |
| 9 | Privatizaciones | 51,4%, corte 30-06-2026 | Fuentes externas confirman el estado desigual de las nueve empresas, no la escala propia 0–4 | Compatible | Media | Revisar las 18 normas nuevas pendientes y actualizar fecha de dato |
| 10 | Inversiones RIGI | 23,5%, 25-08-2026 | 21 aprobados por USD 46.708 M y 23 en evaluación por USD 152.271 M: 23,47% | Confirmado | Alta | Registrar fecha de corte del universo; vigilar altas posteriores |
| 11 | Concesiones viales | 28,7% = 2.614/9.091 km | La Resolución 1379/2026 adjudicó formalmente la Etapa III, más de 3.900 km adicionales | Discrepante | Alta | Marcar Etapa III adjudicada y recalcular antes de publicar |
| 12 | Asistencia directa (TDPS) | 100%, devengado 2026 | Prensa confirma pagos directos, pero no permite probar externamente el 100% del devengado clasificado | Compatible | Media-baja | No equiparar automáticamente partida 5.1.4 con ausencia total de intermediación operativa |
| 13 | Orden público (piquetes) | -74,2% CABA, 2025 vs 2023 | 240 en 2025; 11,3% de 8.239 en 2023 equivale a ~931 | Confirmado | Alta | Enlazar la nota que contiene base, método y cobertura |
| 14 | Libertad de opción en salud | 31,8%, mar-2026 | Estudio sectorial: ~2,5 M directos sobre ~6,8 M con prepaga; confirma magnitud, no igual denominador | Compatible | Media | Explicar por qué RNEMP da 8,369 M frente a estimaciones sectoriales de 6,8 M |

**Conteo:** 7 confirmados · 5 compatibles · 1 discrepante · 1 no verificable independientemente.

## Evidencia detallada

### 1. Brecha cambiaria (cepo)

TN publicó para el 25 de agosto CCL de $1.600,29 y mayorista de $1.510. La fórmula `(1600,29 / 1510 - 1) × 100` produce 5,98%, que redondea exactamente al 6,0% del tablero. La misma nota calcula mal la brecha blue/mayorista en su texto, por lo que aquí se usaron las cotizaciones informadas y no ese cálculo editorial. **Confirmado, confianza alta.**

Fuente: [TN — cotizaciones del 25 de agosto de 2026](https://tn.com.ar/economia/2026/08/25/dolar-a-cuanto-cotizan-el-oficial-y-las-otras-opciones-cambiarias-este-martes-25-de-agosto/).

### 2. Apertura comercial

Data Portuaria y la AAACI informan exportaciones por USD 9.055 millones e importaciones por USD 6.861 millones: el denominador de USD 15.916 millones coincide. La prensa basada en ARCA reporta $881.128 millones de derechos de exportación y $545.789 millones de importación. La suma, convertida a un A3500 representativo de junio, queda en torno de USD 0,96–0,98 mil millones; el cociente está alrededor de 6,1%, compatible con 6,18%. La reproducción exacta depende del promedio cambiario empleado por el colector, no visible en la card. **Compatible, confianza media.**

Fuentes: [Data Portuaria — intercambio de junio](https://dataportuaria.com/es/argentina/comercio-exterior/el-comercio-exterior-argentino-cerro-junio-con-un-superavit-de-us-2-194-millones), [AAACI — exportaciones e importaciones de junio](https://aaaci.org.ar/las-exportaciones-se-dispararon-y-crece-el-superavit/), [histórico mayorista de junio](https://datulis.com/cotizaciones/dolar/mayorista/2026/06/30).

### 3. Desregulación normativa

La cifra y sus componentes coinciden: 719 normas de desregulación, 2.803 normas anteriores modificadas o eliminadas y 16.771 artículos acumulados a julio. La corroboración periodística deriva del informe oficial; valida la transcripción, no constituye una auditoría jurídica independiente de cada artículo. Además, la propia metodología reconoce 40 normas cuyo texto no estaba disponible, por lo que la cifra es una cota inferior. **Confirmado como conteo publicado, confianza alta; no confirmado como impacto económico.**

Fuentes: [Economis — 16.771 artículos y metodología](https://economis.com.ar/desregulacion-sturzenegger-ya-contabiliza-16-771-articulos-modificados-o-eliminados/), [Ministerio — Desregulación en números](https://www.argentina.gob.ar/desregulacion).

### 4. Dotación del Estado

Grupo EPC calcula una baja de 20,4% entre diciembre de 2023 y junio de 2026 para el agregado que publica INDEC (341.465 a 271.696). CEPA ya ubicaba el recorte en 20% a abril y la prensa en 20% a mayo. El -20,36% del tablero para la APN sin empresas es coherente y queda respaldado por un cálculo externo casi idéntico. Debe cuidarse el rótulo porque el informe externo llama “total APN” a un universo más amplio que la cifra de 184.202 agentes mostrada en la card. **Confirmado, confianza alta.**

Fuentes: [Grupo EPC — empleo público a junio de 2026](https://grupo-epc.com/informes/informe-de-evolucion-de-empleo-y-rrhh-del-sncti-julio-2026/), [Centro CEPA — datos a abril](https://centrocepa.com.ar/documentos/informes/804-la-dotacion-de-personal-del-sector-publico-nacional-datos-a-abril-2026), [TN — recorte a mayo](https://tn.com.ar/economia/2026/06/30/en-mayo-continuo-la-caida-del-empleo-publico-y-el-gobierno-ya-recorto-un-20-de-los-puestos-desde-que-asumio/).

### 5. Gasto de funcionamiento

CEPA, usando Hacienda e INDEC, calcula un ajuste real de 31,4% en junio de 2026 frente a junio de 2023. Coincide al redondeo con -31,37%. Su cuadro también informa $2,1095 billones en junio de 2026 y $435.464 millones en junio de 2023, los mismos órdenes del detalle CIGOB. **Confirmado, confianza alta.**

Fuentes: [CEPA — ingresos, gastos y resultado a junio de 2026](https://centrocepa.com.ar/documentos/informes/821-analisis-de-los-ingresos-gastos-y-resultados-del-sector-publico-nacional-datos-de-junio-2026), [OPC — ejecución de junio de 2026](https://opc.gob.ar/ejecucion-presupuestaria/ejecucion-mensual-base-devengado/analisis-de-la-ejecucion-presupuestaria-de-la-administracion-nacional-junio-2026/).

### 6. Reestructuración de organismos

Las fuentes externas confirman una política de disoluciones, fusiones y transformaciones y describen un paquete de “más de 40” organismos. No existe, sin embargo, un padrón independiente estable que reproduzca las 11 altas vigentes seleccionadas por CIGOB ni un documento externo que convierta 45 en el 100% del plan. Como el 24,4% es exactamente `11/45`, cualquier cambio de universo altera el indicador. **No verificable independientemente, confianza media.**

Fuentes: [Gobierno — proceso de más de 40 organismos](https://www.argentina.gob.ar/node/466388), [TN — nueva revisión integral del Estado](https://tn.com.ar/politica/2026/08/02/el-gobierno-avanza-con-una-revision-integral-del-estado-y-prepara-mas-recortes-del-gasto-publico-antes-de-2027/), [Tesorería — organismos fusionados o disueltos](https://www.argentina.gob.ar/economia/tesoreria-general-de-la-nacion/organismos-de-la-administracion-central-fusionados-o).

### 7. Fondo de Asistencia Laboral

La Ley 27.802 y el Decreto 408/2026 existen y no aparecen suspendidos al corte. El artículo 27 del decreto difiere la vigencia hasta el 1 de noviembre de 2026; análisis jurídicos externos coinciden en que todavía no opera. Con la fórmula declarada por CIGOB —50 puntos por construcción normativa, 20 por vigencia y 30 por adopción— el resultado es reproducible: 50. **Confirmado, confianza alta.**

Fuentes: [Decreto 408/2026](https://www.argentina.gob.ar/normativa/nacional/decreto-408-2026-426272/texto), [Estudio Nunes — análisis de la reglamentación](https://estudionunes.com.ar/fondo-de-asistencia-laboral-fal-que-establece-la-reglamentacion-del-decreto-408-2026/), [Estudio Vilaplana — vigencia y controversia constitucional](https://estudiovilaplana.com.ar/2026/05/15/fondo-asistencia-laboral-fal-ley-27802-vigencia-funcionamiento-inconstitucionalidad/).

### 8. Litigiosidad laboral

La card mide dos ventanas móviles de doce meses: 127.363 juicios frente a 124.767, variación 2,08%. La SRT informa 10.699 juicios en mayo de 2026 frente a 11.937 en mayo de 2025, de modo que el flujo mensual cae aunque el acumulado móvil todavía suba. Una nota de mayo proyectaba 138.600 demandas para 2026 a partir del primer cuatrimestre, confirmando el nivel, pero no reproduce las dos ventanas del tablero. **Compatible, confianza media.**

Fuentes: [SRT — últimos datos de litigiosidad](https://www.srt.gob.ar/estadisticas/lit_ultimos_datos.php), [El Tribuno — litigiosidad en el primer cuatrimestre](https://www.eltribuno.com/nacionales/2026-5-24-0-0-0-la-litigiosidad-laboral-sigue-en-alza).

### 9. Privatizaciones

La escala 0–4 y su promedio son una codificación propia, por lo que ninguna nota puede confirmar “51,4%” directamente. El seguimiento externo sí respalda que Transener se completó, AySA e Intercargo estaban en licitación, ENARSA avanzaba por activos, Belgrano Cargas y Corredores Viales por concesiones, Nucleoeléctrica seguía parcial y YCRT buscaba inversores. El snapshot declara 18 normas nuevas aún no revisadas y mantiene fecha de dato 30 de junio: eso impide elevar el veredicto. **Compatible, confianza media.**

Fuentes: [Data Legislativa — estado de los procesos al 12 de agosto](https://www.datalegislativa.com/2026/08/12/el-congreso-analiza-las-privatizaciones/), [iProfesional — procesos de agosto](https://www.iprofesional.com/negocios/461965-metrogas-aysa-y-belgrano-cargas-las-tres-privatizaciones-que-podrian-avanzan-en-agosto.amp), [Gobierno — Transener en etapa final](https://www.argentina.gob.ar/noticias/la-privatizacion-de-transener-entra-en-su-etapa-final-tras-la-apertura-de-las-ofertas).

### 10. Inversiones RIGI

El Observatorio RIGI reportó 44 iniciativas por USD 198.979 millones: 21 aprobadas por USD 46.708 millones y 23 en evaluación por USD 152.271 millones. `46.708 / 198.979 × 100 = 23,47%`, exactamente 23,5% redondeado. Casa Rosada también informó 21 aprobados y USD 46.700 millones el 4 de agosto. Existen trackers secundarios que ya muestran más altas; por eso la fecha de corte debe quedar explícita. **Confirmado al universo informado el 20-08-2026, confianza alta.**

Fuentes: [Stornia — balance del Observatorio RIGI](https://stornia.com/articulo/argentina/economia-y-finanzas/---/argentina-recibe-44-proyectos-por-us198979-millones-bajo-el-rigi), [Analista Macro — 21 aprobados por USD 46.700 millones](https://analistamacro.com/2026/08/05/economia/el-rigi-ya-aprobo-21-proyectos-por-us-46-700-millones/), [Casa Rosada — conferencia del 4 de agosto](https://www.casarosada.gob.ar/informacion/conferencias/51333-conferencia-de-prensa-del-vocero-presidencial-adrian-ravier-desde-casa-rosada-04-08-2026).

### 11. Concesiones viales

El tablero mantiene la Etapa III como “disponible para adjudicar” y sólo suma 2.614 km. No se trata únicamente de un anuncio político: la Resolución 1379/2026, fechada el 20 de agosto y publicada en el Boletín Oficial del 25, adjudica expresamente los ocho renglones de la Etapa III. Son más de 3.900 km adicionales. Con el denominador actual de 9.091 km, aun usando 3.900 como cota inferior, el numerador subiría al menos a 6.514 km y el indicador a aproximadamente 71,65%. **Discrepante, confianza alta.**

Fuentes: [Boletín Oficial — Resolución 1379/2026](https://www.boletinoficial.gob.ar/detalleAviso/primera/346271/20260824), [CONTRAT.AR — dictamen de preadjudicación](https://contratar.gob.ar/EVALUACIONOFERTA/PreAdjudicarVisualizarDictamenCiudadano.aspx?qs=BQoBkoMoEhzhFlcUFoNWNuUJoXlC7r9lUOp%7CDNYblmweZtJdjpWCcUn99UTMGmCnrEtbYHNgkBfAwWWpRzNvCShb20aJScfzMOuP4dzyJBO1wDp0OcB183l6if9boXN%7CTL8MJ3AyHRIxfu4Qy%2FGUN4%2FaoxQmEqrr8diGk0%2FKs5GiNO6oiPdAcWREfHcpzJ5JMeCme2V1wMcH6Oo4eYk6Vld4IUY4zpm6fnfHYe0Za2TS192UyhdBdw%3D%3D), [Diario Río Negro — cobertura de la adjudicación](https://www.rionegro.com.ar/politica/el-gobierno-confirmo-la-concesion-de-3-900-km-de-rutas-nacionales-que-tramos-y-corredores-abarca-4692284/).

### 12. Asistencia directa (TDPS)

El cálculo presupuestario da $542.901 millones en la partida 5.1.4 y cero en las partidas que el modelo considera intermediadas, de donde surge 100%. La prensa y el rediseño normativo confirman que Volver al Trabajo, Acompañamiento Social y otras prestaciones se pagan directamente a beneficiarios. No obstante, una clasificación por objeto del gasto prueba el destinatario presupuestario, no necesariamente toda la cadena operativa; tampoco se encontró una auditoría externa del monto de $542.901 millones. **Compatible, confianza media-baja.**

Fuentes: [La Nación — pagos directos y eliminación del control de organizaciones](https://www.lanacion.com.ar/politica/los-piquetes-se-redujeron-mas-del-527-desde-que-asumio-milei-hay-menos-protestas-de-las-nid13012026/), [norma del programa Volver al Trabajo](https://servicios.infoleg.gob.ar/infolegInternet/anexos/395000-399999/396928/norma.htm).

### 13. Orden público (piquetes)

La Nación informa 240 piquetes en CABA durante 2025 y 8.239 en todo el país en 2023. También dice que CABA representaba 11,3% del total de 2023: `8.239 × 0,113 = 931`, que coincide con la base local. `(240 / 931 - 1) × 100 = -74,22%`. Chequeado valida de manera independiente el total nacional de 2023 y el método diario de Diagnóstico Político. **Confirmado, confianza alta.**

Fuentes: [La Nación — cifras 2023–2025 y desglose CABA](https://www.lanacion.com.ar/politica/los-piquetes-se-redujeron-mas-del-527-desde-que-asumio-milei-hay-menos-protestas-de-las-nid13012026/), [Chequeado — verificación del conteo nacional](https://chequeado.com/ultimas-noticias/javier-milei-de-9000-piquetes-por-ano-hoy-ese-numero-es-0/).

### 14. Libertad de opción en salud

El Instituto de Salud Global estimó en abril unos 1,4 millones de titulares y 2,5 millones de personas derivando aportes directamente, sobre aproximadamente 6,8 millones con prepaga. Respalda el orden de magnitud del numerador local de 2,661 millones, pero su denominador es bastante menor que los 8,369 millones del RNEMP. La diferencia parece ser de definición —planes/afiliados estimados frente al padrón administrativo de usuarios— y no permite confirmar exactamente 31,8%. **Compatible, confianza media.**

Fuentes: [Instituto de Salud Global — seguimiento de propuestas de salud](https://isg.org.ar/wp-content/uploads/2026/04/Seguimiento-propuestas-de-salud-anunciadas-en-2023-por-LLA-Milei.pdf), [Superintendencia — libre elección de obras sociales y prepagas](https://www.argentina.gob.ar/node/451904), [SSS — padrón de población](https://seguro.sssalud.gob.ar/index.php?page=poblacion).

## Segundo barrido de los casos no verificables

### Reestructuración de organismos: de «no verificable» a **discrepante**

La búsqueda ampliada permitió cerrar el único expediente que había quedado sin verificación independiente. El 24,4% es aritméticamente `11/45`, pero sus dos unidades no sostienen la etiqueta pública:

- el **11 cuenta normas** halladas por una búsqueda literal de `disolucion` en InfoLeg, no organismos; las propias once normas curadas cierran aproximadamente **18 entidades** porque varios decretos contienen más de una;
- el **45 también es una convención de documentos**, fijada originalmente a partir de «18 docs = 40%», y no una meta pública de 45 organismos;
- el mecanismo de descubrimiento no cubre el universo de cierres. El padrón de la Tesorería registra, entre otros, la absorción del ENOHSA en diciembre de 2024 y otros egresos, mientras que el registro curado usado por el indicador no contiene ENOHSA. El listado gubernamental difundido al vencer las facultades delegadas también enumera cierres adicionales y 29 fondos fiduciarios, muy por encima de los casos que captura la consulta literal.

La comparación externa no habilita a reemplazar 24,4% por otro porcentaje exacto: mezcla organismos, programas, fondos, áreas y actos normativos, y no existe una meta final cerrada. Sí alcanza para una conclusión más fuerte que la primera ronda: **24,4% no es un porcentaje verificable de organismos disueltos ni una medida exhaustiva del avance real**. Es la proporción de once documentos seleccionados sobre una convención de 45 documentos, presentada bajo una unidad distinta.

**Nuevo veredicto:** **discrepante, confianza alta**. Debe salir del índice hasta definir un numerador y denominador homogéneos. Dos opciones auditables serían: (a) conteo acumulado de entidades cerradas contra un padrón inicial explícito, sin llamarlo «avance»; o (b) porcentaje de una lista objetivo oficial y congelada, si el Gobierno publica una. No corresponde usar `18/45 = 40%` como corrección automática: sólo arreglaría parcialmente la unidad del numerador y mantendría el denominador arbitrario.

Fuentes adicionales: [Tesorería General — organismos fusionados o disueltos, ejercicio 2026](https://www.argentina.gob.ar/economia/tesoreria-general-de-la-nacion/organismos-de-la-administracion-central-fusionados-o), [Infobae — listado de 101 modificaciones difundido por el Ministerio](https://www.infobae.com/economia/2025/07/08/la-lista-completa-de-la-motosierra-cuales-son-los-100-organismos-publicos-cerrados-o-modificados-durante-el-gobierno-de-milei/), [Infobae — detalle de cierres, transformaciones y 29 fondos](https://www.infobae.com/politica/2025/07/07/adorni-dijo-que-los-organismos-publicos-que-milei-cerro-por-decreto-representaron-un-ahorro-de-2-mil-millones-dolares/), [Decreto 345/2025 — universo oficial de 111 organismos al 07-02-2025](https://www.argentina.gob.ar/normativa/nacional/decreto-345-2025-413035/texto).

## Hallazgo prioritario

Tras el segundo barrido hay **dos errores fuertes y accionables**. En **Concesiones viales**, el tablero conserva la Etapa III como no adjudicada pese a que la Resolución 1379/2026 la adjudica formalmente; con los valores publicados, el 28,7% pasa como mínimo a aproximadamente 71,6%. En **Reestructuración de organismos**, el 24,4% mezcla una cantidad de normas con una etiqueta de organismos y depende de una meta convencional no observable; no debe corregirse con otro porcentaje improvisado, sino retirarse o rediseñarse.

En segundo nivel quedan la equivalencia presupuestaria usada por TDPS y la falta del tipo de cambio explícito en apertura comercial.
