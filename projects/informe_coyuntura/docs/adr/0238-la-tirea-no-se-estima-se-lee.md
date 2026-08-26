---
madr: 4
id: '0238'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
archivos: ['scripts/macro.py', 'tests/test_macro_costo_financiamiento.py', 'tests/fixtures/colocaciones_2026_06.json']
relacionado: ['0071', '0258']
ambito: 'Datos · de dónde sale la TIREA con la que se mide el costo del financiamiento del Tesoro'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «Corregir la TIREA: la colocación externa comparable informa 28,32%, no 32,17%»'
---

# ADR-0238 — La TIREA no se estima, se lee

## Contexto y planteo del problema

`costo_financiamiento_tesoro` ([[0071-costo-financiamiento-tesoro]])
publicó **8,07% real anual** para junio de 2026, construido sobre una TIREA
nominal de **32,17%**. La auditoría del 25-ago-2026 fue a buscar la colocación:
junio tuvo **una sola** operación a tasa fija en pesos, la LECAP **S13N6**
(`LECAP/$/13-11-2026`), emitida a la par el 30-06 por $4,18 billones —el mismo
monto que aparecía en la extracción— con **TEM 2,1%** en el cupón. La
Secretaría y el mercado informaron **TIREA 28,32%**. Contra el REM de 22,3%,
eso son **4,92% reales**, no 8,07%: el indicador sobreestimaba el nivel en
**3,15 puntos reales** y la tasa nominal en **385 puntos básicos**.

El error no estaba en el deflactor sino en la reconstrucción. `_tirea_de_fila`
derivaba la tasa del precio de corte y las fechas:

```
n      = meses de CALENDARIO entre emisión y vencimiento
payoff = 1000 · (1 + TEM)^n
TIREA  = (payoff / precio)^(365/días) − 1
```

Para la S13N6, `n` contaba **5** meses (junio→noviembre) sobre un plazo real de
**136 días = 4,53 meses**. Medio mes de capitalización de más, a TEM 2,1%,
anualizado sobre 136 días: 385 pb.

Lo importante es que **no había nada que estimar**. La TIREA de una LECAP o un
BONCAP a tasa fija es un dato publicado: Finanzas informa la TEM en la columna
de cupón y la convención del mercado la anualiza como `(1+TEM)^12 − 1`. El
colector reconstruía a mano —y mal— un número que ya venía en la planilla.

Dos cosas empeoran el diagnóstico. La primera es que el desvío **estaba
documentado en el propio test**: `test_tirea_capitalizable_reproduce_la_gacetilla`
admitía ±3,5 pp y su comentario explicaba que «el cálculo capitaliza por meses
enteros y el oficial usa días exactos, una diferencia de convención que a estos
plazos vale ~2,8 pp». La guarda no protegía contra el error: lo declaraba como
tolerancia. La segunda es que el desvío **no es constante ni de un solo signo**:
reprocesadas las 178 colocaciones a tasa fija en pesos desde diciembre de 2023,
va de **−17,8 pp** (mayo-2024) a **+22,0 pp** (febrero-2025). No se puede
corregir con un ajuste; hay que rehacer la serie.

## Factores de decisión

- **Un dato publicado no se reconstruye.** Si la fuente informa la tasa, el
  colector la lee; reconstruirla sólo agrega una convención propia que puede
  desviarse en silencio.
- **La convención tiene que ser verificable por un tercero** desde un campo de
  la planilla, sin suponer día de liquidación ni base de días.
- **La reconstrucción sigue siendo útil como control**, no como fuente.
- **La serie histórica entera cambia**, así que la corrección no es del último
  punto sino de la reconstrucción completa.

## Opciones consideradas

- **A — Arreglar el conteo de meses y seguir reconstruyendo desde el precio.**
- **B — Leer la tasa oficial del cupón (`(1+TEM)^12 − 1`) y reconstruir sólo
  cuando no hay TEM publicada.**
- **C — Publicar el rendimiento marginal del precio de corte** (opción B para
  emisiones nuevas, rendimiento a vencimiento para reaperturas).

## Decisión

**Opción B.** Para todo instrumento a tasa fija en pesos con TEM publicada, la
TIREA es `(1 + TEM)^12 − 1`, leída del cupón. Las LEDE a descuento no publican
TEM —su rendimiento lo define el precio— y ahí sí se reconstruye:
`(1000/precio)^(365/días) − 1`. Son 3 colocaciones sobre 178.

`_tirea_reconstruida` se conserva pero **no publica**: deriva la tasa del precio
de corte con el payoff sobre el plazo real (`días/30`) y anualiza sobre 360 días
—doce meses de treinta—, que es la misma convención con la que el mercado pasa
de TEM a TIREA. Escrita así, en una emisión nueva colocada a la par tiene que
reproducir la tasa oficial. Reproduce **0,0000 pb de desvío en las 57
colocaciones de ese tipo** desde diciembre de 2023, y eso es lo que verifica el
test de tolerancia que pidió la auditoría.

La card viaja además con el inventario de colocaciones del mes —instrumento,
TIREA y monto de cada una—. Un promedio ponderado sin las operaciones que lo
forman no es auditable, y fue justamente lo que dejó pasar 32,17% sin que nadie
pudiera revisarlo.

### Consecuencias

- Junio de 2026 pasa de **8,07% a 4,92% real**; la TIREA nominal, de 32,17% a
  28,32%. El semáforo sigue **verde** —los dos valores caen en la zona sana de
  la U invertida— pero el puntaje sube, porque 4,92% está más cerca del óptimo
  que 8,07%.
- La serie completa desde diciembre de 2023 se reconstruye. Las bandas se
  revisan contra la serie nueva, no contra la anterior.
- **En una reapertura colocada fuera de la par, el indicador informa la tasa
  contractual del instrumento, no el rendimiento marginal del precio de corte.**
  Es una limitación declarada, no un descuido: la opción C mide mejor el costo
  marginal, pero depende de una reconstrucción del payoff que no se pudo
  verificar contra ninguna gacetilla de reapertura, y la auditoría pidió
  explícitamente priorizar el campo publicado. Queda anotada para revisión.

### Confirmación

`tests/test_macro_costo_financiamiento.py`, contra
`tests/fixtures/colocaciones_2026_06.json` —las 17 filas reales de la licitación
auditada, sin filtrar—:

- la S13N6 da 28,32% y **no puede dar 32,17%**;
- la licitación completa reproduce ~4,92% real y **no 8,07%**;
- la reconstrucción por precio coincide con la tasa oficial **dentro de 5 pb**;
- las 16 filas restantes (USD, CER, dual, TAMAR) quedan afuera, incluida
  `capitalizable "TAMAR TEM"`, que dice la palabra pero no trae número.

Las cinco guardas se probaron **rompiéndolas**: revertido el cálculo al conteo
por meses de calendario, fallan.

## Pros y contras de las opciones

### A — Arreglar el conteo y seguir reconstruyendo

- Bueno, porque es el cambio más chico.
- Malo, porque deja en pie una convención propia —qué base de días, qué fecha de
  liquidación— que puede volver a desviarse sin que nada falle.
- Malo, porque sigue sin haber contra qué validar.

### B — Leer la tasa oficial del cupón

- Bueno, porque el número es el que publica la fuente, reproducible desde un
  campo de la planilla.
- Bueno, porque no depende del precio ni de la base de días: no hay convención
  que romper.
- Bueno, porque deja la reconstrucción libre para hacer de control.
- Malo, porque en una reapertura informa la tasa del cupón y no el rendimiento
  del precio de corte.

### C — Rendimiento marginal del precio de corte

- Bueno, porque es lo que económicamente paga el Tesoro por los pesos que
  levanta hoy.
- Malo, porque en meses dominados por reaperturas se aparta mucho de la tasa
  publicada (hasta 18 pp en febrero de 2025) sin una gacetilla contra la cual
  dirimir cuál de las dos es la que informa la fuente.
- Malo, porque anualizar un remanente de 15 días produce tasas de tres cifras
  que arrastran el promedio del mes.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_macro.md`, caso 16.
- Planilla de origen: Secretaría de Finanzas, «Colocaciones de deuda 2026».
- [[0071-costo-financiamiento-tesoro]] define el indicador y su escala
  de U invertida, que este ADR no toca.
