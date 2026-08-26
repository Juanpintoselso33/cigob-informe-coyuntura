# Reauditoría post-remediación — Gestión

**Fecha de corte:** 25 de agosto de 2026

**Snapshot auditado:** `web/src/data/informe.json`, generado a las 19:27:20 −03:00

**Universo:** los 14 indicadores de la auditoría original; 13 continúan publicados y `reestructuracion_organismos` fue retirado

**Resultado sobre las 13 cards vigentes:** 7 confirmadas, 6 compatibles, 0 discrepantes y 0 no verificables
**Decisión retirada:** 1 discrepancia anterior correctamente excluida del score y de las cards

## Resultado ejecutivo

La remediación resolvió las dos discrepancias originales de Gestión. `concesiones_infraestructura` pasó de 28,7% a 100% al incorporar las adjudicaciones de las etapas II-B y III publicadas en el Boletín Oficial. `reestructuracion_organismos` dejó de puntuar y de mostrarse como card porque `11/45` mezclaba normas con una meta documental sin universo homogéneo.

No queda una cifra discrepante entre las 13 cards publicadas. Sí queda una inconsistencia transversal: la ficha de la dimensión Reforma del Estado todavía dice que se compone de tres medidas e incluye reestructuración, y el bloque de redundancia del snapshot sigue analizando 14 componentes y 76 pares. El ITCG vigente usa correctamente sólo los dos componentes activos de esa dimensión; el residuo está en documentación y analítica derivada, no en el score.

## Matriz completa 14/14

| # | Indicador | Estado actual | Contraste post-cambio | Veredicto actual | Confianza | Cambio respecto de la auditoría original |
|---:|---|---|---|---|---|---|
| 1 | Brecha cambiaria | 5,91%, 25-08-2026 | Fuentes del mismo día ubican CCL en $1.600–1.601 y mayorista en $1.510: brecha 5,98–6,05% | Compatible | Alta | Actualización intradiaria; sin cambio metodológico |
| 2 | Apertura comercial | 6,18%, jun-2026 | ARCA: $881.128 M DEX + $545.789 M DIM; INDEC: USD 15.916 M de intercambio; el cociente convertido por A3500 queda en torno a 6,18% | Compatible | Alta | Sin cambio |
| 3 | Desregulación normativa | 16.771 artículos, jul-2026 | Coincide con 719 normas, 2.803 normas afectadas y 16.771 artículos publicados por el Ministerio y replicados externamente | Confirmado como conteo oficial | Alta | Sin cambio |
| 4 | Dotación del Estado | −20,36% vs dic-2023, jun-2026 | INDEC/prensa: APN 184.202 agentes; total APN+empresas 271.696. El universo y la exclusión de empresas ahora están explícitos | Confirmado | Alta | Mejoró la descripción del universo |
| 5 | Gasto de funcionamiento | −31,37% real vs jun-2023 | CEPA obtiene aproximadamente −31,4% para el mismo agregado y período | Confirmado | Alta | Sin cambio |
| 6 | Reestructuración de organismos | Retirado | La evidencia sigue mostrando que 11 contaba normas que afectaban más entidades y que 45 no era una meta oficial homogénea | Retiro correcto | Alta | Era discrepante; ya no puntúa ni aparece como card |
| 7 | Fondo de Asistencia Laboral | 50/100, 25-08-2026 | Ley 27.802 y Decreto 408/2026 dictados; vigencia diferida al 01-11-2026; la fórmula CIGOB reproduce 50 | Confirmado | Alta | Sin cambio |
| 8 | Litigiosidad laboral | +2,1%, 12m a may-2026 | SRT publica 10.699 juicios en may-2026 contra 11.937 un año antes; el acumulado móvil local es plausible pero el contraste visible no replica las 24 sumas | Compatible | Media-alta | Sin cambio |
| 9 | Privatizaciones | 51,4%, corte 30-06-2026 | Las fuentes confirman el estado heterogéneo de las empresas, pero no la codificación propia 0–4 ni su promedio | Compatible | Media | Sin cambio; conserva rezago declarado |
| 10 | Inversiones RIGI | 23,5%, 25-08-2026 | 21 proyectos con resolución por USD 46.708 M y 23 en evaluación por cerca de USD 152.300 M reproducen 23,5% del pipeline | Confirmado | Alta | Actualización marginal de insumos, mismo resultado |
| 11 | Concesiones viales | 100% = 9.091/9.091 km | Res. 1149/2026 adjudica los cuatro tramos de Etapa II-B; Res. 1379/2026 adjudica los ocho de Etapa III; sumadas I y II, las cuatro etapas cubren el plan | Confirmado | Alta | Corregido desde 28,7%; discrepancia resuelta |
| 12 | Asistencia directa (TDPS) | 100% | La estructura de pagos directos está respaldada, pero la partida presupuestaria 5.1.4 no demuestra por sí sola ausencia total de intermediación operativa | Compatible | Media-baja | Sin cambio |
| 13 | Orden público | 74,2% de reducción en CABA, 2025 vs 2023 | 240 cortes en 2025; 11,3% de 8.239 en 2023 implica aproximadamente 931; la reducción es 74,2% | Confirmado | Alta | Sin cambio |
| 14 | Libertad de opción en salud | 31,8%, mar-2026 | Estudios sectoriales ubican aproximadamente 2,5 M de personas con aportes directos y 6,8 M con prepaga; confirma orden de magnitud, no el padrón RNEMP exacto de 8,369 M | Compatible | Media | Sin cambio |

## Evidencia post-remediación

### Brecha cambiaria

TN informó CCL de $1.600,29 y mayorista de $1.510 durante la jornada; La Nación informó CCL cercano a $1.600 y cierre mayorista de $1.510. Eso produce una brecha en torno a 6%, compatible con el 5,91% capturado por la API a las 18:39. No se eleva a confirmado exacto porque no hay una segunda captura independiente con el mismo timestamp.

Fuentes: [TN — cotizaciones del 25 de agosto](https://tn.com.ar/economia/2026/08/25/dolar-a-cuanto-cotizan-el-oficial-y-las-otras-opciones-cambiarias-este-martes-25-de-agosto/), [La Nación — cierre mayorista del 24 de agosto](https://www.lanacion.com.ar/economia/el-dolar-mayorista-abrio-la-semana-superando-la-barrera-de-los-1500-nid24082026/).

### Apertura comercial

INDEC publicó USD 9.055 M de exportaciones y USD 6.861 M de importaciones en junio, total USD 15.916 M. ARCA informó $881.128 M de derechos de exportación y $545.789 M de importación. La suma nominal, convertida por el A3500 promedio del mes, es aproximadamente USD 984 M; `984 / 15.916 × 100 = 6,18%`.

Fuentes: [INDEC — ICA junio de 2026](https://www.indec.gob.ar/ftp/ica_digital/ica_d_07_26EF37859542/), [ARCA — recaudación y estadística tributaria](https://arca.gob.ar/institucional/estudios/), [ARCA — información agregada de comercio exterior](https://arca.gob.ar/operadoresComercioExterior/informacionAgregada/informacion-agregada.asp).

### Desregulación, dotación y gasto

El conteo de desregulación de julio vuelve a aparecer como 719 normas, 2.803 normas afectadas y 16.771 artículos. Para dotación, fuentes que reproducen INDEC informan 184.202 agentes de APN y 87.494 de empresas en junio. La ficha actual distingue correctamente ambos universos. El gasto real coincide al redondeo con el cálculo externo de CEPA.

Fuentes: [Ministerio de Desregulación](https://www.argentina.gob.ar/desregulacion), [cobertura del conteo de julio](https://www.imago.com.ar/es/politica/36323/el-estado-le-saca-el-pie-de-encima-16771-articulos-menos-en-julio), [dotación de junio](https://www.ellitoral.com/economia/indec-empleoestatal-administracionpublica-recortes-planta-semestre-2026-ahora_0_uNN3HUujhL.amp.html), [CEPA — ejecución a junio de 2026](https://centrocepa.com.ar/documentos/informes/817-la-ejecucion-presupuestaria-de-la-administracion-publica-nacional-datos-a-junio-2026).

### Reforma laboral

El artículo 27 del Decreto 408/2026 difiere el FAL al 1 de noviembre de 2026. Con 50 puntos por construcción normativa, cero por vigencia y cero por adopción, el índice reproduce 50. La SRT confirma los flujos mensuales de litigiosidad; la cifra anual móvil sigue siendo compatible y exige las 24 sumas para una réplica externa exacta.

Fuentes: [Decreto 408/2026](https://www.argentina.gob.ar/normativa/nacional/norma-426272/texto), [SRT — últimos datos](https://www.srt.gob.ar/estadisticas/lit_ultimos_datos.php), [SRT — serie histórica](https://www.srt.gob.ar/estadisticas/lit_serie_historica.php).

### Privatizaciones, RIGI y concesiones

El seguimiento externo conserva el diagnóstico heterogéneo de privatizaciones, por lo que 51,4% continúa como compatible y no confirmado. Para RIGI, el universo publicado permite reproducir `46.708 / (46.708 + 152.302) = 23,47%`. Las dos resoluciones faltantes en la auditoría anterior cierran concesiones: II-B aporta 2.557,11 km y III 3.920,21 km; junto con I y II, el inventario suma 9.090,85 km, que el plan y la card redondean a 9.091.

Fuentes: [estado legislativo de privatizaciones](https://www.datalegislativa.com/2026/08/12/el-congreso-analiza-las-privatizaciones/), [plataforma oficial RIGI](https://www.argentina.gob.ar/economia/rigi), [Res. 1149/2026 — Etapa II-B](https://www.boletinoficial.gob.ar/detalleAviso/primera/345005/20260728), [Res. 1379/2026 — Etapa III](https://www.argentina.gob.ar/normativa/nacional/norma-429144), [página oficial de la RFC](https://www.argentina.gob.ar/transporte/vialidad-nacional/red-federal-de-concesiones).

### Reforma social y orden

La política de pagos directos está documentada, pero no existe evidencia externa suficiente para convertir la clasificación presupuestaria en prueba de ausencia total de intermediación; TDPS permanece compatible. Diagnóstico Político, citado por La Nación, permite reconstruir exactamente 74,2% para CABA. En salud, el benchmark sectorial respalda el numerador y orden de magnitud, pero usa un denominador menor que el padrón administrativo.

Fuentes: [reasignación directa de programas sociales](https://www.argentina.gob.ar/node/201395), [La Nación — piquetes 2023–2025](https://www.lanacion.com.ar/politica/los-piquetes-se-redujeron-mas-del-527-desde-que-asumio-milei-hay-menos-protestas-de-las-nid13012026/), [Instituto de Salud Global — seguimiento del sistema](https://isg.org.ar/wp-content/uploads/2026/04/Seguimiento-propuestas-de-salud-anunciadas-en-2023-por-LLA-Milei.pdf), [norma de derivación directa](https://servicios.infoleg.gob.ar/infolegInternet/anexos/405000-409999/408968/texact.htm).

## Correcciones comprobadas

### Concesiones

La card ya no confía únicamente en el estado atrasado de CONTRAT.AR. El inventario declara para cada etapa el proceso, kilómetros, estado, fuente jurídica, resolución y fecha. II-B y III se consideran adjudicadas por resolución aun cuando el portal siga mostrando `Disponible Para Adjudicar`. La aritmética y el rótulo son consistentes con la unidad elegida.

### Reestructuración

`reestructuracion_organismos` no está en `cinturones.gestion.indicadores` ni en las dimensiones efectivas del ITCG. Reforma del Estado conserva 25% del cinturón y renormaliza automáticamente sus dos componentes activos:

- `reduccion_estado`: 58,33% dentro de la dimensión; 14,58% efectivo del ITCG;
- `gasto_funcionamiento`: 41,67% dentro de la dimensión; 10,42% efectivo.

Los pesos efectivos de los 13 indicadores suman 1 y la dimensión suma 1 entre sus componentes activos.

## Residuo nuevo: suspensión incompleta en metadatos derivados

El score está corregido, pero la publicación no quedó completamente coherente:

1. `web/src/lib/descripciones.ts` y `output/fichas/fichas-gestion.md` todavía definen Reforma del Estado como tres medidas e incluyen reestructuración.
2. `web/src/data/informe.json` publica `itcg.redundancia.n_indicadores = 14`, `n_pares = 76` y texto sobre «14 componentes», aunque sólo existen 13 cards activas.
3. `output/validacion_externa.json` sigue calculando correlaciones y pares con `reestructuracion_organismos`.
4. La serie histórica y los artefactos internos conservan el ID retirado, lo cual puede ser legítimo como archivo, pero los textos públicos no distinguen componente histórico retirado de componente vigente.

**Impacto:** no altera el ITCG 79,6 ni su tensión 2,0, pero sí hace falsa la explicación pública de composición y contamina la lectura del diagnóstico de redundancia.

**Acción recomendada:** excluir indicadores suspendidos de todas las analíticas que describan los componentes vigentes, o rotular explícitamente los análisis históricos como universo antiguo. Actualizar la descripción de Reforma del Estado a dos medidas. Agregar una regresión que compare el conjunto de IDs activos del índice con los IDs usados por fichas, redundancia, sensibilidad y validación externa.

## Resultado del cinturón

| Métrica | Antes de la remediación | Estado actual |
|---|---:|---:|
| Cards publicadas | 14 | 13 |
| ITCG | 73,0 | 79,6 |
| Tensión | 2,7 | 2,0 |
| Confirmadas | 7 | 7 |
| Compatibles | 5 | 6 |
| Discrepantes publicadas | 2 | 0 |
| Retiradas por discrepancia | 0 | 1 |

El cambio de confirmado a compatible en brecha no es una refutación: el valor pasó de 6,0 a 5,91 dentro del día y no existe una captura externa del mismo timestamp. La corrección material del cinturón está bien: las dos discrepancias anteriores dejaron de afectar el producto. Falta cerrar la coherencia de los metadatos derivados.
