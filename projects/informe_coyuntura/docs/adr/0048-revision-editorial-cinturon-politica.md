---
madr: 4
id: '0048'
estado: 'aceptado'
fecha: 2026-07-10
cinturon: 'politica'
archivos: ['scripts/itcp.py', 'scripts/politica.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/publicar.py', 'scripts/gate_calidad.py', 'web/src/lib/*', 'tests/*']
relacionado: ['0064']
ambito: '`scripts/itcp.py` · `scripts/politica.py` · `scripts/descargar_series.py` · `scripts/validacion_externa.py` · `scripts/publicar.py` · `scripts/gate_calidad.py` · `web/src/lib/*` · `tests/*`'
---

# ADR-0048 — Revisión editorial del cinturón política: rotación y protestas a contexto, cohesión fusionada en un compuesto bicameral

| **Precedente directo** | ADR-0036 (paramétrica ITCP), ADR-0046 (`derrotas_legislativas`), ADR-0047 (`rotacion_gabinete`), ADR-0039/0041/0042 (series y bandas de cohesión por cámara) |
| **Fuente** | Documento de revisión CIGOB "260710 REVISIÓN CINTURÓN POLITICA.docx" |

## Contexto y planteo del problema

El 2026-07-10 el revisor de CIGOB entregó la primera revisión editorial del
cinturón política ya implementado. Redefine el alcance del índice: *"mide la
capacidad del gobierno de gestionar y avanzar con las leyes que son relevantes
para cumplir sus promesas en el plan de gobierno"* — un encuadre parlamentario,
más acotado que las 5 dimensiones matusianas de capital político con las que se
construyó el ITCP (ADR-0036).

La revisión valida explícitamente 6 indicadores existentes (eficacia
parlamentaria, sesiones caídas, comisiones sin sanción, adhesión al RIGI,
derrotas legislativas, alineamiento de senadores por provincia) y pide tres
cambios concretos:

1. **`rotacion_gabinete`**: "no sería pertinente en este cinturón". Había
   entrado al índice el día anterior (ADR-0047).
2. **`protestas_caba`**: "no sería pertinente en este cinturón".
3. **Cohesión del bloque LLA (Diputados y Senado)**: "haría uno solo
   compuesto".

No menciona 4 indicadores que sí puntúan (`votometro_ventaja_lla`,
`ratio_dnu`, `movilizacion_cepa`, `iaf_transferencias`). Consultado, el editor
confirmó que la lista **no es exhaustiva** — los no mencionados se mantienen.
Esta es la **lectura mínima** de la revisión: solo se implementa lo explícito.

## Opciones consideradas

- **Lectura amplia de la revisión** (volar también conflicto social e
  imagen/voto, que no encajan en el encuadre parlamentario del revisor):
  descartada por confirmación del editor — su lista no era exhaustiva; los 4
  indicadores no mencionados se mantienen.
- **Borrar los colectores/series de rotación y protestas**: descartado — la
  revisión dice "no pertinente EN ESTE CINTURÓN", no "no medirlo". El costo
  de mantenerlos es cero (protestas ya corre para gestión; rotación es un
  registro curado) y la card de contexto conserva la lectura complementaria.
- **Clave nueva para el compuesto** (`cohesion_bloque_lla`): descartado — el
  precedente de ADR-0036 ya redefinió `cohesion_bloque` conservando la clave
  (manual→Rice), el guard `_es_cohesion_legado` cubre la migración de cache,
  y la clave nueva duplicaba churn en labels/fichas/series sin ganancia. La
  serie del CSV se regenera completa con la fórmula compuesta, así que
  card↔serie quedan consistentes (G3).
- **Promediar las dos cámaras 50/50 dentro del compuesto**: descartado — el
  65/35 preserva la ponderación relativa vigente y aprobada; un 50/50 habría
  sido un cambio de pesos encubierto además de la fusión.

## Decisión

### 1. `rotacion_gabinete` y `protestas_caba` salen del índice Y del tablero

Salen de `DIMENSIONES_ITCP`; se declaran en `itcp.INDICADORES_CONTEXTO` y
`publicar.py` los OCULTA del snapshot (`POLITICA_OCULTOS`) — el mismo
criterio de ADR-0022 para los monetarios nominales de macro: **el tablero
solo muestra lo que integra las dimensiones** (regla confirmada por el
editor el mismo 10-jul, al ver la primera versión que los publicaba como
cards de contexto visibles, estilo gestión). **No se borra nada**: el
colector de rotación, su registro curado (`gabinete_salidas.json`), el
detector InfoLeg, los caches y las series siguen corriendo como seguimiento
interno — el trabajo de ADR-0047 queda disponible para reincorporarse si
una revisión futura lo pide. La card de protestas en GESTIÓN (donde siempre
fue contexto visible) no cambia. Las bandas de ambos quedan en `BANDAS_ITCP`
como referencia histórica (precedente: `gobernadores_alineamiento`); la
ficha metodológica de rotación se retira de /metodologia (los ocultos no
tienen ficha — precedente badlar).

### 2. Cohesión fusionada: compuesto bicameral bajo la clave `cohesion_bloque`

- **Fórmula**: `0,65 × Rice_Diputados + 0,35 × Rice_Senado` — el mismo ratio
  interno 65/35 ≈ 45/25 que las dos cámaras ya tenían como indicadores
  separados (ADR-0036/0047). Si una cámara no tiene dato, renormaliza sobre
  la otra (mismo criterio que la paramétrica ante faltantes).
- **Card única** con `componentes` por cámara (patrón Fondo de Cese, ADR-0013):
  cada cámara conserva su valor, n_actas, fecha y estado de frescura visibles
  en el detalle. Los componentes son además la fuente del carry-forward por
  cámara de la corrida siguiente (`_anterior_camara` migra también desde el
  cache pre-compuesto con las dos cards separadas).
- **Frescura**: el compuesto cuenta como fresco solo si las corridas de AMBAS
  cámaras llegaron a su sitio; `desactualizado` solo si TODAS las cámaras que
  aportan están desactualizadas.
- **Serie**: `fetch_cohesion_bloque_compuesta_mensual` (65/35 renormalizado
  mes a mes sobre las dos series por cámara ya cacheadas por acta). La serie
  de `cohesion_bloque_senado` se purga del CSV (la clave deja de existir como
  indicador); las series por cámara siguen siendo insumos internos.
- **Banda recalibrada contra la serie compuesta** (31 puntos, dic-2023→jun-2026,
  rango 90,3–100,0, media 97,6): anclas **99,9/99,0/97,0/95,0**, distribución
  8/4/9/7/3 por banda — las cinco con datos reales. Las anclas del indicador
  anterior (99,9/99/98/97, ADR-0042) estaban calibradas para Diputados sola;
  el Senado (bloque chico) le mete al compuesto un rango 3 veces más ancho.
- `cohesion_bloque_senado` deja de ser card/indicador; su banda queda como
  referencia histórica y sus labels web se marcan "(fusionado)".

### 3. Dimensiones resultantes (pesos ENTRE dimensiones sin tocar, ADR-0036)

| Dimensión | Peso | Indicadores |
|---|---|---|
| Poder legislativo | 30% | `ratio_dnu` 20 · `eficacia_legislativa` 25 · `veto_quorum` 15 · `comisiones_caidas` 20 · `derrotas_legislativas` 20 |
| Alianzas territoriales | 25% | `iaf_transferencias` 40 · `alineamiento_senadores_prov` 30 · `adhesion_reformas_provincial` 30 |
| Cohesión interna | 20% | `cohesion_bloque` (compuesto bicameral) 100 |
| Conflicto social | 15% | `movilizacion_cepa` 100 |
| Imagen y voto | 10% | `votometro_ventaja_lla` 100 |

**11 indicadores puntúan; 2 quedan como seguimiento interno no publicado**
(antes: 14 puntuaban y se publicaban).

### Consecuencias

- **El ITCP sube**: salen del scoring dos indicadores que puntuaban 10/100
  (rotación en crisis abierta con 7 salidas 12m; protestas +25,4% vs 2023) y
  la dimensión cohesión ya no carga el 30% de rotación. Con los valores del
  10-jul: compuesto de cohesión 99,7 → la dimensión pasa de 73,0 a 93,3; el
  índice de 65,5 a **72,9** (tensión 3,5 → **2,7**). Es el efecto esperable
  de la decisión editorial, no un error — misma clase de salto que
  documentaron ADR-0013 y ADR-0036 al cambiar composición.
- La reconstrucción histórica de `validacion_externa.py` cambia de
  composición (11 series, compuesto incluido) → la correlación ITCP↔EPU se
  recalculó en la misma corrida: r = −0,565 en niveles (n=30; antes −0,618)
  — sigue negativa y válida (lección del 2026-07-09: la validación va DENTRO
  del camino scoped).
- Robustez Monte Carlo con la composición nueva: ITCP 72,9 [70,5–75,8],
  tensión 2,7 [2,4–3,0]; el componente dominante pasa a ser el compuesto de
  cohesión (sin él, el índice cae a 67,7).
- `tests/test_publicar.py::test_politica_itcp_reconcilia` pinea la nueva
  composición (11 en índice; rotación, protestas y senado AUSENTES del
  snapshot, como los ocultos de macro; componentes en el compuesto);
  `test_itcp.py` pinea banda compuesta, dimensiones y contexto;
  `test_politica_cohesion.py` cubre `componer_cohesion_bloque`,
  `_anterior_camara` (incluida la migración del cache viejo) y
  `_entrada_camara`.
- Sin cachés nuevos: el compuesto reusa los stores por acta existentes —
  nada que agregar al `git add` de `data-pipeline.yml`.
- Pendiente declarado: los 4 indicadores no mencionados por la revisión
  quedan en el índice por confirmación verbal del editor; si una revisión
  futura formaliza el encuadre parlamentario, la lectura amplia (sacar
  conflicto social e imagen/voto) es el siguiente candidato a ADR.
