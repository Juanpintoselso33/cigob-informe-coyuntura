# Reauditoría post-remediación de los indicadores de Política

**Corte:** 25 de agosto de 2026.

**Snapshot público auditado:** `projects/informe_coyuntura/web/src/data/informe.json`.

**Perímetro:** los 19 indicadores de la auditoría pre-remediación: 17 continúan como tarjetas públicas y 2 fueron suspendidos.

**Alcance:** cifra, período, unidad, universo, fórmula, definición, peso efectivo, tarjeta, ficha y series expuestas.

## Resultado ejecutivo

| Veredicto | Cantidad |
|---|---:|
| Confirmado | 9 |
| Compatible | 6 |
| Discrepante | 4 |
| No verificable independientemente | 0 |
| **Total** | **19** |

La remediación corrigió los cuatro problemas numéricos prioritarios del barrido anterior: `ratio_dnu` pasó de **1,92 a 1,48**; `iaf_transferencias`, de **+0,8% a +1,6% real**; ACLED, de **−24,1% a −24,0%** por una revisión de un evento; y `cobertura_judicial` conservó **69,63%**, pero ahora explica correctamente el numerador actualizado de **665 sobre 955**. También retiró del índice y de las tarjetas los dos constructos insostenibles, `apoyo_empresario` y `judicializacion`.

Persisten, sin embargo, cuatro discrepancias materiales:

1. **DNU:** el número ya usa 37 normas tipificadas como `Decreto DNU` y 25 leyes publicadas, pero la fórmula y la ficha visibles todavía dicen “DNU dictados / leyes sancionadas” y describen la búsqueda textual descartada.
2. **IAF:** el valor ya resulta de deflactar cada flujo mensual y coincide con la estimación externa de IARAF, pero la fórmula/ficha pública todavía describe cocientes de sumas anuales y un IPC promedio anual.
3. **Apoyo empresario:** la suspensión y la liberación del peso son correctas, pero el valor inválido sigue disponible en el artefacto crudo y en las series públicas.
4. **Judicialización:** ocurre lo mismo: la tarjeta y el peso fueron retirados, pero la serie de “menciones cautelares” sigue publicada bajo el nombre conceptual cuestionado y el artefacto crudo aún la marca `en_indice: true`.

Por tanto, el estado post-cambios es mucho más sólido en cálculo y ponderación que el anterior, pero todavía no es consistente entre **código/snapshot web**, **fichas/formulas** y **artefactos derivados**.

## Metodología y criterio de veredicto

- Se inspeccionaron el estado y el historial de Git, el código de extracción/cálculo, el snapshot web, las fichas TypeScript/Markdown, el informe crudo y las series. No se modificó código ni producto.
- Se volvió a ejecutar la validación de remediación y las pruebas dirigidas a DNU, IAF, cobertura judicial, suspensión de pesos y fichas.
- Para cada indicador se buscó evidencia web actual y trazable. La fuente oficial original se usó como control primario; para confirmar se exigió además una fuente externa equivalente o la reconstrucción completa de los eventos públicos subyacentes, con una fuente externa que corroborara el contexto o al menos un evento material.
- **Confirmado:** coinciden cifra, período, unidad, universo, fórmula y definición. **Compatible:** magnitud y dirección están corroboradas, pero el decimal agregado propio no puede reproducirse externamente. **Discrepante:** al menos uno de esos elementos contradice el cálculo, el rótulo o otra capa pública. **No verificable independientemente:** no existe evidencia suficiente para sostener ni refutar el resultado.
- El veredicto de una fila evalúa el indicador como producto publicado completo, no sólo la división aritmética. Por eso DNU e IAF son discrepantes aunque sus cifras corregidas sean exactas.
- Las páginas y bases dinámicas fueron consultadas al corte. Una fecha de horizonte —por ejemplo, el final del trimestre que esperan las constructoras— no se trató como fecha de observación.

## Perímetro, tarjetas, pesos y series

El snapshot web actual contiene **17 indicadores y 17 tarjetas**. `apoyo_empresario` y `judicializacion` ya no aparecen allí ni aportan al ITCP. Las siete dimensiones conservan sus pesos de diseño y los pesos efectivos de los 17 indicadores suman **1,0000** (la suma binaria observada es `0.9999999999999999`):

| Dimensión | Peso efectivo | Indicadores activos |
|---|---:|---:|
| Poder legislativo | 0,21 | 6 |
| Alianzas territoriales | 0,19 | 3 |
| Cohesión interna | 0,15 | 1 |
| Conflicto social | 0,10 | 2 |
| Imagen y voto | 0,07 | 1 |
| Poder judicial | 0,15 | 3 |
| Sector privado | 0,13 | 1 |
| **Total** | **1,00** | **17** |

La renormalización es correcta: Sector privado queda representado sólo por la brecha de obra pública y Poder judicial por velocidad, actividad de comisiones y cobertura. El ITCP publicado es **70,9** y el score de tensión de Política, **2,9**.

Hay tres residuos de publicación que deben corregirse:

- `web/src/data/series.json` y `output/series/politica.csv` aún contienen las series `apoyo_empresario` y `judicializacion`.
- `output/informe.json` conserva ambos valores; además los marca `en_indice: true`, y en judicialización mantiene `peso_efectivo: 0.03`. Un consumidor del artefacto crudo puede concluir erróneamente que siguen activos.
- `output/informe.md` todavía muestra ambos en la tabla de Política y `output/fichas/fichas-politica.md` conserva sus fichas completas. Los registros individuales de `descripciones.ts`, `formulas.ts` y `fichas.ts` también siguen existiendo; `descripciones.ts` y `fichas.ts` aclaran que ya no puntúan, pero no hay un contrato único que distinga “archivo histórico” de “indicador publicado”.
- Las descripciones de dimensión todavía dicen que Sector privado tiene dos vías —incluida la postura empresaria— y que Poder judicial tiene cuatro —incluidas las cautelares—. La topología verbal ya no coincide con la topología efectiva de 17 tarjetas.

## Matriz completa 19/19

| # | Indicador | Antes → estado actual | Fórmula, período y universo actual | Veredicto | Confianza | Contraste externo y observación post-cambio |
|---:|---|---|---|---|---|---|
| 1 | Ventaja LLA−PJ (Votómetro) | 4,3 pp → **4,3 pp**; 32,1 vs 27,8; 9 encuestas | Agregado ponderado propio, corte 22-07-2026; diferencia en puntos porcentuales entre LLA y PJ | **Compatible** | Media | [EncuestAR](https://encuestar.netlify.app/) registra resultados próximos muy dispersos: Trends 21–28 jul, 32–30 (+2); Rubikon 25–26 jul, 29,3–26,2 (+3,1). [El País](https://elpais.com/argentina/2026-08-21/los-salarios-y-el-empleo-son-las-nuevas-preocupaciones-de-los-argentinos-segun-los-sondeos.html) confirma volatilidad y deterioro de opinión. +4,3 es plausible, no una réplica exacta de los pesos propios. |
| 2 | Ratio DNU / leyes | **1,92 (48/25) → 1,48 (37/25)** | Ventana 25-08-2025/25-08-2026; 37 normas tipificadas `Decreto DNU` / 25 leyes publicadas en BO | **Discrepante** | Alta | La cifra y el inventario de 37 quedaron corregidos; por ejemplo, el [DNU 771/2026](https://www.argentina.gob.ar/normativa/nacional/norma-429094) está tipificado oficialmente como tal. Pero la fórmula web aún dice “DNU dictados / leyes sancionadas” y la ficha describe la vieja búsqueda textual. Valor confirmado; definición pública no. |
| 3 | Brecha de expectativas obra pública−privada | −1,1 pp → **−1,1 pp** | Promedio móvil de 12 brechas mensuales: saldo pública menos saldo privada; la fecha 01-09-2026 es fin del horizonte esperado | **Compatible** | Media-alta | La [encuesta cualitativa del INDEC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-3-42) para jul–sep da privada 12,1−16,8=−4,7 y pública 18,0−29,2=−11,2: brecha mensual −6,5, dirección compatible con el promedio móvil. [Ahora País](https://ahorapais.com/2026/08/07/construccion-cayo-4-1-junio-sube-2-8-semestre/) corrobora el corte coyuntural. Falta una publicación externa de los 12 meses juntos. |
| 4 | Postura pública de AEA y UIA | −0,429 → **suspendido y oculto** | El saldo viejo era (2 apoyos−5 críticas)/7 en 12 meses, con 14 piezas pendientes; ya no tiene fórmula ni peso válidos en el snapshot web | **Discrepante** | Alta | La suspensión es correcta. La [UIA](https://www.uia.org.ar/prensa/4226/) expresó críticas explícitas y también publicó apoyos parciales; [El País](https://elpais.com/argentina/2026-03-05/los-grandes-empresarios-de-argentina-alertan-sobre-la-critica-situacion-de-la-industria-y-le-reclaman-respeto-a-milei.html) corrobora la tensión. El corpus incompleto no sostiene −0,429 y ese valor sigue en series/artefacto crudo. |
| 5 | Conflictividad social nacional (ACLED) | **−24,1% (1.978/2.605) → −24,0% (1.979/2.605)** | Protests+Riots, Argentina, ago-2025/jul-2026 versus año calendario 2023; agosto de 2026 parcial excluido | **Compatible** | Alta | Una extracción autenticada de ACLED, edición 15-08-2026, reproduce 1.979/2.605; la revisión fue sólo julio, 89→90. [ACLED](https://acleddata.com/country/argentina) y su [codebook](https://acleddata.com/methodology/acled-codebook) sostienen cobertura/definición; [FLACSO](https://politicaspublicas.flacso.org.ar/archivos/16194) confirma la relativa estabilización con otra metodología. No es confirmación independiente exacta del mismo agregado. |
| 6 | Jornadas individuales no trabajadas | 4.760.195 → **4.760.195** | Suma mensual móvil de 12 meses hasta mayo de 2026; huelguistas × duración, conflictos laborales nacionales | **Compatible** | Alta | La planilla oficial de [Trabajo](https://www.argentina.gob.ar/trabajo/estadisticas/relaciones-laborales/conflictos-laborales) reproduce la suma. [Infobae](https://www.infobae.com/politica/2026/02/22/conflictividad-laboral-la-cantidad-de-paros-que-hubo-en-2025-fue-la-mas-baja-en-las-ultimas-dos-decadas/) informa 4,493 millones para 2025, compatible al reemplazar meses por ene–may de 2026. No hay total externo con idéntica ventana. |
| 7 | Transferencias federales reales (IAF) | **+0,8% → +1,6% real** | Se deflacta cada flujo mensual de transferencias automáticas por el IPC de ese mes y luego se suman 2024/2025; nominal +43,1%, deflactor efectivo +40,8% | **Discrepante** | Alta | El valor corregido coincide exactamente con IARAF: $60,2 billones y +1,6% real ([Tiempo de San Juan](https://www.tiempodesanjuan.com/economia/como-le-fue-san-juan-el-reparto-la-plata-nacional-moderado-el-ano-mejor-diciembre-n420386)). La [OPC](https://opc.gob.ar/provincias/informe-trimestral-de-transferencias-a-gobiernos-provinciales-y-municipales-datos-a-diciembre-2025/) y la [serie oficial](https://www.argentina.gob.ar/sites/default/files/serie_ron_2003_2025.csv) corroboran el agregado. Pero fórmula/ficha web aún dicen IPC promedio anual, distinto del código. |
| 8 | Eficacia legislativa del Ejecutivo | 15,4% → **15,4%** | 2 leyes / cohorte de 13 proyectos PEN/JGM ingresados 25-08-2024/25-08-2025 y madurados 365 días | **Confirmado** | Alta | La cohorte se reconstruyó completa en [proyectos PE](https://datos.hcdn.gob.ar/api/3/action/datastore_search?resource_id=22b2d52c-7a0e-426b-ac0a-a3326c388ba6&q=-PE-&limit=500), [JGM](https://datos.hcdn.gob.ar/api/3/action/datastore_search?resource_id=22b2d52c-7a0e-426b-ac0a-a3326c388ba6&q=-JGM-&limit=500) y [leyes](https://datos.hcdn.gob.ar/api/3/action/datastore_search?resource_id=68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98&limit=500): sólo 0022-PE-2024→27.783 y 0003-PE-2025→27.799. 2/13=15,4%. |
| 9 | Sesiones de Diputados sin quórum | 10,0% → **10,0%** | 1 reunión en minoría / 10 reuniones convocadas incluidas, últimos 12 meses | **Confirmado** | Alta | La página oficial de [Sesiones](https://www.hcdn.gob.ar/sesiones/) identifica la única “4° Reunión – Expresiones en Minoría” el **23-06-2026** y la prensa reconstruye el fracaso ([La Nación](https://www.lanacion.com.ar/politica/tregua-en-diputados-pro-la-ucr-y-los-provinciales-no-dieron-quorum-y-frustraron-la-ofensiva-nid23062026/)). La API devuelve inicio 21-06 para ese registro: es un defecto de metadato de fecha, no del conteo 1/10. |
| 10 | Adhesión provincial al RIGI | 66,7% → **66,7%** | 16 jurisdicciones adheridas / 24 provincias y CABA | **Confirmado** | Alta | La [lista oficial de jurisdicciones y leyes](https://www.magyp.gob.ar/desarrollo-foresto-industrial/provincias-adheridas.php) contiene exactamente 16; el [Instituto de Crecimiento](https://institutocrecimiento.org/assets/archivos/RIGIConceptual.pdf) reproduce el universo. 16/24=66,67%. |
| 11 | Cohesión del bloque LLA | 99,8% → **99,8%** | Índice de Rice en 34 actas divididas de 90 días; Diputados 100,0 y Senado 99,5, ponderación 65/35 | **Compatible** | Media-alta | En la votación del 06-08 los 21 senadores LLA votaron juntos ([TN](https://tn.com.ar/politica/2026/08/07/uno-por-uno-que-senadores-votaron-a-favor-y-quienes-en-contra-de-la-ley-de-propiedad-privada/)); [Infobae](https://www.infobae.com/politica/2026/05/23/de-la-cohesion-a-los-sutiles-juegos-de-poder-la-compleja-anatomia-de-la-libertad-avanza-en-el-congreso/) describe la alta disciplina. No existe réplica externa de las 34 actas ni de la ponderación propia. |
| 12 | Bloqueo sostenido | 33,3% → **33,3%** | 1 veto todavía en pie / 3 normas desafiadas en 12 meses | **Confirmado** | Alta | [Chequeado](https://chequeado.com/el-explicador/leyes-aprobadas-vetos-e-insistencias-en-que-estado-esta-cada-uno-de-los-proyectos-de-la-oposicion-en-el-congreso/) reconstruye universidad, emergencia pediátrica y ATN: Congreso completó la insistencia en las dos primeras; ATN no obtuvo la segunda cámara. [El País](https://elpais.com/argentina/2025-10-03/el-senado-argentino-consuma-la-revuelta-contra-milei-revierte-el-recorte-a-las-universidades-y-hospitales-pediatricos.html) confirma las dos insistencias completas. 1/3=33,3%. |
| 13 | Desafíos legislativos | 3 → **3 normas** | Conteo de primeras insistencias contra vetos en la ventana móvil de 12 meses | **Confirmado** | Alta | El mismo universo completo de la fila anterior consta de tres normas. [El País](https://elpais.com/argentina/2025-09-12/milei-veta-una-ley-de-financiamiento-provincial-y-escala-en-su-guerra-con-los-gobernadores.html) documenta ATN y [Chequeado](https://chequeado.com/el-explicador/leyes-aprobadas-vetos-e-insistencias-en-que-estado-esta-cada-uno-de-los-proyectos-de-la-oposicion-en-el-congreso/) las tres secuencias. |
| 14 | Producción legislativa | 25 → **25 leyes** | Leyes con sanción definitiva en los 12 meses hasta agosto de 2026 | **Confirmado** | Alta | El recurso público de [leyes sancionadas de Diputados](https://datos.hcdn.gob.ar/dataset/leyes-sancionadas) devuelve 25 filas en la ventana al aplicar la fecha de sanción. [Chequeado](https://chequeado.com/el-explicador/apertura-de-sesiones-2026-que-leyes-se-aprobaron-durante-el-gobierno-de-javier-milei/) aporta control independiente de la producción extraordinariamente baja del período. |
| 15 | Judicialización de la agenda | 1,57% → **suspendido y oculto** | El cálculo viejo era 114/7.273 sumarios SAIJ 2026 con la frase “medida cautelar”; no mide causas contra políticas del PEN | **Discrepante** | Alta | La suspensión es correcta. Las [consultas SAIJ](https://www.saij.gob.ar/busqueda?o=0&p=1&f=Jurisdicci%C3%B3n&r=%28texto%3A%22medida%20cautelar%22%20AND%20fecha-rango%3A%5B20260101%20TO%2020261231%5D%29) cuentan unidades editoriales heterogéneas. La literatura define judicialización como intervención judicial en políticas públicas ([FLACSO/CONICET](https://www.sciencedirect.com/science/article/pii/S0041863318300966)); el viejo universo no exige Estado/PEN ni una política. La serie y el artefacto crudo aún lo exponen. |
| 16 | Velocidad de resolución de la Corte | 45,4% → **45,4%** | 26.524 casos resueltos / 58.424 ingresados en 2025 | **Confirmado** | Alta | La [CSJN](https://w2.csjn.gov.ar/novedades/detalle/13002) publica exactamente ambos conteos y el [anuario 2025](https://www.csjn.gov.ar/archivos/estadisticas/informe_anuario_CSJN_2025.pdf) define el universo. La prensa corroboró el saldo de pendientes. 26.524/58.424=45,40%. |
| 17 | Actividad de comisiones de control | 7 → **7 sesiones** | Sesiones ordinarias numeradas de Acusación y Disciplina, sep-2025/ago-2026 | **Confirmado** | Alta | Se reconstruyeron las cuatro sesiones de Acusación —[12.ª](https://consejomagistratura.gov.ar/index.php/2025/09/17/sesiono-la-comision-de-acusacion-12/), [13.ª](https://consejomagistratura.gov.ar/index.php/2025/12/17/sesiono-la-comision-de-acusacion-13/), [14.ª](https://consejomagistratura.gov.ar/index.php/2026/02/25/sesiono-la-comision-de-acusacion-14/), [15.ª](https://consejomagistratura.gov.ar/index.php/2026/07/15/sesiono-la-comision-de-acusacion-15/)— y tres de Disciplina —[8.ª](https://consejomagistratura.gov.ar/index.php/2026/04/08/sesiono-la-comision-de-disciplina-8/), [9.ª](https://consejomagistratura.gov.ar/index.php/2026/06/03/sesiono-la-comision-de-disciplina-9/), [10.ª](https://consejomagistratura.gov.ar/index.php/2026/08/19/sesiono-la-comision-de-disciplina-10/)—; las secuencias no tienen huecos. |
| 18 | Cobertura de cargos judiciales | 69,63%, texto inconsistente 604/955 → **69,63%, 665/955** | Cargos habilitados no vacantes / 955 cargos habilitados; padrón 05-06 más designaciones y renuncias hasta 25-08 | **Confirmado** | Alta | El padrón base explica 604 titulares+282 subrogantes+69 sin cubrir=955; el cálculo post-corte incorpora 60 designaciones y 5 renuncias y cuenta 665 no vacantes. El Senado aprobó 74 pliegos el 04-06 ([Infobae](https://www.infobae.com/politica/2026/06/04/senado-en-vivo-las-ultimas-noticias-sobre-la-sesion-y-el-nombramiento-de-50-jueces-federales/)) y comenzaron los nombramientos ([Infobae](https://www.infobae.com/politica/2026/06/12/oficializaron-los-nombramientos-de-emilio-rosatti-y-otros-dos-jueces-tras-la-aprobacion-de-los-pliegos-en-el-senado/)). El [dataset oficial](https://datos.jus.gob.ar/dataset/magistrados-justicia-federal-y-de-la-justicia-nacional) permite reconstruir altas/bajas. 665/955=69,6335%. |
| 19 | Alineamiento de senadores no-LLA por provincia | 57,0% → **57,0%** | Promedio simple de 24 provincias, votos de senadores no-LLA en actas nominales de 90 días al 06-08-2026 | **Compatible** | Media-alta | La última votación muestra apoyos de UCR, PRO y bloques provinciales junto a oposición peronista ([Infobae](https://www.infobae.com/politica/2026/08/07/uno-por-uno-como-voto-cada-senador-la-ley-de-inviolabilidad-de-la-propiedad-privada/), [TN](https://tn.com.ar/politica/2026/08/07/uno-por-uno-que-senadores-votaron-a-favor-y-quienes-en-contra-de-la-ley-de-propiedad-privada/)). Es consistente con una media apenas mayoritaria, pero ninguna fuente externa publica el agregado provincial de todas las actas. |

## Hallazgos prioritarios

### 1. Ratio DNU: cálculo corregido, contrato público anterior

La corrección numérica es sustantiva y correcta. En la ventana hay **37** registros cuyo tipo oficial es `Decreto DNU`, no 48 decretos que contienen la expresión “necesidad y urgencia”. El snapshot publica además `inventario_dnu`, por lo que la anterior limitación de auditabilidad quedó resuelta. Los once falsos positivos de la consulta textual ya no se cuentan.

El denominador continúa siendo **25 leyes publicadas**, no sancionadas. Eso es una definición válida si se la aplica simétricamente a ambos términos, pero no coincide con la fórmula visible:

- `descripciones.ts`: “cuántos DNU se dictan por cada ley sancionada”;
- `formulas.ts`: “DNU dictados / leyes sancionadas”;
- `fichas.ts` y la ficha Markdown: todavía describen búsqueda textual y sanciones, e incluso mantienen como limitación que no existe listado.

La corrección recomendada es elegir y repetir en todas las capas una sola definición: **“DNU publicados / leyes publicadas en el Boletín Oficial, ventana de 365 días”**. Debe eliminarse toda referencia al detector textual. Si se desea medir sanciones legislativas, el denominador público de Diputados da 22 para la ventana y el ratio sería 37/22=1,68; no debe mezclarse con el 1,48 actual.

### 2. IAF: cifra externa exacta, fórmula visible equivocada

La remediación corrigió la técnica apropiadamente: cada transferencia mensual se lleva a precios constantes con el IPC del mismo mes antes de sumar. Así, $42,1 billones en 2024 y $60,2 billones en 2025, con +43,1% nominal, resultan en **+1,6% real**. La coincidencia exacta con IARAF elimina la discrepancia numérica anterior.

Pero la fórmula pública todavía sugiere:

`[(transferencias 2025 / transferencias 2024) / (IPC promedio 2025 / IPC promedio 2024) − 1] × 100`.

Esa operación no es algebraicamente equivalente a deflactar los flujos mensuales: pondera el IPC por meses, no por el momento y tamaño de cada transferencia. La ficha debe expresar la operación real, por ejemplo: `Σ_m(T_2025,m / IPC_2025,m) / Σ_m(T_2024,m / IPC_2024,m) − 1`, con base de precios explícita. Hasta que cifra y fórmula coincidan, el producto completo es discrepante.

### 3. Cobertura judicial: conciliación resuelta

La inconsistencia anterior —69,63% junto a “604 de 955”— quedó corregida. La foto del padrón del 05-06 conserva la composición 604 titulares, 282 subrogantes y 69 vacantes; sobre esa base el proceso agrega **60 designaciones judiciales aplicables** y descuenta **5 renuncias**, filtra nombramientos futuros y considera cubierto un cargo si `cargo_vacante=NO`. El numerador actualizado es 665.

Los 74 pliegos aprobados por el Senado no deben confundirse con 74 altas del indicador: el paquete también incluye fiscales/defensores y la regla aplica fecha, cargo y jurisdicción. La prensa confirma la magnitud del acontecimiento y el dataset permite el filtro. El texto actual ya diferencia la foto base de las novedades y la aritmética cierra.

### 4. Suspensiones: puntaje correcto, exposición residual incorrecta

La suspensión de `apoyo_empresario` y `judicializacion` cumple el objetivo principal:

- no aparecen entre las 17 tarjetas;
- no aportan al ITCP;
- sus pesos se liberan y se renormalizan dentro de Sector privado y Poder judicial;
- existen razones y condiciones explícitas de reingreso en la configuración.

No obstante, la retirada no es completa. Las series siguen accesibles, `output/informe.md` todavía los enumera, la ficha Markdown conserva sus tarjetas, el informe JSON crudo los trata como activos y las descripciones de dimensión siguen prometiendo dos rutas en Sector privado y cuatro en Poder judicial. Esto crea varias verdades públicas distintas. La corrección recomendada es una de estas dos, aplicada de modo uniforme:

1. **Retirada estricta:** eliminar ambas claves del JSON de series y marcarlas `en_indice: false`, `suspendido: true`, `peso_efectivo: 0` en todo artefacto derivado.
2. **Archivo histórico explícito:** conservar series bajo un espacio `series_suspendidas`, con fecha, motivo y advertencia visible, sin mezclarlas con indicadores corrientes.

El apoyo empresario sólo debería reingresar después de cerrar y publicar el corpus completo con doble codificación. Judicialización requiere un indicador nuevo basado en causas contra medidas concretas del PEN; no alcanza con renombrar 114 menciones en sumarios.

### 5. Metadatos menores que no cambian el score

- **Quórum:** la web de Diputados y el video fechan la reunión en minoría el 23-06-2026, pero el registro descargado usado por el colector devuelve inicio 21-06. Debe priorizarse la fecha oficial de la sesión o documentar la anomalía; el numerador sigue siendo uno.
- **Construcción:** `fecha_dato=2026-09-01` es el fin del horizonte de expectativas y puede parecer un dato futuro. Conviene separar fecha de encuesta, fecha de publicación e intervalo anticipado.
- **ACLED:** el campo semanal agrupa semanas sábado–viernes y el código asigna la semana completa al mes del sábado. “Ago-2025 a jul-2026” es una suma de buckets semanales, no doce meses calendario estrictos; debe decirse en la ficha.
- **Actividad de comisiones:** siete reuniones confirma actividad formal, no “parálisis de denuncias” ni productividad sustantiva. El nombre visible actual es más prudente; la serie/código interno `paralisis_denuncias` todavía arrastra la interpretación vieja.

## Evidencia reproducible adicional

### ACLED

La descarga autenticada lícita utilizada para el control fue:

`https://acleddata.com/system/files/2026-08/Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-08-15.xlsx`

SHA-256: `6d44a38ef359e243d2e7c93ce5c4ff7b267a553f6aa73feb55d31eef53d55189`.

Contiene las 24 `admin1` argentinas. Desglose:

| Período | Protests | Riots | Total |
|---|---:|---:|---:|
| 2023 | 2.421 (727 filas) | 184 (150 filas) | **2.605** |
| Ago-2025/jul-2026 | 1.858 (689 filas) | 121 (100 filas) | **1.979** |

En el período móvil, los subtipos son: 1.804 protestas pacíficas, 53 protestas con intervención, 1 caso de fuerza excesiva contra manifestantes, 105 manifestaciones violentas y 16 episodios de violencia de turba. Frente al extracto anterior, sólo julio de 2026 cambió de 89 a 90; agosto parcial cambió de 82 a 114 y se excluye. La revisión de un evento equivale a 0,05% del numerador y altera sólo el primer decimal de la variación.

### Cohorte de eficacia legislativa

Los 13 expedientes son: `0012-JGM-2024`; `0016`, `0018`, `0019`, `0020`, `0021`, `0022`, `0023`, `0024` y `0025-PE-2024`; `0001`, `0003` y `0007-PE-2025`. Sólo `0022-PE-2024` y `0003-PE-2025` enlazan con las leyes 27.783 y 27.799. Este inventario cierra tanto numerador como denominador.

### Siete sesiones de comisiones

Acusación presenta una secuencia continua 12.ª→15.ª y Disciplina 8.ª→10.ª. Se excluyen una reunión conjunta con Administración y una audiencia testimonial porque el universo declarado son sesiones ordinarias numeradas. El conteo siete es exacto; su interpretación debe limitarse a actividad formal.

## Comparación agregada antes/después

| Aspecto | Antes de la remediación | Estado actual |
|---|---|---|
| Tarjetas de Política | 19 | **17** |
| Indicadores suspendidos | 0 | **2** (`apoyo_empresario`, `judicializacion`) |
| Ratio DNU | 48/25=1,92, con 11 falsos positivos | **37/25=1,48**, inventario visible |
| IAF real | +0,8% | **+1,6%**, deflación mensual |
| ACLED | 1.978/2.605=−24,1% | **1.979/2.605=−24,0%**, revisión de un evento |
| Cobertura judicial | 69,63% con texto 604/955 | **69,63%=665/955**, altas/bajas conciliadas |
| Peso efectivo total | Incluía dos constructos inválidos | **1,00 sobre 17 activos** |
| Fórmulas/fichas | Método viejo | **DNU e IAF todavía desactualizados** |
| Series/artefacto crudo | 19 constructos | **Aún exponen los dos suspendidos** |

## Validación local

Se ejecutó la verificación de remediación contra el baseline: terminó `[OK]` y comprobó, entre otros cambios, la desaparición de las dos tarjetas, 1,92→1,48, +0,8→+1,6 y −24,1→−24,0.

También se ejecutaron las pruebas dirigidas:

- `test_politica_ratio_dnu.py`
- `test_politica_iaf_deflactor.py`
- `test_politica_judicial.py`
- `test_suspension_libera_el_peso.py`
- `test_fichas_pesos.py`

Resultado: **96 aprobadas**, sin fallos. La suite se ejecutó sin `xdist` porque el complemento no está instalado en el entorno. Estas pruebas certifican cálculo y ponderación; no detectan por sí solas la divergencia semántica de las fórmulas visibles ni la persistencia de series suspendidas.

## Correcciones recomendadas, en orden

1. Actualizar fórmula, ficha, leyenda y descripción de DNU para que digan **publicados/publicadas**, subtipo oficial y ventana de 365 días.
2. Actualizar fórmula y ficha de IAF con la deflación mensual efectivamente implementada.
3. Marcar los suspendidos como tales en `output/informe.json` y separarlos o retirarlos de `series.json`/CSV.
4. Reescribir las descripciones de Sector privado y Poder judicial para 1 y 3 rutas activas, respectivamente.
5. Corregir el metadato 21/23 de junio en quórum y separar fechas de observación/horizonte en construcción.
6. Explicitar la convención semanal sábado–viernes de ACLED y evitar describir sus buckets como meses calendario estrictos.

## Limitaciones

- Votómetro, cohesión y alineamiento son agregados propios. La evidencia externa respalda la dirección y magnitud, pero una confirmación decimal exige publicar las matrices de entrada y pesos.
- ACLED requiere descarga autenticada. La réplica se hizo con acceso autorizado y sin eludir controles, pero no es una fuente independiente: por eso el veredicto es compatible aun con coincidencia casi exacta.
- En jornadas laborales y construcción, la fuente externa no publica exactamente la misma ventana móvil; se controlaron meses y totales próximos.
- Las bases oficiales dinámicas pueden revisar filas. Los inventarios y hashes consignados fijan qué edición se auditó.
