# ITCP — Automatización de `cohesion_bloque` + paramétrica del cinturón política

| | |
|---|---|
| **Fecha** | 2026-07-07 |
| **Ámbito** | `scripts/politica.py` · `scripts/itcp.py` (nuevo) · `scripts/parametrica.py` · `scripts/descargar_series.py` · `data/politica/*` · `tests/` · `docs/adr/` · `docs/cinturon_politica.md` · web |
| **Precedente directo** | ADR-0013 (ITCG), ADR-0018 (ITVC), ADR-0021 (interpolación) |

## Contexto

El cinturón política se puntúa hoy con un promedio simple de fórmulas lineales ad hoc
por indicador (`calcular_score()` en `politica.py`), sin ponderación entre dimensiones
ni bandas explícitas — el mismo estado en que estaba gestión antes de ADR-0013. De los
9 indicadores, 2 son manuales (`cohesion_bloque`, `gobernadores_alineamiento`), congelados
desde 2026-05-23.

Una investigación previa (workflow de 33 agentes, 2026-07-07) encontró que el blocker
documentado de `cohesion_bloque` ("requiere headless browser") es **falso**:
`votaciones.hcdn.gob.ar` es HTML renderizado en servidor, scrapeable con
`requests`+`BeautifulSoup`, sin headless browser — un proyecto de terceros
(`rquiroga7/Como_voto`) ya lo hace a diario. `gobernadores_alineamiento` en cambio sigue
genuinamente sin fuente estructurada: los 4 proxies investigados (Senado, Diputados por
distrito, Presupuesto Abierto, RIGI) miden constructos distintos al que el indicador
declara medir (conducta del Poder Ejecutivo provincial).

Este documento cubre dos sub-proyectos secuenciales: (1) automatizar `cohesion_bloque`
con fuente propia, y (2) construir la paramétrica ITCP que lo consume, espejando
ITCM/ITCG/ITVC, sumando 3 indicadores nuevos y pesando las 5 dimensiones de Matus ya
descriptas en `docs/cinturon_politica.md` (nunca antes pesadas).

## Sub-proyecto 1 — Automatización de `cohesion_bloque`

### Fuente y arquitectura del scraper

Scraping directo a `votaciones.hcdn.gob.ar` (no se depende de `Como_voto`, un repo de
terceros sin licencia formal ni SLA) — decisión tomada explícitamente por el riesgo
reputacional de citar una fuente derivada no oficial como insumo metodológico de un
índice publicado.

Nueva función `fetch_cohesion_bloque()` en `politica.py`, junto a los demás `fetch_*`:

1. **Sesión persistente**: `requests.Session()` + User-Agent estable + `time.sleep(0.3)`
   entre requests — mismo patrón que `_infoleg_session_count` ya usa en este archivo,
   replicando lo que `Como_voto` probó que evita el WAF F5 BIG-IP del sitio.
2. **Descubrimiento de actas**: `POST /votaciones/search {anoSearch: año}` por cada año
   2023→2026 → regex sobre `redirectActa(id, ?, 'slug')` embebidos en el HTML de
   respuesta.
3. **Parsing de acta**: `GET /votacion/{slug}/{id}`, BeautifulSoup(parser='lxml')
   → tabla nominal `(nombre, bloque, provincia, voto)`.
4. **Filtro de bloque**: mapeo propio y acotado `{"la libertad avanza": "LLA",
   "libertad avanza": "LLA"}` — excluye explícitamente aliados ambiguos ("Fuerzas del
   Cielo - Espacio Liberal F.C.E.") que el candidato de terceros normalizaba sin
   distinción.
5. **Filtro de votación "dividida"**: solo actas con al menos un afirmativo y un
   negativo (excluye unanimidades, que no aportan información de cohesión).
6. **Retry/backoff**: hasta 3 reintentos con backoff exponencial ante HTTP 403; agotados
   los reintentos, cae al cache de la serie (mismo patrón que `carne_serie`).

### Metodología: índice de Rice

`cohesion_bloque` pasa a medirse como **índice de Rice** por acta dividida —
`|afirmativos_LLA − negativos_LLA| / (afirmativos_LLA + negativos_LLA)` × 100,
ausentes/abstenciones excluidos del denominador — promediado sobre la ventana móvil de
3 meses. Redefine el indicador de "% alineado con la posición oficial" (que no es
calculable: no hay una posición oficial explícita por votación en los datos) a
"cohesión interna del bloque" — estándar en ciencia política, documentado como ADR
(ver más abajo). El mismo cálculo se reutiliza para el nuevo `cohesion_bloque_senado`.

### Backfill histórico

Itera períodos legislativos 142→144 (dic-2023 en adelante, la convención de backfill
del proyecto) contra `votaciones.hcdn.gob.ar` directamente — el congelamiento en
período 137 era un problema del dataset CKAN viejo, no del sitio de votaciones, que sí
tiene historia completa.

### Guard de frescura (evita confundir receso legislativo con scraper roto)

Se trackean DOS señales independientes en vez de una sola "días desde `fecha_dato`":
- `ultima_corrida_exitosa`: se actualiza cada vez que el scraper completa sin errores
  HTTP (aunque no haya votos nuevos que agregar).
- `fecha_ultimo_voto`: la fecha real del acta más reciente encontrada.

Solo se alerta `desactualizado` si `ultima_corrida_exitosa` supera un umbral (propuesto:
10 días sin una sola corrida exitosa) — nunca por ausencia de votos nuevos, que puede
ser perfectamente normal en receso.

### Validación en CI real

Antes de considerar el indicador "verde" en producción: correr manualmente el workflow
en GitHub Actions (no alcanza con validación local/dev) — el WAF del sitio nunca fue
probado desde un runner real, y este mismo repo ya tuvo el failure mode "200 en local,
403/404 solo desde runners" (CICCRA, commit `2ec13f5`). Es un paso explícito del plan
de implementación, no un supuesto.

### Cambios en `data/politica/manuales.json`

- `cohesion_bloque` se **elimina** del archivo (deja de ser manual) y se agrega a la
  lista de automáticos en `_meta.descripcion`.
- `gobernadores_alineamiento` permanece; se enriquece
  `_meta.pendiente_automatizacion.gobernadores_alineamiento` con los 4 proxies ya
  investigados y descartados (Senado, Diputados por distrito, Presupuesto Abierto,
  RIGI) y la razón de cada descarte, para que no se re-investiguen en el futuro sin
  saber que ya se evaluaron.

## Sub-proyecto 2 — Paramétrica ITCP

### Dimensiones y pesos

Las 5 dimensiones ya están descriptas en `docs/cinturon_politica.md` (nunca se
pesaron). A diferencia de ITCM/ITCG/ITVC, no hay un documento CIGOB que fije estos
pesos — es una decisión editorial explícita, siguiendo la lectura ya presente en el
propio proyecto ("capital político según Matus: capacidad de gobernar, NO
popularidad"):

| Dimensión | Peso | Indicadores |
|---|---|---|
| Poder legislativo | 30% | `ratio_dnu` (25%) · `eficacia_legislativa` (30%) · `veto_quorum` (20%) · `comisiones_caidas` (25%) |
| Alianzas territoriales | 25% | `iaf_transferencias` (40%) · `gobernadores_alineamiento` (30%) · `adhesion_reformas_provincial` (30%, nuevo) |
| Cohesión interna del oficialismo | 20% | `cohesion_bloque` (65%) · `cohesion_bloque_senado` (35%, nuevo) |
| Conflicto social | 15% | `movilizacion_cepa` (60%) · `protestas_caba` (40%, nuevo) |
| Imagen y voto | 10% | `votometro_ventaja_lla` (100%) |

Pesos top-level: los ya acordados en la conversación (30/25/20/15/10), sin ajustes de
redondeo posteriores.

Pesos internos: donde el indicador ya traía una fórmula propia (los 9 actuales) se
preservó el peso relativo implícito en su rango de variación; donde es indicador nuevo,
es operacionalización propia a falta de doc, igual que ADR-0013 hizo para D2-D5 de ITCG.

### Nuevos indicadores

1. **`cohesion_bloque_senado`** — mismo scraper/metodología (índice de Rice) sobre
   `senado.gob.ar/votaciones` (confirmado accesible sin headless, período 144
   presente). Reduce la dependencia de una sola cámara para "cohesión interna".
2. **`adhesion_reformas_provincial`** — % de provincias adheridas formalmente al RIGI
   (tabla MAGyP, confirmada scrapeable, hoy 16/24). Se presenta honestamente como
   adhesión fiscal a un régimen puntual, no como proxy de alineamiento político
   general — no reemplaza a `gobernadores_alineamiento`, que sigue manual.
3. **`protestas_caba`** — ya automatizado para gestión (ACLED, ADR-0017) pero excluido
   de puntuar ahí ("premiaría menos marchas"). En política mide nivel de conflicto
   social como condición de gobernabilidad, no juicio sobre legitimidad de protestar.
   Se **reutiliza el fetcher existente de `gestion.py`** (no se duplica lógica de
   scraping ACLED).

### Tablas de banda

Convención uniforme (low exclusivo, high inclusivo), puntajes canónicos 100/85/65/40/10
para consistencia con ITCM/ITCG. Los umbrales de los 9 indicadores existentes vienen de
los thresholds ya usados en la fórmula ad hoc actual, reconvertidos a escala 0-100
(100 = sin tensión). Los 4 nuevos/recalibrados (`cohesion_bloque`,
`cohesion_bloque_senado`, `adhesion_reformas_provincial`, `protestas_caba`) son
**provisionales** — sin serie histórica propia todavía, a recalibrar cuando el backfill
esté corriendo (mismo caveat que ITCG dejó para sus anclas nuevas en ADR-0013).

```
votometro_ventaja_lla (pp LLA−PJ):      (15,∞,100)·(5,15,85)·(-5,5,65)·(-15,-5,40)·(-∞,-15,10)
ratio_dnu (DNUs/leyes):                 (-∞,0.3,100)·(0.3,0.7,85)·(0.7,1.2,65)·(1.2,2.0,40)·(2.0,∞,10)
movilizacion_cepa (0-100):              (-∞,20,100)·(20,40,85)·(40,60,65)·(60,80,40)·(80,∞,10)
iaf_transferencias (% var real YoY):    (10,∞,100)·(0,10,85)·(-10,0,65)·(-20,-10,40)·(-∞,-20,10)
eficacia_legislativa (%):               (55,∞,100)·(35,55,85)·(15,35,65)·(5,15,40)·(-∞,5,10)
veto_quorum (%):                        (-∞,5,100)·(5,10,85)·(10,20,65)·(20,30,40)·(30,∞,10)
comisiones_caidas (%, 20-30% "normal"): (-∞,30,100)·(30,50,85)·(50,70,65)·(70,85,40)·(85,∞,10)
cohesion_bloque (Rice %) [PROVISIONAL]: (90,∞,100)·(75,90,85)·(60,75,65)·(40,60,40)·(-∞,40,10)
cohesion_bloque_senado [PROVISIONAL]:   mismas bandas que cohesion_bloque (mismo constructo)
gobernadores_alineamiento (%):          (65,∞,100)·(45,65,85)·(25,45,65)·(10,25,40)·(-∞,10,10)
adhesion_reformas_provincial [PROV.]:   (80,∞,100)·(60,80,85)·(40,60,65)·(20,40,40)·(-∞,20,10)
protestas_caba (0-100) [PROVISIONAL]:   (-∞,20,100)·(20,40,85)·(40,60,65)·(60,80,40)·(80,∞,10)
```

Bandas de interpretación del índice agregado (mismas etiquetas que ITCM/ITCG, para leer
los tres índices con la misma vara): `(-∞,20,severamente_apretado)·(20,40,apretado)·
(40,60,moderadamente_apretado)·(60,80,moderadamente_aflojado)·(80,∞,aflojado)`.

Nota esperable: el score publicado va a saltar respecto del actual (4.6/10) al adoptar
la paramétrica — mismo efecto que tuvo ITCG (5.9 → 68.5 en su escala). Es un cambio de
metodología, no un error de cálculo.

### Integración — archivos a tocar

- **`scripts/itcp.py`** (nuevo): `DIMENSIONES_ITCP`, `BANDAS_ITCP`,
  `BANDAS_INTERPRETACION`, `INTERPRETACION_LEGIBLE`, `calcular_itcp()` — espejo
  estructural exacto de `itcg.py`, delega el algoritmo a `parametrica.calcular_indice()`.
- **`scripts/politica.py`**: agrega `fetch_cohesion_bloque`, `fetch_cohesion_bloque_senado`,
  `fetch_adhesion_reformas_provincial`; importa y reutiliza el fetcher ACLED de
  `gestion.py` para `protestas_caba`; reemplaza `calcular_score()` por
  `itcp.calcular_itcp()`; actualiza `INDICADORES_ESPERADOS`.
- **`data/politica/ajustes_itcp.json`** (nuevo, vacío) — mismo mecanismo de overrides
  con vencimiento que `ajustes_itcm/itcg/itvc.json`.
- **`data/politica/manuales.json`** — ver cambios de sub-proyecto 1.
- **`scripts/descargar_series.py`** — backfill de las 4 series nuevas/recalibradas,
  agregado a `POLITICA_DERIVADAS`.
- **`tests/test_itcp.py`** (nuevo, espejo de `test_itcg.py`) — convención de bordes de
  banda, renormalización ante faltantes, overrides con vencimiento — más tests
  unitarios propios: cálculo del índice de Rice contra datos sintéticos, y el guard de
  frescura (última corrida exitosa vs. fecha del último voto).
- **`docs/adr/0035-itcp-parametrica-politica.md`** (nuevo) — documenta pesos de
  dimensión (sin doc CIGOB de respaldo, decisión editorial explícita), la redefinición
  de `cohesion_bloque` a índice de Rice, los 3 indicadores nuevos, y las bandas
  provisionales a revisar.
- **`docs/cinturon_politica.md`** — reescritura completa reflejando la paramétrica
  (mismo tratamiento que `cinturon_gestion.md` recibió en ADR-0013).
- **Web** (`web/src/lib/datos.ts`, `formulas.ts`, `fichas.ts`): el índice se renderiza
  genérico (mismo mecanismo `indiceDe()` que ya soporta ITCM/ITCG/ITVC); se agregan
  fichas metodológicas para los 3 indicadores nuevos y se actualiza la de
  `cohesion_bloque` (nueva metodología Rice), sin números de ADR en el texto público
  (convención ya vigente para las 55 fichas existentes).

## Testing

- `tests/test_itcp.py`: bordes de banda (low exclusivo/high inclusivo), renormalización
  de pesos ante indicadores faltantes (dentro de cada dimensión y entre dimensiones),
  overrides con `vigente_hasta`.
- Test unitario del índice de Rice: dado un set sintético de votos por legislador/bloque,
  verificar el cálculo exacto (incluye caso de unanimidad excluido, caso de
  ausentes/abstenciones excluidos del denominador).
- Test del guard de frescura: simular "corrida exitosa sin votos nuevos" (no debe
  marcar `desactualizado`) vs. "sin corrida exitosa hace 10+ días" (debe marcarlo).

## Riesgos y items provisionales (a revisar post-implementación)

- Bandas de `cohesion_bloque`, `cohesion_bloque_senado`, `adhesion_reformas_provincial`
  y `protestas_caba` son anclas propias sin historia — revisar cuando el backfill esté
  corriendo (mismo patrón que ITCG dejó documentado para sus anclas nuevas).
- El WAF de `votaciones.hcdn.gob.ar` nunca se probó desde un runner real de GitHub
  Actions — validar en la primera corrida real antes de confiar en el indicador.

## Fuera de alcance

- `gobernadores_alineamiento` sigue sin automatizar — ningún proxy investigado mide lo
  que el indicador declara medir. Un proyecto NLP sobre cobertura periodística sigue
  siendo el único camino identificado, y queda fuera de este spec (proyecto separado).
- No se compactan los 4 indicadores de `poder_legislativo` en un compuesto (a
  diferencia del Fondo de Cese en ITCG) — no hay un doc que imponga esa fórmula; se
  mantienen planos por simplicidad y transparencia.
