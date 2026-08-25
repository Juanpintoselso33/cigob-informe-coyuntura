# Auditoría externa de los indicadores publicados — Política

**Snapshot auditado:** `web/src/data/informe.json`, generado el 25 de agosto de 2026.
**Fecha de corte de la auditoría:** 25 de agosto de 2026.
**Cobertura:** 19 de 19 indicadores publicados del cinturón Política.

## Resultado ejecutivo

| Veredicto | Cantidad |
|---|---:|
| Confirmado | 4 |
| Compatible | 7 |
| Discrepante | 2 |
| No verificable independientemente | 6 |
| **Total** | **19** |

Los dos errores materiales encontrados son:

1. **Transferencias federales:** el dato nominal de CIGOB coincide con Hacienda (43,1%), pero el resultado real publicado (+0,8%) no coincide con dos estimaciones externas sobre el mismo agregado anual (+1,6% de IARAF y +1,7% de Politikon). La diferencia no es redondeo: debe revisarse el deflactor o el modo de aplicarlo a flujos mensuales.
2. **Cobertura judicial:** el valor de 69,63% es plausible luego de las designaciones de junio-julio, pero la explicación publicada dice simultáneamente “604 de 955”, que equivale a 63,25%. El valor y el desglose pertenecen a cortes distintos.

También hay tres problemas de transparencia que no permiten llamar “confirmado” a un indicador aunque el orden de magnitud sea plausible: 14 comunicados empresarios detectados y todavía no codificados; agregados propios de votaciones sin matriz auditable publicada; y conteos basados en buscadores o APIs cuya descarga subyacente no queda enlazada desde la ficha.

## Metodología

- Se tomó como verdad de lo publicado el snapshot indicado, no el cache ni una corrida posterior.
- Para cada indicador se comprobó valor, período, unidad, universo y definición. El código, los registros curados y las fichas locales se usaron únicamente para entender el cálculo y detectar inconsistencias internas.
- La fuente oficial original se usó como control primario. Para confirmar se exigió además una fuente externa —academia, organización especializada o prensa seria— o una reconstrucción de todos los eventos subyacentes mediante fuentes públicas.
- **Confirmado:** la cifra y el universo se reproducen o una fuente independiente informa el mismo resultado. **Compatible:** la evidencia independiente respalda magnitud y dirección, pero no permite reproducir exactamente el agregado de CIGOB. **Discrepante:** hay una diferencia material de cifra, período, unidad, universo o explicación. **No verificable independientemente:** no existe una corroboración externa suficientemente equivalente o el cálculo propio no se puede reconstruir con lo publicado.
- En promedios, índices de Rice, saldos codificados y ventanas móviles no se trató como confirmación que una noticia fuera meramente coherente con el resultado.

## Matriz completa 19/19

| # | Indicador | Dato publicado y período | Veredicto | Confianza | Evidencia externa y diferencia | Corrección recomendada |
|---:|---|---|---|---|---|---|
| 1 | Ventaja LLA−PJ (Votómetro) | 4,3 pp; 22-07-2026; LLA 32,1 vs PJ 27,8; 9 encuestas | Compatible | Media | [EncuestAR](https://encuestar.netlify.app/encuestas/) muestra para el entorno temporal resultados heterogéneos: Trends 21–28 jul da LLA 32/PJ 30 (+2), mientras sondeos de mayo-junio van de ventaja opositora a ventajas oficialistas amplias. El +4,3 es plausible, pero no se publica la lista de las 9 encuestas ni sus pesos diarios para reproducirlo. | Publicar las 9 filas, fecha de campo, calificación, decaimiento y peso final. Rotular “agregado propio”, no “dato de julio” sin día de cálculo. |
| 2 | Ratio DNU / leyes | 1,92; 48 DNU/25 leyes; 365 días al 25-08-2026 | No verificable independientemente | Baja | El [balance de Directorio Legislativo](https://alertas-v3.directoriolegislativo.org/eaf3412e-7554-4596-a08f-a811176ad20b%40DL%20-%20Balance%20Legislativo%20-%20Diciembre%202025.pdf) confirma un uso elevado de decretos y baja producción legislativa, pero usa período parlamentario y categorías distintas. La búsqueda de la frase “necesidad y urgencia” es una aproximación y no hay listado público CIGOB de las 48 normas. | Publicar los 48 números de DNU y las 25 leyes con fecha. Clasificar DNU por tipo normativo oficial, no sólo por frase textual. |
| 3 | Brecha de expectativas obra pública−privada | −1,1 pp, promedio móvil 12 meses; `fecha_dato` 01-09-2026 | Compatible | Media | La prensa que reproduce el cuadro INDEC para jun–ago informa saldos: privada 14,4−18,3=−3,9; pública 16,1−23,7=−7,6; brecha mensual −3,7 pp, dirección compatible con el promedio de −1,1 ([APF Digital](https://www.apfdigital.com.ar/amp/noticias/2026/07/12/462859-encuesta-cualitativa-de-la-construccion-del-indec-preve-perspectivas-desfavorables-para-el-periodo-junio-agosto-2026)). No se pudo reconstruir externamente los 12 meses. `2026-09-01` es el extremo del trimestre esperado, no una observación futura. | Separar `fecha_publicacion`, `mes_encuesta` y `periodo_expectativa`; mostrar los 12 saldos mensuales. |
| 4 | Postura pública de AEA y UIA | −0,429; 2 apoyos/5 críticas, 12 meses a ago-2026 | No verificable independientemente | Baja | La dirección crítica está respaldada: [El País](https://elpais.com/argentina/2026-03-05/los-grandes-empresarios-de-argentina-alertan-sobre-la-critica-situacion-de-la-industria-y-le-reclaman-respeto-a-milei.html) documentó los reclamos contemporáneos de UIA y AEA. Pero la selección y codificación exacta de siete textos es propia. Además, el snapshot admite **14 comunicados pendientes de codificar**, más que los siete computados: el saldo puede cambiar materialmente. | No puntuar mientras haya pendientes dentro de la ventana. Publicar corpus, regla de inclusión, codificación por caso y fecha de cierre; recalcular 7/7 sólo con corpus completo. |
| 5 | Conflictividad social (país) | −24,1%; 1.978 eventos en 12 meses hasta jul-2026 vs 2.605 en 2023 | No verificable independientemente | Baja | [ACLED Argentina](https://acleddata.com/country/argentina) permite comprobar definición y cobertura territorial, pero no expone en una página pública el agregado exacto. [FLACSO](https://politicaspublicas.flacso.org.ar/wp-content/uploads/2024/12/Informe-No-46_-La-conflictividad-social-durante-el-primer-ano-del-gobierno-de-Javier-Milei-1.pdf) confirma conflictividad sostenida con otra base y metodología, no los conteos 1.978/2.605. | Versionar el extracto ACLED con filtros, fecha de descarga, tipos de evento y deduplicación; aclarar que 12 meses móviles se comparan con un año calendario. |
| 6 | Jornadas individuales no trabajadas | 4.760.195; 12 meses hasta may-2026 | Compatible | Media-alta | [Infobae](https://www.infobae.com/politica/2026/02/22/conflictividad-laboral-la-cantidad-de-paros-que-hubo-en-2025-fue-la-mas-baja-en-las-ultimas-dos-decadas/) informa 4.493.000 jornadas en 2025; la cifra móvil de CIGOB es compatible al sustituir meses de 2025 por ene–may 2026. La definición huelguistas × duración coincide con literatura académica ([UNLP/Redalyc](https://www.redalyc.org/journal/3873/387378739017/html/)). No hallamos una suma externa exacta hasta mayo. | Publicar los 12 valores mensuales que suman 4.760.195 y precisar si se incluyen ámbitos público y privado y conflictos nacionales. |
| 7 | Transferencias federales reales (IAF) | +0,8% real; 2025 vs 2024; nominal +43,1%, IPC +41,9% | Discrepante | Alta | Hacienda confirma $60.285.191,1 millones vs $42.133.458,3 millones y +43,1% nominal ([Boletín Fiscal 4T-2025](https://www.economia.gob.ar/onp/documentos/boletin/4totrim25/4totrim25.pdf)). Pero IARAF estima +1,6% real ([Tiempo de San Juan](https://www.tiempodesanjuan.com/economia/como-le-fue-san-juan-en-el-reparto-la-plata-nacional-moderado-en-el-ano-mejor-en-diciembre-n420386)) y Politikon +1,7% ([El Diario de La Pampa](https://www.eldiariodelapampa.com.ar/la-pampa/68249/la-pampa-quedo-entre-las-provincias-con-menor-crecimiento-de-la-coparticipacion)). | Reproducir deflación mes a mes a pesos constantes y contrastarla contra IARAF/Politikon. Si se mantiene +0,8%, documentar qué IPC promedio y ponderación producen la diferencia. |
| 8 | Eficacia legislativa del Ejecutivo | 15,4%; 2 de 13 proyectos enviados 25-08-2024/25-08-2025 y madurados un año | No verificable independientemente | Baja | Las [estadísticas del Senado](https://www.senado.gob.ar/parlamentario/estadisticas) y el [balance de Directorio Legislativo](https://directoriolegislativo.org/es/informes/balance-legislativo-2024/) muestran proyectos del PEN convertidos en ley, pero no usan la cohorte madurada de CIGOB. No se publican los 13 expedientes ni los dos matches; por tanto, no se puede comprobar universo ni enlace proyecto→ley. | Publicar cohorte completa, expediente, fecha de envío, ley resultante y regla para tratados, retiros, reproducciones y proyectos fusionados. |
| 9 | Sesiones de Diputados sin quórum | 10,0%; 1 de 10 convocadas en 12 meses | Compatible | Media-alta | La sesión en minoría del 23-06-2026 está registrada por Diputados como “4° Reunión – Expresiones en Minoría” ([plan de labor](https://www.hcdn.gov.ar/secparl/dclp/plan_de_labor/plt.html)) y fue cubierta por [La Nación](https://www.lanacion.com.ar/politica/tregua-en-diputados-pro-la-ucr-y-los-provinciales-no-dieron-quorum-y-frustraron-la-ofensiva-nid23062026/). La prensa confirma el numerador; no encontramos un recuento independiente de las diez convocatorias. | Enlazar las diez convocatorias y declarar exclusiones (asambleas, informativas, homenajes, cuartos intermedios y convocatorias retiradas). |
| 10 | Adhesión provincial al RIGI | 66,7%; 16 de 24 jurisdicciones | Confirmado | Alta | La lista oficial contiene exactamente 16 provincias con su ley ([MAGyP](https://www.magyp.gob.ar/desarrollo-foresto-industrial/provincias-adheridas.php)). Una fuente legislativa provincial también afirmó que ya eran 16 ([diario de sesiones de Río Negro](https://web.legisrn.gov.ar/legislativa/sesiones/documento?d=diario&id=1413)); el [Instituto de Crecimiento](https://institutocrecimiento.org/assets/archivos/RIGIConceptual.pdf) reproduce la lista. 16/24=66,67%. | Sin corrección de cifra. Cambiar la fuente visible: la página está alojada en MAGyP pero no es una “tabla del Ministerio de Agricultura” sobre política agropecuaria; enlazarla directamente. |
| 11 | Cohesión del bloque LLA (bicameral) | 99,8%; Rice, 34 actas divididas, 90 días; Diputados 100/Senado 99,5 | Compatible | Media | La cobertura de votaciones muestra disciplina casi total: en la votación del 06-08 los 21 senadores LLA votaron afirmativamente ([TN](https://tn.com.ar/politica/2026/08/07/uno-por-uno-que-senadores-votaron-a-favor-y-quienes-en-contra-de-la-ley-de-propiedad-privada/)); [Infobae](https://www.infobae.com/politica/2026/05/23/de-la-cohesion-a-los-sutiles-juegos-de-poder-la-compleja-anatomia-de-la-libertad-avanza-en-el-congreso/) describe una bancada altamente cohesionada. No hay publicación externa del agregado Rice de 34 actas ni de la ponderación 65/35. | Publicar matriz acta×legislador, criterio “acta dividida”, tratamiento de ausencias y fórmula bicameral. |
| 12 | Bloqueo sostenido | 33,3%; 1 de 3 normas desafiadas sigue en pie | Confirmado | Alta | Las tres normas de la ventana son los vetos a financiamiento universitario, emergencia pediátrica y ATN. Diputados insistió con las dos primeras el 17-09 y Senado completó la insistencia el 02-10; ATN sólo tuvo insistencia del Senado el 18-09 y sigue sin segunda cámara. La secuencia está documentada por [Chequeado](https://chequeado.com/el-explicador/leyes-aprobadas-vetos-e-insistencias-en-que-estado-esta-cada-uno-de-los-proyectos-de-la-oposicion-en-el-congreso/) y [El País](https://elpais.com/argentina/2025-09-19/milei-sufre-una-nueva-derrota-en-el-congreso-enfrentado-con-la-mayoria-de-los-gobernadores.html). 1/3=33,3%. | Sin corrección de cifra. En la ficha, enumerar siempre las tres normas para que el denominador no quede opaco. |
| 13 | Desafíos legislativos | 3 normas en 12 meses | Confirmado | Alta | Es el mismo universo reconstruido en la fila anterior: dos primeras votaciones de insistencia el 17-09-2025 y una el 18-09-2025. [El País](https://elpais.com/argentina/2025-09-17/el-congreso-argentino-rechaza-el-veto-de-milei-a-las-leyes-de-financiamiento-universitario-y-emergencia-pediatrica.html) confirma las dos primeras y la cobertura del 19-09 confirma ATN. | Sin corrección de cifra. Mostrar lista y fechas; aclarar que el dato se fecha por mes y que la ventana del código es de meses calendario, no exactamente 365 días. |
| 14 | Producción legislativa | 25 leyes sancionadas en 12 meses a ago-2026 | Compatible | Media | La baja base está confirmada por Directorio Legislativo: 11 leyes en el período 2025-26 ([balance](https://alertas-v3.directoriolegislativo.org/eaf3412e-7554-4596-a08f-a811176ad20b%40DL%20-%20Balance%20Legislativo%20-%20Diciembre%202025.pdf)). Para 2026, un recuento de prensa informaba 18 leyes al cierre del primer semestre ([Prensa Libre](https://prensalibreonline.com.ar/politica/pese-a-la-crisis-de-adorni-milei-logro-mas-leyes-en-el-primer-semestre)). El rolling de 25 es plausible al cruzar períodos, pero la fuente externa no ofrece el mismo corte. | Publicar las 25 leyes con fecha de sanción y definir si convenios internacionales y leyes promulgadas por insistencia cuentan. |
| 15 | Judicialización de la agenda | 1,57%; 114 de 7.273 sumarios SAIJ de 2026 con “medida cautelar”; marcado desactualizado | No verificable independientemente | Baja | No se encontró fuente académica o periodística que replique 114/7.273. El buscador [SAIJ](https://www.saij.gob.ar/busqueda) permite una consulta, pero el resultado cambia con la edición de la base. Además, el universo son todos los sumarios federal+nacional que mencionan cautelares, no litigios sobre medidas del Gobierno: la definición no sostiene el título “judicialización de la agenda”. | Renombrar “densidad de menciones cautelares en SAIJ” o construir un universo de causas contra políticas del PEN. Guardar URL/consulta y extracto fechado; resolver por qué el snapshot lo marca desactualizado pese a una consulta 2026. |
| 16 | Velocidad de resolución de la Corte | 45,4%; 26.524 resueltos/58.424 ingresados en 2025 | Confirmado | Alta | La [CSJN](https://w2.csjn.gov.ar/novedades/detalle/13002) publica exactamente 58.424 ingresos y 26.524 casos resueltos; 26.524/58.424=45,40%. [La Nación](https://www.lanacion.com.ar/politica/la-corte-de-tres-jueces-exhibe-un-record-en-la-resolucion-de-causas-nid24052026/) corroboró el saldo no resuelto de 31.900. Universo, año y fórmula coinciden. | Sin corrección de cifra. Aclarar que “expedientes” y “casos” se usan como equivalentes porque así los presenta el anuario. |
| 17 | Actividad de comisiones de control | 7 sesiones de Acusación+Disciplina en 12 meses a ago-2026 | No verificable independientemente | Media-baja | El archivo oficial del [Consejo](https://consejomagistratura.gov.ar/index.php/comisiones/) permite identificar las sesiones numeradas —incluida Disciplina del 19-08-2026—, pero no se encontró un observatorio o prensa que haya contado el mismo universo. La selección excluye sesiones conjuntas, extraordinarias y audiencias testimoniales, decisión metodológica de CIGOB. | Publicar las siete notas incluidas y las excluidas. Renombrar: “actividad” es descriptivo; “parálisis de denuncias” no se desprende del simple número de reuniones. |
| 18 | Cobertura de cargos judiciales | 69,63%; detalle: 604 titulares, 282 subrogantes, 69 sin cubrir sobre 955 | Discrepante | Alta | El corte previo era cercano a 63%: ACIJ/INECIP contabilizó 370 vacantes sobre 1.002 cargos al 17-04 ([informe](https://acij.org.ar/wp-content/uploads/2026/04/Quienes-podrian-ser-los-proximos-jueces-y-juezas-del-Poder-Judicial-de-la-Nacion-abril-2026.pdf)). Luego hubo 74 acuerdos y decenas de nombramientos ([Chequeado](https://chequeado.com/el-explicador/el-senado-aprobo-74-pliegos-judiciales-quien-es-quien-detras-de-estos-nombramientos/), [Infobae](https://www.infobae.com/politica/2026/06/25/pese-a-haber-nombrado-70-jueces-milei-sigue-sin-designar-a-la-jueza-michelli-la-justificacion-del-gobierno-y-los-3-casos-similares/)), por lo que 69,63% es plausible. Pero **604/955=63,25%, no 69,63%**; el valor incorpora designaciones posteriores mientras el texto conserva la foto del padrón. Además, 604+282+69=955, de modo que el desglose no puede explicar 69,63%. | Publicar el numerador actualizado (aprox. 665/955 si el 69,63% es correcto) y una tabla de altas/bajas posteriores al padrón; no mezclar composición del 05-06 con valor de agosto. Conciliar también 955 “habilitados” con el universo externo de 1.002 incluyendo no habilitados. |
| 19 | Alineamiento de senadores no-LLA por provincia | 57,0%; promedio simple de 24 provincias, 90 días a 06-08-2026 | Compatible | Media | La votación más reciente exhibe una coalición territorial mixta: 37 afirmativos, incluidos 21 LLA y apoyos de UCR, PRO, Misiones, Corrientes y Chubut; 33 negativos, incluidos peronistas y senadores de otras provincias ([Infobae](https://www.infobae.com/politica/2026/08/07/uno-por-uno-como-voto-cada-senador-la-ley-de-inviolabilidad-de-la-propiedad-privada/), [TN](https://tn.com.ar/politica/2026/08/07/uno-por-uno-que-senadores-votaron-a-favor-y-quienes-en-contra-de-la-ley-de-propiedad-privada/)). Es compatible con alineamiento levemente mayoritario, pero ninguna fuente externa reproduce el promedio provincial de todas las actas ni el 57,0%. | Publicar tabla provincia×acta y regla de promedio. Informar cuántas provincias tuvieron votos observados; no imputar 24 si alguna no participó. |

## Detalle y razonamiento por indicador

### 1. Ventaja LLA−PJ

La unidad y la resta están bien definidas: 32,1−27,8=4,3 pp. El problema no es aritmético sino de auditabilidad. EncuestAR ofrece una base externa útil y muestra que las mediciones cercanas al corte eran muy dispersas. Esa dispersión hace plausible un agregado +4,3 y, al mismo tiempo, impide inferirlo de una sola encuesta. Sin las nueve observaciones, sus calificaciones y el peso por recencia, el valor sólo puede calificarse como compatible.

### 2. Ratio DNU / leyes

La división publicada es correcta: 48/25=1,92. Sin embargo, “DNU” se detecta con una búsqueda textual dentro de decretos, no con un campo normativo inequívoco. Directorio Legislativo confirma la conclusión sustantiva —muchos decretos frente a pocas leyes—, pero no la ventana móvil ni los conteos. El valor exacto no es verificable independientemente mientras no se publique el inventario.

### 3. Brecha de expectativas de construcción

La evidencia periodística permite recalcular un mes del insumo y confirma que, en ese corte, la obra pública tenía un saldo más negativo que la privada. CIGOB publica un promedio de doce brechas, por lo que no corresponde comparar −3,7 mensual con −1,1 móvil como si fueran el mismo dato. La fecha futura es una cuestión de rotulado: septiembre es el final del trimestre que las empresas anticipan, no una observación realizada en septiembre.

### 4. Postura empresaria

Se comprobaron externamente pronunciamientos críticos y también mensajes de apoyo o valoración parcial. No se puede validar el saldo exacto sin aceptar la selección y la adjudicación propia de CIGOB. El problema decisivo es operativo: hay 14 textos pendientes dentro del corpus detectado y sólo siete computados en la ventana. Aunque algunos pendientes pudieran resultar neutros o quedar fuera por destinatario, el indicador no demuestra que el denominador esté cerrado.

### 5. Conflictividad nacional

ACLED define eventos y ofrece cobertura subnacional, pero el agregado exacto requiere descargar los datos con credenciales y repetir filtros. FLACSO cuenta protestas a partir de prensa y por eso sirve como contraste conceptual, no numérico. También debe advertirse que comparar una ventana móvil de 12 meses con todo 2023 introduce estacionalidad distinta aunque ambas duren aproximadamente un año.

### 6. Jornadas no trabajadas

El total anual 2025 de 4,493 millones informado por prensa es muy cercano al rolling 4,760 millones a mayo de 2026. La diferencia de 267 mil es plausible al desplazar cinco meses, y las magnitudes mensuales oficiales conocidas son suficientes para descartar un error de orden. Falta, no obstante, una tabla externa que replique exactamente la suma móvil.

### 7. Transferencias federales

El control nominal es exacto: el boletín fiscal informa 60,285 billones frente a 42,133 billones y +43,1%. La diferencia aparece al deflactar. CIGOB aplica un único IPC promedio anual y obtiene +0,8%; IARAF y Politikon, que trabajan con montos mensuales a precios constantes, obtienen alrededor de +1,6/+1,7%. Para un flujo distribuido durante todo el año, la práctica robusta es deflactar cada mes y luego sumar.

### 8. Eficacia legislativa

El indicador no mide “leyes del Gobierno en 2026”, sino el destino de una cohorte enviada un año antes y dejada madurar 365 días. Esa decisión evita castigar proyectos recién enviados, pero crea un universo que ninguna estadística externa estándar reproduce. Sin expediente por expediente, 2/13 no puede auditarse.

### 9. Falta de quórum

La única sesión fallida sí está corroborada y fechada. La tasa depende de qué se considera “sesión legislativa convocada”. El denominador puede variar si se incluyen expresiones en minoría, sesiones informativas, preparatorias, homenajes o convocatorias superpuestas; por eso se mantiene “compatible” hasta publicar las diez filas.

### 10. Adhesión al RIGI

Es el caso más limpio de la dimensión territorial: hay una lista de 16 provincias con ley identificada y una declaración legislativa independiente que coincide. El denominador 24 incluye las 23 provincias y CABA. Aunque la tabla no lista CABA entre las adheridas, eso no altera el 16/24.

### 11. Cohesión LLA

Las noticias y actas visibles muestran un bloque que en general vota unido; la última votación relevante tuvo apoyo de todos los senadores LLA. El índice de Rice excluye o trata de manera particular ausencias y sólo tiene sentido en votaciones divididas. La cifra 99,8 depende de 34 decisiones de inclusión y de una ponderación bicameral propia, por lo que la evidencia externa valida la lectura, no el decimal.

### 12–13. Bloqueo sostenido y desafíos

Ambos indicadores comparten el mismo denominador. En septiembre de 2025 se desafiaron tres vetos: universidad, pediatría/garrahan y ATN. Los dos primeros superaron ambas cámaras; el tercero sólo superó el Senado. Por eso hay tres desafíos, dos caídas y una norma sostenida: 1/3=33,3%. La reconstrucción de cada evento permite confirmar ambos resultados.

### 14. Producción legislativa

El orden de magnitud bajo está sobradamente respaldado, pero los recuentos públicos divergen porque algunos usan año calendario, otros período parlamentario y otros sólo iniciativas sustantivas. La ventana móvil de CIGOB cruza esos cortes. La forma de convertir “compatible” en “confirmado” es sencilla: publicar el inventario de 25 leyes.

### 15. Judicialización

La operación computada es 114/7.273=1,567%, redondeada correctamente. No obstante, una búsqueda por el texto “medida cautelar” mide cómo SAIJ titula o resume fallos, no cuántas políticas del Ejecutivo fueron judicializadas. El número puede ser técnicamente reproducible en un momento y conceptualmente no corresponder al nombre del indicador. Debe corregirse la definición antes de interpretar su semáforo como capital político.

### 16. Velocidad de la Corte

Es una reproducción directa y correcta del anuario: 26.524/58.424=45,4%. La lectura “por debajo de 100% acumula atraso” también es aritméticamente correcta para ese año, aunque no describe duración de los expedientes ni productividad por juez.

### 17. Sesiones de comisiones de control

El Consejo publica notas numeradas, lo que permite controlar huecos de secuencia. CIGOB suma sólo sesiones ordinarias numeradas de Acusación y Disciplina y excluye otros formatos. Ese criterio es defendible, pero no es obvio y no cuenta con corroboración externa; siete reuniones tampoco prueban por sí solas actividad sustantiva ni resolución de denuncias.

### 18. Cobertura judicial

La evolución externa explica por qué el porcentaje pudo subir: entre abril y julio se aprobaron y designaron decenas de jueces. El snapshot, sin embargo, mezcla el porcentaje actualizado con la composición estática del padrón. Si el denominador permanece en 955, 69,63% exige aproximadamente 665 titulares, no 604. La corrección debe ser de datos y texto juntos, no sólo una nota aclaratoria.

### 19. Alineamiento provincial en Senado

Las votaciones recientes confirman que varios senadores no-LLA de fuerzas provinciales acompañan al oficialismo mientras otros se oponen. El resultado 57% es razonable para ese cuadro. Pero promediar primero dentro de cada provincia y después entre provincias da el mismo peso a distritos con diferente cantidad de votos observados; es un indicador propio cuyo decimal no tiene corroboración independiente sin la matriz completa.

## Prioridades de corrección

1. **Alta:** reconciliar cobertura judicial (69,63% vs 604/955) y recalcular transferencias con deflación mensual.
2. **Alta:** suspender o marcar incompleto el saldo empresario hasta codificar los 14 pendientes.
3. **Alta:** corregir el nombre/universo de “judicialización de la agenda”.
4. **Media:** publicar inventarios de DNU, leyes, proyectos del PEN, convocatorias y normas desafiadas.
5. **Media:** publicar matrices de cohesión y alineamiento con tratamiento de ausencias.
6. **Baja:** separar fechas de publicación, observación y horizonte esperado en construcción; homogeneizar “365 días” frente a “12 meses calendario”.

## Limitaciones de esta auditoría

- ACLED no ofreció un agregado público indexable equivalente a la consulta local; no se confundió ausencia de corroboración con falsedad.
- SAIJ y el Consejo de la Magistratura son fuentes oficiales dinámicas. Una consulta posterior puede cambiar por edición o nuevas publicaciones.
- Las notas de prensa que reproducen datos oficiales sólo se usaron como corroboración cuando aportaban un recuento propio, un desglose o una reconstrucción del evento; no se consideró independencia una simple copia del comunicado original.
- Los veredictos se refieren al snapshot del 25-08-2026. No deben trasladarse automáticamente a una corrida posterior.

## Segundo barrido de los seis casos inicialmente no verificables

Esta sección conserva la matriz original y documenta una segunda investigación, más profunda, de sus seis casos inicialmente clasificados como **No verificable independientemente**. Se descompuso cada cifra, se reconstruyeron universos públicos cuando fue posible y se buscaron controles en fuentes oficiales alternativas, prensa, academia y archivos. Los veredictos revisados son los siguientes:

| Indicador revisado | Veredicto del segundo barrido | Confianza | Resultado decisivo |
|---|---|---|---|
| Ratio DNU / leyes | **Discrepante** | Alta | Los 48 son resultados de una búsqueda textual; sólo 37 están tipificados por InfoLeg como DNU. Además, las 25 leyes son publicaciones, no sanciones. |
| Postura pública de AEA y UIA | **Discrepante** | Alta | El saldo 2−5 sobre siete casos es reproducible, pero el corpus no estaba cerrado: había 14 textos pendientes, varios sustantivos. |
| Conflictividad social (país) | **No verificable independientemente** | Media-baja | La aritmética y el universo ACLED son coherentes; el archivo fechado que permitiría repetir 1.978/2.605 ya no está disponible sin sesión y su URL devuelve 404. |
| Eficacia legislativa del Ejecutivo | **Confirmado** | Alta | La cohorte pública contiene exactamente 13 expedientes PE/JGM y sólo dos aparecen en leyes sancionadas: 27.783 y 27.799. |
| Judicialización de la agenda | **Discrepante** | Alta para la definición; baja para el conteo | 114/7.273 está bien dividido, pero mide densidad de una frase en sumarios curados de todo tipo, no litigios contra la agenda del PEN. |
| Actividad de comisiones de control | **Confirmado** | Alta | Se reconstruyeron las siete sesiones numeradas: cuatro de Acusación y tres de Disciplina, sin huecos en cada secuencia. |

Aplicados estos resultados al conjunto de 19 indicadores, el balance revisado sería **6 confirmados, 7 compatibles, 5 discrepantes y 1 no verificable independientemente**. El cuadro inicial queda intacto para conservar la trazabilidad del primer barrido.

### SB-1. Ratio DNU / leyes — discrepante

**Componentes corroborables.** La operación publicada, 48/25=1,92, es aritméticamente correcta. El problema está en qué representan ambos conteos. La búsqueda de InfoLeg solicita `tipoNorma=Decreto`, una ventana por **fecha de publicación** y el texto libre “necesidad y urgencia”. Su resultado devuelve 48 normas, pero la propia ficha de resultados distingue el subtipo normativo: sólo **37** llevan la etiqueta “Decreto DNU”. Las otras once son diez decretos comunes y un decreto reglamentario que simplemente contienen la frase buscada en sus considerandos o referencias.

Los 37 DNU identificados son: 628, 627, 658, 697, 793, 805, 825, 849, 941 y 942 de 2025; y 2, 17, 26, 34, 41, 49, 73, 80, 88, 149, 203, 252, 264, 274, 314, 473, 490, 571, 580, 585, 594, 650, 667, 681, 717, 736 y 771 de 2026. Los falsos positivos son: **615, 651, 696, 812 y 931/2025; 27, 58, 79, 82, 605 y 710/2026**. La ficha oficial del [DNU 771/2026](https://www.argentina.gob.ar/normativa/nacional/norma-429094) lo rotula expresamente “Decreto DNU”; en cambio, el [decreto 710/2026](https://www.argentina.gob.ar/normativa/nacional/norma-428615/texto) se dicta por los incisos 1 y 2 del artículo 99 y regula compras de la OSFA, y el [decreto 58/2026](https://www.argentina.gob.ar/normativa/buscar-boletin?numero_boletin=35841&s=1) figura como reglamentario. Son controles directos de por qué la coincidencia textual no equivale a tipo normativo.

**Denominador y período.** InfoLeg devuelve 25 leyes porque el formulario también filtra por publicación en el Boletín Oficial. Sin embargo, el indicador dice “leyes sancionadas”. El recurso oficial alternativo de Diputados, [leyes sancionadas](https://datos.hcdn.gob.ar/api/3/action/datastore_search?resource_id=68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98&limit=500), contiene **22 sanciones definitivas** entre el 25-08-2025 y el 25-08-2026. La diferencia no es semántica menor: por ejemplo, la ley universitaria 27.795 fue [sancionada el 21-08-2025 y publicada el 21-10-2025](https://www.argentina.gob.ar/normativa/nacional/ley-27795-419006/normas-modifican), por lo que entra en el filtro InfoLeg pero cae fuera de una ventana por sanción.

**Cálculo reproducible y corrección.** Si se conserva el criterio efectivo de publicación para ambos términos, el resultado depurado es **37/25=1,48**. Si se respeta la definición publicada de leyes sancionadas, es **37/22=1,68**. Ninguno es 1,92. Debe usarse el subtipo oficial DNU y escoger una única fecha jurídica —publicación o sanción— para numerador y denominador. También debe publicarse el inventario, no sólo el total.

### SB-2. Postura pública de AEA y UIA — discrepante

**Componentes corroborables.** Los siete casos efectivamente codificados en la ventana sí forman un saldo reproducible: dos apoyos y cinco críticas al Ejecutivo, por lo que (2−5)/7=−0,4286. Se localizaron evidencias externas de los episodios centrales: [Infobae sobre el cierre de Fate y la reacción crítica de UIA](https://www.infobae.com/economia/2026/02/18/la-uia-lamento-el-cierre-de-fate-y-advirtio-que-la-industria-enfrenta-competencia-global-con-practicas-desleales/), [DataPortuaria sobre el apoyo de usuarios al avance de la Vía Navegable Troncal](https://dataportuaria.com/es/argentina/puertos/las-entidades-que-representan-a-los-usuarios-de-la-hidrovia-celebran-publicacion-de-la-resolucion-anpyn-n-deg-28-2026-que-da-por-finalizada-la-etapa-2-del-proceso-licitatorio-de-la-via-navegable-troncal), [El País sobre los reclamos simultáneos de UIA y AEA](https://elpais.com/argentina/2026-03-05/los-grandes-empresarios-de-argentina-alertan-sobre-la-critica-situacion-de-la-industria-y-le-reclaman-respeto-a-milei.html) y el [comunicado crítico completo de UIA del 11 de marzo](https://www.uia.org.ar/prensa/4226/). Por tanto, el problema no es la división ni que los siete eventos sean ficticios.

**Por qué el agregado publicado no es válido.** Al cierre existían **14 novedades sin segunda codificación**, frente a sólo siete observaciones puntuadas. No eran catorce piezas manifiestamente neutras. Entre ellas estaba “La UIA celebra la reducción de retenciones a productos industriales”, un apoyo explícito a una medida del Ejecutivo ([texto UIA](https://www.uia.org.ar/uia/novedades/la-uia-celebra-la-reduccion-de-retenciones-a-produ)); también “La UIA se reunió con Luis Caputo”, cuya cobertura independiente recoge preocupación por la demora de la reactivación y una batería de pedidos al Gobierno ([Infobae](https://www.infobae.com/economia/2026/05/19/tras-el-cruce-del-gobierno-con-los-industriales-caputo-se-reunio-con-la-uia-cuales-fueron-los-principales-ejes-de-discusion/)), y una toma de posición sobre el [Súper RIGI](https://www.uia.org.ar/uia/novedades/la-uia-analizo-el-impacto-del-super-rigi-en-el-des). Que algunos de los otros once resulten institucionales o neutros no permite omitir los tres sin adjudicarlos bajo la misma regla.

El registro metodológico local, además, declara que las novedades pendientes **no puntúan** hasta una segunda pasada con kappa suficiente. Publicar −0,429 mientras había más textos pendientes que computados contradice esa regla de cierre. No puede proponerse un saldo alternativo responsable sin codificar los 14 casos completos; sí puede afirmarse que −0,429 es el saldo de un **subcorpus incompleto**, no de la postura de AEA+UIA en doce meses. La corrección es suspender el valor, fechar el cierre del corpus y volver a calcular tras la adjudicación de los 14.

### SB-3. Conflictividad social nacional — sigue no verificable independientemente

**Componentes corroborables.** El numerador se compone de agosto de 2025 a julio de 2026 —el agosto de 2026 parcial se excluye— y suma 1.978 eventos; el año calendario 2023 suma 2.605. La variación es (1.978/2.605−1)×100=−24,07%, redondeada correctamente a −24,1%. La definición también coincide con el [codebook de ACLED](https://acleddata.com/methodology/acled-codebook): “Protests” incluye protesta pacífica, protesta con intervención y fuerza excesiva; “Riots” incluye manifestación violenta y violencia de turba. La [página de agregados](https://acleddata.com/conflict-data/download-data-files/aggregated-data) confirma que los archivos regionales se publican por semana y unidad administrativa 1. Como control de escala, ACLED informó que ya registraba **más de 2.000 protestas** en Argentina desde el inicio del gobierno de Milei hasta marzo de 2025 ([informe regional de abril de 2025](https://acleddata.com/update/latin-america-and-caribbean-overview-april-2025)).

**Intento de réplica y bloqueo.** El extracto utilizado declara como origen directo `Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-08-08.xlsx`, pero su [URL fechada](https://acleddata.com/system/files/2026-08/Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-08-08.xlsx) devuelve 404 en el segundo barrido y la página de descarga exige una sesión myACLED. El perfil de [Argentina en ACLED](https://acleddata.com/country/argentina) permite explorar tendencias, pero no expone una tabla indexable con los dos totales. FLACSO y la prensa usan otros universos —noticias o conflictos laborales—, por lo que no sustituyen la réplica ACLED.

La conclusión y la magnitud son **compatibles** con la evidencia publicada, pero el decimal sigue sin verificación independiente. Falta preservar y enlazar el XLSX exacto, su hash, las filas `Argentina × Protests/Riots`, las sumas mensuales y la fecha de descarga; alternativamente, una consulta exportable de ACLED Explorer con filtros y versión. Es el único caso de los seis que permanece en esta categoría.

### SB-4. Eficacia legislativa del Ejecutivo — confirmado

**Reconstrucción del denominador.** Se repitió la cohorte con los recursos públicos de Diputados: proyectos publicados entre el 25-08-2024 y el 25-08-2025, tipo “Mensaje y proyecto de ley”, expediente `PE` o `JGM`. Las búsquedas directas son [proyectos PE](https://datos.hcdn.gob.ar/api/3/action/datastore_search?resource_id=22b2d52c-7a0e-426b-ac0a-a3326c388ba6&q=-PE-&limit=500), [proyectos JGM](https://datos.hcdn.gob.ar/api/3/action/datastore_search?resource_id=22b2d52c-7a0e-426b-ac0a-a3326c388ba6&q=-JGM-&limit=500) y [leyes sancionadas](https://datos.hcdn.gob.ar/api/3/action/datastore_search?resource_id=68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98&limit=500). La lista cerrada tiene 13 expedientes:

`0012-JGM-2024`; `0016`, `0018`, `0019`, `0020`, `0021`, `0022`, `0023`, `0024` y `0025-PE-2024`; `0001`, `0003` y `0007-PE-2025`.

**Reconstrucción del numerador.** Dos `PROYECTO_ID` aparecen en el registro de sanciones: `0022-PE-2024`, suspensión de las PASO, ley **27.783** —el [Boletín de Asuntos Entrados de Diputados](https://www2.hcdn.gob.ar/secparl/dsecretaria/bae/bae2024/2.3.html) enlaza expresamente expediente y ley—; y `0003-PE-2025`, reformas tributarias, ley **27.799**, con sanción definitiva el 26-12-2025 corroborada tanto por [InfoLeg](https://www.argentina.gob.ar/normativa/nacional/ley-27799-2025-422008) como por el [registro del Senado](https://www.senado.gob.ar/parlamentario/comisiones/verExp/31.25/CD/PL?KeepThis=true&TB_iframe=true&height=700&width=950). La ficha pública del [proyecto 0022-PE-2024](https://www.hcdn.gob.ar/comisiones/permanentes/cjusticia/proyecto.html?exp=0022-PE-2024) confirma fecha, origen PEN y trámite.

No aparecen sanciones para los otros once identificadores. Por tanto, **2/13=15,38%, redondeado a 15,4%**, con período, universo y regla de maduración coincidentes. La mejora pendiente es de transparencia —publicar estas 13 filas en la ficha—, no de cifra.

### SB-5. Judicialización de la agenda — discrepante por definición

**Parte numérica.** 114/7.273×100=1,5674%, correctamente redondeado a 1,57%. Las consultas que definen el cálculo son [numerador: texto “medida cautelar”, 2026, faceta jurisdicción](https://www.saij.gob.ar/busqueda?o=0&p=1&f=Jurisdicci%C3%B3n&r=%28texto%3A%22medida%20cautelar%22%20AND%20fecha-rango%3A%5B20260101%20TO%2020261231%5D%29) y [denominador: todos los documentos de 2026](https://www.saij.gob.ar/busqueda?o=0&p=1&f=Jurisdicci%C3%B3n&r=%28fecha-rango%3A%5B20260101%20TO%2020261231%5D%29), sumando las facetas Federal y Nacional. En este segundo barrido el endpoint respondió 403, por lo que no fue posible certificar nuevamente los conteos dinámicos ni comparar un export contra la foto del snapshot.

**Parte conceptual.** La evidencia metodológica confirma que los sumarios no son un censo de expedientes. SAIJ capacita específicamente en **compilación, elaboración de sumarios e indización** de sentencias ([Poder Judicial de San Juan](https://www.jussanjuan.gov.ar/escuela-judicial/seminario-de-sumarizacion-e-indizacion-de-documentos-jurisprudenciales-y-de-tecnicas-de-tratamiento-documental-de-legislacion/)); incluso las pautas judiciales de sumarización explican que de un fallo pueden elaborarse varios sumarios, uno por doctrina, y que se abstraen hechos del caso ([Poder Judicial de Mendoza](https://www2.jus.mendoza.gov.ar/corte2/interno/pautas.php)). El denominador 7.273 mide, entonces, unidades editoriales heterogéneas, no causas ni políticas.

La academia define la judicialización de políticas públicas como intervención de tribunales sobre la formulación o ejecución de decisiones públicas; las cautelares son un mecanismo dentro de ese fenómeno ([artículo de FLACSO/CONICET](https://www.sciencedirect.com/science/article/pii/S0041863318300966)). La consulta publicada no exige que sea parte el Estado nacional, que se impugne una medida del PEN, que la cautelar se conceda ni que el litigio afecte su agenda. Incluye cautelares laborales, comerciales, penales y civiles entre privados. Por ello, aun si 114 y 7.273 se congelaran y reprodujeran exactamente, el indicador seguiría siendo **discrepante en universo y definición**. Debe renombrarse “densidad de menciones cautelares en sumarios SAIJ Federal+Nacional” o reconstruirse causa por causa un universo contra medidas del Ejecutivo. Para validar el número faltan además un export fechado, identificadores de los 114 documentos y estado concedida/rechazada.

### SB-6. Actividad de comisiones de control — confirmado

**Reconstrucción completa.** La ventana de septiembre de 2025 a agosto de 2026 contiene cuatro sesiones ordinarias numeradas de Acusación y tres de Disciplina:

- Acusación: [12.ª, 17-09-2025](https://consejomagistratura.gov.ar/index.php/2025/09/17/sesiono-la-comision-de-acusacion-12/); [13.ª, 17-12-2025](https://consejomagistratura.gov.ar/index.php/2025/12/17/sesiono-la-comision-de-acusacion-13/); [14.ª, 25-02-2026](https://consejomagistratura.gov.ar/index.php/2026/02/25/sesiono-la-comision-de-acusacion-14/); [15.ª, 15-07-2026](https://consejomagistratura.gov.ar/index.php/2026/07/15/sesiono-la-comision-de-acusacion-15/).
- Disciplina: [8.ª, 08-04-2026](https://consejomagistratura.gov.ar/index.php/2026/04/08/sesiono-la-comision-de-disciplina-8/); [9.ª, 03-06-2026](https://consejomagistratura.gov.ar/index.php/2026/06/03/sesiono-la-comision-de-disciplina-9/); [10.ª, 19-08-2026](https://consejomagistratura.gov.ar/index.php/2026/08/19/sesiono-la-comision-de-disciplina-10/).

Las secuencias 12→15 y 8→10 no tienen huecos y el [archivo general del Consejo](https://consejomagistratura.gov.ar/index.php/comisiones/) muestra la última sesión. La prensa corroboró de modo independiente la reunión del 19 de agosto y una decisión disciplinaria adoptada allí ([Agencia Noticias Argentinas](https://noticiasargentinas.com/politica/polemica-entre-abogados-y-jueces-de-cara-a-las-elecciones-del-consejo-de-la-magistratura-a-raiz-de-una-sancion_a6a861be181183b8c11309dcf)). Se excluyeron correctamente una conjunta de Disciplina con Administración del 19-11-2025 y una audiencia testimonial de Acusación del 10-03-2026, porque no son sesiones ordinarias numeradas. El reglamento dispone que reuniones ordinarias y extraordinarias se documenten por acta ([texto actualizado](https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-404-2007-131584/actualizacion)), lo que refuerza el control de cobertura.

El conteo **7** queda confirmado para el universo declarado. La cautela conceptual permanece: siete reuniones miden actividad formal, no cantidad de denuncias resueltas, sanciones ni ausencia de “parálisis”. El título público “Actividad de comisiones de control” es adecuado; no debe interpretarse como productividad sustantiva sin incorporar asuntos tratados y decisiones.

## Tercer barrido — Conflictividad social nacional (ACLED)

### Veredicto revisado

**Compatible — confianza alta.** El valor publicado queda reproducido exactamente desde el artefacto derivado y fechado que conserva el repositorio: **1.978/2.605−1 = −24,0691%, redondeado a −24,1%**. Además, una descarga autenticada lícita de la edición de ACLED inmediatamente posterior, con corte semanal 15-08-2026, produjo **1.979/2.605−1 = −24,0307%, redondeado a −24,0%**. La diferencia es un solo evento en el numerador —**0,0506%** de 1.978— y se localiza en julio de 2026, que pasó de 89 a 90; agosto parcial pasó de 82 a 114 y fue correctamente excluido por la regla de cierre. La base 2023 permaneció en 2.605.

No se eleva a “confirmado”: la segunda extracción proviene del mismo productor, una semana más tarde, y ACLED es una base viva que revisa retrospectivamente sus registros. Tampoco existe un conteo externo independiente con el mismo universo, clasificación y ventana. La evidencia independiente sí sostiene que se trata de un fenómeno y una escala plausibles, pero no replica el decimal: FLACSO registró **304 conflictos** en el corpus que presenta como 2025 y describió una estabilización relativa frente al primer año, aunque reconoce sesgos de proximidad e intensidad y usa sólo Clarín y Página/12 ([informe 49](https://politicaspublicas.flacso.org.ar/wp-content/uploads/2026/03/Informe-No-49_-La-conflictividad-social-durante-el-segundo-ano-del-gobierno-de-Javier-Milei-OPPRE-FLACSO-Argentina.pdf)); CIVICUS, citando ACLED, informó al menos 40 manifestaciones nacionales sólo en la segunda mitad de marzo de 2025 ([CIVICUS Monitor](https://monitor.civicus.org/explore/unprecedented-police-crackdown-on-pension-protests/)). El PDF de FLACSO contiene además una inconsistencia que impide usarlo como réplica temporal: su introducción imprime “11 de diciembre de 2025 a 10 de diciembre de 2026”, fechas futuras e incompatibles con un informe sobre el segundo año publicado en marzo de 2026; por el contenido parece un error de rotulado, pero no se lo corrige por inferencia. Son controles de contexto, no sustitutos numéricos.

Con esta reclasificación, el saldo consolidado de los 19 indicadores pasa a **6 confirmados, 8 compatibles, 5 discrepantes y 0 no verificables independientemente**. Este tercer barrido sustituye únicamente el veredicto de SB-3; conserva como registro los resultados anteriores.

### Réplica del snapshot y estabilidad entre publicaciones

El JSON derivado del cierre está congelado en el commit `1a958756fac46df7b068df8e46d3e1b53eb49640` del 25-08-2026 03:43:46 UTC ([archivo público en GitHub](https://github.com/Juanpintoselso33/cigob-informe-coyuntura/blob/1a958756fac46df7b068df8e46d3e1b53eb49640/projects/informe_coyuntura/data/gestion/protestas_caba.json); [contenido raw](https://raw.githubusercontent.com/Juanpintoselso33/cigob-informe-coyuntura/1a958756fac46df7b068df8e46d3e1b53eb49640/projects/informe_coyuntura/data/gestion/protestas_caba.json)). Su SHA-256 es `b053f959f03ee403c0f6447aab115d9f06e50b9aaed18bd9d6dc59ba8f8f5f52`. Las sumas mensuales reproducibles son:

| Ventana rotulada | Valores mensuales del store | Total |
|---|---|---:|
| ene–dic 2023 | 135, 196, 325, 315, 217, 303, 344, 152, 205, 105, 132, 176 | **2.605** |
| ago-2025–jul-2026 | 150, 193, 104, 132, 106, 127, 210, 216, 251, 279, 121, 89 | **1.978** |

El historial versionado aporta un control adicional de revisiones: la base 2023 fue 2.605 en las veinte versiones inspeccionadas. El móvil fue 1.925 con el archivo hasta la semana del 11-07, 1.952 hasta 18-07, 1.972 hasta 25-07 y 1.978 tanto en los cortes 01-08 como 08-08. Esto es coherente con la política de una base semanal que incorpora semanas y corrige eventos previos; no constituye una fuente independiente, pero sí una cadena de procedencia verificable.

La descarga de control utilizó la URL declarada por ACLED para `Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-08-15.xlsx` ([enlace fechado](https://acleddata.com/system/files/2026-08/Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-08-15.xlsx)), con SHA-256 `6d44a38ef359e243d2e7c93ce5c4ff7b267a553f6aa73feb55d31eef53d55189`. Bajo los mismos filtros arrojó 24 valores distintos de `admin1`, es decir, las 23 provincias más CABA. La reconciliación fue:

| Ventana | `Protests` | Filas | `Riots` | Filas | Total |
|---|---:|---:|---:|---:|---:|
| base rotulada 2023 | 2.421 | 727 | 184 | 150 | **2.605** |
| móvil rotulado ago-2025–jul-2026 | 1.858 | 689 | 121 | 100 | **1.979** |

Para el móvil de control, los subtipos suman exactamente 1.979: `Peaceful protest` 1.804, `Protest with intervention` 53, `Excessive force against protesters` 1, `Violent demonstration` 105 y `Mob violence` 16. Esto confirma que el filtro no omite subtipos dentro de los dos `event_type` elegidos.

### Auditoría de filtros, unidad temporal y agregación

La transformación local hace cuatro operaciones: exige `country == "Argentina"`; conserva `event_type` en `{Protests, Riots}`; suma la columna `events` sobre todos los `admin1` y `sub_event_type`; y asigna cada fila al mes de `week` mediante `%Y-%m`. La [guía de agregados de ACLED](https://acleddata.com/use-access/how-use-acleds-aggregated-data) confirma que `events` ya es el número de eventos discretos para una combinación semana–admin1–subtipo y que `week` es el **sábado inicial de una semana sábado–viernes**. El [codebook](https://acleddata.com/methodology/acled-codebook) confirma que `Protests` abarca protesta pacífica, con intervención y con fuerza excesiva, y `Riots`, manifestación violenta y violencia de turba. No hace falta una deduplicación local de filas agregadas: se depende de la identificación y revisión de eventos que realiza ACLED.

Hay, sin embargo, dos límites de implementación que deben corregirse en la documentación futura:

- **Los rótulos no representan meses calendario estrictos.** Todo el bloque semanal se atribuye al mes del sábado inicial. La “base 2023” corresponde en la práctica a semanas iniciadas del 07-01-2023 al 30-12-2023 —aproximadamente 07-01-2023 a 05-01-2024—, no al 01-01–31-12; el móvil corresponde a semanas iniciadas del 02-08-2025 al 25-07-2026 —aproximadamente 02-08-2025 a 31-07-2026—. Ambas ventanas comprenden 52 semanas, lo que conserva una duración comparable, pero no autoriza llamarlas literalmente “año calendario 2023” y “agosto a julio” sin esta salvedad.
- **El store pierde dimensiones de control.** Conserva sólo totales por mes, no la lista de jurisdicciones ni el desglose por `event_type` y `sub_event_type`. Por eso la afirmación “24 jurisdicciones” es cierta en la descarga de control del 15-08, pero no se puede probar exclusivamente desde el snapshot del 08-08. Tampoco hay una validación automática de que llegaron las 24 antes de publicar.

### Vías públicas y archivos alternativos agotados

No se usó ningún bypass. La [documentación de la API](https://acleddata.com/api-documentation/getting-started) exige una cuenta myACLED y token; una consulta anónima devolvió HTTP 403 `Access denied`. El [Explorer de Argentina](https://acleddata.com/country/argentina) ofrece visualización, pero no una tabla anónima exportable con estos filtros. La URL original del corte 08-08 devuelve 404 y la del 15-08 redirige al login cuando se abre sin sesión. La consulta del [índice CDX de Internet Archive para el XLSX del 08-08](https://web.archive.org/cdx/search/cdx?url=acleddata.com/system/files/2026-08/Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-08-08.xlsx&output=json&filter=statuscode:200) no devolvió capturas. Las búsquedas de código público en [GitHub](https://github.com/search?q=%22Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-08-08.xlsx%22&type=code) y de datasets en [Hugging Face](https://huggingface.co/datasets?search=ACLED) tampoco localizaron un espejo contemporáneo; los resultados hallados eran clientes de API, experimentos antiguos o subconjuntos ajenos al indicador. El historial Git del proyecto conserva únicamente el JSON agregado, no el XLSX.

Esta ausencia es consistente con la licencia vigente. El [EULA de ACLED](https://acleddata.com/eula) permite publicar materiales transformativos que no hagan reconstruible el dataset, pero prohíbe redistribuir el contenido original y compartir credenciales; la [política de atribución](https://acleddata.com/attributionpolicy) pide además consignar la fecha de acceso porque ACLED es una base viva. Por eso “subir el XLSX al repositorio público” no es una corrección admisible sin autorización escrita de ACLED.

### Decisión editorial y artefacto mínimo exigible

**Decisión: mantener el indicador, pero rediseñar su trazabilidad antes del próximo cierre; no retirarlo ahora.** La réplica una semana posterior, la diferencia de sólo un evento y la base idéntica descartan un error material en −24,1%. Debe cambiarse el rótulo a “52 semanas agregadas por semana de inicio vs 52 semanas base 2023”, o migrar a datos de evento para construir meses calendario verdaderos. Si en el próximo cierre no puede producirse el paquete de auditoría siguiente, corresponde **suspenderlo del score** hasta poder hacerlo:

1. XLSX original guardado en un archivo interno de acceso restringido, con autorización/licencia aplicable, URL, fecha y hora UTC de descarga, tamaño y SHA-256; nunca credenciales ni redistribución pública.
2. Manifiesto de consulta y transformación versionado: país exacto, tipos incluidos, tratamiento de todos los subtipos, campo sumado, regla de semana y mes parcial, zona temporal y commit del código.
3. Reconciliación no reversible y publicable con número y lista de `admin1`, totales por `event_type` y subtipo para base y móvil, cantidad de filas, sumas mensuales y controles `subtipos = tipo = total`.
4. Acta de segunda ejecución por otra persona con acceso autorizado a ACLED, sobre el mismo hash si se verifica el snapshot o sobre una edición posterior si se evalúa estabilidad; en el segundo caso deben listarse todas las revisiones por mes.
5. Consulta a ACLED sobre qué extractos o comprobantes pueden compartirse. Si autorizara un export congelado, ése sería el artefacto exacto para confirmar el dato; si no, el hash del archivo restringido más la doble ejecución y la tabla transformativa son la máxima auditabilidad lícita alcanzable.

Hasta completar ese paquete, el indicador es **compatible y materialmente reproducido, pero no confirmado por una fuente independiente**.
