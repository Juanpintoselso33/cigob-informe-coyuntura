# Reverificación de los indicadores de Política

**Corte de la auditoría:** 26 de agosto de 2026.

**Código auditado:** `e1dfab84` (`main`).

**Snapshot auditado:** `web/src/data/informe.json`, generado el 25 de agosto de
2026 a las 21:39:35 −03:00.

**Perímetro:** los mismos 19 indicadores del barrido anterior: 17 componentes
vigentes y 2 suspendidos conservados como archivo.

## Resultado ejecutivo

| Veredicto | Cantidad |
|---|---:|
| Confirmado | 12 |
| Compatible | 6 |
| Discrepante | 1 |
| No verificable independientemente | 0 |
| **Total** | **19** |

La remediación posterior al barrido del 25 de agosto resolvió sus cuatro
discrepancias conocidas:

- `ratio_dnu` conserva el valor correcto, **1,48 = 37/25**, y ahora la fórmula,
  la ficha y la unidad dicen lo que efectivamente corre: DNU publicados sobre
  leyes publicadas en el Boletín Oficial, identificando los DNU por tipo
  jurídico;
- `iaf_transferencias` conserva **+1,6% real** y ahora todas las capas describen
  la deflación de cada flujo mensual por el IPC de su propio mes;
- `apoyo_empresario` y `judicializacion` están fuera de las 17 tarjetas y del
  ITCP, y en el artefacto crudo figuran `en_indice: false`, sin peso ni puntaje,
  con motivo y condición de reingreso. Sus series se conservan deliberadamente
  como archivo histórico.

La nueva pasada sí encontró una discrepancia que el barrido anterior había
dado por confirmada: **`paralisis_denuncias` cuenta siete coincidencias de una
forma de URL, no todas las sesiones de las dos comisiones**. El archivo oficial
y hasta el universo curado del propio repositorio contienen reuniones dentro
de la misma ventana que el regex omite cuando la nota tiene un título
descriptivo. El valor publicado **7** subestima el universo declarado.

## Criterio de veredicto

- **Confirmado:** cifra, período, unidad, universo, cálculo y capas públicas
  coinciden con una fuente externa exacta o con un inventario oficial completo.
- **Compatible:** fuentes externas corroboran definición, magnitud y dirección,
  pero no publican el mismo agregado propio con el mismo decimal.
- **Discrepante:** al menos una de las capas contradice la cifra, el universo o
  la fórmula que afirma medir.
- Los indicadores suspendidos se evalúan por la integridad de su retirada, no
  por la validez del último número archivado que motivó la suspensión.

La comparación externa se repitió al 26 de agosto. El snapshot tiene corte del
25; una publicación posterior no se exige retroactivamente a esa foto.

## Perímetro, topología y pesos

El snapshot web contiene exactamente **17 tarjetas**. Sus identificadores
coinciden uno por uno con los 17 componentes presentes en las siete dimensiones
del ITCP. Los pesos efectivos suman `0,9999999999999999`, es decir, **1,00** a
precisión de máquina.

| Dimensión | Peso efectivo | Componentes vigentes |
|---|---:|---:|
| Poder legislativo | 0,21 | 6 |
| Alianzas territoriales | 0,19 | 3 |
| Cohesión interna | 0,15 | 1 |
| Conflicto social | 0,10 | 2 |
| Imagen y voto | 0,07 | 1 |
| Poder judicial | 0,15 | 3 |
| Sector privado | 0,13 | 1 |
| **Total** | **1,00** | **17** |

Las descripciones ya reflejan la topología real: Sector privado declara una
sola vía activa y Poder judicial tres; ambas explican cuál fue suspendida. La
ficha de `brecha_obra_publica` declara 100% de su dimensión y 13% efectivo. La
de cada suspendido presenta las bandas únicamente como regla histórica.

## Matriz completa 19/19

| # | Indicador | Valor y corte | Veredicto | Confianza | Reverificación externa y de producto |
|---:|---|---|---|---|---|
| 1 | Ventaja LLA−PJ (Votómetro) | **4,3 pp**, 9 encuestas, corte 22-07-2026 | **Compatible** | Media | El agregado ponderado es propio. EncuestAR y las encuestas contemporáneas muestran ventajas próximas pero dispersas; la prensa confirma la volatilidad del período. Sin la matriz completa externa no se replica exactamente el 4,3. [EncuestAR](https://encuestar.netlify.app/) · [El País](https://elpais.com/argentina/2026-08-21/los-salarios-y-el-empleo-son-las-nuevas-preocupaciones-de-los-argentinos-segun-los-sondeos.html). |
| 2 | Ratio DNU / leyes | **1,48 = 37/25**, 25-08-2025/25-08-2026 | **Confirmado** | Alta | El inventario expuesto contiene 37 normas tipificadas `Decreto DNU`; el [DNU 771/2026](https://www.argentina.gob.ar/normativa/nacional/norma-429094) confirma tipo y fecha del extremo reciente. Código, unidad, fórmula, descripción y ficha dicen ahora “publicados/publicadas”; no quedan referencias activas al detector textual anterior. |
| 3 | Brecha de expectativas obra pública−privada | **−1,1 pp**, promedio móvil de 12 meses; horizonte jul–sep-2026 | **Compatible** | Media-alta | La encuesta cualitativa del INDEC y su cobertura periodística confirman expectativas peores en obra pública; para jul–sep el saldo público es 18,0−29,2=−11,2. No se publica externamente el promedio de las doce brechas que construye CIGOB. [INDEC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-3-42) · [control externo](https://www.eldestapeweb.com/economia/construccion-no-despega-cayo-actividad-empresas-anticipan-meses-dificiles-202687174936). |
| 4 | Postura pública de AEA y UIA | **Suspendido**; último saldo archivado −0,429 | **Confirmado** | Alta | No aparece como tarjeta ni componente y no conserva peso/puntaje en `output/informe.json`. El bloque `suspendido` explica el corpus abierto y la condición de reingreso. La serie sigue disponible sólo como archivo histórico, coherente con ADR-0259/0265. La evidencia externa sigue mostrando posturas mixtas y confirma por qué siete textos no bastaban. [UIA](https://www.uia.org.ar/prensa/4226/) · [El País](https://elpais.com/argentina/2026-03-05/los-grandes-empresarios-de-argentina-alertan-sobre-la-critica-situacion-de-la-industria-y-le-reclaman-respeto-a-milei.html). |
| 5 | Conflictividad social nacional (ACLED) | **−24,0% = 1.979/2.605**, ago-2025/jul-2026 vs 2023 | **Compatible** | Alta | La edición autenticada ya auditada reproduce numerador y denominador. ACLED confirma universo `Protests`+`Riots` y cobertura nacional, pero no hay otra fuente que replique ese agregado exacto. [Perfil Argentina de ACLED](https://acleddata.com/country/argentina) · [codebook](https://acleddata.com/sites/default/files/wp-content-archive/uploads/dlm_uploads/2024/10/ACLED-Codebook-2024-7-Oct.-2024.pdf). |
| 6 | Jornadas individuales no trabajadas | **4.760.195**, 12 meses hasta mayo de 2026 | **Compatible** | Alta | La planilla oficial permite reproducir la suma móvil. El control externo publica 4,493 millones para el año calendario 2025, magnitud coherente al reemplazar meses por enero–mayo de 2026. [Secretaría de Trabajo](https://www.argentina.gob.ar/trabajo/estadisticas/conflictos-laborales-0) · [Infobae](https://www.infobae.com/politica/2026/02/22/conflictividad-laboral-la-cantidad-de-paros-que-hubo-en-2025-fue-la-mas-baja-en-las-ultimas-dos-decadas/). |
| 7 | Transferencias federales reales (IAF) | **+1,6% real**, 2025 vs 2024 | **Confirmado** | Alta | La ficha y la fórmula ya expresan `Σ(T_m/IPC_m)` para cada año. El control externo publica $60,28 billones y +1,6% real, coincidencia exacta. [Ámbito](https://www.ambito.com/economia/transferencias-provincias-reportan-recuperacion-2025-respaldada-giros-no-automaticos-n6238149) · [OPC](https://opc.gob.ar/provincias/informe-trimestral-de-transferencias-a-gobiernos-provinciales-y-municipales-datos-a-diciembre-2025/). |
| 8 | Eficacia legislativa del Ejecutivo | **15,4% = 2/13**, cohorte madura | **Confirmado** | Alta | El inventario de trece expedientes PEN/JGM y sus dos leyes se mantiene reproducible contra los datasets oficiales de [proyectos](https://datos.hcdn.gob.ar/dataset/proyectos-parlamentarios) y [leyes sancionadas](https://datos.hcdn.gob.ar/dataset/leyes-sancionadas). Fórmula, período, score y peso no cambiaron. |
| 9 | Sesiones de Diputados sin quórum | **10,0% = 1/10**, últimos 12 meses | **Confirmado** | Alta | La [página oficial de sesiones](https://www.hcdn.gob.ar/sesiones/) y [Videos Abiertos](https://videos.hcdn.gob.ar/categorias?t=10) muestran una sola reunión en minoría, el 23-06-2026. Persiste el metadato 21/23 de junio en una API, sin efecto sobre 1/10. |
| 10 | Adhesión provincial al RIGI | **66,7% = 16/24** | **Confirmado** | Alta | La tabla oficial mantiene 16 jurisdicciones y sus leyes; universo explícito: 23 provincias+CABA. [MAGyP](https://www.magyp.gob.ar/desarrollo-foresto-industrial/provincias-adheridas.php). |
| 11 | Cohesión del bloque LLA | **99,8%**, Rice bicameral 65/35, 90 días | **Compatible** | Media-alta | Las votaciones recientes corroboran disciplina completa de los 21 senadores LLA, pero ninguna fuente externa publica la réplica de las 34 actas ni la ponderación CIGOB. [Data CP, acta 2800](https://www.datacp.ar/congreso/votacion/senadores/2800) · [La Nación](https://www.lanacion.com.ar/politica/uno-por-uno-como-votaron-los-senadores-la-ley-de-propiedad-privada-nid07082026/). |
| 12 | Bloqueo sostenido | **33,3% = 1/3**, 12 meses | **Confirmado** | Alta | Universidad y emergencia pediátrica completaron la insistencia; ATN no completó ambas cámaras. El universo sigue siendo tres y la fórmula distingue desafío de caída. [Chequeado](https://chequeado.com/el-explicador/leyes-aprobadas-vetos-e-insistencias-en-que-estado-esta-cada-uno-de-los-proyectos-de-la-oposicion-en-el-congreso/) · [La Nación](https://www.lanacion.com.ar/politica/el-senado-busca-imponer-el-financiamiento-a-las-universidades-y-hospitales-pediatricos-nid02102025/). |
| 13 | Desafíos legislativos | **3 normas**, 12 meses | **Confirmado** | Alta | Son las mismas tres primeras insistencias del universo anterior; los eventos y la ventana cierran. [Chequeado](https://chequeado.com/el-explicador/leyes-aprobadas-vetos-e-insistencias-en-que-estado-esta-cada-uno-de-los-proyectos-de-la-oposicion-en-el-congreso/) · [El País, veto ATN](https://elpais.com/argentina/2025-09-12/milei-veta-una-ley-de-financiamiento-provincial-y-escala-en-su-guerra-con-los-gobernadores.html). |
| 14 | Producción legislativa | **25 leyes**, últimos 12 meses | **Confirmado** | Alta | El recurso oficial de [leyes sancionadas](https://datos.hcdn.gob.ar/dataset/leyes-sancionadas), filtrado por fecha de sanción definitiva, devuelve 25 en la ventana. La ficha y la unidad no lo confunden con publicaciones del Boletín Oficial. |
| 15 | Judicialización de la agenda | **Suspendido**; último 1,57% archivado | **Confirmado** | Alta | Está fuera de cards, score y dimensiones; el crudo lo marca `en_indice:false`, sin campos de scoring, y declara por qué la búsqueda SAIJ no identifica causas contra el Ejecutivo. Su página/ficha queda sólo como archivo histórico. [Buscador SAIJ](https://www.saij.gob.ar/busqueda?o=0&p=1&f=Jurisdicci%C3%B3n&r=%28texto%3A%22medida%20cautelar%22%20AND%20fecha-rango%3A%5B20260101%20TO%2020261231%5D%29). |
| 16 | Velocidad de resolución de la Corte | **45,4% = 26.524/58.424**, año 2025 | **Confirmado** | Alta | El Anuario definitivo de la CSJN publica exactamente ambos universos; 26.524/58.424=45,40%. [CSJN](https://w3.csjn.gov.ar/novedades/detalle/13002). |
| 17 | Actividad de comisiones de control | Publica **7 sesiones**, 12 meses a agosto de 2026 | **Discrepante** | Alta | El regex sólo acepta `sesiono-la-comision-de-(acusacion|disciplina)-N`. Omite reuniones que la fuente oficial describe como sesiones ordinarias cuando la nota tiene otro título. Dentro de la ventana calendario correcta —septiembre de 2025 a agosto de 2026— las sesiones sustantivas del 17-03 y 28-05 llevan el mínimo a **9**. El archivo oficial contiene además cinco eventos de comisión en notas combinadas; si la pregunta publicada es literalmente cuántas veces sesionaron, el inventario completo llega a **14**. La reunión del 06-08-2025 también demuestra el defecto del extractor, pero queda fuera de esa ventana exacta. [Archivo de Acusación](https://consejomagistratura.gov.ar/index.php/category/comision-de-acusacion/) · [Archivo de Disciplina](https://consejomagistratura.gov.ar/index.php/category/comision-de-disciplina/) · [sesión ordinaria del 28-05](https://consejomagistratura.gov.ar/index.php/2026/05/28/la-comision-de-acusacion-propone-al-plenario-iniciar-el-proceso-de-remocion-del-juez-salmain/). |
| 18 | Cobertura de cargos judiciales | **69,63% = 665/955**, corte operativo agosto de 2026 | **Confirmado** | Alta | La card, el detalle y la ficha ya concilian padrón base, designaciones y renuncias; no reaparece “604/955” como explicación vigente. Los 74 pliegos del Senado no se suman ciegamente porque incluyen otros cargos y fechas. [Dataset oficial](https://datos.jus.gob.ar/dataset/magistrados-justicia-federal-y-de-la-justicia-nacional) · [control de nombramientos](https://www.infobae.com/politica/2026/06/12/oficializaron-los-nombramientos-de-emilio-rosatti-y-otros-dos-jueces-tras-la-aprobacion-de-los-pliegos-en-el-senado/). |
| 19 | Alineamiento de senadores no-LLA por provincia | **57,0%**, 90 días al 06-08-2026 | **Compatible** | Media-alta | La última votación muestra apoyo mixto de PRO, UCR y fuerzas provinciales y rechazo justicialista, coherente con una media apenas mayoritaria. No hay réplica externa del promedio provincial de todas las actas. [Data CP](https://www.datacp.ar/congreso/votacion/senadores/2800) · [La Nación](https://www.lanacion.com.ar/politica/uno-por-uno-como-votaron-los-senadores-la-ley-de-propiedad-privada-nid07082026/). |

## Discrepancia nueva: el regex cuenta títulos, no sesiones

El código vigente usa:

```python
_RE_SESION = re.compile(
    r"sesion[oó]?-?(?:la|las)?-?comisi[oó]n-de-(acusacion|disciplina)-(\d+)"
)
```

El sufijo numérico está en el *slug* de WordPress. La auditoría anterior lo
interpretó como número oficial de sesión y tomó la secuencia 12→15 de Acusación
y 8→10 de Disciplina como prueba de cobertura. La página oficial no presenta
esos números en el título ni en el cuerpo: el sufijo funciona como
desambiguación de URLs con títulos repetidos. Cuando una sesión genera una
noticia de resultado, el título cambia y deja de cumplir el regex.

La contradicción se puede demostrar sin criterio externo nuevo. El archivo
`data/politica/denuncias_comisiones_universo.json` permite contrastar estas
“acciones concretas” alrededor de la ventana:

| Fecha | Comisión | Qué dice la fuente |
|---|---|---|
| 06-08-2025 | Acusación | “En su reunión del día de hoy…”; propone abrir un proceso de remoción |
| 17-03-2026 | Acusación | “celebró … una nueva sesión ordinaria”; propone acusar a dos jueces |
| 28-05-2026 | Acusación | “celebró … su sesión ordinaria”; propone iniciar otra remoción |

El store afirma que esas notas “no sólo sesionan sino que resuelven” y las
separa por ser un fenómeno distinto. Para un indicador que se presenta como
**cantidad de sesiones**, resolver durante la reunión no hace que deje de ser
sesión. La exclusión subestima precisamente la actividad sustantiva que la
definición dice observar.

El archivo vivo agrega cinco reuniones de comisión dentro de la ventana en notas
conjuntas o combinadas: Acusación 12-11-2025 y 22-04-2026; Disciplina
19-11-2025, 26-11-2025 y 13-05-2026. La del 13-08-2025 confirma la misma clase
de omisión, pero queda fuera del corte calendario. El producto puede excluirlas, pero entonces
debe renombrar el indicador y explicar que mide sólo una subclase editorial de
notas; hoy promete “cuántas veces sesionaron”.

La corrección mínima es contar las dos reuniones sustantivas dentro de la
ventana: **9**, no 7. La corrección completa de acuerdo con el título y la
definición publicados es **14**. En ambos casos el efecto paramétrico es el
mismo:

| Escenario | Puntaje del componente | Poder judicial | ITCP | Tensión Política |
|---|---:|---:|---:|---:|
| Publicado: 7 | 45,0 | 60,7 | 70,9 | 2,9 |
| Mínimo conciliado: 9 | 10,0 | 52,0 | 69,6 | 3,0 |
| Inventario completo: 14 | 10,0 | 52,0 | 69,6 | 3,0 |

## Verificación de las cuatro correcciones anteriores

### DNU

- `formulas.ts`: publicados/publicadas, misma convención de fecha;
- `fichas.ts` y `output/fichas/fichas-politica.md`: tipo jurídico, paginado e
  inventario, sin describir el método textual reemplazado;
- snapshot e informe: unidad `DNUs publicados por ley publicada`, 37/25;
- serie reconstruida bajo el mismo filtro.

**Resultado:** corregido de punta a punta.

### IAF

- `formulas.ts`: cociente de dos sumas de flujos mensuales deflactados;
- ficha: jurisdicciones incluidas/excluidas, año completo, IPC nacional por mes
  y base común;
- snapshot: +1,6%, +43,1% nominal y deflactor efectivo +40,8%;
- contraste externo: +1,6% real.

**Resultado:** corregido de punta a punta.

### Apoyo empresario y judicialización

- no están entre las 17 tarjetas ni en las dimensiones del ITCP;
- `output/informe.json`: `en_indice:false`, bloque `suspendido`, sin
  `peso_efectivo`, `peso`, `aporte_score` ni `puntaje_*`;
- `output/informe.md`: tabla separada, rotulada como archivo que no integra el
  índice;
- las descripciones de dimensión cuentan uno y tres componentes activos;
- las series históricas permanecen en `series.json`/CSV por decisión explícita
  de archivo, pero no generan una card vigente.

**Resultado:** corregidos de punta a punta como suspensiones.

## Fichas Markdown correctas; Word institucional vencido

`output/fichas/fichas-politica.md`, que el pipeline regenera y usa como contrato
actual, coincide con el snapshot: ITCP 70,9, 17 indicadores, DNU 1,48, IAF 1,6,
pesos renormalizados y sin fichas vigentes de los dos suspendidos.

El archivo `output/fichas/Fichas Semaforo Politica.docx` es distinto: el propio
README aclara que los Word son manuales y representan la última versión enviada,
no un espejo nocturno. El verificador encuentra **20 fallas** contra el snapshot,
entre ellas:

- ITCP 65,0 en vez de 70,9;
- DNU 1,92 en vez de 1,48;
- IAF 0,8 en vez de 1,6;
- pesos anteriores a las suspensiones;
- fichas de más para `apoyo_empresario` y `judicializacion`;
- falta la ficha de jornadas individuales no trabajadas.

No se degradaron por esto las 19 filas: el barrido anterior definió “ficha” como
la capa TypeScript/Markdown vigente y el Word tiene un contrato explícito de
entrega manual. Sí debe regenerarse y pasar el gate antes de volver a circularlo.

## Validación local

Se ejecutaron 19 archivos de pruebas sobre ITCP, colectores políticos, DNU,
IAF, Poder Judicial, bloqueos, cohesión, publicación, topología, suspendidos y
sincronización de fichas Markdown.

**Resultado:** `439 passed in 31.91s`.

El control directo de pesos dio 17 componentes y suma efectiva
`0.9999999999999999`. La discrepancia de sesiones no está cubierta por la suite:
los tests verifican que el parser reproduzca su regex y el store, no que el
regex cubra todas las reuniones que la fuente oficial denomina sesiones.

También se ejecutó `scripts/fichas/verificar.py`: devolvió 61 fallas globales,
20 de ellas en el Word de Política, por las razones documentadas arriba.

## Recomendaciones

1. Redefinir `paralisis_denuncias` sobre eventos reales de sesión, no sobre una
   forma de *slug*. Parsear título+cuerpo y mantener un inventario deduplicado,
   con clasificación explícita de ordinaria, extraordinaria, audiencia y
   reunión conjunta.
2. Decidir si las sesiones combinadas entran. Si la respuesta es no, cambiar el
   nombre, la definición y la limitación para no prometer “cuántas veces
   sesionaron”. En cualquier variante, las tres reuniones sustantivas ya
   reconocidas por el repo no pueden desaparecer del conteo de sesiones.
3. Agregar fixtures de las notas del 06-08-2025, 17-03-2026, 28-05-2026 y una
   sesión combinada; romper el regex debe hacer fallar una prueba de cobertura
   contra inventario, no sólo una prueba sintáctica.
4. Recalcular la serie histórica, el puntaje, Poder judicial y el ITCP después
   de cerrar el universo.
5. Antes de distribuir fichas institucionales, regenerar y verificar el Word de
   Política contra el snapshot vigente.

## Conclusión

La remediación corrigió las cuatro discrepancias conocidas del cinturón y dejó
coherentes score, pesos, fórmulas, fichas web/Markdown y suspensiones. La nueva
verificación baja Política a **una discrepancia activa sobre 17 componentes**:
el conteo de sesiones de control judicial. No es un problema cosmético: cambia
el componente de 45 a 10 puntos, la dimensión judicial de 60,7 a 52,0 y el ITCP
de 70,9 a aproximadamente 69,6.
