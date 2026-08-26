# Reauditoría post-remediación — Impacto social / Vida cotidiana

**Fecha de corte:** 25 de agosto de 2026

**Estado auditado:** `06c3e18e` (`data(informe): el supermercado llega a junio de 2026`)

**Artefactos:** `web/src/data/informe.json`, `web/src/data/series.json`,
`output/series/vida_cotidiana.csv`, `output/fichas/fichas-vida_cotidiana.md`,
colectores, `scripts/publicar.py`, `scripts/itvc.py` y metadatos de la web.

**Cobertura:** 19/19 del perímetro previo: 18 indicadores activos y una serie
experimental suspendida (`sentimiento_digital`).

## Conclusión ejecutiva

La remediación corrigió los cuatro errores objetivos de dato o universo y retiró
del score el constructo que no superó la validación externa. El snapshot actual
publica **18 cards activas**, todas puntuables, con ITCIS **93,8** y tensión
**6,2/10**. Los pesos efectivos de las 18 suman exactamente **1,0000**.

El nuevo barrido no encontró un dato numérico incorrecto en el snapshot, pero sí
dos discrepancias entre artefactos que impiden cerrar la auditoría sin reservas:

1. `subocupacion_demandante` tiene id, valor y unidad correctos, pero la
   definición pública aún dice «qué porcentaje de los ocupados», cuando INDEC
   la calcula sobre la **PEA**.
2. `consumo_supermercados` está correctamente en junio = **82,1** en snapshot,
   serie y colector, pero la ficha generada quedó en mayo = **83,2**, puntaje
   91,2 y descripción del antiguo espejo. El puntaje efectivo actual es 90,1.

**Conteo de veredictos:** **10 Confirmados · 7 Compatibles · 2 Discrepantes ·
0 No verificables independientemente**. En `sentimiento_digital`, “Confirmado”
se refiere a que su **suspensión** es correcta; no rehabilita el índice de
búsquedas como medición válida de sentimiento.

## Método

Para cada fila se controlaron cifra, período, unidad, cobertura, universo,
serie, transformación, polaridad y peso. Se usó la fuente productora como
control primario y una publicación académica, observatorio, cámara o prensa
trazable como contraste. Una nota que sólo reproduce al productor controla la
transcripción, pero no constituye una segunda medición independiente.

Las combinaciones propias —carnes, empleadores pequeños, trabajo independiente,
motorización y búsquedas— se evaluaron por reproducibilidad de insumos y
fórmula. No se equiparó un proxy cercano con la misma estadística. Los
veredictos son:

- **Confirmado:** número, definición y transformación se reproducen sin
  diferencia material.
- **Compatible:** magnitud y dirección tienen respaldo externo, pero el
  universo o modelo propio no tiene una réplica exacta independiente.
- **Discrepante:** existe una diferencia material en cifra, período, unidad,
  universo, fórmula o metadato publicado.
- **No verificable independientemente:** ni una réplica ni un contraste externo
  suficiente permiten auditar la afirmación.

La validación local incluyó una descarga en vivo de los tres colectores más
sensibles. Devolvió: trabajo independiente 20,60% en mayo (2.587 mil
independientes y 9.967 mil asalariados; 22,05% con monotributo social),
supermercados 82,1318 en junio, base 2017, e ICC nacional 40,22944 en agosto.

## Matriz completa 19/19

| # | Indicador / estado | Cifra, período, unidad y universo actuales | Serie, fórmula y peso efectivo | Contraste externo | Veredicto | Acción residual |
|---:|---|---|---|---|---|---|
| 1 | Salario real vs. canasta (`brecha_salario_cbt`) | 3,87 canastas, jun-2026; RIPTE formal estable / CBT por adulto equivalente GBA | Rebase directo: 3,87 / promedio 4T23; índice 112,5; 13,38% | RIPTE $1.915.878,76 y CBT $495.622: cociente 3,8656 | **Confirmado**, alta | Mantener visible que no es ingreso de un hogar ni salario medio de toda la economía |
| 2 | IPC alimentos (`ipc_alimentos`) | 1,98% m/m, jul-2026; Alimentos y bebidas no alcohólicas, total nacional | La card muestra la tasa; el score usa el nivel relativo alimentos/IPC general; índice 107,6; 8,75% | INDEC/IPEC y prensa redondean alimentos a 2,0% e IPC general a 2,1% | **Confirmado**, alta | Conservar la distinción entre tasa de card e insumo acumulado del score |
| 3 | Canasta de servicios / salario (`peso_tarifas`) | 14,5% del RIPTE, ago-2026; hogar representativo AMBA | Transformación por umbrales de asequibilidad, no rebase; índice 112,6; 11,25% | IIEP UBA-CONICET publica 14,5% y canasta de $289.622 | **Confirmado**, media-alta | No generalizar AMBA a cobertura nacional |
| 4 | Alquiler real (`alquiler_real`) | 1,47% m/m, jul-2026; rubro alquiler IPC-GBA | Nivel de alquiler relativo al IPC general GBA, base 4T23; índice 64,8; 5,00% | Zonaprop: 1,6% en avisos CABA; confirma orden, no universo | **Compatible**, media | Rotular siempre IPC-GBA y contratos/precios relevados, no avisos nuevos |
| 5 | Consumo total de carnes (`consumo_carnes_total`) | 114,45 kg/hab/año, PM12 a jun-2026; vacuna + aviar + porcina | Nivel SAGYP y evolución propia desde faena/población; índice 95,0; 0,88% | CICCRA confirma ~47 kg de vacuna y la dirección; no replica las tres carnes | **Compatible**, media | Publicar componentes y no presentar nivel SAGYP y reconstrucción INDEC como una sola serie homogénea |
| 6 | Informalidad (`informalidad`) | 37,9%, 1T-2026; asalariados sin descuento, 31 aglomerados EPH | Invertido: 35,7 / 37,9 = 94,2; 8,27% | UNR distingue 37,9% asalariados de 44,2% todos los ocupados | **Confirmado**, alta | Mostrar «1T-2026», no simular que `2026-01-01` es enero |
| 7 | Trabajo independiente (`trabajo_independiente`) | 20,60%, may-2026; autónomos + monotributo general sobre esas categorías y tres grupos asalariados; sin monotributo social | Base 4T23 19,1167%; invertido: 19,1167 / 20,60 = 92,8; 2,42% | SIPA/prensa confirman total y composición; fórmula propia se reproduce; con régimen social da 22,05% | **Compatible**, media-alta | Acortar la fuente textual: hoy dice «total» aunque el universo restringido está correctamente enumerado en unidad y detalle |
| 8 | Empleadores PyME activos (`mortalidad_pymes`) | 460.777, may-2026; empleadores SRT con hasta 50 trabajadores y al menos una persona cubierta | 460.777 / base 491.483,7 = 93,8; 3,57% | CEPA/Fundar informan 30.633 empleadores totales menos desde nov-2023, magnitud consistente | **Compatible**, media | El id técnico todavía promete mortalidad; mide stock neto, no altas y bajas brutas |
| 9 | Construcción (`despacho_cemento`) | 148,1, jun-2026; ISAC nacional desestacionalizado | 148,11 / base 180,19 = 82,2; 3,26% | Serie externa reproduce 148,11 | **Confirmado**, alta | Migrar el id legado cuando sea posible; card y ficha ya dicen ISAC |
| 10 | Subocupación demandante (`subocupacion_demandante`) | 7,5%, 1T-2026; tasa EPH sobre la PEA | Invertido: 6,8 / 7,5 = 90,7; 1,24%; 40 filas históricas migradas; `pluriempleo` no subsiste | INDEC y CEPA confirman 7,5% y el denominador PEA | **Discrepante**, alta | Corregir `descripciones.ts` y la ficha: aún dicen «porcentaje de los ocupados» |
| 11 | Empleo privado registrado (`empleo_registrado`) | 6.106,526 mil puestos, may-2026; asalariados privados SIPA | 6.106,5 / base 6.379,77 = 95,7; 5,43% | Prensa reproduce 6,107 millones y caída mensual de 0,1% | **Confirmado**, alta | Redondear presentación a 6.106,5 mil; la precisión de una persona es innecesaria |
| 12 | Victimización IVI (`inseguridad`) | 28,0% de hogares, abr-2026; delito en 12 meses previos, 40 centros urbanos | Invertido contra enero-2024; índice 102,1; 4,50% | IVI: 996 hogares; ENV-INDEC 2017 27,5% y UCA 2016 26,4% respaldan magnitud, no el corte | **Compatible**, media | Publicar muestra e intervalo; no usar denuncias como réplica de victimización |
| 13 | ICC UTDT (`icc_utdt`) | 40,2, ago-2026; **total nacional** | 40,229 / base nacional 44,133 = 91,1; único componente activo de percepción; 8,25% | UTDT/prensa publican 40,23 y distinguen CABA 39,87 | **Confirmado**, alta | Sincronizar texto de dimensión/ficha: aún habla de dos métodos. Aclarar en JSON que `peso: 0.8182` es diseño y `peso_efectivo: 0.0825` implica 100% interno activo |
| 14 | Pobreza nowcast (`pobreza_nowcast`) | 31,6% de personas; semestre ene-jun 2026, 31 aglomerados | Empalme con base oficial e inversión; índice 126,9; 7,30% | UTDT publica 31,6%, IC95% [30,1; 33,0]; BCRA ~30% para otro subperíodo | **Compatible**, media-alta | Card debe priorizar «semestre móvil» e intervalo, no fecha puntual junio |
| 15 | Sentimiento digital (`sentimiento_digital`) — **suspendido** | Serie experimental 58,2 en jul-2026; no existe card actual | Conserva 67 puntos; peso efectivo 0; no entra a ITCIS; su 1,50% previo fue absorbido por ICC | Google advierte que Trends es muestra normalizada y no encuesta; Ipsos/ICC dieron validación adversa | **Confirmado el retiro**, alta | Mantener fuera hasta términos/topics predeclarados, vintages y validación temporal fuera de muestra; limpiar metadatos dormidos que aún lo describen como componente |
| 16 | Motorización total (`motorizacion_total`) | 30,9 vehículos 0 km/1.000 habitantes, PM12 a jul-2026; autos + motos, sin Tierra del Fuego | Rolling 12m per cápita ya base 100; índice 142,9, exento de techo 140; 0,89% | Julio: 43.758 autos y 71.217 motos; acumulados 339.359 y 511.986 | **Compatible**, media | Publicar los 12 meses, población usada y exclusión territorial en la card principal |
| 17 | Ventas en supermercados (`consumo_supermercados`) | Snapshot/serie: 82,1, jun-2026; ventas constantes desestacionalizadas, base 2017=100 | 82,1318 / base 91,1866 = 90,1; 5,61%; fuente directa XLS + espejo sólo como contraste | INDEC y prensa confirman junio y caída mensual ~1%; descarga viva reproduce 82,1 | **Discrepante**, alta | Regenerar ficha: todavía muestra may-2026 = 83,2, índice 91,2, 113 puntos y rezago del espejo |
| 18 | Mora de familias (`mora_familias`) | 14,52%, may-2026; personales + tarjetas ponderados por saldo | Invertido: base 2,4933 / 14,52 = 17,2; 7,00% | Personales 15,9% y tarjetas 13,1%; el ponderado cae correctamente entre ambos | **Confirmado**, alta | Publicar saldos y ponderaciones para réplica externa exacta |
| 19 | Servicio de deuda (`carga_servicio_deuda_hogares`) | 24,076%, abr-2026; capital + intereses / masa salarial registrada, ambos PM3 | Invertido: base 10,1927 / 24,076 = 42,3; 3,00% | BCRA, CEPA, UNSAM y prensa publican 24,1% | **Confirmado**, alta | Mantener explícito que no cubre ingresos laborales informales |

## Verificación de score, pesos y series

### Reconciliación aritmética

La suma de `indice_itvc × peso_efectivo` de las 18 cards es **93,77004**;
las diferencias de redondeo por dimensión llevan al **93,8** publicado. La
transformación a tensión también reconcilia:

`5 - (93,8 - 100) × 0,2 = 6,24 → 6,2`.

Los seis pesos dimensionales no cambiaron:

| Dimensión | Peso | Puntaje actual |
|---|---:|---:|
| Ingresos y consumo | 28,06% | 112,2 |
| Presión de precios | 25,00% | 101,3 |
| Vulnerabilidad financiera | 10,00% | 24,7 |
| Prospectivas de empleo | 24,19% | 92,5 |
| Confianza y percepción | 8,25% | 91,1 |
| Seguridad | 4,50% | 102,1 |

En percepción, la tabla de diseño conserva `icc_utdt: 0.8182` y
`sentimiento_digital: 0.1818` para que la suspensión sea reversible. El motor
quita el suspendido y renormaliza: ICC queda con **100% interno activo** y
**8,25% efectivo**. El cálculo es correcto. El problema es sólo de contrato y
documentación: el JSON conserva el campo ambiguo `peso: 0.8182`, mientras la
ficha web específica sí declara 100% y la descripción general de la dimensión
todavía habla de dos componentes.

### Integridad de series

- `output/series/vida_cotidiana.csv` tiene 40 observaciones bajo
  `subocupacion_demandante`; no hay filas `pluriempleo`.
- ICC tiene 60 puntos publicados en el recorte web y el colector reconstruye la
  serie nacional desde 2001. No queda la columna Capital en card ni score.
- Supermercados contiene 114 puntos, enero-2017 a junio-2026. Junio =
  82,131832 y mayo fue revisado a 82,98/83,0.
- Sentimiento conserva 67 puntos, pero su clave no aparece entre las 18 cards ni
  entre los componentes calculados del ITCIS.

## Comparación antes / después de la remediación

| Caso prioritario | Antes de `7fc68b68` | Estado actual | Evaluación |
|---|---|---|---|
| Trabajo independiente | 20,6%, rótulo genérico «% del empleo registrado» | 20,6%, universo enumerado, sin monotributo social; contrafactual 22,05% | Corrección conceptual sustantiva; valor y score 92,8 no cambian |
| Pluriempleo → subocupación | `pluriempleo`, 7,5%, unidad `%`; peso 1,24% | `subocupacion_demandante`, 7,5% de la PEA; serie migrada; mismo peso | Migración de id correcta; persiste una frase pública con denominador viejo |
| ICC UTDT | 39,9 de CABA rotulado nacional; índice 91,2; peso 6,75% | 40,2 nacional; índice 91,1; peso efectivo 8,25% | Dato/geografía corregidos; absorción del peso correcta; texto de dimensión quedó viejo |
| Supermercados | 83,2, may-2026, rótulo 2004=100; índice 91,2 | 82,1, jun-2026, 2017=100; índice 90,1; peso 5,61% | Snapshot, colector y serie correctos; ficha generada no acompañó la última corrida |
| Sentimiento digital | Card 58,2; índice invertido 171,8 recortado a 140; peso 1,50% | Sin card, sin score, peso efectivo 0; serie experimental preservada | Retiro confirmado; no confundir reproducibilidad aritmética con validez del constructo |

En conjunto, el perímetro pasó de 19 a 18 cards. El score de tensión fue de
**6,1 a 6,2** y el ITCIS de **94,6 a 93,8**. Es el efecto agregado de cambiar
ICC, actualizar supermercados y retirar el aporte favorable de búsquedas; no se
debe atribuir toda la diferencia a una sola corrección.

## Fuentes externas directas

1. Salario/canasta: [RIPTE oficial](https://www.argentina.gob.ar/node/201033),
   [El Tablero](https://eltablero.ar/variables/datos-158.1_REPTE_0_0_5-remuneracion-imponible-promedio-de-los-trabajadores-estables-ripte),
   [CBT junio](https://calcular.ar/canasta-basica/junio-2026).
2. Precios: [INDEC IPC](https://www.indec.gob.ar/Nivel4/Tema/3/5/31),
   [IPEC Misiones, cuadro nacional/NEA](https://www.ipec.misiones.gov.ar/economia/indice-de-precios/ipc-noreste-argentino/julio-2026/).
3. Servicios: [IIEP UBA-CONICET, agosto](https://economicas.uba.ar/iiep/reporte-de-tarifas-y-subsidios-agosto-2026/),
   [TN](https://tn.com.ar/economia/2026/08/21/una-familia-del-amba-necesito-casi-290000-en-agosto-para-cubrir-los-gastos-de-luz-gas-agua-y-transporte/).
4. Alquileres: [TN/Zonaprop](https://tn.com.ar/economia/2026/08/05/los-alquileres-en-caba-subieron-16-en-julio-los-barrios-mas-caros-y-los-mas-baratos/),
   [INDEC, cobertura IPC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31).
5. Carnes: [CICCRA, informe junio](https://es.scribd.com/document/1064230513/Informe-CICCRA-Junio-2026),
   [SAGYP, información bovina](https://www.magyp.gob.ar/sitio/areas/bovinos/informacion_sectorial/?ignoreCache=1).
6. Informalidad y subocupación: [UNR](https://unr.edu.ar/informalidad-laboral-la-medicion-que-faltaba/),
   [IIEP UBA-CONICET](https://economicas.uba.ar/iiep/panorama-del-empleo-informal-y-la-pobreza-laboral-jun-2026/),
   [EPH 1T-2026](https://infoecos.com.ar/wp-content/uploads/2026/06/indecmercadodetrabajo.pdf),
   [CEPA](https://centrocepa.com.ar/documentos/informes/813-analisis-de-la-situacion-del-mercado-de-trabajo-datos-al-primer-trimestre-2026).
7. SIPA: [estadísticas laborales oficiales](https://www.argentina.gob.ar/node/142148),
   [empleo total y categorías en mayo](https://www.primeraedicion.com.ar/nota/101132367/empleo-registrado-cayo-tercer-mes-consecutivo-argentina/),
   [empleo privado 6,107 millones](https://sintesisinformativa.com/2026/08/24/empleo-privado-formal-mismo-nivel-2016/).
8. Empleadores: [serie histórica SRT](https://www.srt.gob.ar/estadisticas/cf_serie_historica_up.php),
   [CEPA, datos a mayo](https://centrocepa.com.ar/documentos/informes/832-analisis-de-la-dinamica-laboral-y-empresarial-datos-a-mayo-2026).
9. Construcción: [serie ISAC externa](https://boletinextraoficial.com/actividad-economica/isac/),
   [INDEC ISAC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-3-42).
10. Victimización: [UTDT/LICIP, abril](https://www.utdt.edu/ver_contenido.php?id_contenido=26535&id_item_menu=23763),
    [ENV 2017 INDEC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-34-155),
    [UCA/CONICET](https://repositoriosdigitales.mincyt.gob.ar/vufind/Record/CONICETDig_767567854b5058d4d5ae460f87723419).
11. Confianza y pobreza: [ICC agosto, 40,23](https://cholilaonline.ar/2026/08/la-confianza-del-consumidor-cayo-11-en-agosto-pero-se-mantiene-por-encima-de-2025.html),
    [UTDT, nowcast 31,6%](https://www.utdt.edu/ver_contenido.php?id_contenido=22217&id_item_menu=36605).
12. Trends: [Google, muestreo y normalización](https://support.google.com/trends/answer/4365533?hl=es),
    [términos vs. temas](https://support.google.com/trends/answer/17309543?hl=es),
    [revisión académica de 360 estudios](https://madoc.bib.uni-mannheim.de/68637/1/1-s2.0-S0049089X24001212-main.pdf),
    [Ipsos julio 2026](https://www.ipsos.com/sites/default/files/ct/news/documents/2026-08/Argentina%20Report%20-%20What%20Worries%20the%20World%20Jul%2026_ESP.pdf).
13. Motorización: [autos, ACARA](https://fedebossio.com.ar/patentamientos.html),
    [autos y motos de julio](https://mercadosyseguros.com/patentamientos-julio-autos-30-y-motos-30/),
    [datos DNRPA](https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-automotores).
14. Supermercados: [planilla histórica INDEC](https://www.indec.gob.ar/ftp/cuadros/economia/serie_supermercados.xlsx),
    [INDEC, junio](https://www.indec.gob.ar/indec/Portada),
    [Infobae, contraste de variaciones](https://www.infobae.com/economia/2026/08/21/cayeron-las-ventas-en-supermercados-mayoristas-y-shoppings-en-junio-segun-el-indec/).
15. Deuda: [TN, personales y tarjetas](https://tn.com.ar/economia/2026/07/25/la-morosidad-de-las-familias-llego-al-128-en-mayo-y-alcanzo-el-nivel-mas-alto-en-mas-de-20-anos/),
    [CEPA](https://centrocepa.com.ar/documentos/informes/822-endeudamiento-y-mora-en-familias-y-empresas),
    [UNSAM/CETyD](https://noticias.unsam.edu.ar/2026/08/18/un-mercado-laboral-saturado-y-hogares-cada-vez-mas-endeudados-nuevo-informe-de-coyuntura-del-cetyd/),
    [Infobae, carga 24,1%](https://www.infobae.com/economia/2026/07/17/mora-record-los-argentinos-destinan-casi-un-cuarto-de-su-salario-a-pagar-deudas/?outputType=amp-type).

## Pruebas y límites

Se ejecutó el verificador de remediación contra la línea base: **OK**, score
global 3,9 → 3,7. También se ejecutaron 111 pruebas focalizadas de ICC,
supermercados, universos, suspensión, trabajo independiente e ITCIS: **111
pasaron**.

Persisten límites externos, no fallas del pipeline: no existe una encuesta de
victimización nacional contemporánea equivalente al IVI; no hay publicación
independiente del total exacto de tres carnes, del recorte SRT ≤50 ni del
rolling de motorización; y Google Trends no aporta valencia ni una muestra
inmutable. Esos límites explican los siete “Compatible” y la suspensión de
sentimiento, en vez de fabricar confirmaciones por falsa equivalencia.
