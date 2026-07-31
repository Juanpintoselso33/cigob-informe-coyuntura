---
madr: 4
id: '0035'
estado: 'aceptado'
nota_estado: 'Aceptado e implementado — Componente A y Componente B, 2026-07-10'
fecha: '2026-07-07 (propuesto) · 2026-07-10 (decidido e implementado, misma sesión)'
cinturon: 'espiritu'
archivos: ['scripts/vida_cotidiana/collectors/trends.py', 'scripts/espiritu_epoca.py', 'scripts/descargar_series.py', 'data/vida/intencion_migratoria_serie.json', 'data/vida/componente_b_migracion.json', 'data-pipeline.yml']
ambito: '`scripts/vida_cotidiana/collectors/trends.py` (fetch compartido Componente A) · `scripts/espiritu_epoca.py` · `scripts/descargar_series.py` (Componente A y B) · `data/vida/intencion_migratoria_serie.json` · `data/vida/componente_b_migracion.json` (nuevo) · `data-pipeline.yml` · ficha metodológica'
---

# ADR-0035 — Índice de intención migratoria: 4º indicador de espíritu_epoca

## Contexto y planteo del problema

El usuario acercó una guía (`guia_google_trends_indice_emigracion.md`, fuera del repo) para un
"Componente A — Índice de Expectativa de Futuro" del cinturón espíritu de época: mide intención
de emigrar vía Google Trends (términos tipo "emigrar", "ciudadanía italiana/española", "trabajo
en el exterior"), organizados en 5 tandas de hasta 5 términos, con un desglose regional opcional
y una tanda de control filtrada por categoría "Empleo". La guía está escrita como instructivo
manual paso a paso (abrir trends.google.com, descargar CSV, pegar en Excel/pandas cada mes).

Hoy `espiritu_epoca.py` tiene 3 proxies "v1 PROVISIONAL", todos reutilizando datos que el
pipeline ya extrae en otro lado (política de diseño explícita del archivo: "no re-fetchea
nada, evita rate-limits y doble parseo"):
- `icc_utdt` — confianza del consumidor (UTDT), leído de vida_cotidiana.
- `sentimiento_digital` — Google Trends de malestar inmediato ("inflación", "precios",
  "inseguridad", "trabajo"), leído de `vida_cotidiana/collectors/trends.py` (pytrends,
  automatizado, ADR-0034).
- `clima_electoral` — ventaja LLA−PJ del Votómetro, leído de política.

## Factores de decisión

### Análisis (esta conversación)

**No es redundante con `sentimiento_digital`.** Miden constructos distintos: `sentimiento_digital`
es ansiedad económica/seguridad del momento (reactivo al ciclo); intención migratoria es un
indicador de "salida" en el sentido de Hirschman (voz vs. salida) — gente que dejó de creer en
el cambio político/económico del país, un signal más estructural y más severo. Ninguno de los
3 proxies actuales de espíritu_epoca captura esto — llenaría un hueco conceptual real, no un
duplicado.

**Desajuste de nombre/alcance.** "Índice de Expectativa de Futuro" es más amplio que lo que la
guía realmente mide (intención migratoria pura, vía términos de emigración). Si se implementa,
documentar explícitamente el alcance angosto en la ficha pública, o renombrar a algo más preciso
(ej. "índice de intención migratoria").

**El proceso manual de la guía está desalineado con el proyecto — pero es automatizable
directamente.** Google Trends ya está automatizado en este mismo repo vía `pytrends`
(`scripts/vida_cotidiana/collectors/trends.py`) sin necesidad de clicks manuales. El problema de
normalización cruzada entre tandas que la guía resuelve manualmente (término ancla "dólar
blue") ya tiene un precedente arquitectónico mejor en el propio repo: ADR-0034 diseñó
`sentimiento_digital` con "ventana fija + cociente intra-consulta, inmune a la renormalización
de Trends" — evita el problema de fondo en vez de parchearlo con un ancla.

**Riesgo real: multiplicación de exposición a rate-limit.** La guía propone hasta 7 corridas de
Trends por mes (5 tandas de términos + desglose regional + tanda de control "Empleo") — mucho
más que el único batch que ya usa `sentimiento_digital`, que la propia `trends.py` documenta
como frágil ("Rate limits: Google bloquea requests frecuentes. Aceptar fallas silenciosas").
Automatizar esto tal cual multiplicaría ese punto de fragilidad ya conocido.

**Disciplina correcta que la guía sí trae:** nunca reportar el indicador solo — cruzarlo
siempre contra un "Componente B" de datos duros (fuga real de investigadores CONICET, trámites
de ciudadanía/visa reales). Coincide con el patrón ya establecido en el proyecto de no confiar
en un proxy de búsqueda aislado.

## Opciones consideradas

- **Seguir la guía tal cual (proceso manual mensual)**: descartado — contradice ADR-0001 y el
  patrón ya automatizado de Trends en este mismo repo.
- **Espejar el patrón dual exacto de `sentimiento_digital`** (card nightly + serie separada):
  descartado — no resuelve el pedido de evitar llamadas repetidas a Trends para meses ya
  registrados; la fuente única mensual gateada por frescura cumple el mismo rol con menos
  exposición a rate-limit.
- **Sumar Componente B en esta misma iteración**: evaluado inicialmente como fuera de alcance
  (mezclaría dos fuentes de datos totalmente distintas en un mismo cambio) — revertido ese
  mismo día a pedido del usuario; ver "Implementación de Componente B" más abajo.

## Decisión

### Decisión (2026-07-10)

1. **Alcance de tandas**: se implementa el Componente A **completo** de la guía — las 5 tandas
   (intención, ciudadanías, trabajo/visas, destinos, diagnóstico de causa) + desglose regional +
   tanda de control filtrada por categoría "Empleo". Pero de las 5 tandas, **solo la Tanda 1
   (intención expresada) se convierte en proxy puntuable**; las Tandas 2-5 + regional quedan
   como contexto/diagnóstico guardado en el store, sin entrar a `calcular_score()` — evita
   diluir el score con proxies correlacionados entre sí.
2. **Nombre**: `indice_intencion_migratoria` — alcance angosto y preciso, no "expectativa de
   futuro" genérica.
3. **Componente B**: **implementado en esta misma sesión** (2026-07-10), a pedido explícito del
   usuario tras el barrido de fuentes — ver sección "Implementación de Componente B" más abajo
   para el detalle de arquitectura. Investigación previa (mismo día): no hay
   fuente argentina automatizable (CONICET solo publica actas PDF caso por caso sin agregado;
   DNM no desagrega por motivo). Candidatas reales para una iteración futura: **US State
   Department** — visas mensuales a argentinos por categoría (H1B/F1/L1/J1/O1), dato duro,
   mensual, parseable (`travel.state.gov`); **verificado** el mismo día bajando y parseando
   con `openpyxl` el archivo real de septiembre 2025
   (`.../MonthlyNIVIssuances/Excel/FY2025/SEPTEMBER 2025 - NIV Issuances by Nationality and
   Visa Class.xlsx`, estructura `Nationality | Visa Class | Issuances`, una fila por
   combinación): Argentina esa corrida, 31.362 emisiones totales, de las cuales las clases
   relevantes para migración (no turismo) son chicas frente al total dominado por B1/B2 —
   J1 1.664 · L1 48 · H1B 41 · F1 40 · O1 25. Excel disponible desde FY2023 (oct-2022) en
   adelante — cubre de sobra el backfill del proyecto (dic-2023+); antes de FY2023 solo hay
   PDF. **INE (España)** e **ISTAT/AIRE (Italia)** — ciudadanía adquirida por argentinos, dato
   duro pero **anual**, ambas también **verificadas** el mismo día:
   - **INE**: API pública limpia (`servicios.ine.es/wstempus/js/ES/DATOS_TABLA/15800`, sin
     scraping, JSON), serie "Argentina, Total" del cuadro de adquisiciones de nacionalidad
     española de residentes — 2023: 7.208 · 2024: 8.558 · 2025: 11.291 (tendencia creciente).
   - **ISTAT/AIRE**: ZIP/CSV descargable (`demo.istat.it/data/aire/AIRE_it.zip`, sin
     scraping), columna "Acquisizioni di cittadinanza" filtrando `Paese=Argentina,
     Sesso=Totale` — 2022: 25.846 · 2023: 33.130 · 2024: 33.492 (coincide con el comunicado
     de prensa oficial de ISTAT: "in Argentina circa 33mila" en 2023, en su mayoría por
     reconocimiento *iure sanguinis*).
   Barrido ampliado el mismo día a más destinos reales de la emigración argentina, dos
   candidatas más **verificadas**:
   - **Canadá (IRCC)**: CSV público abierto (`ircc.canada.ca/opendata-donneesouvertes/data/
     ODP-PR-Citz.csv`, sin scraping, actualizado **mensualmente** — el único candidato nuevo
     con esa cadencia), residentes permanentes por país de ciudadanía. Argentina, valores
     redondeados a 5 por privacidad (no sirven para sumar exacto, sí para tendencia):
     entre 15 y 60 por mes en el último año (jun-2025 a abr-2026, el dato más reciente
     disponible).
   - **Chile (SERMIG, ex-DEM)**: Excel descargable (`serviciomigraciones.cl/.../RD-Resueltas-
     2o-semestre-2025.xlsx`, sin scraping), microdato con país + año + tipo de resolución —
     residencias definitivas OTORGADAS a argentinos, serie completa 2000-2025: 2023: 1.139 ·
     2024: 928 · 2025 (parcial): 580. Actualización semestral, no mensual.
   - **Uruguay (DNM)** quedó descartado por ahora: solo publica capítulos en PDF (no CSV/Excel),
     más costoso de automatizar de forma confiable que las demás fuentes — candidata débil, no
     verificada en detalle.
   - **Argentina (datos.gob.ar, Dirección Nacional de Migraciones)**: revisado y descartado —
     el dataset mide extranjeros que ENTRAN al país (dirección opuesta a la que buscamos) y
     está desactualizado desde 2020.

   **Segundo barrido (mismo día), pedido específicamente por cadencia** — el usuario marcó
   que anual/semestral es demasiado lento para cruzar contra un indicador mensual de Trends:
   - **US State Department — Immigrant Visa (IV), no solo NIV**: además del NIV ya verificado
     (visas temporales, incluye turismo), el State Dept también publica **mensual** la
     "Monthly Immigrant Visa Issuances by Foreign State of Chargeability" (green cards reales,
     inmigración permanente, no turismo) — **verificado** bajando y parseando el archivo real
     de septiembre 2025 (misma estructura `Country | Visa Class | Issuances`): Argentina, 63
     emisiones ese mes (IR1/IR5 — cónyuges/padres de ciudadano 11+11, F1-F4 reunificación
     familiar, E1-E3 tratado de comercio/inversión, DV lotería de visas). Volumen chico pero
     es la señal MÁS directa de inmigración permanente real que se encontró, y mensual.
   - Se intentó bajar el equivalente español (INE, tabla de flujo de inmigración por país de
     origen, id. 24290) para ver si tenía mejor cadencia que la de nacionalización — la tabla
     resultó impracticable de bajar entera vía API (>30MB, la respuesta se corta) y su
     periodicidad declarada por el propio INE es igual "Semestral" que la de emigración con
     destino al extranjero ya revisada — no hay mejora de cadencia disponible del lado
     español; se descarta seguir por ahí.

   En total, de seis fuentes evaluadas, **cinco quedan verificadas y automatizables sin
   bloqueos** (EEUU —con DOS series mensuales, NIV y IV—, Canadá, España, Italia, Chile) —
   todas API o descarga directa, ninguna requiere unlocker ni scraping de HTML. Cadencias
   mixtas: **mensual** (EEUU ×2, Canadá) vs. **anual/semestral** (España, Italia, Chile,
   confirmado como techo de cadencia real de esas fuentes, no solo falta de búsqueda) — un
   cruce real de Componente B tendría que vivir en `descargar_series.py` como series
   independientes con su propia cadencia cada una, no forzarlas a la mensual del Componente A.
   Se deja como próximo ADR, no se mezcla con el Componente A (fuentes y formatos totalmente
   distintos) en este cambio.
4. **Backfill**: **2021-01**, igual que `sentimiento_digital` (ADR-0034) — consistencia dentro
   del mismo cinturón; evita series de longitud distinta entre los dos indicadores de Trends.
5. **Peso en `calcular_score()`**: **igual** — promedio simple de 4 (sin pesos ad-hoc; el
   cinturón entero sigue siendo v1 provisional sin paramétrica formal).
6. **Arquitectura de fetch — fuente única mensual, gateada por frescura** (decisión de diseño,
   no una de las 5 preguntas originales, pero necesaria para resolver el riesgo de rate-limit
   sin sacrificar alcance): en vez de espejar el patrón dual de `sentimiento_digital` (card
   nightly vía `trends.py` + serie histórica separada vía `descargar_series.py`, dos llamadas a
   Trends independientes), este indicador usa **un solo store mensual**
   (`data/vida/intencion_migratoria_serie.json`) que alimenta tanto la card/score como la serie
   pública. Una función compartida en `trends.py` chequea si el store ya tiene el mes calendario
   actual antes de llamar a pytrends — si sí, no hay llamada de red. Cuando el mes es nuevo,
   corre el batch completo (Tanda 1 + control Empleo + regional, mismo payload; Tandas 2-4 con
   payloads propios, solo último valor sin backfill; Tanda 5 con comparación de tendencia contra
   Tanda 1 → etiqueta `motivo_dominante`). Como el store se reemplaza entero en cada corrida sana
   (nunca mezcla corridas distintas), todos los valores de un momento dado vienen de la MISMA
   consulta — el cociente entre meses es estable (mismo principio de ADR-0034), por lo que se
   puede puntuar directo del último valor del store sin necesitar una card por separado.
   `espiritu_epoca.py` y `descargar_series.py` llaman a la misma función: el que corra primero
   esa noche hace el fetch real si hace falta, el otro reutiliza el store ya fresco.

### Consecuencias

- `INDICADORES_ESPERADOS` de `espiritu_epoca.py` pasa a 4 (`icc_utdt`, `sentimiento_digital`,
  `clima_electoral`, `indice_intencion_migratoria`); `calcular_score()` suma una línea
  `valor / 10` (mismo estilo lineal que `sentimiento_digital`).
- Nuevo store `data/vida/intencion_migratoria_serie.json` — **debe agregarse al `git add` de
  `data-pipeline.yml` en el mismo cambio que lo crea** (precedente: 3 cachés se perdieron por
  este motivo el 2026-07-09).
- Nueva ficha metodológica en `lib/fichas.ts`, registro institucional, con la limitación
  permanente "búsqueda ≠ intención real" y nota de que el Componente B queda pendiente (sin
  referencias a números de ADR en el texto público, mismo estándar que las 55 fichas existentes).
- `SCORING`/`SCORE_EXPLICACION` en `publicar.py`: entrada espejo, rama genérica (sin scoring
  dedicado, igual que hoy).
- Términos de Tanda 1 (puntuable): `emigrar de argentina`, `como irme de argentina`, `quiero
  irme del pais`, `vivir en el exterior`, `trabajo en el exterior`. Tanda 5 (diagnóstico, ya
  dada por la guía): `inflacion argentina`, `inseguridad argentina`, `no hay futuro en
  argentina`. Tandas 2-4 (contexto): ciudadanías, trabajo/visas, destinos — ver implementación
  para el detalle exacto de keywords.

## Más información

### Implementación de Componente B (2026-07-10, misma sesión)

**Qué se guarda y dónde.** Un store nuevo, `data/vida/componente_b_migracion.json`, con las
6 fuentes evaluadas (5 verificadas + reintento fallido de una 6ª), cada una con su cadencia
nativa — sin forzar todo a mensual:

```json
{
  "_meta": {"actualizado": "2026-07-10", "fuentes": {"...": "..."}},
  "eeuu_niv":   {"mensual": {"2023-12": 12345, "...": "..."}},
  "eeuu_iv":    {"mensual": {"2023-12": 58, "...": "..."}},
  "canada_pr":  {"mensual": {"2023-12": 20, "...": "..."}},
  "espana_nacionalidad": {"anual": {"2023": 7208, "2024": 8558, "2025": 11291}},
  "italia_aire":        {"anual": {"2022": 25846, "2023": 33130, "2024": 33492}},
  "chile_residencia":   {"anual": {"2000": 617, "...": "...", "2025": 580}}
}
```

**Por qué NO es un 5º indicador puntuable.** Mismo principio que las Tandas 2-5 del
Componente A: sumar 6 series más a `calcular_score()` diluiría el promedio del cinturón con
proxies de naturaleza completamente distinta (dato duro de otros países vs. búsquedas locales),
sin una paramétrica formal que las pondere. Componente B es **contexto de validación** del
Componente A (nota metodológica de la guía original: "nunca reportarse solo"), no una tensión
propia. Se expone como un campo `contexto_duro` en la card de `indice_intencion_migratoria`
(`espiritu_epoca.py`), con el último valor de cada fuente — visible en el JSON público, sin
entrar al score ni (por ahora) con visualización dedicada en la web — eso queda como posible
fase 2 si se decide mostrarlo.

**Por qué backfill completo en las que se puede.** Canadá (CSV con todo 2015→hoy), España
(API con todo el histórico de la tabla), Italia (ZIP con 2022-2024, todo lo que publica
ISTAT) y Chile (Excel con 2000-2025) entregan su serie completa en una sola descarga — se
guarda todo, no hay motivo para recortar. Los dos de EEUU (NIV e IV) publican un archivo por
mes: se backfillea desde dic-2023 (convención del proyecto) con un loop de descargas, y las
corridas siguientes solo agregan el mes nuevo (append incremental al store, no se re-descargan
meses ya guardados).
