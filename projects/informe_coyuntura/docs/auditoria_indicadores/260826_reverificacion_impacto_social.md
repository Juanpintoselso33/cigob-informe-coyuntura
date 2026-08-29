# Reverificación posterior al segundo arreglo — Impacto social / Vida cotidiana

**Fecha de corte:** 26 de agosto de 2026

**Estado auditado:** `e1dfab84` (`fix(web): las fichas dejaban media tarjeta blanca`)

**Comparación:** reauditoría del 25 de agosto sobre `06c3e18e` y cambios hasta
`e1dfab84`, en particular `d2288021` y la corrida publicada a las 21:39 del
25 de agosto.

**Cobertura:** 19/19 del perímetro histórico: 18 indicadores activos y
`sentimiento_digital`, retirado del ITCIS pero conservado como serie de archivo.

## Conclusión ejecutiva

El cinturón queda **sin discrepancias por indicador** en este barrido:
**12 Confirmados · 7 Compatibles · 0 Discrepantes · 0 No verificables**.
Los dos discrepantes del expediente anterior quedaron cerrados de punta a
punta:

1. `subocupacion_demandante` ya dice en la descripción, la ficha fuente y la
   ficha generada que el denominador es la **población económicamente activa**.
   El 7,5% del 1T-2026 coincide con el cuadro 1.1 del INDEC.
2. `consumo_supermercados` ya muestra junio de 2026 = **82,1**, base 2017,
   tanto en card como en serie, ficha fuente y ficha Markdown generada. La
   planilla oficial descargada el 26 de agosto devuelve **82,1318322352606**
   para la serie desestacionalizada; contra la base 4T-2023 produce el índice
   ITCIS **90,1** publicado.

También quedó corregida la descripción de **Confianza y percepción**: ya no
promete dos métodos vigentes. Declara al ICC como único componente activo y
explica por qué las búsquedas salieron del índice.

El snapshot conserva **18 cards activas = 18 componentes del ITCIS**, sin
faltantes ni extras. Sus pesos efectivos suman **1,0000** y la suma directa
`indice_itvc × peso_efectivo` da **93,77004**, que redondea a **ITCIS 93,8** y
tensión **6,2/10**. `sentimiento_digital` no tiene card, peso ni aporte al
score; sus 67 puntos quedan en `series.json` como archivo, de acuerdo con la
explicación pública.

## Método de esta reverificación

Se repitió la matriz del barrido anterior, controlando valor, período, unidad,
universo, fuente, transformación, polaridad, puntaje, peso efectivo, serie y
ficha. Para los siete compuestos o recortes propios se exigió reproducibilidad
de insumos y fórmula, y se mantuvo **Compatible** cuando una fuente externa
corrobora magnitud y dirección pero no replica exactamente el universo.

Las fuentes externas del expediente anterior se volvieron a contrastar con el
snapshot nuevo. Se reabrieron o descargaron especialmente las fuentes de los
tres cambios sensibles: EPH, supermercados e ICC. Ninguna fuente nueva
publicada entre ambos cortes obliga a cambiar un veredicto.

## Matriz completa 19/19

| # | Indicador / estado | Dato publicado y universo | Fórmula, score y peso efectivo | Control externo actual | Veredicto |
|---:|---|---|---|---|---|
| 1 | Salario real vs. canasta (`brecha_salario_cbt`) | 3,87 canastas, jun-2026; RIPTE formal estable / CBT adulto equivalente GBA | 3,8656 / base 4T23; 112,5; 13,38% | RIPTE $1.915.878,76 y CBT $495.622,30 reproducen 3,8656 | **Confirmado**, alta |
| 2 | IPC alimentos (`ipc_alimentos`) | 1,98% m/m, jul-2026; alimentos y bebidas, total nacional | La card muestra tasa; el score usa nivel alimentos/IPC; 107,6; 8,75% | INDEC y contraste provincial/prensa redondean a 2,0%, con IPC general 2,1% | **Confirmado**, alta |
| 3 | Canasta de servicios / salario (`peso_tarifas`) | 14,5% del RIPTE, ago-2026; hogar representativo AMBA | Umbrales de asequibilidad; 112,6; 11,25% | IIEP UBA-CONICET publica 14,5% y $289.622 | **Confirmado**, media-alta |
| 4 | Alquiler real (`alquiler_real`) | 1,47% m/m, jul-2026; rubro alquiler del IPC-GBA | Nivel alquiler / IPC general GBA, base 4T23; 64,8; 5,00% | Zonaprop informa 1,6% para avisos CABA: orden similar, universo distinto | **Compatible**, media |
| 5 | Consumo total de carnes (`consumo_carnes_total`) | 114,45 kg/hab/año, PM12 a jun-2026; vacuna + aviar + porcina | Reconstrucción por faena/población; 95,0; 0,88% | CICCRA confirma el componente vacuno y la dirección, no el total de tres carnes | **Compatible**, media |
| 6 | Informalidad (`informalidad`) | 37,9%, 1T-2026; asalariados sin descuento jubilatorio, 31 aglomerados | Invertido: 35,7 / 37,9 = 94,2; 8,27% | EPH distingue 37,9% entre asalariados de 44,2% sobre todos los ocupados | **Confirmado**, alta |
| 7 | Trabajo independiente (`trabajo_independiente`) | 20,60%, may-2026; autónomos + monotributo general sobre cinco categorías SIPA; sin monotributo social | Invertido: base 19,1167 / 20,60 = 92,8; 2,42% | Los totales SIPA reproducen 2.587 mil / 12.554 mil; con régimen social daría 22,05% | **Compatible**, media-alta |
| 8 | Empleadores PyME activos (`mortalidad_pymes`) | 460.777, may-2026; empleadores SRT con hasta 50 trabajadores y cobertura ART | 460.777 / base 491.483,7 = 93,8; 3,57% | SRT respalda la serie; CEPA/Fundar confirman la contracción de empleadores, no el recorte exacto ≤50 | **Compatible**, media |
| 9 | Construcción (`despacho_cemento`) | 148,1, jun-2026; ISAC nacional desestacionalizado | 148,112 / base 180,19 = 82,2; 3,26% | La serie oficial y su espejo reproducen 148,11 | **Confirmado**, alta |
| 10 | Subocupación demandante (`subocupacion_demandante`) | 7,5%, 1T-2026; tasa EPH sobre la PEA | Invertido: 6,8 / 7,5 = 90,7; 1,24%; 40 puntos migrados | INDEC: 7,5% y definición sobre PEA; descripción y ficha actuales dicen lo mismo | **Confirmado**, alta |
| 11 | Empleo privado registrado (`empleo_registrado`) | 6.106,526 mil puestos, may-2026; asalariados privados SIPA | 6.106,5 / base 6.379,77 = 95,7; 5,43% | Publicación SIPA y prensa: aproximadamente 6,107 millones | **Confirmado**, alta |
| 12 | Victimización IVI (`inseguridad`) | 28,0% de hogares, abr-2026; delito en los 12 meses previos, 40 centros urbanos | Invertido contra ene-2024; 102,1; 4,50% | IVI confirma el corte; ENV 2017 y UCA respaldan magnitud, no período ni muestra | **Compatible**, media |
| 13 | ICC UTDT (`icc_utdt`) | 40,2, ago-2026; total nacional | 40,229 / base nacional 44,133 = 91,1; 8,25%; 100% interno activo en percepción | UTDT/prensa publican 40,23 nacional y separan las regiones | **Confirmado**, alta |
| 14 | Pobreza nowcast (`pobreza_nowcast`) | 31,6% de personas; semestre ene-jun 2026, 31 aglomerados | Empalme con base oficial e inversión; 126,9; 7,30% | UTDT publica 31,6%, IC95% [30,1; 33,0]; otros nowcasts usan subperíodos distintos | **Compatible**, media-alta |
| 15 | Sentimiento digital (`sentimiento_digital`) — retirado | Último archivo: 58,2, jul-2026; no existe card actual | Sin peso, score ni componente; 67 puntos históricos preservados | Google documenta muestreo/normalización y ausencia de valencia; la validación externa adversa justifica el retiro | **Confirmado el retiro**, alta |
| 16 | Motorización total (`motorizacion_total`) | 30,9 vehículos 0 km/1.000 hab., PM12 a jul-2026; DNRPA autos + motos, sin TDF | Rolling per cápita rebaseado; 142,9; 0,89% | ACARA informa 43.758 autos y 71.217 motos en su corte; DNRPA revisado da 44.886 y 72.418 en el colector | **Compatible**, media |
| 17 | Ventas en supermercados (`consumo_supermercados`) | 82,1, jun-2026; ventas constantes desestacionalizadas, base 2017=100 | 82,131832 / base 91,1866 = 90,1; 5,61%; 114 puntos | La planilla oficial vigente reproduce exactamente 82,131832 y −1,019% m/m | **Confirmado**, alta |
| 18 | Mora de familias (`mora_familias`) | 14,52%, may-2026; personales + tarjetas ponderados por saldo | Invertido: base 2,4933 / 14,52 = 17,2; 7,00% | BCRA/prensa: personales 15,9% y tarjetas 13,1%; el ponderado queda entre ambos | **Confirmado**, alta |
| 19 | Servicio de deuda (`carga_servicio_deuda_hogares`) | 24,076%, abr-2026; capital + intereses / masa salarial registrada, ambos PM3 | Invertido: base 10,1927 / 24,076 = 42,3; 3,00% | BCRA, CEPA, UNSAM y prensa publican 24,1% | **Confirmado**, alta |

## Cierre de las discrepancias anteriores

### 1. Subocupación demandante

El INDEC define la tasa como subocupados demandantes sobre PEA y publica 7,5%
para el 1T-2026. En `e1dfab84` esa definición ya coincide en:

- `web/src/lib/descripciones.ts`;
- `web/src/lib/fichas.ts`;
- `output/fichas/fichas-vida_cotidiana.md`;
- unidad y fuente de `web/src/data/informe.json`;
- 40 observaciones bajo `subocupacion_demandante` en CSV y JSON.

No quedan filas `pluriempleo` en la serie vigente. Las menciones que subsisten
en snapshots históricos o en el historial de cambios describen el nombre
anterior y no forman parte del contrato actual.

### 2. Supermercados

La planilla oficial `serie_supermercados.xlsx`, descargada de nuevo el 26 de
agosto, tiene en `Cuadro 1`:

- fecha: 2026-06-01;
- serie original: 78,6796321;
- serie desestacionalizada: **82,1318322352606**;
- variación mensual desestacionalizada: **−1,019394%**;
- tendencia-ciclo: 82,2290092.

El producto toma correctamente la segunda columna conceptual, no la serie
original ni tendencia-ciclo. Card, `series.json`, CSV, ficha fuente y ficha
Markdown dicen junio, 82,1, base 2017 y puntaje 90,1. La mención a mayo = 83,2
que queda en la ficha está dentro de la **política de revisiones**: documenta
que al sumar junio el INDEC revisó mayo a 83,0; no es el valor vigente.

### 3. Percepción y sentimiento digital

La dimensión publica ICC = 91,1 con peso 8,25%. El peso de diseño interno del
ICC se renormaliza a 100% porque `sentimiento_digital` está suspendido. La
descripción general y las fichas explican expresamente esa transición; ya no
afirman que hoy se mida por dos vías.

Conservar `sentimiento_digital` en `series.json` es coherente con ese contrato:
se publica como archivo experimental, pero no aparece entre cards ni entre los
18 componentes calculados. Si en el futuro se decidiera que ningún suspendido
puede aparecer tampoco en series públicas, eso exigiría cambiar el contrato;
no es una inconsistencia de este estado.

## Integridad de score, pesos y series

- Cards activas: **18**.
- Componentes presentes en las seis dimensiones: **18**, exactamente los
  mismos ids; no hay faltantes ni extras.
- Suma de pesos dimensionales: **1,0000**.
- Suma de pesos efectivos de cards: **1,0000**.
- Suma directa de cards: **93,77004**.
- Suma por dimensiones: **93,76432**; la diferencia es sólo el redondeo a una
  decimal dentro de cada dimensión.
- Publicado: **ITCIS 93,8**, tensión **6,2/10**.
- `subocupacion_demandante`: 40 puntos; `pluriempleo`: 0.
- `consumo_supermercados`: 114 puntos, ene-2017 a jun-2026; último 82,131832.
- `icc_utdt`: 60 puntos en el recorte web; último 40,2 nacional.
- `sentimiento_digital`: 67 puntos de archivo; sin card ni peso.

La corrida versionada de las 21:25 en la que SAGYP no respondió conserva la
evidencia del fallo. La siguiente, 21:39, recuperó junio = 114,45. La nueva
guarda hace que una caída futura degrade `consumo_carnes_total` en vez de
hacer desaparecer la card; el valor y el score actuales no dependen de esa
simulación.

## Fichas y artefactos derivados

El Markdown vigente `output/fichas/fichas-vida_cotidiana.md` está sincronizado
con el snapshot. Los tests contrastan valor, período, unidad, color, peso e
índice de todas las fichas y pasan.

Hay una salvedad operativa fuera de los 19 veredictos: el archivo manual
`output/fichas/Fichas Semaforo Vida cotidiana.docx` es la última versión
circulada al equipo, no un espejo automático del snapshot. El verificador marca
**12 fallas** contra el estado actual, entre ellas ICC viejo, supermercados en
mayo y sentimiento todavía como ficha. El propio README del generador dice que
los DOCX son manuales y deben pasar el gate antes de enviarse. Por lo tanto:

- no afecta la web, el ITCIS ni el Markdown versionado;
- **no debe volver a distribuirse ese DOCX sin regenerarlo**.

## Pruebas focalizadas

Se ejecutaron dos lotes, **281 pruebas en total**, todas aprobadas:

- 242 pruebas de supermercados, contrato público, fichas Markdown, ITCIS,
  empleo registrado, publicación, redundancia, suspensiones, trabajo
  independiente, universos, ICC nacional, vintages y pesos web;
- 39 pruebas de fuente caída, bandas/pesos de fichas, etiquetas y semáforos.

El verificador separado de DOCX devolvió las 12 diferencias sociales descritas
arriba. No se cuentan como fallas de los tests ni como discrepancias de las
cards: es justamente el gate avisando que el Word manual está desactualizado.

## Fuentes externas

1. Mercado laboral: [EPH 1T-2026, INDEC](https://infoecos.com.ar/wp-content/uploads/2026/06/indecmercadodetrabajo.pdf),
   [estadísticas laborales oficiales](https://www.argentina.gob.ar/node/142148),
   [situación del trabajo registrado](https://www.argentina.gob.ar/trabajo/estadisticas/situacion-y-evolucion-del-trabajo-registrado),
   [serie histórica SRT](https://www.srt.gob.ar/estadisticas/cf_serie_historica_up.php).
2. Supermercados: [planilla histórica INDEC](https://www.indec.gob.ar/ftp/cuadros/economia/serie_supermercados.xlsx),
   [calendario oficial de difusión](https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_2sem2026.pdf),
   [contraste periodístico de junio](https://www.infobae.com/economia/2026/08/21/cayeron-las-ventas-en-supermercados-mayoristas-y-shoppings-en-junio-segun-el-indec/).
3. Confianza y pobreza: [ICC agosto, 40,23](https://www.primeraedicion.com.ar/nota/101134060/confianza-consumidor-interior-cayo-agosto-2026/),
   [nowcast de pobreza UTDT](https://www.utdt.edu/ver_contenido.php?id_contenido=22217&id_item_menu=36605).
4. Precios e ingresos: [RIPTE oficial](https://www.argentina.gob.ar/trabajo/seguridadsocial/ripte),
   [IPC INDEC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31),
   [IIEP UBA-CONICET, tarifas agosto](https://economicas.uba.ar/iiep/reporte-de-tarifas-y-subsidios-agosto-2026/).
5. Actividad y consumo: [ISAC INDEC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-3-42),
   [SAGYP, información bovina](https://www.magyp.gob.ar/sitio/areas/bovinos/informacion_sectorial/?ignoreCache=1),
   [DNRPA, datos abiertos](https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-automotores),
   [ACARA/prensa, autos julio](https://www.lanacion.com.ar/autos/los-patentamientos-cayeron-30-en-julio-y-el-mercado-acumula-una-baja-del-12-nid31072026/),
   [ACARA/prensa, motos julio](https://www.lanacion.com.ar/autos/las-motos-crecen-en-ventas-y-estos-son-los-modelos-que-mas-se-buscan-nid05082026/).
6. Seguridad: [IVI UTDT](https://www.utdt.edu/ver_contenido.php?id_contenido=26535&id_item_menu=23763),
   [ENV 2017 INDEC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-34-155).
7. Deuda de hogares: [mora por producto](https://tn.com.ar/economia/2026/07/25/la-morosidad-de-las-familias-llego-al-128-en-mayo-y-alcanzo-el-nivel-mas-alto-en-mas-de-20-anos/),
   [CEPA](https://centrocepa.com.ar/documentos/informes/822-endeudamiento-y-mora-en-familias-y-empresas),
   [carga del servicio, 24,1%](https://www.infobae.com/economia/2026/07/17/mora-record-los-argentinos-destinan-casi-un-cuarto-de-su-salario-a-pagar-deudas/?outputType=amp-type).
8. Búsquedas: [Google Trends, muestreo y normalización](https://support.google.com/trends/answer/4365533?hl=es),
   [términos frente a temas](https://support.google.com/trends/answer/17309543?hl=es),
   [revisión académica](https://madoc.bib.uni-mannheim.de/68637/1/1-s2.0-S0049089X24001212-main.pdf).

## Dictamen

La remediación social queda **cerrada en el producto vigente**: los 18
indicadores activos son coherentes con sus fuentes, definiciones, series,
fórmulas y pesos, y el retiro del decimonoveno es explícito y efectivo. Los
siete “Compatible” siguen siendo límites de replicación externa de universos o
compuestos propios, no errores detectados.

La única acción pendiente es operativa: regenerar el DOCX manual antes de
volver a enviarlo. No hace falta cambiar ningún valor, fórmula ni peso del
ITCIS a partir de esta reverificación.
