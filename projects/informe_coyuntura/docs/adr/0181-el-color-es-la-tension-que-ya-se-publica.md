---
madr: 4
id: '0181'
estado: 'aceptado'
fecha: 2026-08-08
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/parametrica.py', 'scripts/publicar.py', 'web/src/lib/datos.ts']
relacionado: ['0121', '0021']
continuado_por: ['0182']
ambito: 'Semáforo de 4 colores · capa de lectura sobre los cinco cinturones'
origen: 'Cuatro documentos CIGOB del 2026-08-05/08 (las 15 fichas de Gestión, ITCG_completo_semaforo y el de indicadores y semáforos del cinturón político) que piden un semáforo de 4 colores, cada uno con una regla de corte distinta'
---

# ADR-0181 — El color es la tensión que ya se publica, no una escala nueva

## Contexto y planteo del problema

CIGOB entregó cuatro documentos entre el 5 y el 8 de agosto de 2026 pidiendo
un semáforo de cuatro colores por indicador, dimensión e índice, con los
umbrales expresados en la unidad real del indicador —km, artículos, centavos
por dólar, agentes— y no en puntaje.

**Tres de esos documentos traen una regla de color, y las tres no coinciden.**
Antes de elegir una había que entender de dónde salía cada una, así que se
reprodujo su aritmética contra el código. Eso dio tres hallazgos que
condicionan la decisión.

**(a) El semáforo de las fichas no es un sistema nuevo: es el puntaje
invertido.** Cada umbral "en unidad propia" de las 15 fichas de Gestión sale
de interpolar hacia atrás las anclas de `BANDAS_ITCG`, con cortes en puntaje
**65 / 45 / 25**. Se verificó exacto en 12 indicadores independientes, sin
excepciones: apertura `≤5,25 centavos` es el ancla de 65 · dotación `≤−6%` es
el ancla de 65 · desregulación `13.300 art → 65,0`, `7.250 → 45,0`, `3.850 →
25,0` · concesiones `4.095 km = 45%` es el ancla de 65. No es un criterio
paralelo al motor: es el motor, leído al revés.

**(b) `ITCG_completo_semaforo` parte de una premisa falsa.** Ese documento
propone cortes **85/55/25** y los justifica como *"el punto medio entre tus
anclas (100/70/40/10)"*. Las anclas del ITCG **no son** 100/70/40/10: son
**100/85/65/40/10** —cinco niveles, no cuatro— en 13 de sus 15 tablas
(`desregulacion_normativa` usa 100/85/60/35/10 y `fal_modernizacion_laboral`
usa 100/50/10). Con esa premisa el documento llega a colores distintos de los
de las propias fichas de Gestión en 5 de 14 indicadores. No es una diferencia
de criterio entre dos documentos: uno de los dos está calculando sobre una
tabla que no existe.

**(c) El informe ya pintaba con dos varas distintas.** `semaforoDimension()`
en `web/src/lib/datos.ts` usaba verde `≥60` para los índices 0-100 —que es
**tensión 4**— y verde `≥95` para el ITVC base-100 —que es **tensión 6**. El
mismo color significaba dos cosas distintas según el cinturón, y nadie lo
había declarado en ningún lado. Cualquier regla nueva que no toque esto la
consolida.

## Factores de decisión

- El semáforo es una **capa de lectura**: no puede mover ningún puntaje, peso,
  banda ni índice. Si el diff toca una tabla de bandas, se salió del alcance.
- Un color tiene que significar lo mismo en las cinco páginas del informe. Con
  dos varas, "verde" no es un dato: es un adorno que depende del cinturón.
- Los cortes tienen que derivarse de algo que el informe **ya publica** y que
  el lector puede verificar, no de una construcción ad hoc explicada en un
  documento que el pipeline no lee.
- El ITVC es base-100 y no puntúa 0-100. La regla tiene que atravesar las dos
  escalas sin inventar una segunda regla para la segunda escala.
- Los cortes tienen que vivir en **una constante**. Si CIGOB quiere otra vara,
  cambiarla tiene que costar tres números, no una refactorización.

## Opciones consideradas

- **A — la de las fichas: 65/45/25.** Es lo que las 15 fichas de Gestión ya
  implementan.
- **B — la de `ITCG_completo`: 85/55/25.**
- **C — la tensión publicada: 60/40/20** (elegida).
- **Histéresis de dos meses sobre cualquiera de las tres** — descartada, ver
  "Más información".

## Decisión

**El color es la tensión 0-10 que el informe ya publica, partida en cuatro
tramos.** Los cortes viven en `CORTES_SEMAFORO`, en `scripts/parametrica.py`,
y son la única fuente de verdad:

```python
CORTES_SEMAFORO = (("verde", 4.0), ("amarillo", 6.0), ("naranja", 8.0), ("rojo", INF))
```

| Color | Tensión | Índices 0-100 | ITVC base-100 |
|---|---|---|---|
| 🟢 Verde | ≤ 4 | puntaje ≥ 60 | índice ≥ 105 |
| 🟡 Amarillo | ≤ 6 | 40 – 59,9 | 95 – 104,9 |
| 🟠 Naranja | ≤ 8 | 20 – 39,9 | 85 – 94,9 |
| 🔴 Rojo | > 8 | < 20 | < 85 |

**No es una escala nueva.** Los cortes 60/40/20 son los bordes de
`BANDAS_INTERPRETACION` —`(−∞,20] severamente apretado · (20,40] apretado ·
(40,60] moderadamente apretado · (60,80] moderadamente aflojado · (80,∞)
aflojado`—, que el informe ya publica como etiqueta de cada índice. Verde es
"moderadamente aflojado o mejor", amarillo es "moderadamente apretado",
naranja es "apretado", rojo es "severamente apretado". Los cortes del ITVC
salen de despejar su propia fórmula publicada, `tensión = 5 − (índice−100) ×
0,2`: tensión ≤4 ⟺ índice ≥105, ≤6 ⟺ ≥95, ≤8 ⟺ ≥85.

Eso **unifica la vara**: el mismo color es la misma tensión en los cinco
cinturones, y corrige el hallazgo (c) de arriba en vez de arrastrarlo.

El color se calcula siempre sobre la tensión **sin redondear** — `aporte_score`
está redondeado a un decimal y usarlo como insumo rompe el borde. El detalle
está en ADR-0182, junto con el resto de la mecánica de los umbrales.

`semaforoDimension()` desaparece de la web. En su lugar `semaforoDe(x)` **lee**
el color que viene en el snapshot: hay una sola definición del corte y está en
Python.

### Consecuencias

**Contra la regla A que usan las fichas entregadas, seis indicadores cambian
de color a los valores de hoy, y los seis mejoran:**

| Cinturón | Indicador | Puntaje | A (65/45/25) | C (60/40/20) |
|---|---|---|---|---|
| macro | recaudación | 43,0 | 🟠 | 🟡 |
| macro | presión de dolarización | 64,5 | 🟡 | 🟢 |
| macro | IAI | 61,0 | 🟡 | 🟢 |
| gestión | RIGI | 63,5 | 🟡 | 🟢 |
| gestión | concesiones viales | 44,6 | 🟠 | 🟡 |
| política | ratio DNU | 22,0 | 🔴 | 🟠 |

**Que los seis mejoren no es una virtud del criterio: es la consecuencia
mecánica de bajar los tres cortes.** Cualquier indicador que estuviera entre
60 y 65, entre 40 y 45 o entre 20 y 25 tenía que subir de color, y ninguno
podía bajar. Queda escrito para que se pueda discutir, no como argumento a
favor.

**Y vida cotidiana se ve peor. Ese es el precio real de unificar la vara.** Al
pasar el ITVC de "verde = tensión 6" a "verde = tensión 4", el reparto de sus
16 componentes cambia así:

| Componente | Índice | Tensión | Antes (3 colores) | Ahora |
|---|---|---|---|---|
| inseguridad | 102,1 | 4,6 | 🟢 | 🟡 |
| mortalidad de pymes | 96,5 | 5,7 | 🟢 | 🟡 |
| empleo registrado | 96,1 | 5,8 | 🟢 | 🟡 |
| informalidad | 94,2 | 6,2 | 🟡 | 🟠 |
| ICC UTDT | 90,9 | 6,8 | 🟡 | 🟠 |
| pluriempleo | 90,7 | 6,9 | 🟡 | 🟠 |
| consumo de carne | 89,3 | 7,1 | 🔴 | 🟠 |
| despacho de cemento | 85,7 | 7,9 | 🔴 | 🟠 |

**Seis componentes empeoran y dos mejoran.** El reparto pasa de 8 verde · 3
amarillo · 5 rojo a **5 verde · 3 amarillo · 5 naranja · 3 rojo**, y **el ITVC
total (90,3) pasa de amarillo a naranja**. No es que vida cotidiana haya
empeorado: es que hasta ahora se pintaba con una vara **dos puntos de tensión
más indulgente** que la del resto del informe, y ahora se pinta con la misma.

Otras consecuencias:

- `web/public/dashboard.css` gana `--naranja` y `--naranja-soft`, más las
  reglas `.sem-naranja` y `.cg-verdict.naranja`. El genoma de
  `CinturonCard.astro` pasa a cuatro tramos.
- Revertir a la regla A cuesta **tres números** en `CORTES_SEMAFORO` (3,5 /
  5,5 / 7,5). Lo que A no tiene es una regla para el ITVC: habría que inventar
  una segunda, que es exactamente el problema que esta decisión cierra.
- El cálculo del color sale del cliente. Hasta agosto de 2026 la web lo
  derivaba de un número; ahora lo lee. Dos definiciones del mismo corte en dos
  lenguajes se desincronizan sin que falle nada.

### Confirmación

26 tests en `tests/test_semaforo.py`, `tests/test_publicar_semaforo.py` y
`tests/test_web_semaforo.py`:

- Los bordes exactos: tensión 4,0 → verde y 4,01 → amarillo; puntaje 60,0 →
  verde y 59,9 → amarillo (convención low-exclusivo / high-inclusivo, la misma
  del motor).
- El ITVC en los suyos: índice 105 → verde, 104,9 → amarillo, 95 → amarillo,
  94,9 → naranja, 85 → naranja, 84,9 → rojo.
- Que ningún color publicado contradiga su propio puntaje: recalcular el color
  sobre el campo publicado da el mismo color.
- **Que el semáforo no movió ningún número**: `itcm.valor`, `itcg.valor`,
  `itcp.valor`, `itvc.valor` y `score_global` son idénticos antes y después de
  correr `publicar._semaforos()` sobre el mismo snapshot. Es invariancia
  directa —el mismo snapshot contra sí mismo— y no una comparación contra una
  fixture congelada, que sólo probaría "no cambió desde tal día".
- Que los cuatro colores tienen token CSS y reglas de genoma y verdict, y que
  ningún `.ts` deriva el color de un número.

## Pros y contras de las opciones

**A — 65/45/25 (las fichas de Gestión)**

- Bueno: es lo que los documentos entregados ya implementan; adoptarla no
  obliga a explicarle a nadie por qué cambió un color.
- Bueno: sus 15 tablas en unidad propia ya están escritas y revisadas.
- Malo: su derivación es ad hoc —65 es el ancla del medio, 25 el punto medio
  de las dos peores, 45 el punto medio de esos dos— y no se apoya en nada que
  el informe publique.
- Malo: no se extiende al ITVC sin inventar una segunda regla, así que deja en
  pie la inconsistencia (c).
- Malo: 65 y 45 caen en el medio de los tramos de `BANDAS_INTERPRETACION`, así
  que el color y la etiqueta del mismo índice pueden decir cosas distintas.

**B — 85/55/25 (`ITCG_completo_semaforo`)**

- Bueno: es el documento que discute explícitamente la regla, con preguntas
  abiertas planteadas por el equipo.
- Malo: su justificación es aritmética sobre anclas que el ITCG no tiene
  (100/70/40/10 contra las 100/85/65/40/10 reales). Corregida la premisa, el
  resultado no se sostiene.
- Malo: contradice las fichas del mismo lote en 5 de 14 indicadores, sin
  declararlo.
- Malo: verde a puntaje 85 es una vara mucho más dura que la de cualquier
  etiqueta publicada, así que casi todo el informe quedaría amarillo o peor.

**C — 60/40/20 (la tensión publicada)** — elegida

- Bueno: un solo criterio para los cinco cinturones, derivado de dos fórmulas
  que el informe ya publica y que el lector puede verificar.
- Bueno: el color coincide con la etiqueta de interpretación del índice, así
  que las dos lecturas no pueden contradecirse.
- Bueno: la regla vive en una constante de cuatro tuplas.
- Malo: mueve seis colores respecto de las fichas entregadas y ocho respecto
  de lo que la web mostraba en vida cotidiana. Un lector que venía mirando el
  ITVC ve el índice pasar a naranja sin que ningún dato haya cambiado.
- Malo: los umbrales en unidad propia de las 15 fichas de Gestión, tal como
  están escritos, dejan de ser los vigentes.

## Más información

### Por qué la histéresis de dos meses quedó afuera

`ITCG_completo_semaforo` §5 propone exigir **dos meses consecutivos** del lado
nuevo antes de mover un color, para amortiguar tres indicadores que están al
borde de un corte. Se descarta por la relación entre lo que cuesta y lo que
resuelve: obliga a **persistir el color de la corrida anterior** —estado nuevo
en un pipeline que hoy recalcula todo desde cero, sin memoria entre corridas—
para un problema que el informe ya resuelve declarando cuáles indicadores
están al borde. Además introduce una clase de falla nueva: un color que no se
puede reproducir mirando sólo el snapshot de hoy.

Si más adelante se quiere, se agrega **sobre** el color publicado, sin tocar el
motor: la tensión y el color de cada corrida quedan en el snapshot y en
BigQuery (ADR-0180), así que la serie necesaria ya se está acumulando.

### La pregunta abierta: la vara del ITVC

Lo implementado es la **vara unificada**: verde a tensión 4 en los cinco
cinturones. Si CIGOB prefiere conservar para el ITVC la vara vieja —verde a
tensión 6, que es la que venía usando la web sin haberlo declarado— eso es una
**excepción explícita que hay que decidir y anotar acá**, no algo que pueda
quedar por omisión. Volver atrás son dos líneas en
`parametrica.color_de_indice_base100`.

Se deja escrito de este lado porque la asimetría importa: la vara unificada es
defendible sin nota al pie, la vara indulgente sólo es defendible si alguien
la firma.

### Dos consecuencias que aparecieron implementando

**Una colisión de nombre que funcionaba por orden de ejecución.** El colector
`macro.py` ya escribía un campo `semaforo` en el indicador `idc`: un string de
tres colores por z-score (`> +0,5 σ` verde, `±0,5 σ` amarillo, `< −0,5 σ`
rojo), ajeno al motor paramétrico, que `publicar.py` leía para armar el texto
del modal. El bloque `semaforo` nuevo lo pisaba. No rompía nada porque
`_scoring_indice` corre antes que `_semaforos` en el mismo archivo — por orden,
no por diseño. Se renombró a **`banda_idc`** en el colector y en la lectura. La
caché vieja de `output/cache/macro.json` todavía trae la clave anterior y se
autocura en la próxima corrida del colector; mientras tanto degrada a un
paréntesis vacío, no a un crash.

**`verdictDeCinturon(estado)` NO se unificó, y es deliberado.** El chip de cada
cinturón sigue con tres colores porque no sale de la tensión: sale del `estado`
editorial del cinturón (`estable` / `en_tension` / `alerta` / `critico`), que
alimenta el BLUF, el panel de tensión, `cinturonesRojos` y `score_global`.
Cambiarlo sería un cambio de índice, no de presentación — justo lo que este
ADR se prohíbe. La clase CSS `.cg-verdict` es compartida y está indexada por
nombre de color, no por qué concepto lo produjo, así que recibe `naranja` igual.
**Unificar el chip del cinturón con el color de su índice queda pendiente
declarado, no olvidado.**

### Lo que el semáforo no toca

`itcg.py`, `itcm.py`, `itcp.py` y `itvc.py` no cambian: ni bandas, ni pesos, ni
dimensiones. Ningún puntaje, ningún índice y `score_global` se mueven. Está
comprobado por test, no sólo declarado acá.
