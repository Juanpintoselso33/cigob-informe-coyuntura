# 10 — Glosario

Para lectores CIGOB no técnicos y colaboradores nuevos. Términos como se
usan en ESTE proyecto.

## Del sistema

- **Cinturón**: cada una de las cuatro áreas de seguimiento (macro, gestión,
  vida cotidiana, política), del marco Matusiano. Espíritu de época fue la
  quinta hasta ADR-0205.
- **Paramétrica**: índice compuesto con reglas explícitas de agregación
  (pesos, bandas o rebases) — ITCM, ITCG, ITVC, ITCP.
- **Tensión (0-10)**: la escala común de todos los cinturones; mayor = más
  tensión para el gobierno.
- **Snapshot**: la foto congelada (`informe.json` + `series.json`) que la
  web sirve; cada deploy es un snapshot completo.
- **Colector**: script que baja los datos crudos de una fuente y los deja en
  cache. El ensamblador NO refresca — solo une caches.
- **Store (resiliente)**: archivo en `data/` que guarda la última serie sana
  de una fuente frágil; si la fuente se cae, la serie se sirve de ahí.
- **Carry-forward**: si una fuente falla en la corrida, el indicador publica
  su último dato conocido con su fecha (nunca un hueco).
- **Override / ajuste del analista**: corrección manual de un puntaje con
  justificación, publicada como nota en el modal (`ajustes_*.json`).

## Del motor

- **Banda**: rango de valores de un indicador con un puntaje asignado
  (ej. inflación 2-4% mensual → 60 pts).
- **Ancla / interpolación**: en vez de saltos de escalón entre bandas, el
  puntaje se interpola linealmente entre los puntos medios de las bandas
  (ADR-0021).
- **B100 / rebase**: expresar una serie como índice con 100 = su nivel en el
  período base (4T-2023, el arranque del mandato). >100 = mejor que el
  arranque.
- **Base declarada**: cuando la fuente no midió el 4T-2023, se usa otra base
  explícita (ej. IVI: ene-2024) y se dice en la ficha.
- **Renormalización**: si un componente no tiene dato, su peso se reparte
  proporcionalmente entre los presentes (dentro de la dimensión y entre
  dimensiones).
- **Winsorización (asimétrica)**: tope de 140 a los componentes B100 — un
  boom puntual no compra compensación ilimitada. Sin piso: las caídas no se
  recortan (ADR-0033).
- **Dimensión crítica**: dimensión bajo el umbral crítico; se marca en rojo
  y la web avisa que el promedio del índice no la compensa (ADR-0020).
- **Ragged edge**: cuando los insumos de un indicador de familia tienen
  distinto rezago; se titula al último mes COMÚN y el fresco queda como
  provisorio (ADR-0030).
- **Mono-indicador**: dimensión que descansa en un solo indicador (riesgo de
  transmisión directa de errores; decisión abierta D9).

## De la robustez

- **Monte Carlo / p05-p95**: se recalcula el índice miles de veces
  perturbando pesos e insumos al azar; el rango publicado dice cuánto puede
  moverse el índice sin que cambie la historia (ADR-0019).
- **Dominante (leave-one-out)**: el indicador que más arrastra el índice —
  se publica cuánto valdría el índice sin él.
- **Par propio**: el ancla externa de cada índice (ITCM↔riesgo país,
  ITCG↔Merval USD, ITVC↔ICC, ITCP↔EPU Argentina): una serie de
  mercado/encuesta que NO alimenta al índice y debería co-moverse con él.
- **Matriz cruzada (3×3)**: cada índice contra las tres anclas — muestra si
  cada uno mide algo propio o todos miden lo mismo (ADR-0031).
- **Niveles vs primeras diferencias**: correlación de las series tal cual
  vs correlación de sus cambios mensuales. En una muestra con una sola gran
  tendencia, los niveles correlacionan "gratis"; las diferencias son la
  prueba exigente.
- **Lead-lag**: probar si un índice se mueve ANTES que su ancla (anticipa) o
  junto (coincidente). Resultado documentado: los cuatro son coincidentes.
- **Circularidad**: cuando el ancla externa también es componente del índice
  (el ICC pesa 6,75% del ITVC) — por eso la validación se calcula también
  sin-ICC.

## De las fuentes (siglas)

- **RIPTE**: Remuneración Imponible Promedio de los Trabajadores Estables
  (Sec. Trabajo) — el salario formal de referencia.
- **CBT / CBA**: Canasta Básica Total / Alimentaria (INDEC) — líneas de
  pobreza e indigencia.
- **EPH**: Encuesta Permanente de Hogares (INDEC) — informalidad,
  subocupación (trimestral).
- **IPI / ISAC / ICA / EMAE**: índices INDEC de producción industrial,
  construcción, comercio exterior y actividad.
- **ICC / ICG (UTDT)**: Índices de Confianza del Consumidor y en el Gobierno
  (Universidad Di Tella, mensuales).
- **IVI (LICIP-UTDT)**: Índice de Victimización — % de hogares que sufrió un
  delito en 12 meses, denunciado o no (la "cifra negra" incluida).
- **SNIC / SAT**: Sistema Nacional de Información Criminal (anual) y sus
  Sistemas de Alerta Temprana (Min. Seguridad).
- **EMBI / riesgo país**: prima de los bonos soberanos vs Treasuries (JP
  Morgan; vía ArgentinaDatos).
- **CCL**: dólar Contado Con Liquidación — el tipo de cambio financiero
  usado para el Merval en USD.
- **TCRM / ITCRM**: Tipo de Cambio Real Multilateral (BCRA).
- **REM**: Relevamiento de Expectativas de Mercado (BCRA).
- **BADLAR**: tasa de depósitos mayoristas — la tasa pasiva de referencia.
- **TDPS**: Tasa Directa de Prestaciones Sociales — % del gasto social que
  llega sin intermediarios (elaboración propia sobre SIDIF).
- **RIGI**: Régimen de Incentivo para Grandes Inversiones.
- **DP**: Diagnóstico Político (consultora; monitoreo de piquetes).
- **ACLED**: Armed Conflict Location & Event Data — eventos de protesta.
- **pytrends**: cliente no oficial de Google Trends (escala relativa 0-100
  que se renormaliza por consulta — ver ADR-0034).
