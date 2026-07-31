---
madr: 4
id: '0019'
estado: 'parcial'
nota_estado: 'parcialmente aceptada (decisión 1 aceptada e implementada; 2-6 pendientes de decisión del editor)'
fecha: 2026-07-03
cinturon: 'gestion'
relacionado: ['0056', '0071', '0075', '0078']
origen: 'contraste metodológico contra la literatura de índices compuestos, pedido por el editor'
---

# ADR-0019 — Revisión metodológica de las tres paramétricas (ITCM · ITCG · ITVC)

## Contexto y planteo del problema

Las tres paramétricas se contrastaron contra el canon metodológico de índices
compuestos: el **Handbook on Constructing Composite Indicators** (OCDE/JRC
2008, los "10 pasos"), la crítica de **Ravallion** a los *mashup indices*
(World Bank Research Observer, 2011), la reforma del **IDH 2010** (paso de
media aritmética a geométrica por el problema de compensabilidad), el
post-mortem del **Doing Business** (discontinuado en 2021 por manipulación
discrecional no documentada) y la metodología **ICRG** de PRS Group (riesgo
político 0-100 por componentes de peso fijo y puntaje por bandas — el linaje
directo de ITCM/ITCG).

**Lo que la revisión validó** (no requiere cambios):

1. *Dashboard + índice*: la crítica central de Ravallion (el índice oculta
   sus componentes) no aplica — los 57 indicadores se publican individualmente
   con serie, fórmula y aporte; el índice es la capa de lectura. La
   descomponibilidad (paso 10 JRC) es ejemplar.
2. *Gobierno de la discreción*: los overrides del analista
   (`ajustes_*.json`) exigen justificación, tienen vencimiento, se versionan
   en git y se publican en la web. Es el antídoto exacto de lo que mató al
   Doing Business (ajustes de dirección sin registro). Mantener como está.
3. *ITVC*: puntuar niveles acumulados (no tasas mensuales) y resolver la
   polaridad del endeudamiento con la mora observada son correcciones que la
   literatura reclama y casi ningún índice implementa.
4. *Disciplina de datos*: ADR-0001 (cero hardcodeo), backfill completo
   (ADR-0012), reproducibilidad en CI, excepciones documentadas.

**Lo que la revisión encontró** son seis brechas típicas de índices jóvenes,
que se documentan acá como decisiones separadas.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

### Decisión 1 — Análisis de sensibilidad y robustez (ACEPTADA, implementada)

**Problema.** El paso 7 del Handbook JRC ("la radiografía del índice") es
requisito, no opcional: sin él no se sabe cuánto del valor publicado es señal
y cuánto es artefacto de los pesos y umbrales elegidos. Es también la crítica
más repetida de Ravallion (¿qué tan robusto es el ranking a mover los pesos?).

**Decisión.** `scripts/sensibilidad.py` corre tres experimentos por índice y
publica el rango de robustez:

- **Perturbación de pesos** (Monte Carlo, N=2000, semilla fija): cada peso de
  dimensión y de indicador se multiplica por U(0,8; 1,2) y se renormaliza —
  el índice se recalcula desde los puntajes publicados. Responde: ¿cuánto
  depende el número de la ponderación exacta del doc?
- **Incertidumbre de banda** (solo ITCM/ITCG, que puntúan por umbrales): cada
  componente salta a la banda vecina con probabilidad 7,5% hacia cada lado —
  proxy de "el valor está cerca de un umbral". Responde: ¿cuánto pesan los
  acantilados de la discretización?
- **Leave-one-out**: el índice recalculado excluyendo cada indicador (con la
  renormalización estándar). Identifica los componentes dominantes.

Salida: `output/sensibilidad.json` + resumen legible. El rango p05-p95 se
reporta junto al valor puntual ("ITCG 68,5 · robustez 65-72"). Pendiente
operativo: decidir si el rango se publica en la nota metodológica de la web
(recomendado) o queda como control interno.

### Decisión 2 — Compensabilidad entre dimensiones (RESUELTA → ADR-0020, opción b)

**Problema.** Las tres paramétricas agregan con promedio ponderado **lineal**
⇒ sustituibilidad perfecta: un colapso en una dimensión se compensa con
exceso en otra. El IDH abandonó la media aritmética en 2010 exactamente por
esto (pasó a geométrica: "el desarrollo es vivir mucho Y sano Y educado, no
mucho O sano O educado"). Casos vivos: en el ITCG la reforma laboral (10/100)
queda tapada por el componente cambiario (~90); en el ITVC el boom de motos
(175,9) amortigua el colapso crediticio (31,7).

**Opciones.**
- (a) *Status quo documentado*: mantener lineal (más comunicable; el ICRG
  también es lineal) y declarar la sustituibilidad como supuesto del marco.
- (b) *Flag de dimensión crítica* (recomendada): mantener lineal pero
  publicar una alerta visible cuando una dimensión cae bajo un umbral (p.ej.
  puntaje < 30) — señal no compensable en la web, sin tocar la fórmula.
- (c) *Media geométrica* (o mixta): cambia la fórmula de agregación de
  dimensiones; castiga desequilibrios pero rompe la comparabilidad histórica
  y complica la comunicación ("¿por qué bajó si nada empeoró?").

**Recomendación:** (b). Costo bajo, no rompe series, hace visible el problema.

### Decisión 3 — Efectos escalón de las bandas en ITCM/ITCG (RESUELTA → ADR-0021, opción b)

**Problema.** La discretización pierde información y crea acantilados: dos
valores casi iguales a ambos lados de un umbral difieren 15-25 puntos de
componente, y un indicador que oscila alrededor de un umbral hace "parpadear"
el índice sin cambio real. El Handbook critica los umbrales categóricos por
"arbitrariedad del umbral y omisión del nivel absoluto". El ITVC (continuo)
no sufre esto.

**Opciones.**
- (a) *Status quo*: bandas puras, fieles a las tablas del doc CIGOB; el
  ruido de borde queda medido por el experimento de bandas de la Decisión 1.
- (b) *Interpolación lineal dentro de la banda* (recomendada): puntaje
  continuo por tramos usando los umbrales del doc como nodos (piecewise
  linear). Mantiene los anclajes institucionales, elimina los saltos.
  Requiere recalcular el histórico del índice (los valores cambian unos
  puntos) y actualizar los tests pineados.
- (c) *Histéresis*: mantener bandas pero exigir que el valor cruce el umbral
  con un margen (p.ej. 5%) para cambiar de banda. Menos limpio conceptualmente.

**Recomendación:** (b), coordinado con CIGOB porque altera los valores
publicados (es un cambio de método, amerita su propio ADR de ejecución).

**Evidencia medida (2026-07-03, `scripts/interpolacion_sombra.py`).** El
estudio sombra recalcula ambos índices con puntaje continuo (anclaje en el
punto medio de cada banda, lineal entre anclajes, plano en los extremos;
overrides respetados) sobre los valores crudos publicados en el snapshot:

- **ITCM: 51,7 (bandas) → 54,7 (interpolado), Δ +3,0** · tensión 4,8 → 4,5.
- **ITCG: 68,5 → 71,2, Δ +2,7** · tensión 3,1 → 2,9.
- La lectura cualitativa NO cambia (misma banda de interpretación en ambos),
  pero los deltas POR COMPONENTE llegan a ±13 puntos (IdC +13 · TCRM +12,4 ·
  gasto de funcionamiento +13,1 · cepo +12,7 · opción salud −10,2): las
  bandas truncan información real que la interpolación conserva.
- El sesgo agregado de hoy es positivo (+3/+2,7) porque varios indicadores
  están en la mitad ALTA de su banda — con otros datos podría ser negativo:
  es ruido de discretización, no un sesgo estructural.
- Combinado con el hallazgo de la Decisión 1 (las bandas duplican el σ del
  índice), el caso para la interpolación es: misma lectura, menos ruido de
  umbral, sin acantilados mes a mes. Costo: recalcular el histórico y
  actualizar los tests pineados. Detalle completo por indicador en
  `output/interpolacion_sombra.json`.

### Decisión 4 — Doble conteo de la brecha cambiaria en el ITCG (RESUELTA → ADR-0021, opción b)

**Problema.** El Handbook exige tratar la correlación entre componentes.
`cepo_mulc` (brecha CCL/mayorista) es un indicador del ITCG **y** el ILCE de
`apertura_comercial` contiene la misma brecha con peso 40% ⇒ dentro de
reformas económicas la brecha pesa ~1,6 veces su peso nominal. (Versión
estructural en el ITCM: el IPC entra como deflactor de recaudación real, IDM
e IdC — un shock inflacionario mueve tres componentes a la vez; esto es
inherente al diseño y basta declararlo.)

**Opciones.**
- (a) *Declararlo*: nota en ADR-0013 y en la ficha del ILCE ("comparte el
  componente cambiario con cepo_mulc"). Cero código.
- (b) *ILCE sin brecha* (recomendada a mediano plazo): el ILCE queda solo con
  la alícuota efectiva (renormalizado), y la brecha puntúa una sola vez vía
  cepo_mulc. Cambia el valor del componente (~81 → ~68 hoy) — coordinar con
  CIGOB porque el ILCE es fórmula del doc 260702.
- (c) *Repesar dentro de la dimensión* para compensar la correlación:
  opaco, no recomendado.

**Recomendación:** (a) ya, (b) para la próxima revisión del doc con CIGOB.

### Decisión 5 — Concentración del ITVC en un solo dato (PENDIENTE)

**Problema.** La dimensión vulnerabilidad financiera (10% del ITVC) es UN
componente (I_EC), que hoy resta ~7 puntos del índice él solo. Una revisión
metodológica del BCRA en la serie de mora movería el ITVC sin cambio real.
El doc ya prevé el fallback (IV.2.3); el leave-one-out de la Decisión 1
cuantifica la exposición en cada corrida.

**Opciones.**
- (a) *Status quo medido*: aceptar la concentración (es fiel al doc) con el
  LOO publicado como advertencia.
- (b) *Segundo componente en la dimensión* (p.ej. carga financiera de los
  hogares: servicios de deuda/ingreso, si BCRA lo publica): requiere
  investigación de fuente y bendición de CIGOB (cambia pesos internos).

**Recomendación:** (a) ahora; explorar la fuente de (b) sin apuro.

### Decisión 7 — TDPS saturado: indicador de asistencia sin información marginal (PENDIENTE, requiere CIGOB)

**Problema (detectado en la revisión uno-por-uno del 03-jul-2026).** El TDPS
mide el % del devengado pagado directo a personas (partida 5.1.4 / total de
transferencias). Está clavado en 100% desde 2024: al medir el canal de PAGO,
la promesa quedó cumplida casi por diseño tras el Dto. 198/2024 (el pago del
Potenciar ya era mayormente bancarizado; el baseline 2023 era 95-99%). El
indicador está bien MEDIDO (verificado contra el devengado real, ADR-0015)
pero saturado: pesa 4% del ITCG y ya no discrimina nada — información
marginal nula.

**Opciones para discutir con CIGOB:**
a) Dejarlo como está (documenta la promesa cumplida; costo: 4% del índice
   congelado en 100).
b) Reemplazar la métrica por una viva de la misma dimensión: % del padrón
   con contraprestación verificada, o beneficiarios activos vs baseline
   (fuente candidata: Presupuesto Abierto metas físicas / informes SIEMPRO).
c) Reasignar su peso dentro de reforma social y orden (protocolo/salud) y
   dejarlo como contexto "promesa cumplida".

Sin urgencia: no distorsiona (aporta un 100 legítimo), solo desaprovecha peso.

### Decisión 6 — Validación externa (RESUELTA — implementada, resultados favorables)

**Problema.** Paso 9 del JRC: correlacionar el índice con variables externas
relacionadas. (Corrección respecto de la primera redacción de este ADR: el
ICC SÍ integra el ITVC con 7,5% del peso — por eso la validación se hace
contra el **ITVC recalculado sin el ICC**, evitando la circularidad.)

**Implementación (2026-07-03, `scripts/validacion_externa.py`).** Reconstruye
la serie MENSUAL del ITVC desde las series de componentes (31 meses,
dic-2023 → jun-2026; el último punto reproduce exactamente el valor publicado
— validación de toda la cadena de cómputo) y correlaciona contra el ICC de
UTDT (encuesta de percepción, fuente totalmente independiente):

- **Niveles, ITVC sin ICC vs ICC: r = 0,55** (n=30) — co-movimiento claro
  entre condiciones materiales y percepción del consumidor, sin redundancia
  (no miden lo mismo: r ≈ 0,95 habría indicado que el ITVC sobra).
- Primeras diferencias: r = 0,35 — los cambios mes a mes también co-mueven.
- Rezagos ±1 mes: leve ventaja del ITVC adelantado (0,49 vs 0,44) — sugerencia
  (no concluyente con n=30) de que las condiciones materiales preceden al
  ánimo, no al revés.

**Lectura:** validez de constructo razonable para un índice de 3 meses de
diseño. **Publicado en la web** (03-jul-2026): bloque "Validación externa"
en la sección Robustez (cabecera propia + card, misma estructura que el
bloque Monte Carlo), con el gráfico de co-movimiento y las correlaciones;
`publicar._validacion_*` embebe el estudio en el snapshot — correr
`validacion_externa.py` lo actualiza.

> **ACTUALIZADO (30-jul-2026, ADR-0154 y sus enmiendas).** El ancla del ITCM
> **ya no es el riesgo país**: pasó a ser el Índice Líder de la UTDT, y el
> reemplazo es total — el riesgo país no se calcula ni se nombra más en el
> informe. El motivo está medido: acompañaba al índice en niveles (−0,82) pero
> daba **−0,08 en primeras diferencias**, o sea que fuera de la tendencia común
> del período no validaba nada. Lo que sigue vigente de esta sección es el
> DISEÑO —reconstruir el índice mes a mes y contrastarlo contra una variable
> externa que no lo compone— y el criterio que de acá salió. Los números de
> abajo son los de julio de 2026 y se conservan como registro de la decisión.

**Ampliación (03-jul-2026): ITCM ↔ riesgo país.** El estudio reconstruye
también la serie mensual del ITCM (10 de 12 componentes tienen serie; sin
capítulo inversión ni overrides — el nivel difiere del publicado, valida la
EVOLUCIÓN) y la contrasta con el riesgo país (EMBI, promedio mensual,
ArgentinaDatos, serie diaria desde 1999): **r = −0,73 en niveles** (n=30) —
el signo negativo esperado: cuando el ITCM sube (la macro afloja), el
mercado cobra menos por el riesgo argentino. Publicado en la página de
macro con el riesgo país invertido y series normalizadas al rango.
**Ampliación (03-jul-2026, cierre de la trilogía): ITCG.** Reconstrucción
mensual desde las series de 14 de 15 componentes. Dos contrastes:

- **Convergente — ITCG ↔ riesgo país: r = −0,86 en niveles** (n=32), la más
  fuerte de las tres validaciones: el mercado pricea la ejecución acumulada
  de reformas. Publicado en la página de gestión.
- **Discriminante — ITCG ↔ ICG UTDT (confianza en el gobierno): r = −0,60
  en niveles, ≈0 en diferencias.** La hipótesis ingenua era positiva; el
  hallazgo es sustantivo: el ITCG es ACUMULATIVO (la ejecución se suma)
  mientras la confianza sigue el ciclo político (luna de miel → erosión).
  El índice mide gestión, no popularidad — divergir de la popularidad es
  evidencia de validez discriminante, no un defecto. Serie ICG completa
  (2001→hoy, `fetch_icg_serie`, XLS transpuesto de UTDT con Referer
  obligatorio) queda en series.json.

Las TRES paramétricas quedan validadas externamente: ITVC↔ICC +0,52 ·
ITCM↔EMBI −0,73 · ITCG↔EMBI −0,86 (con discriminante ICG documentado).

### Consecuencias

- La Decisión 1 corre desde hoy (`scripts/sensibilidad.py`); el resto queda
  explícitamente ABIERTO para decisión del editor/CIGOB — este ADR es el
  temario de esa conversación.
- Ninguna brecha encontrada invalida los valores publicados: son omisiones
  de control, no errores de cómputo. La familia metodológica (bandas expertas
  tipo ICRG + índice base-100 de seguimiento) tiene precedente sólido.
- Referencias: OECD/EC-JRC (2008) *Handbook on Constructing Composite
  Indicators*; Ravallion (2011) *Mashup Indices of Development*, WBRO 27(1);
  UNDP HDR (2010) nota técnica del IDH; World Bank (2021) statement de
  discontinuación del Doing Business; PRS Group, *ICRG Methodology*.
