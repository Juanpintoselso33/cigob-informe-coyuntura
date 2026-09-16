---
madr: 4
id: '0318'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'macro'
indicadores: [recaudacion]
archivos: ['scripts/macro.py', 'web/src/lib/fichas.ts', 'tests/test_macro_recaudacion_dgi.py']
relacionado: ['0072', '0127', '0152', '0153', '0216', '0319']
ambito: 'Cinturón Macro · `recaudacion` · IVA-DGI y créditos/débitos bancarios (impuesto al cheque) como variables de control'
origen: 'Pedido del equipo (apuntes 15-sep-2026, sección B → MACRO): incorporar variables de control para corregir distorsiones del agregado y evitar sobreponderar el efecto estacional'
---

# ADR-0318 — IVA-DGI y cheque entran como control de `recaudacion`, no como card

## Contexto y planteo del problema

`recaudacion` publica un solo agregado: la base imponible real desestacionalizada
de la Dirección General Impositiva (impuestos internos) más los sistemas de la
Comisión Arbitral (ADR-0127, ADR-0152). Es una suma útil para medir base
imponible, pero mezcla cosas que no son actividad económica: vencimientos
trasladados, cambios normativos, reasignaciones entre impuestos. Cuando el
agregado sube, no hay forma de saber desde la card si subió porque hay más
actividad o porque alguna de esas otras causas movió el número.

El equipo pidió sumar dos series más ligadas a la actividad económica —IVA-DGI
doméstico y créditos/débitos bancarios (impuesto al cheque)— **como control**,
no como un componente más del índice: sirven para leer si el agregado y la
actividad van en el mismo sentido, y de paso evitan sobreponderar el efecto
estacional del agregado (que ya es grande — ADR-0152 documenta 30 puntos de
amplitud cruda entre el mes más alto y el más bajo).

## Factores de decisión

- **ADR-0153 / ADR-0216 («o integra el índice, o no es card»).** Un indicador
  que se publica como card propia y no puntúa cae en el `else` de
  `publicar.py` que le pone nota de contexto, y `tests/test_cierre_pymes.py`
  lo verifica para todo el cinturón. IVA-DGI y cheque no van a puntuar —el
  equipo los pidió como control, no como indicador nuevo—, así que una card
  propia para cada uno violaría la regla apenas se las publicara.
- El puntaje de `recaudacion` no cambia en este ADR. Si el control revela un
  mes concreto donde el agregado está distorsionado, eso es un hallazgo para
  reportar, no una recalibración de bandas por esta vía.
- Las tres series (agregado, IVA-DGI, cheque) coinciden en el corte de
  publicación —2026-08 al momento de escribir esto—, así que compararlas no
  agrega un desfasaje de calendario que la propia comparación tendría que
  explicar.

## Opciones consideradas

1. Publicar IVA-DGI y cheque como cards de contexto nuevas.
2. Sumarlos al agregado como un tercer componente en nivel (como se hizo con
   COMARB).
3. Insertarlos como control dentro de la card y la ficha existentes de
   `recaudacion`, sin puntuar: mismo patrón que `aporte_provincial_pct`.

## Decisión

Opción 3. `fetch_recaudacion()` en `scripts/macro.py` calcula, además del
valor que puntúa, la variación interanual real de IVA-DGI y de cheque (mismo
IPC como deflactor, ver ADR-0319 para el método) y el sentido del agregado en
la misma unidad. El resultado —valores y si van en el mismo sentido o
divergen— entra en `detalle_txt`, igual que ya hace `aporte_provincial_pct`
con el aporte provincial: información que viaja con la card sin ser un
insumo del puntaje. La ficha (`web/src/lib/fichas.ts`) declara las dos series
nuevas en `fuente.serie`, describe el control en `transformaciones` y declara
en `limitaciones` qué NO puede afirmar el control (ver ADR-0319).

### Consecuencias

- `recaudacion` sigue siendo una sola card, con un solo puntaje y una sola
  banda — no cambia nada de lo que mide el ITCM.
- El control es best-effort: si fallan las series de IVA-DGI o cheque, la
  card de recaudación publica igual (try/except propio dentro de
  `fetch_recaudacion`), sólo que sin la lectura de control ese mes.
- Ingresos Brutos provinciales (COMARB) sigue como componente del agregado,
  no como control — ya está resuelto por `scripts/comarb.py` y no se toca acá.

### Confirmación

`tests/test_macro_recaudacion_dgi.py` fija los dos ids de serie
(`INDEC_IVA_DGI_ID`, `INDEC_CHEQUE_ID`) y prueba `_control_tributario` con
datos sintéticos: detecta la divergencia cuando el agregado sube mientras los
dos controles caen, y —control negativo, para que el primero no pase por
default `diverge=True`— no marca divergencia cuando los tres se mueven en el
mismo sentido.

## Pros y contras de las opciones

- **1. Cards nuevas:** viola ADR-0153/ADR-0216 apenas se publican sin puntuar.
- **2. Sumarlas al agregado:** perdería justamente la utilidad de un control
  —que se pueda comparar contra el agregado— y cambiaría el puntaje de
  `recaudacion` sin que el equipo lo haya pedido.
- **3. Control dentro de la card existente:** repite un patrón ya probado
  (`aporte_provincial_pct`), no agrega cards, no toca el puntaje.

## Más información

- ADR-0072: por qué `recaudacion` mide base imponible y actividad, no
  viabilidad fiscal.
- ADR-0127: por qué la DGI y no la recaudación total.
- ADR-0152: por qué el agregado es un nivel desestacionalizado, no una
  variación.
- ADR-0153 / ADR-0216: la regla «o integra el índice, o no es card».
- ADR-0319: el método del control (mismo deflactor, misma aritmética).
