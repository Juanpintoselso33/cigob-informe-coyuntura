# Diseño — Capa de semáforo de 4 colores

**Fecha:** 2026-08-08
**Estado:** aprobado para planificación
**Origen:** cuatro documentos CIGOB del 2026-08-05/08 (ver §1)

---

## 1. De dónde sale esto

Cuatro documentos entregados por CIGOB:

| Documento | Qué trae |
|---|---|
| `indicadores y semaforos.docx` | Semáforo de 4 colores para el **cinturón político**: 6 dimensiones, 11 indicadores, umbrales en unidad propia |
| `ITCG_completo_semaforo.docx` | Regla de color para el ITCG: propone `puntaje ≥85 / 55 / 25`, más 3 preguntas abiertas |
| `Fichas SemaforoGestion Bloque 1.docx` | 8 fichas de Gestión con tabla de color en unidad propia |
| `Fichas Semaforo Gestion Bloque2.docx` | 7 fichas de Gestión, ídem, **más anotaciones editoriales a mano** |

### 1.1 Qué se encontró al verificarlos contra el código

Cuatro hallazgos que condicionan el diseño. Los tres primeros salieron de
reproducir la aritmética de los documentos; el cuarto, de leer el snapshot.

**(a) El semáforo de las fichas no es un sistema nuevo: es el puntaje invertido.**
Cada umbral "en unidad propia" de las 15 fichas de Gestión sale de interpolar
hacia atrás las anclas de `BANDAS_ITCG`, con cortes en **puntaje 65 / 45 / 25**.
Verificado exacto en 12 indicadores independientes: apertura `≤5,25 centavos` es
el ancla de 65 · dotación `≤−6%` es el ancla de 65 · desregulación `13.300 art →
65,0`, `7.250 → 45,0`, `3.850 → 25,0` · concesiones `4.095 km = 45% =` ancla de
65. Sin excepciones.

**(b) Los dos documentos se contradicen, y `ITCG_completo` parte de una premisa
falsa.** Ese documento propone cortes 85/55/25 justificados como "el punto medio
entre tus anclas (100/70/40/10)". Las anclas del ITCG **no son** 100/70/40/10:
son **100/85/65/40/10** — cinco niveles, no cuatro. Con esa premisa llega a
colores distintos de los de las propias fichas en 5 de 14 indicadores.

**(c) Los "datos duros que faltan" ya están publicados.** Las fichas piden como
mejora de transparencia datos que `detalle_txt` ya trae en el snapshot: RIGI
*"21 proyectos aprobados (US$ 46.708M) / 22 en evaluación (US$ 101.241M)"* ·
litigiosidad *"128.619 juicios en 12m vs 125.153 previos"* · concesiones *"2.614
de 9.091 km adjudicados"* · apertura *"US$ 984 M sobre US$ 15.916 M"*. Es un
problema de **presentación** en `/metodologia`, no de recolección.

**(d) Los números de las fichas ya envejecieron.** Se escribieron contra la
corrida del 31-jul: ITCG 78,22 (hoy 79,4), RIGI 24,6% (hoy 31,6%). Cualquier
umbral escrito en prosa vuelve a envejecer igual.

---

## 2. Objetivo

Publicar un color de 4 niveles por indicador, por dimensión y por índice, en los
cinco cinturones, **sin tocar ningún puntaje ni ningún peso**, y presentar en la
ficha pública los umbrales que determinan ese color expresados en la unidad real
del indicador (cortes de calle, km, agentes, actos, centavos por dólar).

No-objetivo explícito: el semáforo no cambia el ITCG, el ITCM, el ITCP, el ITVC
ni el score global. Es una capa de lectura.

---

## 3. Decisión central: qué define el color

**El color es la tensión 0-10 que el informe ya publica, en cuatro tramos.**

| Color | Tensión | Índices 0-100 | ITVC base-100 |
|---|---|---|---|
| 🟢 Verde | ≤ 4 | puntaje ≥ 60 | índice ≥ 95 |
| 🟡 Amarillo | ≤ 6 | 40 – 59,9 | 85 – 94,9 |
| 🟠 Naranja | ≤ 8 | 20 – 39,9 | 75 – 84,9 |
| 🔴 Rojo | > 8 | < 20 | < 75 |

No es una escala nueva. Los cortes 60/40/20 son **los bordes de
`BANDAS_INTERPRETACION`**, que el informe ya publica como etiqueta de cada
índice: verde = "moderadamente aflojado" o mejor · amarillo = "moderadamente
apretado" · naranja = "apretado" · rojo = "severamente apretado". La derivación
del ITVC usa su propia fórmula publicada (`tensión = 5 − (índice−100) × 0,2`).
Y coincide con lo que `semaforoDimension()` ya hace hoy con 3 colores (verde
≥60, rojo <40): el cambio es agregar el cuarto tramo, no mover el criterio.

### 3.1 Opciones consideradas y por qué se descartaron

| Opción | Cortes | Por qué no |
|---|---|---|
| A — la de las fichas | 65/45/25 | Es lo que las 15 fichas ya implementan, y esa es toda su ventaja. Su derivación es ad hoc (65 = ancla del medio, 25 = punto medio de las dos peores, 45 = punto medio de esos dos) y no se apoya en nada publicado. No se extiende al ITVC sin inventar una segunda regla. |
| B — la del doc ITCG | 85/55/25 | Su justificación no se sostiene: supone anclas 100/70/40/10 que el ITCG no tiene. |
| **C — tensión publicada** | **60/40/20** | **Elegida.** Un solo criterio para los cinco cinturones, derivado de dos fórmulas que el informe ya publica, y compatible con el semáforo de dimensión que ya existe. |

El costo de descartar A es cero en trabajo: los umbrales en unidad propia se
**calculan**, no se escriben (§4.1), así que la regla vive en una constante.

### 3.2 Efecto honesto

Contra la regla A que usan las fichas entregadas, **6 indicadores cambian de
color** a los valores de hoy, y los 6 mejoran:

| Cinturón | Indicador | Puntaje | A | C |
|---|---|---|---|---|
| macro | recaudación | 43,0 | 🟠 | 🟡 |
| macro | presión de dolarización | 64,5 | 🟡 | 🟢 |
| macro | IAI | 61,0 | 🟡 | 🟢 |
| gestión | RIGI | 63,5 | 🟡 | 🟢 |
| gestión | concesiones viales | 44,6 | 🟠 | 🟡 |
| política | ratio DNU | 22,0 | 🔴 | 🟠 |

Que todos mejoren no es una virtud del criterio: es la consecuencia mecánica de
bajar los tres cortes. Queda escrito para que se pueda discutir; revertir a A es
cambiar tres números en una constante.

### 3.3 Rechazado: histéresis de dos meses

El doc `ITCG_completo` §5 propone exigir dos meses consecutivos del lado nuevo
antes de mover un color, para amortiguar tres indicadores que están al borde de
un corte. Se descarta: obliga a persistir el color de la corrida anterior —
estado nuevo en un pipeline que hoy recalcula todo desde cero en cada corrida —
para un problema que el informe ya resuelve declarando cuáles están al borde. Si
más adelante se quiere, se agrega sobre el color publicado sin tocar el motor.

---

## 4. Arquitectura

Tres capas, cada una con una responsabilidad: el motor calcula, `publicar.py`
publica, la web lee. La web no recalcula ningún color.

### 4.1 Motor — `scripts/parametrica.py`

Dos funciones nuevas y una constante.

```python
CORTES_SEMAFORO = (("verde", 4.0), ("amarillo", 6.0), ("naranja", 8.0), ("rojo", INF))

def color_de_tension(tension: float) -> str: ...
def umbrales_en_unidad(indicador: str, escala: Escala) -> list[dict] | None: ...
```

`color_de_tension` es la única fuente de verdad del corte. Todo lo demás
—puntaje 0-100, índice base-100— llega ahí por la fórmula de tensión que ya
existe (`tension_de_indice`, y la de `base100` para el ITVC).

`umbrales_en_unidad` interpola las anclas **hacia atrás** en los puntajes 60, 40
y 20, y devuelve los tramos **en la unidad cruda del indicador**. Requisitos:

- **Transformaciones.** Si el indicador declara una transformación en
  `Escala.transformaciones`, hay que aplicar la **inversa** para volver a la
  unidad cruda — el mismo camino que ya usa `span_crudo`. Sin esto,
  `rem_ipc_12m` publicaría su umbral en equivalente mensual (1,82%) en vez de
  anual (24,2%), que es lo que muestra la card.
- **No monotonía.** `costo_financiamiento_tesoro` (ITCM) tiene anclas
  `[(−5, 20), (−2,5, 55), (3, 100), (9, 75), (16, 45), (20, 15)]`: óptimo en el
  medio, malo en los dos extremos. Cada corte lo cruza **dos veces**, y el mapa
  de colores real es este:

  | | naranja | amarillo | **verde** | amarillo | naranja | rojo |
  |---|---|---|---|---|---|---|
  | desde | −∞ | −3,57 | **−1,89** | 12,52 | 16,68 | 19,35 |

  Verde es un **intervalo cerrado** (`−1,89` a `12,52`), no un `≥` ni un `≤`; los
  partidos en dos tramos son amarillo y naranja. Del lado izquierdo nunca hay
  rojo: por debajo de −5 el puntaje satura en 20 y se queda en naranja. La
  función devuelve una lista de tramos por color, no un tramo. Es el único caso
  hoy; el diseño lo soporta en general porque nada impide que aparezca otro.
- **Deduplicación.** Cuando un corte coincide con un ancla exacta, el valor cae
  en el borde de dos segmentos y ambos lo reportan (ej. `apertura_comercial`
  devuelve `9 / 9` para el corte de 40). Hay que colapsarlos.
- **Sin anclas → sin tabla.** Los indicadores de vida cotidiana y espíritu de
  época no tienen tabla de bandas (componentes base-100 y fórmulas 0-10).
  Reciben color igual, y `umbrales_en_unidad` devuelve `None`: la ficha declara
  que este indicador no tiene umbrales en unidad propia y por qué.

Umbrales resultantes del ITCG, para pinear en tests:

| Indicador | Verde | Amarillo | Naranja |
|---|---|---|---|
| cepo (brecha %) | ≤ 14 | ≤ 20 | ≤ 23,33 |
| apertura (centavos/USD) | ≤ 6 | ≤ 9 | ≤ 10,33 |
| desregulación (artículos) | ≥ 11.000 | ≥ 6.000 | ≥ 3.400 |
| dotación (% vs dic-23) | ≤ −5,2 | ≤ −2 | ≤ −0,67 |
| gasto funcionamiento (% real) | ≤ −8,5 | ≤ −2,5 | ≤ −0,83 |
| masa salarial (% real) | ≤ −7,3 | ≤ −2,5 | ≤ −0,83 |
| reestructuración (% avance) | ≥ 46 | ≥ 30 | ≥ 23,33 |
| FAL (actos 0-100) | ≥ 55 | ≥ 43,75 | ≥ 31,25 |
| litigiosidad (% 12m/12m) | ≤ 2,5 | ≤ 12,5 | ≤ 17,5 |
| privatizaciones (% avance) | ≥ 41 | ≥ 25 | ≥ 18,33 |
| RIGI (% cartera) | ≥ 29,5 | ≥ 17,5 | ≥ 12,5 |
| concesiones (% km) | ≥ 41 | ≥ 25 | ≥ 18,33 |
| asistencia directa (% TDPS) | ≥ 67 | ≥ 45 | ≥ 35 |
| orden público (% reducción) | ≥ 32,5 | ≥ 12,5 | ≥ 4,17 |
| libertad salud (% usuarios) | ≥ 36 | ≥ 20 | ≥ 13,33 |

### 4.2 Publicación — `scripts/publicar.py`

Cada indicador del snapshot gana un bloque:

```json
"semaforo": {
  "color": "amarillo",
  "tension": 4.1,
  "umbrales": [{"color": "verde", "desde": null, "hasta": 6.0}, ...],
  "unidad": "% del intercambio (alícuota efectiva)",
  "por_que": "6,18 centavos por dólar está en el tramo 6,01–9,00 que corresponde a Amarillo — 0,18 centavos por encima del piso de Verde."
}
```

`umbrales` es una **lista de tramos**, no un diccionario por color: un color
puede aparecer más de una vez, que es como se representa el caso no monótono de
§4.1. Un `desde`/`hasta` en `null` es extremo abierto. La ficha renderiza la
lista tal cual, así que soportar el caso no monótono no requiere nada especial
en la web.

Lo mismo para cada dimensión y cada índice, derivado de su puntaje con la misma
función. `por_que` se genera con la misma aritmética que produce el color, no se
escribe a mano: es lo que evita que la prosa se desincronice del dato.

La conversión a las unidades legibles que muestran las fichas (cortes de calle,
km, agentes, actos) se hace donde esa aritmética **ya vive**, junto al indicador
—`protocolo_antipiquetes` ya conoce la base 931 cortes de 2023,
`reduccion_estado` los 231.305 agentes de dic-2023— y no en la ficha.

### 4.3 Web

- `web/src/lib/datos.ts`: `semaforoDimension(puntaje, base100)` calcula el color
  en el cliente con 3 niveles. Pasa a `semaforoDe(x)`, que **lee** el color
  publicado. El cálculo sale del cliente: hay una sola definición del corte, y
  está en Python.
- `web/public/dashboard.css` (el fuente; `dist/` es salida de build): hoy define
  `--verde #16A34A` / `--amarillo #CA8A04` / `--rojo #DC2626`, cada uno con su
  variante `-soft`, y las clases `.cg-genoma-seg.sem-*` y `.cg-verdict.*`. Hay
  que agregar `--naranja` + `--naranja-soft` y las dos reglas `.sem-naranja` y
  `.cg-verdict.naranja`. Elegir un naranja que se distinga de `--amarillo` a
  tamaño de punto, y verificar contraste del par texto/fondo como en las tres
  reglas existentes.
- `IndicadorTile.astro`: punto de color en la card.
- `pages/metodologia/[id].astro`: tres secciones nuevas por ficha —
  1. **"Semáforo — valores que determinan el color"**: la tabla de `umbrales`,
     con la nota de conversión cuando la unidad legible es derivada (§4.2).
  2. **"Datos concretos detrás del valor"**: `detalle_txt`, que hoy solo se ve
     en el modal. Es el hallazgo (c) de §1.1: no hay que producir nada nuevo.
  3. **"Color vigente y por qué"**: `semaforo.por_que` + la distancia al corte
     más cercano.
- `CinturonCard.astro` pasa a 4 tramos en el genoma.

### 4.4 Qué NO se toca

`itcg.py`, `itcm.py`, `itcp.py`, `itvc.py` no cambian: ni bandas, ni pesos, ni
dimensiones. Si el diff toca una tabla de bandas, algo se salió del alcance.

---

## 5. Tests

En `tests/test_parametrica.py`:

- El color en el corte exacto: tensión 4,0 → verde y 4,01 → amarillo; puntaje
  60,0 → verde y 59,9 → amarillo (la convención de bordes del motor es low
  exclusivo / high inclusivo y el semáforo la respeta).
- **Reversibilidad**, recorriendo las tablas completas de los tres índices —57
  indicadores: 15 del ITCG, 17 del ITCM y 25 del ITCP, incluidas las bandas que
  el ITCP conserva como referencia histórica—: `puntaje_de(umbral_verde) ==
  60,0` con tolerancia de redondeo. Es el test que detecta un error de
  interpolación inversa sin depender de valores pineados, y recorrer las tablas
  y no el snapshot lo hace independiente de qué indicadores estén en el índice
  ese día.
- El no monótono `costo_financiamiento_tesoro` devuelve **dos** tramos para cada
  corte, y el verde es `[−1,89 ; 12,5]`.
- Un indicador con transformación (`rem_ipc_12m`) devuelve el umbral en unidad
  **cruda** (anual), no en la transformada.
- Deduplicación: ningún tramo aparece repetido cuando el corte cae en un ancla.

En `tests/test_publicar.py`:

- Todo indicador con `aporte_score` tiene `semaforo.color` (66 de 67 hoy; el
  único sin `aporte_score` es `asistencia_directa`, que está fuera del índice).
- Ningún color contradice su tensión: recalcular `color_de_tension` sobre el
  campo publicado da el mismo color.
- El semáforo no movió ningún número: `itcg.valor`, `itcm.valor`, `itcp.valor`,
  `itvc.valor` y `score_global` idénticos a antes del cambio.

En `tests/test_web_labels.py` (mismo patrón que la comprobación de etiquetas):

- Los cuatro colores tienen token CSS definido.

---

## 6. ADRs

| ADR | Título | Estado |
|---|---|---|
| 0181 | El color es la tensión que ya se publica, no una escala nueva | aceptado |
| 0182 | Los umbrales del semáforo se calculan, no se escriben | aceptado |
| 0183 | Rediseño del cinturón político según el documento de agosto | **propuesto** |

ADR-0181 documenta la decisión de §3 con las tres opciones, la premisa falsa del
doc `ITCG_completo` (§1.1 b) y el efecto honesto de §3.2. ADR-0182 documenta la
interpolación inversa, el caso no monótono y por qué la tabla de umbrales no
vive en prosa (§1.1 d). ADR-0183 registra el rediseño del ITCP sin aplicarlo
(§7).

Recordatorio del repo: los ids van **entre comillas** en el frontmatter
(`id: '0181'`), y el índice se regenera con `python scripts/adr_coherencia.py`.

---

## 7. Fuera de alcance (decidido, con destino)

Tres cosas vienen en los documentos y **no** entran en esta entrega, porque
mueven números publicados y un cambio de color no debe venir mezclado con un
cambio de índice.

**7.1 Anotaciones editoriales del bloque 2.** Escritas a mano en los títulos de
las fichas: *"Masa salarial pública — CREO QUE DEBERIAMOS SACARLO"* · *"Gasto de
funcionamiento — DEBERIAMOS SACAR PERSONAL DE FFAA Y SEGURIDAD"* · *"Dotación
del Estado (APN) — HABRIA QUE SACAR FFAA Y DE SEGURIDAD"*. Sacar masa salarial
baja el ITCG de 79,4 a 78,8. Lo de FFAA es factible: la ficha de dotación ya
reporta la planta civil sola (−19,0% vs −18,6% del conjunto a feb-2026). Entrega
y ADR propios.

**7.2 Rediseño del ITCP.** El doc político lista 11 indicadores en 6 dimensiones.
Diez mapean a indicadores existentes; *"Postura de los Sindicatos"* no existe y
requiere fuente y sistema de puntajes por tipo de acción. El doc **no menciona**
8 que hoy sí puntúan: producción legislativa, veto/quórum, desafíos
legislativos, bloqueo sostenido, transferencias federales (0,40 de su
dimensión), velocidad de resolución, parálisis de denuncias y conflictividad
nacional. Además propone reabrir la cohesión por cámara, lo que revierte
ADR-0048. Va a ADR-0183 en estado `propuesto`, con el efecto calculado, para que
CIGOB lo apruebe o lo baje sin bloquear el semáforo.

**7.3 Defectos de los umbrales del doc político.** Al traducirlos hay
discrepancias que hay que resolver antes de usarlos, y que se anotan en
ADR-0183 en vez de resolverse por cuenta propia:

- **Cohesión del bloque**: verde = "100%", amarillo = "75% a 89,9%". El tramo
  **90–99,9% no tiene color**.
- **Ratio DNU/leyes**: naranja llega a 3,0 y rojo es "producción legislativa
  cero" — que no es un punto del mismo eje (con leyes = 0 la ratio es infinita).
  El tramo **mayor a 3,0 no tiene color**.
- **Designación de jueces**: verde/amarillo se definen por % de vacantes
  cubiertas y rojo por % de pliegos aprobados en el Senado. Son dos ejes
  distintos en una misma escala.
- **Votómetro**: los tramos son condiciones compuestas (% propio, brecha con el
  segundo y posición), no un único eje; el indicador vigente mide la ventaja en
  puntos porcentuales.
- El indicador *"Postura Pública de las Cámaras Empresarias"* **aparece dos
  veces**; el segundo es, por su contenido, la brecha de expectativas de obra
  pública vs privada.

---

## 8. Definition of done

Vale la cadena completa del `CLAUDE.md`, no el commit:

1. `python scripts/generar_informe.py` → `publicar.py` → `gate_calidad.py`
2. `python -m pytest tests -q` (el gate y pytest son puertas distintas)
3. `npm run build` en `web/`
4. Merge y push **a `main`** — una rama no llega al sitio
5. Abrir `https://cigob-informe-coyuntura.vercel.app/` y **leer un color ahí**
6. `python scripts/bigquery_export.py` — la corrida manual no se espeja sola

El cambio es de presentación, así que alcanza con la ruta de un cinturón
(`gestion.py` → `generar_informe.py` → `publicar.py`) salvo que se toque algo
transversal; pero el semáforo se publica en los cinco, así que la verificación
en producción tiene que mirar al menos un indicador de vida cotidiana (sin tabla
de umbrales) y uno del ITCM (con tabla).
