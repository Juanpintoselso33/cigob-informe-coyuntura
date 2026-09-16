---
madr: 4
id: '0321'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'macro'
indicadores: [recaudacion]
archivos: ['scripts/macro.py', 'web/src/lib/fichas.ts', 'tests/test_macro_recaudacion_dgi.py', 'docs/adr/0318-iva-cheque-entran-como-control-no-como-card.md', 'docs/adr/0319-control-tributario-mismo-deflactor-mismo-sentido.md']
relacionado: ['0072', '0127', '0152', '0239', '0318', '0319', '0326']
ambito: 'Cinturón Macro · `recaudacion` · encuadre de IVA-DGI/cheque, tope de retroceso, banda muerta'
origen: 'Revisión adversarial de ADR-0318/ADR-0319 (15-sep-2026), previa al PR #28'
---

# ADR-0321 — Es una descomposición del agregado, no un control independiente

## Contexto y planteo del problema

ADR-0318 y ADR-0319 llaman "control tributario" a comparar el sentido del
agregado DGI+COMARB contra IVA-DGI y créditos/débitos bancarios (impuesto al
cheque). El nombre y el texto publicado ("control", "controles", "diverge del
control") dan a entender que son una fuente independiente que verifica al
agregado desde afuera.

Eso es falso por construcción: el propio docstring de `fetch_recaudacion`
dice que la DGI **suma** "IVA doméstico, Ganancias, créditos y débitos,
internos" — IVA-DGI y el impuesto al cheque son dos de los sumandos del
agregado, no una serie ajena. Medido sobre las series reales
(`INDEC_RECAUDACION_ID`, `INDEC_IVA_DGI_ID`, `INDEC_CHEQUE_ID`, ventana
2020-01 a 2026-08): IVA-DGI + cheque son entre 30,2% (2024-05) y 61,9%
(2025-01) del agregado DGI, 53,6% en agosto de 2026; IVA-DGI solo es entre
23% y 48% según el mes.

Cuando el agregado sube 10,2% y el texto dice que el IVA (24% del agregado
ese mes) "diverge" porque cae 2,9%, está describiendo aritmética de
composición —el 76% restante subió lo suficiente para arrastrar el total—
como si fuera una señal externa. Eso no es lo que pidió el equipo (cruzar el
agregado contra impuestos ligados a la actividad para detectar
distorsiones), pero **la forma de nombrarlo y de afirmar sobre él sí estaba
mal**: descomponer un agregado en sus partes y leer de cuál viene el
movimiento es exactamente lo que corresponde — llamarlo "control" que
"confirma" o "diverge" de forma independiente no.

La revisión encontró además tres defectos de implementación en el mismo
código (`_control_tributario`, `scripts/macro.py`): sin tope de retroceso si
IVA/cheque se atrasan, sin banda muerta en el entorno de cero, y una lista de
meses de divergencia incompleta en la verificación de campo de ADR-0319
(faltaba julio). Se corrigen acá junto con el encuadre porque comparten el
mismo código y el mismo texto publicado.

## Factores de decisión

- No se saca la funcionalidad: el pedido del equipo (cruzar el agregado
  contra los impuestos ligados a la actividad) sigue vigente y es útil.
- Lo que cambia es la afirmación: de "control/verificación independiente" a
  "descomposición del propio agregado en la porción ligada a actividad y el
  resto".
- El texto publicado (`detalle_txt`) y la ficha no pueden seguir diciendo que
  divergir "sí es señal" de algo ajeno a la actividad, porque la divergencia
  puede originarse enteramente dentro de la propia composición del agregado
  (p. ej. un cambio de alícuota del cheque, o un vaivén de Ganancias, que no
  entra en esta descomposición).
- Un rezago de publicación de IVA/cheque no puede quedar sin tope ni sin
  aviso: un dato de hace varios meses presentado sin marca se lee como
  fresco.
- La banda muerta tiene que ser coherente con la precisión publicada (un
  decimal): lo que se muestra como 0,0% no puede leerse como un sentido.

## Opciones consideradas

1. Dejar el nombre "control" y sólo corregir los tres defectos de
   implementación (tope, banda muerta, mes faltante).
2. Sacar la funcionalidad completa por estar mal encuadrada.
3. Renombrar a "descomposición", corregir las afirmaciones del texto público
   y la ficha para que digan lo que el cálculo realmente muestra, corregir
   los tres defectos de implementación, y dejar un ADR propio que explique el
   porqué del cambio de encuadre sin reescribir la historia de ADR-0318/0319.

## Decisión

Opción 3.

- `scripts/macro.py`: `_control_tributario()` pasa a describirse como
  descomposición en su docstring; el texto de `detalle_txt` dice "Composición
  (…)" en lugar de "Control (…)" y reformula la interpretación de la
  divergencia en términos de "de dónde vino el movimiento" en vez de
  "confirma/contradice". `_real_ia_pm3` se renombra a `_real_ia_mensual`
  (nunca calculó un promedio móvil de 3 meses). Se agrega
  `MAX_RETROCESO_DESCOMPOSICION_MESES = 3`: más allá de ese rezago entre
  IVA/cheque y la card, no hay descomposición ese mes; dentro del tope se
  publica con `meses_atraso` y el texto lo declara. Se agrega
  `BANDA_MUERTA_SENTIDO_PCT = 0.05`: el signo se calcula sobre los valores ya
  redondeados a un decimal, así que 0,0% no cuenta como sentido para ninguna
  de las tres series.
- `web/src/lib/fichas.ts`: `serie`, `transformaciones`, `limitaciones` y
  `faltantes` de `recaudacion` se reescriben con el encuadre de
  descomposición; se baja la afirmación de que divergir "sí es señal" de algo
  ajeno a la actividad (era una sobreafirmación aun antes de este ADR: la
  propia ficha ya reconocía que evasión, alícuotas y anticipos afectan
  también a IVA/cheque, y afirmaba la señal en la oración siguiente); se
  agrega `cambios` fechado hoy.
- `docs/adr/0318-*.md` y `docs/adr/0319-*.md`: no se reescriben — quedan como
  el registro de la decisión original— pero se les agrega una nota de
  corrección que apunta a este ADR, y ADR-0319 corrige la lista de meses de
  divergencia (agrega julio) y el nombre de la función.
- `tests/test_macro_recaudacion_dgi.py`: nuevos tests para el tope de
  retroceso, el desfasaje dentro del tope, la banda muerta en cero y el borde
  fuera de la banda.

### Consecuencias

- El puntaje de `recaudacion` no cambia (igual que en ADR-0318): esto es sólo
  encuadre y calidad de la descomposición existente.
- El texto publicado deja de sonar a verificación externa cuando es
  aritmética de composición.
- Un mes con IVA/cheque muy atrasados deja de mostrar un dato viejo como si
  fuera del mes de la card.
- El entorno de cero deja de poder mostrar tres números "0,0%" y afirmar que
  van en sentidos distintos.

### Confirmación

Los mismos tests de ADR-0319 (`test_control_tributario_detecta_divergencia_*`,
`*_no_marca_divergencia_falsa_*`, `*_es_none_sin_mes_comun`) más los nuevos:
`test_control_tributario_tope_de_retroceso`,
`test_control_tributario_marca_el_desfasaje_dentro_del_tope`,
`test_control_tributario_banda_muerta_en_cero`,
`test_control_tributario_no_diverge_en_borde_de_banda`.

**Verificación de campo repetida (2026-09-15, series de datos.gob.ar hasta
2026-08, recalculada directamente con `_indec_serie` y
`comarb.base_imponible_real_sa`, no copiada de ADR-0319):**

| Mes | Agregado (i.a. real) | IVA-DGI (i.a. real) | Cheque (i.a. real) | Diverge |
|---|---|---|---|---|
| 2026-01 | +0,6% | −3,3% | −0,4% | Sí |
| 2026-02 | −0,5% | −3,5% | −7,8% | No |
| 2026-03 | −0,3% | −0,1% | +4,3% | Sí |
| 2026-04 | +1,2% | −1,3% | +2,1% | Sí |
| 2026-05 | +10,1% | −2,9% | −3,5% | Sí |
| 2026-06 | −3,7% | −4,1% | −0,3% | No |
| 2026-07 | +10,0% | +5,6% | −11,3% | Sí |
| 2026-08 | −0,8% | −3,0% | −9,1% | No |

Cinco de ocho meses divergen (63%), no cuatro: **julio** quedó afuera de la
verificación de campo de ADR-0319 y es tan marcado como mayo (agregado
+10,0% con cheque en −11,3%). IVA+cheque son entre 30,2% y 61,9% del agregado
DGI en la ventana 2020-2026 (53,6% en agosto de 2026) — el fundamento
numérico de por qué esto es descomposición y no control independiente.

## Pros y contras de las opciones

- **1. Sólo corregir implementación, mantener "control":** más rápido, pero
  deja el texto público afirmando una independencia que no existe.
- **2. Sacar la funcionalidad:** desatiende el pedido explícito del equipo;
  la utilidad de descomponer el agregado es real, el problema era el nombre y
  la afirmación, no la existencia del cálculo.
- **3. Renombrar y corregir:** conserva la utilidad, corrige lo que estaba
  mal, dos ADRs quedan como registro histórico con una nota de corrección en
  vez de reescribirse.

## Más información

- ADR-0072: por qué `recaudacion` mide base imponible y actividad.
- ADR-0127: por qué la DGI (no el total) y su apertura en IVA/Ganancias/
  créditos y débitos/internos.
- ADR-0152: por qué el agregado es un nivel desestacionalizado.
- ADR-0239: por qué un deflactor de calendario no aplica acá (interanual de
  un mes puntual, no suma de flujos).
- ADR-0318: la decisión original de sumar IVA-DGI y cheque como "control".
- ADR-0319: el método de cómputo (deflactor, unidad) — sigue vigente; este
  ADR corrige su encuadre, su lista de meses y el nombre de una función.
