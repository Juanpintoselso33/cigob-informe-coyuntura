---
madr: 4
id: '0036'
estado: 'aceptado'
fecha: 2026-07-07
cinturon: 'politica'
archivos: ['scripts/itcp.py', 'scripts/politica.py', 'scripts/parametrica.py', 'scripts/descargar_series.py', 'data/politica/*', 'tests/test_itcp.py']
relacionado: ['0058', '0059']
modificado_por: ['0088']
ambito: '`scripts/itcp.py` (nuevo) · `scripts/politica.py` · `scripts/parametrica.py` · `scripts/descargar_series.py` · `data/politica/*` · `tests/test_itcp.py` · web'
---

# ADR-0036 — ITCP: el cinturón de política se puntúa con la paramétrica de 5 dimensiones (decisión editorial, sin doc CIGOB)

| **Precedente directo** | ADR-0013 (ITCG), ADR-0018 (ITVC), ADR-0021 (interpolación), ADR-0017 (`protestas_caba`/ACLED), ADR-0037 (`cohesion_bloque` — scraping implementado pero bloqueado en producción) |

## Contexto y planteo del problema

El cinturón de política se puntuaba con un **promedio simple** de fórmulas lineales ad
hoc por indicador (`calcular_score()` en `politica.py`), sin ponderación entre
dimensiones ni bandas explícitas — el mismo estado en que estaba gestión antes de
ADR-0013 y vida cotidiana antes de ADR-0018. `docs/archivo/cinturon_politica.md` ya describe
las **cinco dimensiones de Matus** (poder legislativo, alianzas territoriales, cohesión
interna del oficialismo, conflicto social, imagen y voto) pero nunca las pesó: cada
indicador aportaba 1/9 del score final, sin distinguir "capacidad de gobernar" de
"popularidad".

De los 9 indicadores existentes, 2 eran manuales y estaban congelados desde
2026-05-23: `cohesion_bloque` y `gobernadores_alineamiento`. ADR-0037 (mismo día, misma
tanda de trabajo) documenta que `cohesion_bloque` ya tiene scraping propio implementado
y testeado contra `votaciones.hcdn.gob.ar`, pero está bloqueado en producción por
detección anti-bot del sitio — el indicador sigue publicando desde cache hasta que se
resuelva el acceso. Este ADR no depende de que ese bloqueo se resuelva: cubre la
paramétrica que consume `cohesion_bloque` (automatizado o no) junto con 3 indicadores
nuevos.

## Opciones consideradas

- **Compactar `poder_legislativo` en un indicador compuesto** (los 4 indicadores hoy
  planos: `ratio_dnu`, `eficacia_legislativa`, `veto_quorum`, `comisiones_caidas`) —
  a diferencia del Fondo de Cese que ADR-0013 sí compactó en ITCG, acá no hay un
  documento que imponga esa fórmula agregada. Se mantiene desagregado por simplicidad
  y transparencia: cada indicador se lee y audita por separado.
- **Usar composición del Senado por provincia o transferencias de Presupuesto Abierto
  (ATN) como proxy directo de `gobernadores_alineamiento`** — construct-invalid: la
  composición del Senado mide bancas legislativas, no conducta del Poder Ejecutivo
  provincial; Presupuesto Abierto no tiene columna de corte provincial confirmada y el
  organismo correcto para ATN es Interior, no Economía. Ya investigado y descartado
  explícitamente el 2026-07-07, documentado en
  `data/politica/manuales.json._meta.pendiente_automatizacion` para no repetir la
  investigación sin saber que ya se hizo. (La adhesión al RIGI sí se automatiza, pero
  como indicador nuevo y distinto — `adhesion_reformas_provincial` — que mide adhesión
  fiscal puntual, no alineamiento político general.)

## Decisión

Implementar el **ITCP** (0-100, mayor = más capital político / capacidad de gobernar;
tensión = (100−ITCP)/10) con el mismo motor que ITCM/ITCG/ITVC — `scripts/itcp.py`,
espejo estructural exacto de `itcg.py`, delegando el algoritmo (bandas
low-exclusivo/high-inclusivo, renormalización ante faltantes, overrides con
vencimiento) a `scripts/parametrica.py`. Overrides del analista en
`data/politica/ajustes_itcp.json` (nuevo, mismo mecanismo que
`ajustes_itcm/itcg/itvc.json`).

### Pesos de dimensión: sin doc CIGOB de respaldo

A diferencia de ITCM (doc de financiamiento), ITCG ("260702 AJUSTE PARAMETRICA
GESTIÓN") e ITVC (doc de vida cotidiana), **no existe un documento CIGOB que fije estos
pesos**. Es una decisión editorial explícita, apoyada en la lectura ya presente en el
propio proyecto: capital político según Matus es **capacidad de gobernar, NO
popularidad** — por eso "imagen y voto" pesa deliberadamente menos que las otras
cuatro dimensiones, en vez del peso dominante que tendría en un índice de popularidad.

| Dimensión | Peso | Indicadores (peso interno) |
|---|---|---|
| Poder legislativo | 30% | `ratio_dnu` (25%) · `eficacia_legislativa` (30%) · `veto_quorum` (20%) · `comisiones_caidas` (25%) |
| Alianzas territoriales | 25% | `iaf_transferencias` (40%) · `gobernadores_alineamiento` (30%) · `adhesion_reformas_provincial` (30%, nuevo) |
| Cohesión interna del oficialismo | 20% | `cohesion_bloque` (65%) · `cohesion_bloque_senado` (35%, nuevo) |
| Conflicto social | 15% | `movilizacion_cepa` (60%) · `protestas_caba` (40%, nuevo) |
| Imagen y voto | 10% | `votometro_ventaja_lla` (100%) |

Pesos internos: donde el indicador ya traía una fórmula propia (los 9 originales) se
preservó el peso relativo implícito en su rango de variación; donde es indicador nuevo,
es operacionalización propia a falta de doc — mismo criterio que ADR-0013 usó para las
dimensiones D2-D5 de ITCG.

### `cohesion_bloque`: redefinido a índice de Rice

El indicador medía (según su definición manual original) "% de legisladores alineados
con la posición oficial del bloque". Esa posición oficial **no es un dato disponible**:
no hay, por acta, una declaración explícita de cuál es la posición del bloque más allá
de cómo vota la mayoría de sus propios miembros. Se redefine a **índice de Rice**
(estándar en ciencia política) sobre actas de votación divididas:
`|afirmativos_LLA − negativos_LLA| / (afirmativos_LLA + negativos_LLA) × 100`,
ausentes/abstenciones excluidos del denominador, promediado sobre la ventana móvil de
3 meses. El detalle del scraper (`votaciones.hcdn.gob.ar`, sesión persistente, parsing
de tabla nominal, backfill 2023→actual, guard de frescura) y su bloqueo actual en
producción están documentados en ADR-0037; este ADR cubre solo la redefinición
metodológica y su lugar en la paramétrica.

### Indicadores nuevos y su alcance honesto

1. **`cohesion_bloque_senado`** — mismo cálculo (índice de Rice) sobre
   `senado.gob.ar/votaciones`. Es **complementario**, no reemplaza a la medición sobre
   Diputados: reduce la dependencia de una sola cámara para "cohesión interna", pero
   ambas cámaras se ponderan dentro de la misma dimensión (65/35), no se promedian a
   ciegas.
2. **`adhesion_reformas_provincial`** — % de provincias adheridas formalmente al RIGI
   (tabla MAGyP). Se presenta honestamente como **adhesión fiscal a un régimen
   puntual**, no como proxy de alineamiento político general — explícitamente **no
   reemplaza** a `gobernadores_alineamiento`, que sigue manual y sin automatizar (ver
   Opciones descartadas).
3. **`protestas_caba`** — ya automatizado para gestión vía ACLED (ADR-0017), donde
   está excluido de puntuar porque "premiaría menos marchas". En política se reutiliza
   el fetcher existente de `gestion.py` (no se duplica lógica de scraping ACLED) pero
   con una **lectura distinta**: acá mide nivel de conflicto social como condición de
   gobernabilidad, no un juicio sobre la legitimidad de protestar. Es la misma serie,
   dos interpretaciones editorialmente distintas según el cinturón que la consume.

   Hallazgo real durante la integración (Task de wiring en `main()`, no hipotético): la
   tabla de bandas inicial para `protestas_caba` se copió de `movilizacion_cepa`
   asumiendo una escala 0-100, pero `gestion.fetch_protestas_caba()` expone `valor`
   como el **conteo crudo** de eventos ACLED acumulado 12 meses (en la corrida real del
   07-jul, 301 eventos) — una tabla pensada para 0-100 lo habría bandeado mal. Se
   corrigió para puntuar sobre `var_vs_2023` (% de variación de eventos vs. la base
   2023), que sí es comparable a otros indicadores %-variación del índice (p. ej.
   `iaf_transferencias`), con la tabla invertida (menos protesta que en 2023 = mejor):
   `(-∞,-30,100)·(-30,-10,85)·(-10,10,65)·(10,30,40)·(30,∞,10)`.

### Bandas provisionales a recalibrar

Convención uniforme (low exclusivo, high inclusivo), puntajes canónicos 100/85/65/40/10.
Los 9 indicadores originales usan umbrales derivados de la fórmula ad hoc que
reemplazan. Los 4 nuevos/recalibrados — `cohesion_bloque`, `cohesion_bloque_senado`,
`adhesion_reformas_provincial` y `protestas_caba` — son **anclas propias sin historia
todavía** y quedan marcadas como PROVISIONAL en `itcp.BANDAS_ITCP`, a revisar cuando el
backfill esté corriendo con más recorrido (mismo caveat que ADR-0013 dejó documentado
para las anclas nuevas de ITCG).

### `gobernadores_alineamiento` sigue manual

No se automatiza en este ADR. Sigue con su valor manual (`data/politica/manuales.json`)
y su camino de automatización pendiente documentado en
`_meta.pendiente_automatizacion.gobernadores_alineamiento`, con los 4 proxies ya
investigados y descartados (ver Opciones descartadas) para que no se re-evalúen sin
saber que ya se probaron.

### Consecuencias

- El ITCP en la corrida real del 07-jul puntúa **64,7 → banda "moderadamente
  aflojado"**, tensión (100−64,7)/10 = **3,5** — cambio de metodología respecto del
  score de promedio simple que este ADR reemplaza (documentado en el spec de diseño
  como 4,6/10 bajo la fórmula anterior), mismo tipo de salto que tuvo ITCG al adoptar
  su paramétrica (5,9 → 68,5). No es un error de cálculo: es el efecto esperable de
  pasar de "todo pesa igual" a pesos deliberados.
- Lectura por dimensión de esa misma corrida: **poder legislativo 36,8 — el cuello de
  botella** (`eficacia_legislativa` y `comisiones_caidas` ambos en la banda mínima,
  10/100, mientras `veto_quorum` está en 100/100: el Ejecutivo no pierde quórum, pero
  buena parte de su agenda no avanza ni sale de comisión); alianzas territoriales 86,4;
  cohesión interna del oficialismo 86,3; conflicto social 48,2; imagen y voto 75,6.
- Indicadores del índice: 9 → **12** (3 nuevos: `cohesion_bloque_senado`,
  `adhesion_reformas_provincial`, `protestas_caba`). `gobernadores_alineamiento` sigue
  siendo el único indicador puramente manual sin camino de automatización viable
  identificado; `cohesion_bloque` tiene automatización lista pero bloqueada en
  producción (ADR-0037) y publica desde cache mientras tanto.
- `parametrica.py` pasa a ser el motor común de ITCM, ITCG, ITVC e **ITCP**: una sola
  implementación de bandas/renormalización/overrides, pineada ahora también por
  `tests/test_itcp.py` (bordes de banda, renormalización ante faltantes, overrides con
  vencimiento, más el caso propio de `protestas_caba` puntuando sobre `var_vs_2023`).
- **Riesgos / pendiente**: las 4 bandas provisionales no tienen historia propia
  todavía — revisar cuando el backfill acumule más recorrido. La dimensión "cohesión
  interna del oficialismo" depende hoy de un indicador (`cohesion_bloque`) que publica
  desde cache indefinidamente hasta que se resuelva el bloqueo anti-bot de HCDN
  (ADR-0037); si esa resolución tarda, el 65% de esa dimensión queda congelado en el
  último valor conocido. `docs/archivo/cinturon_politica.md` y las fichas metodológicas web de
  los 3 indicadores nuevos (mismo tratamiento que `cinturon_gestion.md` recibió en
  ADR-0013) quedan como trabajo posterior, fuera del alcance de este ADR.
