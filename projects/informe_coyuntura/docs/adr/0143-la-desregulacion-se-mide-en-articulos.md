# ADR-0143 — La desregulación se mide en artículos, no en normas

- **Estado**: Aceptado
- **Fecha**: 2026-07-26
- **Ámbito**: ITCG · `desregulacion_normativa` · bandas · serie · card · ficha
- **Modifica**: ADR-0125 (la fuente sigue siendo la misma; cambia la unidad)
- **Origen**: revisión externa del cinturón de gestión (23-jul-2026)

## El planteo, y por qué la propuesta literal no iba

La revisión externa propuso fijar el techo de la banda en **300 normas**. No se
tomó: el programa lleva **689** y suma unas 36 por mes, así que ese ancla habría
hecho nacer el indicador saturado en 100 y sin recorrido — el mismo defecto que
ADR-0142 aceptó a sabiendas para el FAL y que no conviene repetir en la
dimensión que más pesa del ITCG.

Pero el mismo documento traía una observación más profunda, sin propuesta
asociada:

> "es cierto como se señala que se cuentan por igual normas como si fueran
> equivalentes, y de hecho no lo son"

**Eso sí se resuelve, y con un dato que el propio Ministerio ya publica.**

## Lo que se encontró leyendo los informes

El informe mensual publica **tres** cifras, no una:

| | jun-2026 |
|---|---|
| normas de desregulación | 689 |
| normas modificadas o eliminadas | 2.699 |
| **artículos modificados o eliminados** | **16.178** |

Usábamos la primera. La tercera mide **volumen de texto regulatorio
efectivamente removido** en lugar de cantidad de actos administrativos firmados:
un decreto que reescribe quinientos artículos y una resolución que toca uno
dejan de pesar igual. Es exactamente la objeción de la revisión externa.

### Se descartó el ratio contra el stock regulatorio, por incommensurabilidad

Antes de recalibrar se buscó eliminar la convención del techo dividiendo por el
stock de regulación vigente. **El denominador existe**: la faceta `Estado de
Vigencia` de SAIJ da **16.825 normas nacionales vigentes de alcance general**
(11.261 decretos + 5.564 leyes).

**Pero los universos no son conmensurables, y se verificó leyendo, no
suponiendo.** El informe de julio-2025 dice «396 normas de desregulación que
eliminan o modifican 1.157 **normativas anteriores**», y los ejemplos del
informe de junio-2026 incluyen la Resolución 197/2026 del INPI derogando la
**Resolución** INPI 283/2015. O sea: el numerador del Ministerio **incluye
resoluciones**, y ese denominador de SAIJ **son sólo leyes y decretos**. El
cociente habría dividido peras por manzanas. Queda registrado para que nadie
repita el intento.

## La serie: existe desde dic-2023 y está validada

Los informes en prosa (hasta abr-2026) traen una **Figura 5**, «evolución
acumulada» de artículos, con una barra por mes desde dic-2023 — la misma técnica
de extracción vectorial de ADR-0125, apuntada a otra figura. En la página
conviven dos gráficos (la Figura 4 es la misma variable *por mes*), así que entre
los grupos de barras se toma el monótono creciente con más barras.

**Validación**: nueve informes independientes, cada uno con su Figura 5
calibrada contra su propio titular. En los meses solapados, **cinco dan
diferencia exacta cero** y el peor caso es **45 artículos sobre una serie que
llega a 16.178 — 0,3%**. Mismo orden de error relativo que la extracción de
normas que ya estaba en producción.

Serie resultante: **1.150 artículos (dic-2023) → 16.178 (jun-2026)**, 31 puntos,
rango ×14.

## Bandas

```
(30000, INF, 100) · (15000, 30000, 85) · (7000, 15000, 60)
(2500, 7000, 35)  · (-INF, 2500, 10)
```

Cortes redondos que reparten los 31 puntos de la serie **4/8/11/8** sobre las
cuatro bandas inferiores, con la superior vacía a propósito porque el programa
está a mitad de camino.

Con 16.178 el puntaje es **71,3**, contra los **73,3** que daba el conteo de
normas: **la unidad cambió, el resultado no**, que es lo que pide ADR-0045 para
no mover un número recalibrando. La escala sigue siendo **convención nuestra**
—el Ministerio publica el recuento pero no declara meta— y eso queda dicho en el
comentario de las bandas, en la fórmula pública y en la ficha.

REVISAR cuando el acumulado pase de 24.000: al ritmo de 2026 (~360
artículos/mes) eso ocurre hacia fines de 2027.

## Lo implementado

- `gestion.py`: `_desreg_backfill_grafico(url, ancla, figura)` parametrizado, con
  selección del grupo de barras monótono más largo; `desregulacion_oficial_serie(metrica)`
  con `DESREG_METRICAS`; el fetch pasa a artículos y publica normas y normas
  afectadas **como contexto de la card**.
- `itcg.py`: bandas nuevas. `descargar_series.py`: la serie publicada.
- Web: `fichas.ts`, `datos.ts`, `descripciones.ts`, `formulas.ts`.
- Tests: **se corrigió un test que pasaba por la razón equivocada** —
  `test_el_backfill_coincide_con_las_cifras_de_portada` seguía validando el
  backfill de normas, que ya no puntúa. Ahora está parametrizado y valida las
  dos series, con tolerancia proporcional a cada escala. Se agregó
  `test_lo_que_puntua_son_articulos_no_normas`.

## Consecuencias

- El store `desregulacion_oficial.json` gana la clave `backfill_articulos`
  junto a `backfill_grafico`. Las dos series se conservan: la de normas sigue
  alimentando el contexto de la card.
- La limitación de fondo **no desaparece**: contar artículos corrige la
  equivalencia entre normas de peso muy distinto, pero un artículo que libera un
  mercado sigue contando igual que uno que ajusta una definición. Está declarado
  en la ficha.
