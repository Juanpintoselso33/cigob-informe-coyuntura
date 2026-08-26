# Reauditoría post-remediación · Macroeconomía

**Fecha de corte:** 25 de agosto de 2026

**Snapshot auditado:** `web/src/data/informe.json`, generado el 25/08/2026 a las 19:27:20 (UTC−3)

**Universo:** 17/17 indicadores publicados del cinturón Macro

**Código revisado:** `scripts/macro.py`, `scripts/desequilibrio_monetario.py`, `scripts/itcm.py`, `scripts/parametrica.py` y pruebas específicas

**Ficha contrastada:** `output/fichas/fichas-macro.md`

## Metodología y criterio de veredicto

Esta reauditoría parte del estado actual, no de los resultados de la auditoría anterior. Para cada indicador se controlaron: cifra, período, unidad, universo, fórmula, datos auxiliares publicados, puntaje, dimensión y peso efectivo. La fuente oficial se usó como control primario y se realizó una búsqueda web específica de corroboración en prensa económica, consultoras, centros de estudios o literatura metodológica. Una nota que sólo replica el comunicado oficial controla transcripción y período, pero no constituye por sí sola una estimación independiente.

En índices propios CIGOB se separaron tres planos: exactitud de los insumos, reproducción de la fórmula y validez del constructo/puntaje. La aritmética exacta no basta para confirmar un rótulo causal ni el signo normativo de una escala.

- **Confirmado:** cifra, corte, unidad, universo y significado coinciden con evidencia trazable, dentro del redondeo.
- **Compatible:** la aritmética cierra y el contraste externo sostiene magnitud/sentido, pero no existe un equivalente idéntico o hay una diferencia explicable de universo/revisión.
- **Discrepante:** hay una contradicción material en el valor, universo, definición o tratamiento dentro del score.
- **No verificable:** falta el insumo indispensable para reproducirlo o no existe evidencia suficiente siquiera para juzgar compatibilidad.

La validación automática de remediaciones terminó sin fallas y las pruebas dirigidas arrojaron **67 aprobadas**. Los pesos efectivos suman **1,0000** y los pesos internos de cada dimensión también suman uno. Por tanto, no se detectó una rotura mecánica de series, pesos o agregación; sí se detectó un dato de entrada todavía incorrecto y tres escalas/constructos que continúan sin sustento suficiente.

## Matriz ejecutiva — cobertura 17/17

| # | Indicador | Publicado actual | Universo/fórmula auditada | Puntaje · peso | Veredicto | Confianza | Recomendación |
|---:|---|---|---|---:|---|---|---|
| 1 | Inflación mensual | 2,11% · jul-26 | IPC nacional, nivel general, m/m | 72,8 · 10,40% | **Confirmado** | alta | Sin corrección. |
| 2 | Reservas netas CIGOB | USD 11.962 M · 31-jul | SDDS estricto + Tesoro + BOPREAL 12m | 67,8 · 5,44% | **Compatible** | media | Mantener visible la definición CIGOB y rangos alternativos. |
| 3 | Capacidad prestable (IdC) | −0,32σ · jul-26 | z-scores de precio, volumen y asignación 30/40/30 | 49,3 · 3,36% | **Compatible** | alta numérica / media conceptual | Renombrar o rediseñar el componente de asignación neto de encajes. |
| 4 | EMAE interanual | 2,69% · jun-26 | EMAE nacional, i.a. | 69,5 · 6,60% | **Confirmado** | alta | Sin corrección. |
| 5 | Difusión EMAE | 80% (12/15) · jun-26 | sectores con variación i.a. positiva, igual peso | 80,0 · 2,20% | **Confirmado** | alta | Conservar visible 12/15. |
| 6 | IPI manufacturero 3m | −2,00% · abr-jun | media de tres variaciones i.a. revisadas | 32,0 · 2,20% | **Compatible** | alta | Publicar los tres puntos revisados. |
| 7 | Saldo comercial 12m | USD 22.481 M · jul-25/jun-26 | exportaciones menos importaciones, 12 meses | 85,0 · 4,80% | **Confirmado** | alta | Mostrar ventana y ambos totales. |
| 8 | Base imponible real | 88,2 · jun-26 | DGI seleccionada + seis sistemas COMARB; 4T-23=100 | 43,0 · 7,20% | **Compatible** | media | Publicar serie, empalme y factores estacionales. |
| 9 | TCRM | 85,47 · jul-26 | promedio mensual BCRA, dic-15=100 | 48,7 · 11,00% | **Compatible** | media-alta | Rotular “promedio mensual” y versionar XLSX. |
| 10 | REM inflación 12m | 21,8% · encuesta jul-26 | expectativa para los próximos doce meses | 81,9 · 5,20% | **Confirmado** | alta | Sin corrección. |
| 11 | Brecha de crecimiento real M3–M2 | 4,7 pp · jul-26 | M3 privado real i.a. − M2 transaccional real i.a. | 50,0 · 5,20% | **Discrepante** | media-alta | Mantener el valor, pero retirar/recalibrar el score hasta justificar signo y bandas. |
| 12 | Tensión monetaria CIGOB | 50,86 · jun-26 | matriz A: liquidez transaccional; B: compra neta sin fines específicos | 49,1 · 5,20% | **Discrepante** | alta | Reestimar la matriz; el peso punitivo de B conserva una interpretación refutada. |
| 13 | IAI físico | −0,18% · jun-26 | 65% ISAC + 35% importaciones de capital, i.a. | 59,2 · 7,20% | **Confirmado** | alta | Mostrar −0,2% y pesos 65/35. |
| 14 | Pagos digitales y productividad (ICIP) | 8,36% · abr-26 | 57% pagos de servicios tech + 43% IPI/empleo | 73,4 · 4,80% | **Discrepante** | alta | Sacarlo de Inversión o sustituir el primer insumo; no asignar signo positivo automático. |
| 15 | Crédito privado real en pesos | −1,5% · jul-26 | préstamos en pesos al sector privado, punta i.a., deflactados | 32,8 · 3,20% | **Confirmado** | alta | Remediación correcta; explicitar punta frente a promedio. |
| 16 | Costo real del Tesoro | 5,80% · jul-26 | TIREA ponderada por VE contra REM 12m | 88,3 · 4,00% | **Discrepante** | alta | Corregir reaperturas: el valor reproducible es ≈4,18%, no 5,80%. |
| 17 | Resultado primario/recaudación | 5,55% · 12m a jun | resultado primario SPN / recaudación tributaria, 12m | 82,2 · 12,00% | **Compatible** | alta | Publicar numerador y denominador; no compararlo con % del PIB. |

## Comparación antes/después de los cinco casos remediados

| Indicador | Antes de la remediación | Estado publicado actual | Resultado de esta reauditoría |
|---|---|---|---|
| `costo_financiamiento_tesoro` | 8,07% real, jun-26; una TIREA reconstruida erróneamente | 5,80% real, jul-26; TIREA nominal 28,87% | **Sigue discrepante.** La emisión nueva de fin de mes está bien, pero la reapertura S30N6 usa el cupón contractual (31,37%) en vez de la TIREA de corte (25,59%). |
| `credito_privado` | +2,5% real, mezclaba pesos y moneda extranjera revaluada | −1,5% real, sólo préstamos en pesos | **Corregido y confirmado.** First Capital obtiene −1,3% con una estimación de IPC previa; la diferencia desaparece con IPC definitivo/redondeo. |
| `idm` | “Exceso de pesos sobre demanda”, 4,73 pp | “Brecha de crecimiento real M3–M2 transaccional”, 4,7 pp | **Nombre corregido; score pendiente.** El valor es exacto, pero las bandas todavía castigan mecánicamente una brecha positiva como si fuera exceso monetario. |
| `desequilibrio_monetario` | “Dolarización dentro y fuera del sistema” | “Tensión monetaria CIGOB” y B descrito como compra neta | **Rótulo corregido; score pendiente.** La matriz y su asimetría no cambiaron y el código interno aún razona en términos de “fuga”. |
| `icip` | “Capitalización digital” | “Pagos de servicios digitales y productividad” | **Rótulo descriptivo corregido; ubicación/signo pendientes.** Sigue en la dimensión Inversión y todo aumento de pagos eleva el ITCM. |

El score macro visible permaneció en **3,6** y la paramétrica en **64,1** tras la remediación. Esto no prueba neutralidad: cambios opuestos y redondeos pueden compensarse. Los tests confirman la mecánica; no confirman la validez económica de las bandas.

## Auditoría de la superficie publicada: remediación incompleta

El JSON y los títulos principales cambiaron, pero la lectura activa que recibe el usuario no quedó remediada de punta a punta. No se trata sólo de antecedentes preservados en el historial de cambios:

- En `web/src/lib/formulas.ts`, la fórmula activa de IDM todavía presenta M2 como “pesos que la gente QUIERE” y su leyenda afirma “Positivo = sobran pesos → presión sobre precios y brecha”. Esto contradice directamente el ADR que reconoce que aquí no existe una función estimada de demanda de dinero.
- En el mismo archivo, la leyenda activa de tensión monetaria conserva las esquinas “fuga oculta fuera del sistema” y sostiene que “la fuga fuera del sistema es la señal grave”, aunque dos frases antes reconoce que B no informa el destino y que gran parte quedó depositada localmente.
- En `web/src/lib/fichas.ts`, las transformaciones activas de IDM todavía dicen “Positivo = sobran pesos” y `dobleUso` vuelve a llamar a M2 “demanda transaccional”. En tensión monetaria, `dobleUso` habla de “salida efectiva de divisas” y “la misma fuga”, y una limitación activa interpreta retrospectivamente “poca fuga”. Son campos renderizables, no menciones históricas.
- Para ICIP, `web/src/lib/formulas.ts` define los insumos como “variaciones interanuales de la inversión intangible” y `web/src/pages/[slug].astro` presenta activamente “ICIP (capitalización digital...)”. La ficha reconoce la ambigüedad, pero el resumen narrativo sigue atribuyendo formación de capital.
- En cambio, las entradas fechadas `cambios` que dicen “se publicaba como...” o explican por qué se retiró un nombre son historia metodológica válida y no deben contarse como deuda editorial.

Este hallazgo refuerza —y por sí solo bastaría para sostener— los veredictos **Discrepante** de IDM, tensión monetaria e ICIP en el estado post-cambios. La corrección debe abarcar fórmula, leyenda, ficha activa y narrativa de capítulo, además del nombre de la card.

## Evidencia detallada por indicador

### 1. Inflación mensual (`ipc_total`)

**Control actual.** 2,11% mensual, julio de 2026, IPC nacional nivel general. El INDEC comunicó 2,1%; el segundo decimal proviene de la serie descargable. Chequeado confirma mes, unidad y 2,1%, además de 19,3% acumulado y 33,8% i.a. No hay transformación de universo. El puntaje 72,8 reproduce la interpolación declarada y su peso efectivo es `0,26 × 0,40 = 0,104`.

**Fuentes:** [INDEC — IPC](https://www.indec.gob.ar/Nivel4/Tema/3/5/31), [Chequeado — inflación julio 2026](https://chequeado.com/el-explicador/la-inflacion-de-julio-de-2026-fue-del-21-y-rompio-con-3-meses-de-caidas-intermensuales/).

**Veredicto:** **Confirmado**, confianza alta. Sin corrección.

### 2. Reservas netas CIGOB (`reservas_bcra`)

**Control actual.** `5.820 + 3.606 + 2.537 = 11.963` millones; el 11.962 publicado responde a componentes internos no redondeados. Es una convención CIGOB: SDDS estricto más depósitos del Tesoro y BOPREAL de hasta doce meses. La Bolsa de Comercio de Rosario ubicó las netas de fin de julio en USD 7.000–10.000 millones bajo otras deducciones; análisis privado encontró cerca de USD 11.948 millones con una metodología corta comparable. Las brutas y la dirección son consistentes, pero “reservas netas” no tiene una definición única.

**Fuentes:** [BCRA — SDDS](https://www.bcra.gob.ar/normas-especiales-para-la-divulgacion-de-datos-fmi/), [Bolsa de Comercio de Rosario — reservas](https://www.bcr.com.ar/es/mercados/investigacion-y-desarrollo/informativo-semanal/noticias-informativo-semanal/las-reservas-2), [Inversiones Andinas — research julio](https://inversionesandinas.com/research-de-mercados-julio-2026/).

**Veredicto:** **Compatible**, confianza media. La card debe conservar “metodología CIGOB” y el desglose.

### 3. Capacidad prestable (`idc`)

**Control actual.** La cuenta se reproduce: tasa real BADLAR −0,469 pp, depósitos privados en pesos −2,525% real i.a. y holgura `1 − 103,376/124,667 = 17,079%`. Con medias/desvíos históricos, los z-scores son 0,363, −0,202 y −1,153; `0,30×0,363 + 0,40×(−0,202) + 0,30×(−1,153) = −0,317σ`, publicado −0,32σ.

La aparente contradicción con el 67% préstamos/depósitos de Criteria quedó reconciliada. El XLSX monetario del BCRA usa promedios mensuales y **sector no financiero total**: `102.663.784,903 / 152.696.766,806 = 67,230%`. CIGOB usa saldos de fin de mes y **sector privado**: `103.375.772 / 124.667.259 = 82,919%`. No son el mismo denominador. La literatura prudencial, sin embargo, define capacidad de fondeo sobre depósitos utilizables, normalmente netos de encajes, por lo que el nombre continúa siendo más fuerte que el cociente bruto.

**Fuentes:** [BCRA — Informe Monetario julio](https://www.bcra.gob.ar/publicaciones/informe-monetario-mensual-julio-de-2026/), [BCRA — XLSX de indicadores julio](https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/indicadores-informe-monetario-mensual-2026-07.xlsx), [Criteria — julio 2026](https://criteria.com.ar/informes-monetarios-mensuales/informe-monetario-bcra-julio-2026-que-paso-con-la-base-monetaria-el-credito-y-las-reservas/), [BCRA — estabilidad financiera y capacidad prestable](https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/ief0225.pdf), [FMI — guía de indicadores de solidez financiera](https://www.imf.org/en/-/media/files/data/2019/2019-fsi-guide.pdf).

**Veredicto:** **Compatible**, confianza alta para cifra/universo y media para constructo. Publicar los niveles y fijar la ventana de estandarización; para llamarlo capacidad prestable, descontar encajes y otros fondos no prestables.

### 4. EMAE interanual (`emae_ia`)

**Control actual.** 2,69% i.a. en junio; prensa económica informó 2,7% y +0,8% mensual desestacionalizado. El dato, corte y unidad coinciden. Puntaje 69,5 y peso `0,11 × 0,60 = 0,066` reproducidos.

**Fuentes:** [Forbes Argentina — EMAE junio](https://www.forbesargentina.com/money/la-actividad-economica-crecio-08-junio-sectores-impulsaron-suba-cuales-quedaron-rojo-n95986/amp), [Reuters vía MarketScreener](https://es.marketscreener.com/noticias/actividad-econ-mica-de-argentina-2-7-en-junio-indec-ce7859d3df8bf427).

**Veredicto:** **Confirmado**, confianza alta.

### 5. Difusión sectorial EMAE (`emae_difusion`)

**Control actual.** Doce de quince sectores crecieron i.a.; `12/15 = 80%`. Las tres bajas —Administración pública, Electricidad/gas/agua y Enseñanza— coinciden con el detalle difundido. Es una amplitud de conteo con igual peso, no aporte al EMAE. Puntaje y valor coinciden en 80,0; peso efectivo 2,2%.

**Fuentes:** [El Cronista — EMAE y 12/15](https://elcronista-el-cronista-prod.web.arc-cdn.net/economia-politica/la-actividad-economica-reboto-en-junio-crecio-27-impulsada-por-la-mineria-y-el-campo/), [MZ Agro — actividad junio](https://mzagro.com.ar/actividad-economica-junio-emae/).

**Veredicto:** **Confirmado**, confianza alta.

### 6. IPI manufacturero, media de tres meses (`ipi_manufacturero`)

**Control actual.** La serie revisada contiene abril −2,40%, mayo −5,64% y junio +2,02%; la media simple es −2,006%, publicada −2,00%. Las primeras gacetillas difieren levemente por revisión, motivo por el cual un cálculo con titulares iniciales no cierra igual. El puntaje 32,0 y peso 2,2% son correctos para −2,0.

**Fuentes:** [INDEC — IPI manufacturero](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-6-14), [Trading Economics — producción industrial](https://es.tradingeconomics.com/argentina/industrial-production), [Kartal — IPI mayo](https://kartal.com.ar/informes/industria_mayo_2026.php).

**Veredicto:** **Compatible**, confianza alta. La ficha debe decir que CIGOB calcula la media y enumerar los puntos revisados.

### 7. Saldo comercial acumulado doce meses (`saldo_comercial_12m`)

**Control actual.** Exportaciones acumuladas USD 96.824 millones menos importaciones USD 74.343 millones = USD 22.481 millones entre julio de 2025 y junio de 2026. El semestre 2026 fue USD 13.923 millones y junio USD 2.194 millones; la reconstrucción con cifras anuales de prensa queda a 0,12% por redondeos/revisiones. Puntaje 85,0 y peso 4,8% correctos.

**Fuentes:** [TN — comercio primer semestre](https://tn.com.ar/economia/2026/07/20/la-argentina-tuvo-un-superavit-comercial-de-us-13923-millones-en-el-primer-semestre/?outputType=amp), [La Nación — intercambio junio](https://www.lanacion.com.ar/economia/se-quintuplicaron-las-exportaciones-en-el-primer-semestre-y-junio-deja-un-superavit-comercial-de-nid20072026/).

**Veredicto:** **Confirmado**, confianza alta. Mostrar la ventana móvil y no confundirla con enero-junio.

### 8. Base imponible real (`recaudacion`)

**Control actual.** En junio, la selección DGI sumó $11,895 billones y los seis sistemas COMARB $2,182 billones; total $14,077 billones y participación provincial 15,497%. Deflactar, dividir por el factor estacional de junio 1,11886 y normalizar por el promedio 4T-2023 reproduce 88,163 → 88,2. CEPA e IARAF encuentran caídas reales de 8,8% y 7,4% i.a. para universos fiscales más amplios, compatibles con un nivel deprimido frente a 2023, pero no publican el mismo empalme.

**Fuentes:** [COMARB — gacetilla junio](https://www.ca.gob.ar/descargas/gacetillas/2026/Gacetilla_Recaudacion_Mensual_06_Jun_2026.pdf), [CEPA — ingresos junio](https://centrocepa.com.ar/documentos/informes/821-analisis-de-los-ingresos-gastos-y-resultados-del-sector-publico-nacional-datos-de-junio-2026), [La Nación/IARAF — recaudación](https://www.lanacion.com.ar/economia/la-recaudacion-cayo-74-en-junio-tras-el-rebote-de-mayo-nid01072026/), [serie DGI](https://apis.datos.gob.ar/series/api/series/?ids=172.3_SOTAL_DDGI_M_0_0_12&start_date=2023-01-01&end_date=2026-06-30).

**Veredicto:** **Compatible**, confianza media. Publicar factores y serie combinada; “COMARB” no equivale a toda la recaudación provincial.

### 9. Tipo de cambio real multilateral (`tcrm`)

**Control actual.** 85,47, promedio de julio, base diciembre de 2015=100. Apliconomy publica 85,87 con elaboración sobre BCRA y Criteria registra depreciación real mensual; la diferencia de 0,40 punto (0,47%) es compatible con versión/corte de planilla. Definición y unidad corresponden al ITCRM promedio de socios ponderados. Puntaje 48,7, único indicador de la dimensión y peso efectivo 11%.

**Fuentes:** [BCRA — índice y metodología](https://www.bcra.gob.ar/indices-de-tipo-de-cambio-multilateral/), [Apliconomy — agosto 2026](https://apliconomy.com/informe-macroeconomico-agosto-2026/), [Criteria — julio 2026](https://criteria.com.ar/informes-monetarios-mensuales/informe-monetario-bcra-julio-2026-que-paso-con-la-base-monetaria-el-credito-y-las-reservas/).

**Veredicto:** **Compatible**, confianza media-alta. Versionar la descarga para distinguir revisión de error.

### 10. REM de inflación a doce meses (`rem_ipc_12m`)

**Control actual.** 21,8% anual esperado en el relevamiento del 29–31 de julio, publicado el 6 de agosto. Infobae publica exactamente 21,8% para los próximos doce meses y 29,8% para calendario 2026; no deben confundirse. La transformación a equivalente mensual usada sólo para puntuar reproduce 81,9 y el peso es 5,2%.

**Fuentes:** [BCRA — REM julio](https://www.bcra.gob.ar/relevamiento-expectativas-mercado-rem/), [Infobae — expectativas](https://www.infobae.com/economia/2026/08/06/las-consultoras-que-releva-el-bcra-proyectaron-una-inflacion-de-2-para-julio-que-estiman-para-agosto/?outputType=amp-type).

**Veredicto:** **Confirmado**, confianza alta.

### 11. Brecha de crecimiento real M3–M2 transaccional (`idm`)

**Control numérico.** Con circulante privado (var. 17), depósitos privados en pesos (var. 100), M2 transaccional privado (var. 197) e IPC, se obtienen M3 real −3,64% i.a. y M2 real −8,33%; diferencia 4,69 pp, publicada 4,7. El BCRA reporta para julio +1,8% mensual real desestacionalizado de M2 y leve caída de M3; no contradice una comparación de puntas interanuales.

**Problema post-remediación.** El nuevo nombre describe correctamente la operación. Pero el score conserva anclas heredadas del supuesto “exceso”: valores positivos reducen el puntaje (4,7 → 50) sin una validación que muestre que crecer menos M2 que M3 sea necesariamente más tensión. Puede reflejar sustitución desde saldos transaccionales hacia plazo fijo y mayor fondeo estable. La literatura de *monetary overhang* exige comparar dinero observado con demanda estimada a partir de actividad, tasas y expectativas; M3−M2 no aporta ese contrafactual. Por eso cifra y título son correctos, pero el indicador **tal como entra al ITCM** no lo es.

Además, la publicación activa contradice su propio cambio: `formulas.ts` sigue equiparando M2 con “pesos que la gente QUIERE” y concluye “sobran pesos”; `fichas.ts` repite esa conclusión en `transformaciones`. No son citas históricas: son explicaciones vigentes que puede renderizar el sitio.

**Fuentes:** [BCRA — Informe Monetario julio](https://www.bcra.gob.ar/publicaciones/informe-monetario-mensual-julio-de-2026/), [API BCRA — M2 transaccional](https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/197?Desde=2025-07-01&Hasta=2026-07-31), [FMI — definición de monetary overhang](https://www.elibrary.imf.org/view/journals/002/2001/201/article-A004-en.xml).

**Veredicto:** **Discrepante**, confianza media-alta, exclusivamente por tratamiento en el score. Retirar temporalmente del índice o recalibrar signo y anclas contra episodios/outcomes observables.

### 12. Tensión monetaria CIGOB (`desequilibrio_monetario`)

**Control numérico.** A=33,49% es M2 privado transaccional dividido por liquidez privada ampliada; B=USD 2.067,4 millones suma compra neta de billetes y divisas sin fines específicos del sector privado. Sus posiciones históricas 0,1634 y 0,3192, interpoladas en la matriz CIGOB, reproducen 50,86 y puntaje 49,1. El BCRA confirma que en junio las personas humanas compraron USD 2.821 millones, pero el SPNF total fue vendedor neto por USD 456 millones; B es un rubro estrecho, no el saldo privado total.

**Problema post-remediación.** El rótulo visible ya no promete “fuera del sistema”, pero la matriz conserva una asimetría fuerte: deteriorar B puede costar 77,5 puntos frente a 40 para A. Esa penalización se diseñó bajo la tesis de “fuga oculta”; el propio BCRA estima que parte de las compras queda depositada localmente o cancela consumos de tarjeta. El módulo y comentarios internos todavía usan “fuga”. El cambio nominal no validó de nuevo la matriz.

La contradicción también está publicada: la leyenda activa de `formulas.ts` todavía denomina una esquina “fuga oculta fuera del sistema” y justifica la asimetría porque “la fuga fuera del sistema es la señal grave”; `fichas.ts` habla de “salida efectiva” y “la misma fuga”. Esto contradice el campo activo que reconoce correctamente que B no identifica el destino.

**Fuentes:** [BCRA — balance cambiario junio](https://www.bcra.gob.ar/publicaciones/informe-de-evolucion-del-mercado-de-cambios-y-balance-cambiario-junio-de-2026/), [Infobae — demanda de dólares](https://www.infobae.com/economia/2026/07/31/crecio-la-demanda-de-dolares-en-junio-los-argentinos-compraron-mas-de-usd-2400-millones/), [CEPA — balance cambiario](https://centrocepa.com.ar/documentos/informes/814-principales-ejes-del-balance-cambiario-del-banco-central-datos-a-mayo-2026).

**Veredicto:** **Discrepante**, confianza alta, por la escala. Mantener A y B como datos separados y suspender el compuesto hasta justificar los cuatro vértices con evidencia.

### 13. Índice anticipador de inversión física (`iai`)

**Control actual.** ISAC +4,0% i.a. e importaciones de bienes de capital −8,0% i.a.; mientras no existe histórico suficiente de patentamientos, los pesos se renormalizan 65/35. `0,65×4,0 + 0,35×(−8,0) = −0,20%`, compatible con −0,18 por insumos no redondeados. Revista Mercado confirma el ISAC y Fundación Encuentro la caída de bienes de capital. Puntaje 59,2 y peso efectivo 7,2% correctos.

**Fuentes:** [Revista Mercado — construcción junio](https://mercado.com.ar/informes-especiales/la-construccion-crecio-4-en-junio-y-cerro-el-semestre-con-una-suba-de-28), [Fundación Encuentro — coyuntura agosto](https://www.fundacionencuentro.com/projects/informe-mensual-de-coyuntura-macroecon%C3%B3mica---agosto-2026).

**Veredicto:** **Confirmado**, confianza alta. Mostrar el redondeo −0,2 y la renormalización.

### 14. Pagos de servicios digitales y productividad (`icip`)

**Control numérico.** Pagos de servicios informáticos +15,582% i.a.; productividad aparente IPI/empleo −1,210%. `0,57×15,582 + 0,43×(−1,210) = 8,363%`, publicado 8,36. El nombre nuevo enumera, sin sobreinterpretar, ambos insumos.

**Problema post-remediación.** El indicador sigue en la dimensión **Inversión** y una suba de pagos digitales eleva automáticamente el puntaje (8,36 → 73,4). La OCDE distingue formación de capital de consumo intermedio: servicios de nube/SaaS suelen contabilizarse como consumo intermedio y pueden sustituir inversión propia. Un aumento puede responder a volumen, precio, tipo de cambio o dependencia importadora. Renombrarlo no convierte pagos corrientes en inversión ni determina un signo positivo.

La narrativa activa tampoco terminó de cambiar: `formulas.ts` llama a los insumos “variaciones interanuales de la inversión intangible” y `[slug].astro` aún presenta ICIP como “capitalización digital”. El historial fechado que registra el nombre anterior es legítimo; estas dos expresiones, en cambio, son texto vigente.

**Fuentes:** [API nacional — insumos](https://apis.datos.gob.ar/series/api/series/?ids=185.1_PAGO_SERVIICA_0_M_38,453.1_SERIE_ORIGNAL_0_0_14_46,50.3_ICS_0_M_12&start_date=2025-04-01&end_date=2026-04-30), [OCDE — medición de servicios de nube](https://www.oecd.org/en/publications/2019/03/measuring-the-digital-transformation_g1g9f08f/full-report/component-37.html), [OCDE — tablas digitales de oferta y utilización](https://www.oecd.org/en/publications/oecd-handbook-on-compiling-digital-supply-and-use-tables_11a0db02-en/full-report/component-6.html), [CIECTI — cuenta satélite digital](https://www.ciecti.org.ar/wp-content/uploads/2023/03/IT17_V06_final.pdf).

**Veredicto:** **Discrepante**, confianza alta, por dimensión y signo. Publicarlo como tablero descriptivo fuera del ITCM o reemplazar pagos por formación de capital digital observable.

### 15. Crédito privado real en pesos (`credito_privado`)

**Control actual.** La remediación cambió correctamente de cartera total en pesos equivalentes a préstamos **en pesos** al sector privado. El saldo de punta crece 31,8% nominal i.a.; con IPC 33,8%, la variación real es aproximadamente −1,5%. First Capital, usando estimación de inflación previa al dato INDEC, obtuvo saldo $104,1 billones, +31,9% nominal y −1,3% real. La diferencia de dos décimas es totalmente explicable. El BCRA publica +1,7% real i.a. para promedios mensuales del sector no financiero: no es el mismo corte/universo.

**Fuentes:** [First Capital — crédito en pesos julio](https://firstcapital.group/es/prensa/1383-los-creditos-en-pesos-profundizaron-su-caida-en-julio-en-medio-de-la-elevada-morosidad), [El Litoral — First Capital](https://www.ellitoral.com/economia/prestamosenpesos-sectorprivado-caida1-julio-argentina-ahora-hoy_0_9U6PsA77xX.amp.html), [BCRA — Informe Monetario julio](https://www.bcra.gob.ar/publicaciones/informe-monetario-mensual-julio-de-2026/).

**Veredicto:** **Confirmado**, confianza alta. El puntaje 32,8, peso 3,2% y semáforo naranja son coherentes con la nueva cifra. Conservar el dato de monedas combinadas sólo como contexto no puntuante.

### 16. Costo real del financiamiento del Tesoro (`costo_financiamiento_tesoro`)

**Publicado y fórmula declarada.** Julio: dos colocaciones a tasa fija en pesos, TIREA ponderada por valor efectivo 28,87%, REM 12m 21,8%; `1,2887/1,218 − 1 = 5,80%` real. Esa cuenta interna cierra, pero uno de sus rendimientos de entrada no es el rendimiento de colocación.

**Error residual comprobado.** Para la reapertura S30N6 del 15/07, el snapshot asigna 31,37%, resultado de anualizar el cupón contractual 2,30% TEM. La Secretaría de Finanzas publicó precio de corte $1.194, valor efectivo $2.382.801 millones y **TIREA de corte 25,59%** (TEM marginal 1,92%). En una reapertura, el cupón fija el flujo pero el precio determina el rendimiento; no puede usarse `(1+cupón TEM)^12−1`. Para la S16O6 nueva del 29/07, precio a la par, valor efectivo $4.612.305 millones y TIREA 27,57%; esa fila sí está bien.

La reconstrucción correcta es:

`TIREA jul = (25,59×2.382.801,223 + 27,57×4.612.304,505) / 6.995.105,728 = 26,8955%`

`costo real = (1,268955 / 1,218 − 1) × 100 = 4,1835%`

Con las bandas vigentes, 4,18% da puntaje **95,1**, no 88,3; la dimensión Financiamiento subiría de 62,0 a **63,7** y el ITCM de 64,1 a **64,4**. Los pesos no están rotos: el input incorrecto se propaga normalmente.

**Fuentes:** [Secretaría de Finanzas — resultado 15/07](https://www.argentina.gob.ar/node/507628), [RoadShow — S30N6 25,59%](https://www.roadshow.com.ar/economia-coloco-us-470-millones-del-nuevo-bonar-2029-y-supero-el-183-de-rollover/), [Bloomberg Línea — resultado fin de julio](https://www.bloomberglinea.com/latinoamerica/argentina/tesoro-argentino-suma-dolares-y-anota-rollover-de-casi-150-en-desafiante-licitacion-de-deuda/), [planilla oficial de colocaciones](https://www.argentina.gob.ar/sites/default/files/colocaciones_31-07-26_1.xlsx).

**Veredicto:** **Discrepante**, confianza alta. Leer TIREA/TEM de corte por licitación o calcular el rendimiento desde precio y flujo para toda reapertura; agregar una prueba con S30N6 y reauditar retrospectivamente las reaperturas.

### 17. Resultado primario sobre recaudación (`resultado_primario`)

**Control actual.** Resultado primario SPN acumulado $11,4057 billones / recaudación tributaria acumulada $205,6663 billones = 5,54575%, publicado 5,55%. IIEP UBA-CONICET confirma superávit primario móvil equivalente a 1,1% del PIB; OPC confirma signo y corte fiscal, pero usa otro denominador. El nombre y la unidad actuales sí dicen “% de la recaudación”. Puntaje 82,2 y peso 12% reproducidos.

**Fuentes:** [IIEP UBA-CONICET — política fiscal julio](https://economicas.uba.ar/iiep/reporte-de-politica-fiscal-julio-2026/), [OPC — ejecución presupuestaria junio](https://opc.gob.ar/ejecucion-presupuestaria/ejecucion-mensual-base-devengado/analisis-de-la-ejecucion-presupuestaria-de-la-administracion-nacional-junio-2026/), [CEPA — SPN junio](https://centrocepa.com.ar/documentos/informes/821-analisis-de-los-ingresos-gastos-y-resultados-del-sector-publico-nacional-datos-de-junio-2026).

**Veredicto:** **Compatible**, confianza alta. Publicar ambos acumulados y evitar compararlo de forma directa con el 1,1% del PIB.

## Integridad de score, series y pesos

- La verificación post-remediación finalizó sin fallas: universos declarados, exclusión de indicadores retirados y perímetro de publicación coinciden.
- Pruebas dirigidas: `test_macro_costo_financiamiento.py`, `test_itcm.py`, `test_constructos_no_prometen_de_mas.py`, `test_universos_declarados.py` y `test_fichas_pesos.py`: **67 passed**.
- Dimensiones del ITCM: estabilidad monetaria 26%, fiscal-comercial 24%, financiamiento 16%, inversión 12%, actividad 11%, competitividad 11%; suma 100%.
- Suma de los 17 pesos efectivos: 100%. No hay renormalización por faltantes ni ajustes manuales activos en el snapshot.
- El crédito corregido conserva serie y universo coherentes y pasa correctamente de 41,7 a 32,8 puntos.
- Los cambios de nombre de IDM, tensión monetaria e ICIP no alteraron sus series ni pesos. Precisamente por eso sus escalas heredadas siguen requiriendo remediación sustantiva.
- La prueba del Tesoro valida emisiones nuevas a la par, pero no cubre el caso crítico de reaperturas fuera de la par. El error no es de agregación: es de selección del rendimiento por fila.

## Resultado final

- **Confirmado:** 7/17.
- **Compatible:** 6/17.
- **Discrepante:** 4/17.
- **No verificable:** 0/17.
- **Cobertura:** 17/17.

Las remediaciones resolvieron por completo el universo de crédito, pero los tres constructos sólo cambiaron en títulos/cards y no en toda la superficie explicativa. Quedan cuatro hallazgos materiales: el costo del Tesoro publica 5,80% donde las TIREA de corte reproducen aproximadamente 4,18%; IDM conserva una orientación de score y textos activos de “sobran pesos”; la tensión monetaria conserva una matriz y leyendas fundadas en “fuga”; e ICIP sigue premiando pagos corrientes dentro de Inversión y llamándolos capitalización/inversión intangible. No hubo bloqueos de datos ni de búsqueda para emitir estos veredictos.
