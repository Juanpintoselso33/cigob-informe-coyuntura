# Auditoría externa de indicadores — Impacto social / Vida cotidiana

**Fecha de corte:** 25 de agosto de 2026
**Snapshot auditado:** `projects/informe_coyuntura/web/src/data/informe.json`
**Definiciones auditadas:** `projects/informe_coyuntura/output/fichas/fichas-vida_cotidiana.md`
**Cobertura:** 19 de 19 indicadores publicados

## Método y alcance

Para cada indicador se controlaron cinco dimensiones: cifra, período, unidad, cobertura geográfica/universo y transformación que lo convierte en componente del ITCIS. El archivo publicado fue la autoridad sobre **qué estaba viendo el usuario al corte**; las fichas se usaron para reconstruir qué se pretendía medir.

La fuente productora u oficial se usó como control primario, pero no se consideró por sí sola corroboración independiente. La búsqueda externa priorizó universidades, centros de investigación, cámaras u observatorios sectoriales y prensa económica con cifras trazables. Cuando una nota sólo reproduce al productor se la trató como control de transcripción, no como una segunda medición. En índices propios se verificaron insumos, fórmula, universo y posibilidad de reproducción; no se equiparó un indicador parecido con el indicador auditado.

Los veredictos significan:

- **Confirmado:** la cifra y su definición se pueden reproducir o corroborar externamente sin una diferencia material.
- **Compatible:** la evidencia externa confirma magnitud y dirección, pero no replica exactamente el universo o el modelo.
- **Discrepante:** hay una diferencia material de cifra, fecha, unidad, geografía, universo o definición.
- **No verificable independientemente:** el productor confirma el dato, pero no existe evidencia externa suficiente para auditarlo como medición separada.

El ITCIS rebasa casi todos los componentes a `100 = promedio del 4T-2023`; invierte los indicadores en los que más significa peor. La canasta de servicios usa, en cambio, umbrales de asequibilidad. Que una cifra de card esté confirmada no valida automáticamente la elección normativa de esa base, sus pesos ni la conversión lineal de índice a tensión.

## Resultado resumido

| # | Indicador publicado | Dato del snapshot | Control externo e independiente | Veredicto | Confianza | Corrección o acción |
|---:|---|---|---|---|---|---|
| 1 | Salario real vs. canasta | 3,87 canastas, jun-2026 | RIPTE $1.915.878,76 / CBT $495.622 = 3,866 | Confirmado | Alta | Aclarar que compara trabajador formal estable con CBT de adulto equivalente, no ingreso de un hogar |
| 2 | IPC alimentos | 1,98% m/m, jul-2026 | Prensa internacional informa 2,0% y 2,1% para IPC general | Confirmado | Alta | Ninguna; mantener visible que el componente usa nivel relativo, no la tasa mensual |
| 3 | Peso de tarifas | 14,5% del RIPTE, ago-2026 | Canasta AMBA $289.622 / salario estimado $1.993.280 = 14,53% | Confirmado | Media-alta | Rotular AMBA y “hogar representativo”; no generalizar a todo el país |
| 4 | Alquiler real | 1,47% m/m, jul-2026 | Avisos nuevos suben 1,4% en GBA Norte y 1,6% en CABA; universo distinto pero consistente | Compatible | Media | Explicitar que IPC-GBA mide alquileres relevados, no avisos nuevos |
| 5 | Consumo total de carnes | 114,45 kg/hab/año, jun-2026 | CICCRA ubica vacuna en 47,0–47,3 kg y confirma sustitución; no replica el total exacto de tres carnes | Compatible | Media | Publicar los tres componentes y no presentar nivel SAGYP/evolución INDEC como una sola serie homogénea |
| 6 | Informalidad laboral | 37,9%, 1T-2026 | UNR e IIEP distinguen 37,9% entre asalariados y 44,2% entre todos los ocupados | Confirmado | Alta | Mostrar “1º trimestre” y “asalariados”; evitar fecha puntual 01-01 |
| 7 | Trabajo independiente | 20,6% del empleo registrado, may-2026 | El universo SIPA total incluye monotributo social; el cálculo local lo excluye del numerador y denominador | Discrepante | Alta | Relabelar denominador como asalariados + autónomos + monotributistas comunes, o incluir monotributo social y recalcular |
| 8 | Empleadores pequeños activos | 460.777, may-2026 | Fundar/CEPA ubican la caída total de empleadores en ~6% desde nov-2023; compatible con índice local 93,8 | Compatible | Media | Publicar padrón mensual reproducible por tramo y aclarar que requiere al menos un trabajador asegurado |
| 9 | Construcción (ISAC) | 148,1 desest., jun-2026 | Serie externa replica 148,11 | Confirmado | Alta | Cambiar el identificador legado `despacho_cemento`; no es despacho de cemento |
| 10 | Subocupación demandante | 7,5%, 1T-2026 | INDEC y análisis externo confirman 7,5%, pero la tasa es sobre la PEA, no sobre los ocupados | Discrepante | Alta | Corregir definición/universo; mostrar período trimestral y retirar identificador legado `pluriempleo` |
| 11 | Empleo privado registrado | 6.106,526 mil, may-2026 | Prensa reproduce 6,107 millones y la baja mensual | Confirmado | Alta | Ninguna; conservar “asalariados privados registrados” |
| 12 | Victimización (IVI) | 28,0% hogares, abr-2026 | El informe UTDT confirma 28%; estadísticas policiales no miden el mismo fenómeno | No verificable independientemente | Media | Publicar muestra, campo e intervalo; no usar denuncias SNIC como falsa corroboración |
| 13 | Confianza del consumidor (ICC) | 39,9, ago-2026 | El ICC nacional es 40,23; 39,87 corresponde a CABA | Discrepante | Alta | Cambiar card a 40,2/40,23 nacional y leer la columna nacional del XLS |
| 14 | Pobreza nowcast | 31,6%, semestre móvil a jun-2026 | UTDT publica 31,6% [30,1; 33,0]; BCRA estimó 30,0% para 1T, compatible pero no igual período | Compatible | Media-alta | Publicar intervalo, 31 aglomerados y “ene-jun”, no fecha puntual junio |
| 15 | Sentimiento digital | 58,2, jul-2026, base 4T-2023 | Google Trends sólo ofrece una muestra normalizada; faltan consultas, valores y artefacto congelado | No verificable independientemente | Baja | Versionar exportación, seis términos, parámetros, fecha/hora y transformación completa |
| 16 | Motorización total | 30,9 0 km/1.000 hab., 12m a jul-2026 | Julio: 43.758 autos y 71.217 motos; acumulados 339.359 y 511.986, consistentes con el rolling propio | Compatible | Media | Publicar los 12 meses, población urbana proyectada y exclusión de Tierra del Fuego |
| 17 | Consumo en supermercados | 83,2, may-2026, “2004=100” | Al corte ya estaba junio: 82,1; mayo fue revisado a 83,0; la base real es 2017=100 | Discrepante | Alta | Actualizar a jun-2026 = 82,1 y corregir unidad/base antes de recomputar ITCIS |
| 18 | Mora de las familias | 14,52%, may-2026 | Personales 15,9% y tarjetas 13,1%; el promedio ponderado necesariamente cae entre ambos | Confirmado | Alta | Publicar saldos/pesos para que 14,52% sea replicable fuera de la planilla |
| 19 | Carga del servicio de deuda | 24,076% masa salarial, abr-2026 | BCRA 24,0758317%; prensa y UNSAM reportan 24,1% | Confirmado | Alta | Ninguna; mantener nota de promedios móviles de tres meses |

**Conteo:** 8 confirmados · 5 compatibles · 4 discrepantes · 2 no verificables independientemente.

## Evidencia detallada

### 1. Salario real vs. canasta (`brecha_salario_cbt`)

El RIPTE de junio fue $1.915.878,76 y la CBT por adulto equivalente, $495.622. La división da `1.915.878,76 / 495.622 = 3,8656`, que redondea exactamente a 3,87. Cifra, período y unidad coinciden. La cobertura, sin embargo, es estrecha: el numerador representa remuneración imponible promedio de trabajadores estables formales y el denominador una CBT de adulto equivalente. No dice cuántas canastas compra “el salario argentino” ni el ingreso de una familia típica.

La transformación positiva —cociente mensual dividido por el promedio oct-dic de 2023 y multiplicado por 100— es reproducible con las dos series mensuales. **Confirmado, confianza alta.**

Fuentes: [El Tablero — serie RIPTE](https://eltablero.ar/variables/datos-158.1_REPTE_0_0_5-remuneracion-imponible-promedio-de-los-trabajadores-estables-ripte), [Calcular — CBT de junio de 2026](https://calcular.ar/canasta-basica/junio-2026), [INDEC — canastas básicas](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-43-149).

### 2. IPC alimentos (`ipc_alimentos`)

EFE informó que Alimentos y bebidas no alcohólicas subió 2,0% en julio y que el IPC general fue 2,1%; 1,98% es el dato no redondeado compatible con esa publicación. Se trata del nivel nacional y del mes de julio, no de GBA.

La card muestra la variación mensual, pero el ITCIS no puntúa esa tasa: calcula el cociente acumulado entre el nivel del IPC general y el nivel de alimentos, rebaseado al 4T-2023, de manera que la comida creciendo menos que el IPC mejora el componente. La fórmula y el sentido son coherentes; conviene mantener esa distinción visible porque 1,98% no es el insumo directo que aparece como 102,8 en el índice. **Confirmado, confianza alta.**

Fuentes: [EFE — inflación de julio de 2026](https://efe.com/economia/2026-08-13/ipc-argentina-julio/), [INDEC — IPC y cobertura](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31).

### 3. Peso de tarifas (`peso_tarifas`)

El IIEP UBA-CONICET publicó para agosto una canasta de servicios públicos de $289.622 para un hogar representativo del AMBA. La cobertura periodística informa un salario estimado de $1.993.280. El cociente es 14,53%, consistente con 14,5%. El dato incluye energía, agua y transporte, pero no alquiler; tampoco es una media nacional.

Es la excepción al rebase 4T-2023. La ficha separa transporte —43% de la canasta, aproximadamente 6,2% del salario— del resto —8,3%— y lo evalúa contra umbrales internacionales de 5% y 10%. La aritmética es reproducible, aunque la elección del hogar, salario y umbrales sigue siendo un supuesto del modelo. **Confirmado como cálculo del hogar representativo AMBA, confianza media-alta.**

Fuentes: [IIEP UBA-CONICET — reporte de tarifas y subsidios de agosto](https://economicas.uba.ar/iiep/reporte-de-tarifas-y-subsidios-agosto-2026/), [CPS Comunicación — canasta y salario empleados](https://cpscomunicacion.com/una-familia-del-amba-necesito-casi-290-000-en-agosto-para-cubrir-los-servicios-publicos/).

### 4. Alquiler real (`alquiler_real`)

La cifra de la card, 1,47%, es la variación mensual del rubro Alquiler de la vivienda del IPC-GBA. Dos termómetros privados cercanos dan 1,4% en GBA Norte y 1,6% en CABA para julio. Respaldan el orden de magnitud, pero miden avisos de unidades nuevas en oferta, mientras el IPC releva precios efectivos de una muestra y contratos en curso. No deben tratarse como réplicas exactas.

El componente usa el nivel de alquiler relativo al IPC general GBA y lo rebasa al 4T-2023; esto elimina la inflación general acumulada, no convierte el rubro en costo de vivienda completo ni controla calidad. **Compatible, confianza media.**

Fuentes: [Mercado/Zonaprop — alquileres del GBA en julio](https://mercado.com.ar/ladrillos-y-proyectos/zonaprop-gba-oeste-fue-la-zona-mas-barata-para-comprar-en-julio-2026), [TN/Zonaprop — alquileres de CABA en julio](https://tn.com.ar/economia/2026/08/05/los-alquileres-en-caba-subieron-16-en-julio-los-barrios-mas-caros-y-los-mas-baratos/), [INDEC — alcance del IPC-GBA](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31).

### 5. Consumo total de carnes per cápita (`consumo_carnes_total`)

El snapshot suma 47,28 kg de vacuna, 47,24 de aviar y 19,93 de porcina: 114,45 kg/hab/año, promedio móvil de doce meses a junio. CICCRA ubicó el consumo vacuno alrededor de 47,0–47,3 kg y una baja del orden de 8% interanual, consistente con el componente vacuno y con la lectura de sustitución hacia pollo y cerdo. No se encontró un observatorio independiente que publicara, al mismo corte y con la misma ventana, el total exacto de las tres carnes.

Hay un límite adicional de reproducibilidad: la card toma el **nivel** del tablero SAGYP, mientras la evolución histórica que se rebasa en el ITCIS se reconstruye con toneladas de faena INDEC y población proyectada. Son magnitudes próximas, pero no una única serie estadística: faena no equivale necesariamente a disponibilidad/consumo y puede omitir comercio exterior o cambios de stock. **Compatible, confianza media.**

Fuentes: [Rosario3/Ecos365 — CICCRA y consumo vacuno de junio](https://www.rosario3.com/ecos365/contenidos/2026/07/30/noticia_0007.html), [Infobae — consumo vacuno del primer semestre](https://www.infobae.com/economia/2026/07/20/el-consumo-de-carne-vacuna-cayo-mas-de-11-en-el-primer-semestre-y-toco-su-menor-nivel-en-30-anos/?outputType=amp-type), [SAGYP — información sectorial bovina](https://www.magyp.gob.ar/sitio/areas/bovinos/informacion_sectorial/?ignoreCache=1).

### 6. Informalidad laboral (`informalidad`)

UNR e IIEP-UBA publicaron dos cifras que deben diferenciarse: 37,9% de informalidad **entre asalariados** y 44,2% cuando se considera el conjunto de ocupados. El tablero usa correctamente la primera. La cobertura son los 31 aglomerados urbanos de la EPH, primer trimestre de 2026; `2026-01-01` es sólo una codificación del trimestre y no una observación de enero.

La inversión del rebase es correcta para la convención del ITCIS: `base 4T23 / tasa actual × 100`, de modo que mayor informalidad reduce el índice. **Confirmado, confianza alta.**

Fuentes: [Universidad Nacional de Rosario — medición ampliada de informalidad](https://unr.edu.ar/informalidad-laboral-la-medicion-que-faltaba/), [IIEP UBA-CONICET — empleo informal y pobreza laboral](https://economicas.uba.ar/iiep/panorama-del-empleo-informal-y-la-pobreza-laboral-jun-2026/), [INDEC — mercado de trabajo EPH](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58).

### 7. Trabajo independiente (`trabajo_independiente`)

El cálculo local es aritméticamente consistente: 2,587 millones de autónomos más monotributistas comunes sobre 9,967 millones de asalariados más esos 2,587 millones produce 20,61%. El problema está en el rótulo “% del empleo registrado”. La definición oficial del total SIPA incluye asalariados privados y públicos, casas particulares, autónomos, monotributistas comunes **y monotributistas sociales**. El snapshot excluye a estos últimos tanto del numerador como del denominador, aunque la prensa informa que forman parte del total de 12,751 millones y que cayeron 2% en mayo.

No es un error de redondeo: es un universo distinto al publicado. Se puede conservar 20,6% si se relabela como participación en `asalariados + autónomos + monotributistas comunes`, o incluir monotributo social y recalcular toda la serie/base. El rebase invertido sólo será interpretable después de fijar ese universo. **Discrepante, confianza alta.**

Fuentes: [Secretaría de Trabajo — definición del total registrado](https://www.argentina.gob.ar/trabajo/estadisticas/situacion-y-evolucion-del-trabajo-registrado), [Primera Edición — total SIPA de mayo y monotributo social](https://www.primeraedicion.com.ar/nota/101132367/empleo-registrado-cayo-tercer-mes-consecutivo-argentina/), [TN — composición del trabajo registrado](https://tn.com.ar/economia/2026/07/16/menos-asalariados-y-mas-monotributas-asi-cambio-el-mercado-laboral-en-el-ultimo-ano/).

### 8. Empleadores pequeños activos (`mortalidad_pymes`)

La SRT define empleador como la unidad que declara al menos un trabajador cubierto. El snapshot cuenta 460.777 empleadores de hasta 50 trabajadores en mayo y rebasa el nivel, no las bajas mensuales. Informes de Fundar/CEPA recogidos por prensa sitúan la destrucción neta total desde noviembre de 2023 a mayo de 2026 en 30.633 empleadores, alrededor de 6%; el índice local 93,8 implica una contracción cercana a 6,2% en el tramo pequeño. Magnitud y dirección son consistentes, pero la publicación externa no replica exactamente el filtro `≤50`.

El nombre técnico “mortalidad” puede inducir a error: el indicador mide stock neto de empleadores activos y no identifica nacimientos y muertes brutas ni causalidad. **Compatible, confianza media.**

Fuentes: [SRT — cobertura y serie histórica por tamaño](https://www.srt.gob.ar/estadisticas/cf_serie_historica_up.php), [Vive/Informe Fundar — pérdida de empresas a mayo de 2026](https://vive.click/las-empresas-no-cierran-de-golpe-primero-se-vacian/).

### 9. Construcción (`despacho_cemento`)

La serie externa del ISAC desestacionalizado reproduce 148,11 en junio, que redondea a 148,1. Es un índice de actividad de la construcción nacional y no toneladas de cemento. El rebase positivo contra el promedio 4T-2023 es directo y usa la variante desestacionalizada, adecuada para una comparación mensual.

La cifra publicada es correcta; el identificador técnico legado `despacho_cemento` no lo es y debería migrarse para impedir confusiones futuras entre dos estadísticas distintas. **Confirmado, confianza alta.**

Fuentes: [Boletín Extraoficial — serie ISAC](https://boletinextraoficial.com/actividad-economica/isac/), [INDEC — actividad de la construcción](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-3-42).

### 10. Subocupación demandante (`pluriempleo`)

El cuadro EPH del primer trimestre confirma 7,5% en los 31 aglomerados. También confirma 11,1% de subocupación total. La discrepancia es conceptual: la tasa oficial de subocupación demandante se expresa como proporción de la **población económicamente activa**, mientras la ficha dice “qué porcentaje de los ocupados trabaja menos de 35 horas y busca activamente trabajar más”. Además, el identificador `pluriempleo` no describe subocupación: una persona puede buscar más horas sin tener dos empleos, o tener dos empleos sin estar subocupada.

La inversión del rebase es coherente con “más presión horaria = peor”, pero hoy rebasa una serie cuyo universo está descrito incorrectamente. Corregir a “personas subocupadas que buscan activamente más trabajo, como porcentaje de la PEA; 31 aglomerados urbanos, 1º trimestre de 2026”. **Discrepante, confianza alta.**

Fuentes: [informe EPH del 1º trimestre alojado por Infoecos](https://infoecos.com.ar/wp-content/uploads/2026/06/indecmercadodetrabajo.pdf), [Centro CEPA — análisis del mercado de trabajo 1T-2026](https://centrocepa.com.ar/documentos/informes/813-analisis-de-la-situacion-del-mercado-de-trabajo-datos-al-primer-trimestre-2026), [El Día — explicación de subocupación demandante](https://www.eldia.com/politica-y-economia/los-que-buscan-un-segundo-trabajo-segun-el-indec-en-la-plata-esa-cifra-duplica-al-promedio-del-pais-politica-y-economia-la-ciudad_1782253140).

### 11. Empleo privado registrado (`empleo_registrado`)

El snapshot contiene 6.106,526 miles de puestos asalariados privados registrados en mayo. La cobertura periodística del informe SIPA publica 6,107 millones, el mismo dato redondeado, y registra la baja mensual. No incluye empleo público, casas particulares, independientes ni empleo no registrado.

El componente usa el nivel mensual contra el promedio 4T-2023. La unidad “miles de puestos” es correcta, aunque una presentación con tres decimales equivale a precisión de una persona y resulta más precisa que la incertidumbre/revisión administrativa; 6.106,5 mil sería suficiente. **Confirmado, confianza alta.**

Fuentes: [Primera Edición — empleo registrado de mayo](https://www.primeraedicion.com.ar/nota/101132367/empleo-registrado-cayo-tercer-mes-consecutivo-argentina/), [Qué Tal Tu Día — empleo privado de mayo](https://quetaltudia.com.ar/nota/7358/el-mercado-).

### 12. Victimización (`inseguridad`)

El LICIP-UTDT publicó 28% de hogares urbanos con al menos un integrante víctima de delito en los doce meses anteriores a abril. El relevamiento fue realizado del 6 al 17 de abril sobre 996 hogares en 40 centros urbanos; con ese tamaño muestral el error de muestreo ronda tres puntos porcentuales antes de considerar diseño y ponderaciones.

No se encontró una encuesta independiente con igual pregunta, ventana y cobertura. El SNIC registra delitos denunciados/conocidos por el Estado y no puede validar una encuesta de victimización, que justamente captura hechos no denunciados. El rebase invertido es reproducible con el histórico UTDT, pero la medición continúa dependiendo de un solo productor. **No verificable independientemente, confianza media.**

Fuentes: [UTDT/LICIP — Índice de Victimización de abril de 2026](https://www.utdt.edu/listado_contenidos.php?id_item_menu=2156), [Ministerio de Seguridad — Sistema Nacional de Información Criminal](https://www.argentina.gob.ar/seguridad/estadisticascriminales).

### 13. Confianza del consumidor (`icc_utdt`)

Este es un error material y reproducible. La prensa informa para agosto un ICC **nacional de 40,23**, con 39,87 en CABA, 38,27 en GBA y 43,82 en Interior. El colector local lee la columna 1 de la hoja regional del XLS, que es CABA, y publica 39,9 como si fuera nacional.

La transformación también usa la serie CABA para la base. Con los valores del XLS, la base 4T-2023 de CABA es aproximadamente 43,780 y `39,867 / 43,780 × 100 = 91,06`. Con la serie nacional la base es aproximadamente 44,143 y `40,229 / 44,143 × 100 = 91,13`. La corrección casi no cambia el componente ni el color, pero sí la cifra, geografía y trazabilidad de la card: debe publicarse 40,2/40,23 nacional y leerse la columna nacional. **Discrepante, confianza alta.**

Fuentes: [Primera Edición — ICC nacional y regiones de agosto](https://www.primeraedicion.com.ar/nota/101134060/confianza-consumidor-interior-cayo-agosto-2026/), [Infobae — ICC 40,2 y CABA 39,9](https://www.infobae.com/economia/2026/08/20/la-confianza-del-consumidor-volvio-a-caer-en-agosto-por-el-deterioro-de-la-situacion-personal/), [UTDT — Índice de Confianza del Consumidor](https://www.utdt.edu/ver_contenido.php?id_contenido=2575&id_item_menu=4982).

### 14. Pobreza nowcast (`pobreza_nowcast`)

UTDT estima 31,6% de personas pobres para el semestre móvil enero-junio de 2026, con intervalo de confianza de 95% entre 30,1% y 33,0%. La cobertura son cerca de 30 millones de personas en los 31 aglomerados urbanos EPH. La estimación combina CBT e ingresos proyectados; no es una observación mensual de junio. El BCRA informó una estimación de 30,0% para el primer trimestre, compatible con el primer subperíodo y con el intervalo, pero no idéntica por ventana y modelo.

El ITCIS invierte y rebasa la serie contra 4T-2023. La operación es replicable a partir de los nowcasts publicados, no el modelo subyacente completo sin sus microdatos/supuestos. La card debería decir “semestre móvil ene-jun 2026” y mostrar el intervalo para no comunicar falsa precisión. **Compatible, confianza media-alta.**

Fuentes: [UTDT — nowcast de pobreza 31,6%](https://www.utdt.edu/ver_contenido.php?id_contenido=22217&id_item_menu=36605), [BCRA — estimación de pobreza del 1º trimestre](https://www.bcra.gob.ar/noticias/conferencia-prensa-ipom-segundo-trimestre-2026/).

### 15. Sentimiento digital (`sentimiento_digital`)

El valor 58,2 es un índice propio construido con seis términos de Google Trends y rebase 4T-2023. Google Trends normaliza cada consulta en una escala relativa 0–100 según período, geografía, categoría, tipo de búsqueda y muestra; una descarga posterior puede revisar valores. El snapshot/ficha no expone en la web los seis valores actuales, el archivo descargado, la hora de consulta, el método de empalme ni parámetros suficientes para obtener exactamente 58,2. Incluso la ficha generada en un corte cercano mostraba 58,4, señal de esa volatilidad.

La literatura puede respaldar el uso de Trends como señal de alta frecuencia, pero no confirma este número particular ni su interpretación como “sentimiento”. Para auditarlo se debe versionar un artefacto de entrada inmutable y la fórmula completa. **No verificable independientemente, confianza baja.**

Fuentes: [Google Trends Argentina](https://trends.google.com.ar/trending?geo=AR&hl=es-419), [Google Trends — ayuda sobre normalización de datos](https://support.google.com/trends/answer/4365533?hl=es), [GoogleTrendArchive — discusión académica sobre archivo y reproducibilidad](https://arxiv.org/abs/2603.21871).

### 16. Motorización total (`motorizacion_total`)

El cálculo local suma 561.671 autos y 790.021 motos patentados en los últimos doce meses: 1.351.692 unidades, 58,4% motos, y lo divide por población urbana proyectada para obtener 30,9 por mil. Las cifras mensuales independientes de julio —43.758 autos y 71.217 motos— y los acumulados enero-julio —339.359 y 511.986— son consistentes con un rolling anual total de ese orden. No se reconstruyeron externamente los doce archivos mensuales completos ni el denominador demográfico exacto.

La serie excluye Tierra del Fuego de todos los meses por una discontinuidad de archivos; eso evita un quiebre, pero la cobertura ya no es nacional completa y debe figurar en la card. La transformación positiva contra 4T-2023 es simple una vez fijados rolling y población. **Compatible, confianza media.**

Fuentes: [Fede Bossio — patentamientos de autos de julio](https://fedebossio.com.ar/patentamientos.html), [La Data Diaria — autos y motos de julio](https://ladatadiaria.com/patentamientos-de-julio-caen-autos-vuelan-motos/), [Datos Argentina/DNRPA — inscripciones iniciales de autos](https://datos.jus.gob.ar/fa_IR/dataset/inscripciones-iniciales-de-autos).

### 17. Consumo en supermercados (`consumo_supermercados`)

Al corte del 25 de agosto el INDEC ya había publicado, el 21 de agosto, la encuesta de junio. La tabla oficial da 82,1 para la serie desestacionalizada de junio, caída mensual de 1,0%; además revisa mayo a 83,0. El snapshot conserva 83,2 en mayo y `desactualizado: false`. También rotula la unidad como `índice (2004 = 100)`, pero la Encuesta de Supermercados vigente usa **base 2017=100**.

Son tres diferencias materiales: último período omitido, revisión histórica no incorporada y base de unidad errónea. La corrección es publicar `82,1, junio de 2026, índice de ventas totales a precios constantes desestacionalizado, base 2017=100`, volver a descargar la historia revisada y recomputar el rebase ITCIS. La prensa confirma -3,1% interanual y -1,0% mensual; no debe confundirse nivel 82,1 con ninguna de esas tasas. **Discrepante, confianza alta.**

Fuentes: [INDEC — Encuesta de supermercados, junio de 2026](https://www.indec.gob.ar/uploads/informesdeprensa/super_08_262444C24851.pdf), [CPS Comunicación — ventas de supermercados de junio](https://cpscomunicacion.com/las-ventas-en-supermercados-y-mayoristas-volvieron-a-caer-en-junio/), [INDEC — alcance de la Encuesta de Supermercados](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-1-34).

### 18. Mora de las familias (`mora_familias`)

La prensa, sobre el anexo del Informe sobre Bancos, informa para mayo 15,9% de irregularidad en préstamos personales y 13,1% en tarjetas; el total de crédito a hogares, que incluye otras líneas, fue 12,8%. La card no usa ese total: pondera sólo personales y tarjetas por sus saldos. Por eso 14,52%, entre 13,1 y 15,9, es coherente con pesos cercanos a la mitad para cada línea. Esta distinción evita comparar falsamente el 14,52% con el 12,8% agregado.

El rebase invertido contra 4T-2023 es directo. Para auditoría plena fuera del XLS oficial, convendría mostrar junto a la card los dos ratios, saldos y ponderaciones del mes. **Confirmado, confianza alta.**

Fuentes: [Infobae — mora de hogares, personales y tarjetas en mayo](https://www.infobae.com/economia/2026/07/24/oficial-la-mora-de-las-familias-volvio-a-crecer-en-mayo-y-casi-triplico-al-nivel-del-ano-pasado/?outputType=amp-type), [BCRA — Informe sobre Bancos](https://www.bcra.gob.ar/publicaciones/informe-sobre-bancos/).

### 19. Carga del servicio de deuda (`carga_servicio_deuda_hogares`)

La planilla de series del Informe de Estabilidad Financiera de julio publica 24,0758316911% para abril de 2026 en CDF/MS, que redondea exactamente a 24,076%. Sus notas definen CDF como pagos de capital e intereses de las familias, MS como masa salarial registrada pública y privada, y confirman que numerador y denominador son promedios de tres meses. La prensa y el CETyD-UNSAM lo resumen como 24,1% o “casi un cuarto del salario”.

El universo no son todos los ingresos de todos los hogares: el denominador es masa salarial registrada. El rebase invertido contra 4T-2023 está correctamente orientado; más servicio de deuda reduce capacidad disponible. **Confirmado, confianza alta.**

Fuentes: [BCRA — Informe de Estabilidad Financiera, primer semestre de 2026](https://www.bcra.gob.ar/publicaciones/informe-de-estabilidad-financiera-primer-semestre-2026/), [Infobae — carga de deuda de 24,1%](https://www.infobae.com/economia/2026/07/17/mora-record-los-argentinos-destinan-casi-un-cuarto-de-su-salario-a-pagar-deudas/?outputType=amp-type), [UNSAM/CETyD — hogares endeudados](https://noticias.unsam.edu.ar/2026/08/18/un-mercado-laboral-saturado-y-hogares-cada-vez-mas-endeudados-nuevo-informe-de-coyuntura-del-cetyd/).

## Hallazgos prioritarios y orden de corrección

1. **ICC nacional mal extraído.** El valor 39,9 es CABA; el nacional es 40,23. Corregir columna, cifra y geografía. El índice rebaseado cambia poco, pero el error de cobertura es inequívoco.
2. **Supermercados está vencido y mal rotulado.** Al corte ya correspondía junio = 82,1, mayo fue revisado a 83,0 y la base oficial es 2017=100, no 2004=100. Requiere redescarga y recálculo.
3. **Trabajo independiente tiene denominador distinto al publicado.** El cálculo excluye monotributo social; el rótulo genérico “empleo registrado” lo incluye según SIPA. Fijar universo y reconstruir base antes de interpretar el componente.
4. **Subocupación demandante usa definición de universo errónea.** El 7,5% está bien, pero es porcentaje de la PEA, no de ocupados; `pluriempleo` además es un nombre técnicamente distinto.
5. **Modelos no auditables.** Sentimiento digital necesita insumos congelados y parámetros; IVI necesita muestra e intervalo visibles y no tiene una medición externa equivalente.

## Bloqueos y límites de la auditoría

- No existe una segunda encuesta equivalente al IVI de UTDT al mismo corte. Los registros de denuncias no son sustituto metodológico.
- Google Trends no garantiza reproducción exacta sin exportación congelada y parámetros completos; por eso 58,2 no puede auditarse desde la publicación.
- Para carnes, motorización y empleadores pequeños, las fuentes externas confirman componentes, magnitud o tendencia pero no publican exactamente la combinación propia completa. Se evitó elevar esos casos a “confirmado”.
- La corroboración de prensa basada en una fuente oficial controla transcripción y contexto, pero no constituye independencia estadística plena. Esa limitación está reflejada en confianza y veredicto.

## Segundo barrido de los indicadores no verificables

Este segundo barrido se limita a los dos casos que quedaron como **No verificable independientemente**. Se buscaron encuestas con pregunta y universo comparables, microdatos o tabulados que permitieran reconstruir las cifras, documentación metodológica y mediciones externas del mismo constructo. Cuando sólo fue posible repetir una consulta a la misma plataforma, se la trató como prueba de reproducibilidad y no como corroboración estadística independiente.

### Resultado revisado

| Indicador | Primer veredicto | Evidencia nueva | Veredicto tras segundo barrido |
|---|---|---|---|
| Victimización IVI (`inseguridad`) | No verificable independientemente, baja | Se recuperaron ficha metodológica y desglose de abril; además, dos encuestas independientes del mismo constructo ubican históricamente la incidencia nacional en 26,4% y 27,5% | **Compatible, confianza media** |
| Sentimiento digital (`sentimiento_digital`) | No verificable independientemente, baja | Se reconstruyó exactamente el 58,2 y una nueva descarga dio 57,3; una encuesta externa comparable por temas no acompaña el supuesto constructo agregado | **No verificable independientemente, confianza baja** |

El conteo revisado que sustituye al del primer barrido es: **8 confirmados, 6 compatibles, 4 discrepantes y 1 no verificable independientemente** (19/19).

### A. Victimización IVI (`inseguridad`)

#### Qué pudo corroborarse

El informe de abril de 2026 fue recuperado en una reproducción documental y su cifra aparece también en prensa: **28,0% de los hogares**, en **40 centros urbanos**, declaró que algún integrante fue víctima de un delito durante los **12 meses anteriores**. El trabajo de campo fue del 6 al 17 de abril, con **996 entrevistas**. El desglose publicado fue GBA 29%, interior 28% y CABA 25%; 60% de las entrevistas se hicieron por teléfono fijo y 40% por celular. También son consistentes las comparaciones informadas: 30,1% en marzo de 2026 y 26,3% en abril de 2025. Esto corrobora cifra, período, unidad y universo declarados por el productor, aunque no aporta una segunda estimación contemporánea.

La plausibilidad externa mejora al reconstruir antecedentes del mismo concepto:

- La Encuesta de la Deuda Social Argentina de la UCA estimó en el tercer trimestre de 2016 que **26,4% de los hogares** tenía al menos un integrante víctima de un delito común durante los 12 meses previos.
- La Encuesta Nacional de Victimización 2017 de INDEC/Ministerio de Seguridad arrojó **27,5% de hogares** víctima de al menos un delito. El portal de la OEA sigue identificando 2017 como la última encuesta nacional oficial argentina disponible, por lo que no existe una contraparte oficial al corte de abril de 2026.
- El Panel de Hogares de la Universidad Nacional del Litoral formuló en 2024 prácticamente la misma pregunta y obtuvo **16,6%** (181 respuestas afirmativas sobre 1.090). Sirve para validar el tipo de medición, no para contrastar el 28% nacional: es otro territorio, diseño y población.

Los dos antecedentes nacionales —26,4% y 27,5%— no confirman abril de 2026, pero muestran que 28,0% está dentro de un orden de magnitud ya observado por operativos independientes. Los registros policiales no son un sustituto: sólo capturan hechos denunciados. El manual de UNODC/UNECE respalda las encuestas de victimización para medir la cifra no denunciada, y a la vez advierte que la ventana móvil de 12 meses, el recuerdo y el *telescoping* limitan las comparaciones temporales.

#### Reclasificación y evidencia aún faltante

Se reclasifica a **Compatible, confianza media**. La cifra y sus metadatos quedan confirmados como publicación del IVI y la magnitud converge con dos mediciones nacionales independientes, pero no se puede reproducir la estimación puntual de abril de 2026. Para elevarla a “confirmado” falta un segundo operativo nacional contemporáneo —o microdatos y ponderadores públicos del IVI— con la misma canasta de delitos, ventana de 12 meses, cobertura urbana y un intervalo de confianza. También faltaría publicar el valor de referencia de 4T-2023 usado por la card para auditar por completo el rebase.

Fuentes directas: [reproducción del Informe de Victimización IVI, abril de 2026](https://www.studocu.com/es-ar/document/universidad-de-san-andres/introduccion-a-las-ciencias-metodologia-de-la-investigacion-y-ciencia/informe-de-victimizacion-ivi-abril-2026-resultados-clave/163759721), [El Norte — 28% y características del operativo](https://diarioelnorte.com.ar/el-indice-de-victimizacion-volvio-a-subir-en-el-ultimo-ano-y-alcanzo-al-28-de-los-hogares-argentinos/), [UCA/CONICET — victimización de hogares, 2010-2016](https://repositoriosdigitales.mincyt.gob.ar/vufind/Record/CONICETDig_767567854b5058d4d5ae460f87723419), [INDEC — Encuesta Nacional de Victimización 2017](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-34-155), [Chequeado — resultado nacional de 27,5% de hogares](https://chequeado.com/ultimas-noticias/sola-el-delito-aumenta-cada-vez-mas-en-la-provincia-de-buenos-aires/), [OEA — inventario argentino de encuestas de victimización](https://www.oas.org/ios/countriesdetails.aspx?country=ARG&lang=es), [UNL — Panel de Hogares 2024](https://www.unl.edu.ar/observatoriosocial/wp-content/uploads/sites/80/2025/02/Onda-2024_Resultados-Ponderados-1.pdf), [UNODC/UNECE — Manual on Victimization Surveys](https://unece.org/statistics/publications/manual-victimization-surveys).

### B. Sentimiento digital (`sentimiento_digital`)

#### Reconstrucción del dato publicado

Los insumos locales congelados permiten reproducir el valor sin residuo. Para cada término exacto, el colector divide el interés de julio de 2026 por el promedio de octubre-diciembre de 2023 y multiplica por 100; después promedia los seis índices con igual peso.

| Término exacto | Oct-Dic 2023 | Julio 2026 | Índice rebaseado |
|---|---:|---:|---:|
| `inflacion` | 61, 68, 79 | 44 | 63,5 |
| `precios` | 67, 72, 88 | 45 | 59,5 |
| `dolar` | 100, 80, 91 | 18 | 19,9 |
| `empleo` | 58, 59, 58 | 37 | 63,4 |
| `inseguridad` | 61, 68, 40 | 37 | 65,7 |
| `corrupcion` | 77, 68, 46 | 49 | 77,0 |

El promedio es **58,1667**, que redondea exactamente a **58,2**. Una descarga nueva, el 25 de agosto, con los mismos términos, geografía AR, búsqueda web y ventana desde 2021 produjo índices 64,0; 56,8; 19,3; 65,1; 65,9 y 76,6: promedio **57,3**. La diferencia de **-0,9 puntos (-1,5%)** confirma que el orden de magnitud se reproduce, pero también evidencia la variación muestral de Google Trends. Es repetición de la misma fuente, no validación independiente.

La documentación de Google explica la causa: Trends trabaja con una muestra, normaliza por tiempo y geografía, incorpora ruido y puede devolver resultados distintos entre extracciones. Además, aquí se consultan *search terms*, no *topics*: `inflacion` sin tilde, por ejemplo, representa los caracteres introducidos y no necesariamente todo el concepto “inflación”. Consultar cada término por separado también deja cada serie en su propia escala 0-100; el rebase individual evita promediar niveles crudos, pero no demuestra que los seis términos midan una única variable latente ni que merezcan igual ponderación. La API oficial en acceso alfa promete escalamiento consistente, pero aún no ofrece una fuente pública estable para rehacer esta serie histórica.

#### Proxy externo de validación de constructo

Como control independiente se construyó un proxy con cuatro temas que aparecen tanto en el índice como en la encuesta mensual *What Worries the World* de Ipsos. Se dividió la proporción de argentinos que mencionó cada preocupación en julio de 2026 por la de diciembre de 2023:

| Tema | Dic. 2023 | Jul. 2026 | Índice encuesta (base dic. 2023=100) | Componente Trends comparable |
|---|---:|---:|---:|---:|
| Inflación | 70% | 33% | 47,1 | `inflacion`: 63,5 |
| Crimen/violencia | 43% | 35% | 81,4 | `inseguridad`: 65,7 |
| Desempleo | 32% | 60% | 187,5 | `empleo`: 63,4 |
| Corrupción | 34% | 33% | 97,1 | `corrupcion`: 77,0 |
| **Promedio simple** | — | — | **103,3** | **67,4** |

El proxy no es numéricamente equivalente: una respuesta de encuesta sobre “preocupación” no es frecuencia de búsqueda y el índice publicado agrega además `precios` y `dolar`. Precisamente por eso no corresponde usar 103,3 como corrección del 58,2. Sí es una prueba adversa de validez: la preocupación por desempleo casi se duplicó frente a diciembre de 2023, mientras la búsqueda exacta `empleo` cayó a 63,4. Sondeos de UBA, UdeSA y Atlas difundidos en agosto también ubican salarios y empleo entre los principales problemas. La divergencia impide interpretar 58,2 como una escala general de “sentimiento” o “urgencia social”; sólo describe este cesto predeterminado de búsquedas.

La literatura metodológica llega a la misma cautela. Una revisión sistemática de 360 estudios encontró debilidades frecuentes de validez interna, fiabilidad entre muestras y generalización; trabajos recientes documentan errores derivados de cambios en la recolección y recomiendan descargas repetidas y pruebas de robustez. La evidencia favorable para *nowcasting* usa selección de términos, validación fuera de muestra y modelos explícitos; no valida automáticamente un promedio simple de seis búsquedas.

#### Veredicto y evidencia aún faltante

Se mantiene **No verificable independientemente, confianza baja**. La afirmación acotada “el algoritmo definido produce 58,2 con la descarga guardada” está confirmada, y 57,3 muestra reproducibilidad aproximada. No está validada la equivalencia entre esa escala y sentimiento, preocupación o urgencia social.

Para una reclasificación se necesita: publicar el CSV versionado de cada extracción y sus parámetros; tomar al menos 5-10 muestras por corte y reportar mediana e incertidumbre; probar términos con/sin tilde y *topics*; justificar selección y pesos antes de observar resultados; y validar el índice completo contra una serie de encuestas contemporáneas como Ipsos, UBA o UdeSA. Hasta entonces, el rótulo técnicamente defendible sería **“atención de búsquedas en seis términos exactos”**, no sentimiento digital.

Fuentes directas: [Google Trends — preguntas frecuentes sobre muestreo y normalización](https://support.google.com/trends/answer/4365533?hl=es), [Google Trends — diferencia entre término y tema](https://support.google.com/trends/answer/17309543?hl=es), [Google — API de Trends en acceso alfa](https://developers.google.com/search/blog/2025/07/trends-api?hl=es-419), [Ipsos Argentina — julio de 2026](https://www.ipsos.com/es-ar/argentina-2026-mejora-la-percepcion-economica-pero-el-empleo-gana-centralidad), [Ipsos — informe argentino de julio de 2026](https://www.ipsos.com/sites/default/files/ct/news/documents/2026-08/Argentina%20Report%20-%20What%20Worries%20the%20World%20Jul%2026_ESP.pdf), [Ipsos — informe global de diciembre de 2023](https://www.ipsos.com/sites/default/files/ct/news/documents/2024-03/Global-Report-What-Worries-the-World-December-23.pdf), [El País — síntesis de sondeos de agosto de 2026](https://elpais.com/argentina/2026-08-21/los-salarios-y-el-empleo-son-las-nuevas-preocupaciones-de-los-argentinos-segun-los-sondeos.html), [Hölzl et al. — revisión sistemática, *Social Science Research*](https://www.sciencedirect.com/science/article/pii/S0049089X24001212), [Lyu et al. — errores de medición en Google Trends](https://link.springer.com/article/10.1007/s44248-024-00013-3), [Rovetta — reproducibilidad de Google Trends](https://www.sciencedirect.com/science/article/pii/S1386505624002260), [Niesert et al. — valor predictivo macroeconómico fuera de muestra](https://www.sciencedirect.com/science/article/pii/S0169207019300147).

## Tercer barrido — Sentimiento digital

### Decisión

El tercer barrido cambia el dictamen del indicador como constructo publicado: **Discrepante, confianza alta**. Esto no contradice que el número sea calculable. La afirmación estricta “esta canasta de seis términos produjo 58,2” está confirmada y su error de muestreo reciente es pequeño. Lo que queda refutado es el salto interpretativo de atención de búsqueda a **sentimiento/urgencia**, y por tanto la inversión “menos búsquedas = mejor” con la que puntúa en el ITCIS.

El conteo que sustituye al del segundo barrido queda en **8 confirmados, 6 compatibles, 5 discrepantes y 0 no verificables** (19/19). La recomendación es **retirarlo de la puntuación hasta rediseñarlo**. Puede conservarse como card contextual, renombrada “Atención de búsquedas en seis términos”, sin semáforo ni valencia positiva/negativa.

### 1. Auditoría de artefactos y estabilidad técnica

El store permite reproducir el dato: cada término se consulta solo, se divide por su propio promedio octubre-diciembre de 2023 y los seis cocientes se promedian con peso 1/6. Los valores congelados dan 58,1667 y redondean a 58,2. La propiedad de invariancia a un factor de escala es correcta; resuelve la normalización de cada consulta, no la validez de los términos ni del promedio.

La serie vigente tiene una historia metodológica muy corta. La canasta de seis términos y el esquema por término nacieron el **21 de agosto de 2026**, cuatro días antes de este corte. Los 67 puntos 2021-2026 son un *backcast* obtenido con consultas actuales, no 67 vintages observados en tiempo real. El ADR-0034 había validado otra canasta —cuatro términos en un payload compartido y con pesos implícitos por volumen—; su correlación `r=+0,76` con inflación no se transfiere automáticamente al indicador actual.

Se localizaron cinco capturas comparables del julio de 2026:

| Fecha/captura | Canasta |
|---|---:|
| 21-ago | 57,617 |
| 23-ago | 58,367 |
| 24-ago | 58,167 |
| 25-ago, store publicado | 58,167 |
| 25-ago, reconsulta de auditoría | 57,960 |

Media **58,055**, desvío estándar **0,284**, rango **0,750** y coeficiente de variación **0,49%**. Entre términos, `corrupcion` tuvo el mayor rango, 4,0 puntos. Cinco rondas adicionales completas —30 consultas, una por término— devolvieron exactamente 57,960 en la misma sesión. Esa igualdad es compatible con caché diario de Google, por lo que no equivale a cinco muestras independientes; las cuatro fechas distintas son la prueba más informativa.

La prueba también expuso fragilidad operativa. Sin el parche local, `pytrends` 4.9.2 falla contra `urllib3` por `method_whitelist`; después de las 30 consultas exitosas Google bloqueó con 429 todos los intentos de variantes con tilde, `desempleo`, `delito` y sugerencias de temas. El repositorio de `pytrends` está archivado desde abril de 2025 y su propio mantenedor advierte que otro wrapper no corrige la calidad de los datos. El cache evita perder el número, pero puede mezclar términos descargados en días distintos y no aporta intervalo de incertidumbre.

**Conclusión de fiabilidad:** el 58,2 es reproducible aproximadamente y estable en el corto plazo. Esto valida la tubería y la aritmética; no valida qué representa.

### 2. Validación longitudinal contra preocupaciones declaradas

Se reconstruyó un panel de diez ondas de *What Worries the World* de Ipsos, usando sólo los cuatro conceptos que pueden alinearse con la canasta: inflación, desempleo, crimen/violencia y corrupción. Para una comparación homogénea se rebasó **cada serie de encuesta y cada término de Trends a diciembre de 2023=100** y luego se promediaron los cuatro.

Esta normalización corrige una limitación del segundo barrido: allí el 103,3 de Ipsos (base diciembre) se contrastó de forma ilustrativa con 67,4 de Trends (base 4T-2023). La comparación equivalente para julio es **103,3 versus 79,6**.

| Onda | Ipsos, preocupaciones (dic-23=100) | Trends, cuatro términos (dic-23=100) |
|---|---:|---:|
| dic-2023 | 100,0 | 100,0 |
| nov-2024 | 91,2 | 111,8 |
| mar-2025 | 95,1 | 103,6 |
| may-2025 | 92,0 | 109,3 |
| jul-2025 | 99,5 | 99,9 |
| nov-2025 | 99,6 | 95,1 |
| dic-2025 | 98,7 | 76,5 |
| mar-2026 | 98,9 | 97,1 |
| abr-2026 | 99,5 | 98,2 |
| jul-2026 | 103,3 | 79,6 |

Si Trends midiera preocupación, la relación esperada sería positiva. Resultó **r=-0,749** en niveles incluyendo la base y **r=-0,788** en las nueve ondas posteriores. En variaciones entre ondas —intervalos irregulares, por lo que es una prueba secundaria— dio **r=-0,542** y sólo **3 de 9** movimientos compartieron dirección. Por término, las correlaciones posteriores a la base fueron: inflación +0,157; empleo/desempleo -0,129; inseguridad/crimen +0,383; corrupción -0,518. Ninguno ofrece una validación fuerte y dos tienen el signo opuesto.

El desacople actual no depende de una sola encuestadora. En julio, Ipsos ubicó desempleo en 60%, crimen en 35%, inflación en 33% y corrupción en 33%. El Monitor de la UBA obtuvo falta de trabajo/desempleo 61%, bajos salarios 57%, inseguridad 46% y corrupción 45% sobre 2.895 casos; UdeSA informó falta de trabajo 39%, bajos salarios 36%, corrupción 34% y pobreza 30%. La búsqueda literal `empleo`, en cambio, está en 63,4 frente a su 4T-2023. Es una conducta distinta, no una medición sustituta.

### 3. Validación contra índices de confianza

Se hicieron dos pruebas adicionales, esperando signo **negativo**: más búsquedas de urgencia deberían acompañar menor confianza.

**Ipsos Global Consumer Confidence.** Entre diciembre de 2025 y julio de 2026, los valores publicados para Argentina fueron 47,9; 48,6; 44,7; 40,3; 40,4; 40,8; 37,4 y 41,8. La canasta Trends fue 61,1; 70,8; 65,3; 71,8; 70,0; 62,4; 58,3 y 58,2. La correlación fue **+0,216 en niveles** y **+0,061 en cambios**, ambos con signo contrario al esperado; sólo 4 de 7 movimientos tuvieron dirección inversa. Son ocho meses, insuficientes para estimación definitiva pero incompatibles con una señal contemporánea clara.

**ICC de UTDT usado en el proyecto.** En los 59 meses comunes, julio de 2021-julio de 2026, la correlación fue **-0,126 en niveles** y **+0,082 en cambios mensuales**: débil o de signo incorrecto. El resultado favorable citado por ADR-0222 sí se reproduce en los últimos 18 meses: `r=-0,562` sobre 17 cambios. Pero al mover esa misma ventana de 18 meses a lo largo de la historia aparecen 42 estimaciones: sólo **8 negativas**, 34 positivas, mediana **+0,194**, mínimo **-0,562** y máximo **+0,632**. La ventana elegida es literalmente la más favorable de las 42 y no generaliza. Además, la auditoría principal determinó que la serie local de ICC está extraída de la columna CABA, no del total nacional, debilitando aún más ese control.

Contra la inflación mensual del INDEC la canasta muestra `r=+0,655` en los 47 meses disponibles y +0,667 en los últimos 36, pero cae a **-0,119 en los últimos 18**. Es señal de régimen: recoge bien el episodio de aceleración 2022-2023 y deja de acompañar la inflación reciente. Una correlación histórica impulsada por el período usado como base no demuestra sentimiento ni capacidad prospectiva.

### 4. Por qué la interpretación falla

- La propia ficha reconoce “mide atención, no sentimiento”, pero el score impone una valencia: menor atención se convierte automáticamente en bienestar. La literatura y Google sólo sostienen la primera proposición.
- Google define un término como la secuencia literal escrita. `inflacion`, `dolar` y `corrupcion` sin tilde no capturan por definición todas las grafías, sinónimos ni conceptos; Google recomienda *topics* cuando se busca un concepto general. No se publicó una prueba de sensibilidad a esas elecciones.
- `empleo` puede ser búsqueda de portales o vacantes, mientras la encuesta pregunta preocupación por **desempleo**. `corrupcion` mide saliencia de escándalos; `dolar` mezcla cotización, dólar blue, turismo y ahorro. Las seis direcciones no comparten valencia.
- El peso igual es transparente, pero no estimado. Los seis términos son casi ortogonales según el propio ADR: eso contradice, más que respalda, tratarlos como manifestaciones intercambiables de un solo factor.
- El componente convierte 58,2 en un valor invertido bruto de **171,8**, recortado en 140. Así aporta el máximo “positivo” pese a que las encuestas muestran máximos o aumentos de preocupación laboral. Con peso efectivo de 1,5%, el techo agrega **0,6 puntos** al ITCIS frente a dejar el componente neutral en 100.

Los resultados coinciden con la evidencia metodológica externa. La revisión de Hölzl et al. sobre 360 estudios encuentra que la mayoría no comprueba validez interna, fiabilidad entre muestras ni generalización. Cebrián y Domenech muestran que el error depende de popularidad y número de extracciones y que promediar descargas reduce inconsistencias; Gummer y Oehrlein documentan un continuo fiabilidad-volumen. La guía aplicada de Lolić et al. propone selección justificada, pretratamiento, PCA/factores dinámicos o modelos predictivos y validación, no una suma ad hoc. Google, por su parte, aclara que Trends es una muestra normalizada con ruido y “no es una encuesta científica”.

### 5. Retiro y rediseño recomendado

**Acción inmediata:** sacar `sentimiento_digital` del cálculo puntuable y conservarlo sólo como contexto descriptivo. No hace falta borrar su serie: debe rotularse como atención relativa de seis términos y mostrarse por término, sin “mejor/peor”, inversión, semáforo ni techo.

**Para volver a puntuarlo:** primero definir un objetivo observable —preocupaciones de Ipsos/UBA/UdeSA, ICC de UTDT/Ipsos o un nowcast económico— y no llamarlo genéricamente sentimiento. Después:

1. Predeclarar familias de términos y *topics*, incluyendo tildes, sinónimos y búsquedas de intención (`desempleo`, `buscar trabajo`, etc.); auditar consultas relacionadas y polisemia.
2. Congelar cada vintage y reunir 5-10 extracciones en días distintos; reportar mediana, rango e ICC de fiabilidad. Las repeticiones dentro del mismo caché diario no cuentan como muestras independientes.
3. Usar la API oficial de Trends, hoy en alfa y con escala consistente, cuando haya acceso. `pytrends` archivado no es una base sostenible. Cambiar de scraper sólo resuelve transporte, no muestreo ni validez.
4. Separar entrenamiento y validación temporal. Comparar promedio simple, pesos regularizados, PCA y factor dinámico con evaluación *rolling out-of-sample*. Exigir signo estable y mejora frente a un baseline que use sólo el último valor de la encuesta.
5. Mantener por separado saliencia, preocupación y polaridad. Si el objetivo es sentimiento, usar la encuesta directamente o texto con clasificación validada; el volumen de búsqueda puede ser una covariable, nunca la etiqueta.

Como alternativas de datos, el Planificador de Palabras Clave de Google Ads ofrece promedios mensuales absolutos o estimados para palabras exactas, aunque redondeados y orientados a publicidad; el dataset internacional de Trends en BigQuery sólo cubre los 25 términos principales y emergentes, útil para saliencia pero no para esta canasta fija. Ninguno reemplaza una encuesta para medir valencia. La solución más simple y auditable es ampliar el peso de ICC/encuestas hasta que un modelo de búsquedas supere una validación externa prospectiva.

Fuentes metodológicas directas: [Google — muestreo, normalización y límites de Trends](https://support.google.com/trends/answer/4365533?hl=es), [Google — términos, grafías y *topics*](https://support.google.com/trends/answer/4359550?hl=es), [Google — término literal frente a tema conceptual](https://support.google.com/trends/answer/17309543?hl=es), [Google Trends API alfa — escala consistente y ventana de cinco años](https://developers.google.com/search/apis/trends), [repositorio archivado de pytrends](https://github.com/GeneralMills/pytrends), [aviso del mantenedor de pytrends](https://github.com/GeneralMills/pytrends/issues/636), [Hölzl et al. — revisión sistemática de 360 estudios](https://madoc.bib.uni-mannheim.de/68637/1/1-s2.0-S0049089X24001212-main.pdf), [Cebrián y Domenech — inconsistencias y número de extracciones](https://doi.org/10.1016/j.techfore.2024.123318), [Gummer y Oehrlein — continuo fiabilidad-volumen](https://journals.sagepub.com/doi/10.1177/08944393241279421), [Lolić et al. — construcción de indicadores con Google Trends](https://ideas.repec.org/a/eee/teinso/v77y2024ics0160791x24000253.html), [Google Ads — métricas históricas de Keyword Planner](https://support.google.com/google-ads/answer/3022575/about-keyword-planner-forecasts), [Google Cloud — dataset internacional de Trends en BigQuery](https://cloud.google.com/blog/products/data-analytics/international-google-trends-datasets-in-bigquery/).

Fuentes de validación: [Ipsos dic-2023](https://www.ipsos.com/sites/default/files/ct/news/documents/2024-03/Global-Report-What-Worries-the-World-December-23.pdf), [Ipsos nov-2024](https://www.ipsos.com/sites/default/files/ct/news/documents/2024-12/Reporte%20Argentina-%20What%20Worries%20the%20World%20Nov%2024-ESP.pdf), [Ipsos mar-2025](https://www.ipsos.com/sites/default/files/ct/news/documents/2025-04/Argentina%20Report%20-%20What%20Worries%20the%20World%20Mar%2025.pdf), [Ipsos may-2025](https://www.ipsos.com/sites/default/files/ct/news/documents/2025-06/Reporte%20Argentina%20-%20What%20Worries%20the%20World%20Mayo%2025.pdf), [Ipsos jul-2025](https://www.ipsos.com/sites/default/files/ct/news/documents/2025-08/Argentina%20Report%20-%20What%20Worries%20the%20World%20Jul%2025_ESP.pdf), [Ipsos nov-2025](https://www.ipsos.com/sites/default/files/ct/news/documents/2025-12/Argentina%20Report%20-%20What%20Worries%20the%20World%20Nov%2025_ESP.pdf), [Ipsos dic-2025](https://www.ipsos.com/sites/default/files/ct/news/documents/2026-01/Argentina%20Report%20-%20What%20Worries%20the%20World%20Dec%2025_ESP.pdf), [Ipsos mar-2026](https://www.ipsos.com/sites/default/files/ct/news/documents/2026-03/Argentina%20Report%20-%20What%20Worries%20the%20World%20Mar%2026_ESP.pdf), [Ipsos abr-2026](https://www.ipsos.com/sites/default/files/ct/news/documents/2026-05/Argentina%20Report%20-%20What%20Worries%20the%20World%20Apr%2026_ESP.pdf), [Ipsos jul-2026](https://www.ipsos.com/sites/default/files/ct/news/documents/2026-08/Argentina%20Report%20-%20What%20Worries%20the%20World%20Jul%2026_ESP.pdf), [Ipsos Consumer Confidence dic-2025](https://www.ipsos.com/es-ar/confianza-en-alta-el-consumidor-argentino-mantiene-el-optimismo-y-enciende-una-luz-de-esperanza), [Ipsos Consumer Confidence ene-2026](https://www.ipsos.com/es-ar/confianza-del-consumidor-argentina-muestra-una-leve-mejora-mensual-pero-lidera-la-caida-anual-en), [feb-2026](https://www.ipsos.com/es-ar/la-confianza-del-consumidor-se-desploma-73-puntos-y-marca-el-peor-desempeno-de-latam), [mar-2026](https://www.ipsos.com/es-ar/arg-q1-2026-tendencia-en-baja-de-la-confianza-del-consumidor), [abr-2026](https://www.ipsos.com/es-ar/confianza-del-consumidor-argentina-permanece-al-final-de-la-tabla-de-latinoamerica), [may-2026](https://www.ipsos.com/es-ar/consumidor-arg-2026-confianza-en-pausa-y-mindset-selectivo), [jun-2026](https://www.ipsos.com/es-ar/confianza-consumidor-arg-pierde-impulso-y-registra-la-mayor-caida-anual), [jul-2026](https://www.ipsos.com/es-ar/argentina-recupera-confianza-pero-sigue-entre-los-mercados-menos-optimistas-de-latam), [UBA/OPSA — monitor julio de 2026](https://www.infobae.com/economia/2026/08/10/el-59-de-los-argentinos-considera-negativa-la-situacion-economica-y-el-desempleo-encabeza-las-preocupaciones-segun-un-informe/?outputType=amp-type), [El País — triangulación UBA, UdeSA y Atlas](https://elpais.com/argentina/2026-08-21/los-salarios-y-el-empleo-son-las-nuevas-preocupaciones-de-los-argentinos-segun-los-sondeos.html).
