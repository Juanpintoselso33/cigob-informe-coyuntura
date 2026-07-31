---
madr: 4
id: '0062'
estado: 'superado'
nota_estado: 'Aceptado · complementa ADR-0061'
fecha: 2026-07-15
cinturon: 'politica'
indicadores: [eficacia_legislativa]
complementa: ['0061']
relacionado: ['0050', '0064', '0068', '0069']
superado_por: ['0061']
continuado_por: ['0063']
ambito: 'Cinturón política · ITCP · `eficacia_legislativa` · fuentes HCDN CKAN'
---

# ADR-0062 — eficacia_legislativa: numerador desde leyes-sancionadas (la sanción del Senado era invisible) y denominador sin comunicaciones administrativas

## Contexto y planteo del problema

Tras el rediseño de cohorte madura (ADR-0061), el valor publicado seguía en
0,0% (0/20). Auditoría pedida explícitamente por el usuario ("me sigue
pareciendo bajísimo — revisá qué estamos considerando como proyecto de ley
y como proyecto aprobado"), esta vez registro por registro contra los datos
crudos de HCDN y contra InfoLeg. **El usuario tenía razón: había dos bugs de
datos, independientes de la ventana temporal.**

### Bug 1 — el numerador era ciego a las sanciones del Senado

La aprobación se detectaba buscando movimientos con `q="SANCION"` en el
dataset `movimientos-de-proyectos` de HCDN. Ese dataset **solo registra la
vida del expediente en Diputados**. Para un proyecto con origen en Diputados
(la vía normal de los proyectos del PE), la sanción definitiva ocurre en el
**Senado** como cámara revisora — y en el dataset de movimientos el último
registro es "PASA A SENADO": la palabra "SANCION" no aparece nunca.

Verificación registro por registro de la cohorte vigente (jul-2024→jul-2025)
contra InfoLeg y el dataset oficial `leyes-sancionadas`:

| Proyecto (expediente) | Ley | Sanción definitiva | Cámara | ¿Visible en movimientos? |
|---|---|---|---|---|
| Reforma para el fortalecimiento electoral (0022-PE-2024) | 27.783 | 2025-02-20 | Senado | No |
| Reformas al régimen penal tributario / "Inocencia Fiscal" (0003-PE-2025) | 27.799 | 2025-12-26 | Senado | No |
| Régimen Penal Juvenil (0010-PE-2024) | 27.801 | 2026-02-27 | Senado | No |

Las tres leyes PE de la cohorte, las tres sancionadas por el Senado, las
tres invisibles para la métrica. Los proyectos que SÍ mostraban movimientos
"SANCION" en el dataset eran mayormente de **origen Senado** (donde Diputados
es la revisora y la sanción definitiva sí queda registrada en HCDN) — es
decir, el sesgo no era aleatorio: castigaba sistemáticamente la vía normal
de los proyectos del Ejecutivo.

### Bug 2 — el denominador contaba comunicaciones administrativas

El filtro de "proyecto PE" era solo el patrón `NNNN-PE-AAAA` en el
expediente. Pero ese patrón también lo llevan las **comunicaciones
administrativas** del Ejecutivo (`TIPO: "MENSAJE"` a secas): avisos de
decretos de veto, comunicaciones de resoluciones. En la cohorte vigente, 4
de los 20 registros eran comunicaciones — piezas que jamás pueden
sancionarse y que inflaban el denominador. Los proyectos reales llevan
`TIPO: "MENSAJE Y PROYECTO DE LEY"`.

### Efecto combinado

Cohorte vigente: publicado **0,0% (0/20)** → real **18,8% (3/16)**. Toda la
serie histórica (y los datos con que ADR-0050 recalibró en su momento, y el
backfill de ADR-0061 de hoy) estaban afectados por los mismos dos bugs.

## Opciones consideradas

- Inferir la sanción desde movimientos ("PASA A SENADO" + algo más)
- Cruzar contra InfoLeg en vez del CKAN de HCDN

## Decisión

### 1. Numerador: dataset oficial `leyes-sancionadas` de HCDN

HCDN publica en el mismo portal CKAN el dataset `leyes-sancionadas`
(`68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98`): una fila por ley con
`PROYECTO_ID` (cruzable directo con proyectos-parlamentarios), número de
`LEY`, `SANCION_DEFINITIVA` y `CAMARA_SANCIONADORA` — **cubre las sanciones
de ambas cámaras**. Un proyecto de la cohorte cuenta como aprobado si su
`PROYECTO_ID` aparece ahí (helper `_leyes_sancionadas_ids()` en
`politica.py`). La serie histórica acota además por `SANCION_DEFINITIVA <=
cierre del mes` para seguir siendo reproducible sin reescritura retroactiva;
filas con fecha "NA" quedan fuera de los puntos históricos (timing no
verificable).

### 2. Denominador: solo `TIPO` con "PROYECTO DE LEY"

El filtro de cohorte exige `"PROYECTO DE LEY" in TIPO` además del patrón de
expediente — las comunicaciones (`TIPO: "MENSAJE"`) quedan fuera.

### 3. `_es_media_sancion` se elimina

Con el numerador tomado de un registro que por construcción solo contiene
sanciones definitivas, la heurística de filtrado de medias sanciones por
texto de movimiento (auditoría 2026-07-09) queda sin objeto y se borra junto
con sus tests, reemplazados por tests del cruce con leyes-sancionadas.

### Consecuencias

- `eficacia_legislativa` pasa de 0,0% (0/20) a **18,8% (3/16)** en la
  cohorte vigente → puntaje ITCP ≈57,6 (banda 5-15/15-30 interpolada) en
  vez del piso 10. Las anclas de ADR-0061 (50/30/15/5, benchmark
  Directorio Legislativo) no cambian: ahora la métrica es genuinamente
  comparable contra ellas.
- La serie histórica completa se regenera con las dos correcciones.
- Dos lecciones de método quedan registradas: (a) cuando un valor "parece
  imposible", auditar los registros crudos uno por uno contra una fuente
  independiente — la metodología puede estar bien razonada sobre datos mal
  contados (ADR-0061 arregló la ventana sobre un numerador roto); (b) un
  dataset "movimientos" de UNA cámara nunca puede ser fuente de verdad
  sobre resultados bicamerales.
- `fetch_eficacia_legislativa()` y `fetch_eficacia_serie()` dejan de
  consultar `movimientos-de-proyectos`; consultan `leyes-sancionadas`.

## Pros y contras de las opciones

### Inferir la sanción desde movimientos ("PASA A SENADO" + algo más)

Rechazada. "Pasa a Senado" es media sanción, no ley; el dataset de
movimientos no tiene forma de registrar lo que pasa después en la otra
cámara. Cualquier heurística sobre esa fuente reconstruye mal exactamente
los casos que importan.

### Cruzar contra InfoLeg en vez del CKAN de HCDN

Rechazada. InfoLeg no expone el vínculo ley→expediente de forma
estructurada (habría que parsear texto norma por norma); `leyes-sancionadas`
trae el `PROYECTO_ID` exacto del mismo portal y con la misma sesión de
descarga que ya usamos.

## Más información

### Precedentes directos

ADR-0061 (cohorte madura, mismo día — su métrica hereda este fix) · ADR-0050 (superado por 0061; sus datos también estaban afectados por este bug)

### Pendiente declarado

`comisiones_caidas` usa el mismo `q="SANCION"` sobre movimientos para
detectar "llegó al recinto" (`politica.py::fetch_comisiones_caidas` y su
serie). Su dirección de conteo es distinta (mide dictámenes varados, y la
aprobación en Diputados —que sí es visible— es lo que más pesa ahí), pero
comparte la fuente con el defecto documentado acá. **Queda flaggeado para
auditoría propia** — no se cambia en este ADR para no alterar dos
indicadores en el mismo movimiento sin revisión editorial.

### Anexo — auditoría de profundidad (mismo día, pedida por el usuario)

Tras el fix, el usuario pidió verificar si 18,8% seguía siendo bajo por otro
error. Resultados de la auditoría exhaustiva:

1. **El filtro `q="-PE-"` no pierde nada**: los PROYECTO_ID de las 161 leyes
   PE del dataset leyes-sancionadas están todos en el dump de proyectos con
   ese filtro (0 faltantes).
2. **La ley 27.784 (antimafia, 0009-PE-2024) no es un faltante**: publicada
   el 2024-07-12, tres días antes del inicio de la cohorte vigente
   (2024-07-15) — pertenece a la cohorte anterior.
3. **El dataset de leyes está completo y al día**: 42 sancionadas en 2024,
   17 en 2025 y 14 en 2026 (máxima: 27.813) — coincide con los conteos de
   Chequeado/HCDN.
4. **Destino de los 16 proyectos de la cohorte, uno por uno**: 3 leyes
   (27.783 PASO, 27.799 Inocencia Fiscal, 27.801 Penal Juvenil) · 3 con
   media sanción en el Senado (2 tratados girados en feb-2026 y Ficha
   Limpia, rechazada en el recinto del Senado por un voto — correctamente
   no cuenta como ley) · 10 sin tratamiento (Aerolíneas, Hojarasca —que
   caducó y fue re-enviada en 2026 con expediente nuevo—, reformas penales,
   partidos políticos). El 18,8% es fiel al registro político conocido; si
   los 2 tratados se sancionan, sube a ~31%.

### ¿Bajar la ventana de maduración? — considerada y descartada

Duración real publicación→sanción de las leyes PE (join proyectos ×
leyes-sancionadas): mediana histórica **68 días** (161 leyes, desde 2008) y
**126 días** desde 2016 — el origen del "2-4 meses" del benchmark. Pero bajo
la gestión actual la distribución se corrió dramáticamente: mediana **310
días**, p75 **653**, con la 27.801 en 592 días, la 27.803 en 685 y la
27.805 en 729. Bajar la maduración mínima (p.ej. cohorte de 6-18 meses)
volvería a subcontar: quedarían sistemáticamente afuera las sanciones que
llegan entre los 12 y 24 meses de trámite — la mitad de los éxitos de esta
era. La ventana 12-24 meses queda como está. Limitación simétrica declarada:
un trámite que supere los 24 meses nunca llega a contarse dentro de su
cohorte (hasta ahora solo pasó con proyectos heredados de la gestión
anterior, p.ej. 27.740: 1.358 días).
