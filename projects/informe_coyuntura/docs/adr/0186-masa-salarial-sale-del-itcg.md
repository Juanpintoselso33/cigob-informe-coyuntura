---
madr: 4
id: '0186'
estado: 'aceptado'
fecha: 2026-08-09
cinturon: 'gestion'
indicadores: [masa_salarial, reforma_estado]
continua: ['0100']
continuado_por: ['0189']
ambito: 'ITCG · `masa_salarial` · dimensión `reforma_estado`'
origen: 'Revisión de fichas de Gestión por CIGOB (ronda de agosto de 2026): "CREO QUE DEBERIAMOS SACARLO" / "Concuerdo, para mi es confuso los métodos de exposición de los datos, no incluir hasta tanto tengamos certeza de afirmaciones."'
---

# ADR-0186 — `masa_salarial` sale del cálculo del ITCG

## Contexto y planteo del problema

Dos voces de CIGOB coincidieron, revisando la ficha de `masa_salarial`, en
que había que sacarlo del índice: la forma en que se expone la fuente genera
dudas sobre las afirmaciones que el indicador permite sostener, y prefieren
no incluirlo mientras esas dudas no estén saldadas. A diferencia de la
observación sobre `reestructuracion_organismos` (ADR-0185), acá no hay un
defecto puntual de etiqueta que corregir: es un pedido de retirar el
indicador del cálculo mientras dure la incertidumbre.

`masa_salarial` mide la variación real de la masa salarial del Sector
Público Nacional (AIF, remuneraciones devengadas) contra el mismo mes de
2023, deflactada por IPC. Pesaba 20% de la dimensión `reforma_estado`
(35/25/20/20 junto a `reduccion_estado`, `gasto_funcionamiento` y
`reestructuracion_organismos`), 5,0% del ITCG total.

## Factores de decisión

- El precedente directo es ADR-0100 (`asistencia_directa`): un indicador
  puede salir del CÁLCULO sin salir del TABLERO. La card, la ficha y la
  serie mensual se siguen publicando; lo que se retira es el peso en el
  índice. CIGOB pidió "no incluir... hasta tener certeza" — eso se lee como
  "que no puntúe", no como "que desaparezca": el dato en sí no está bajo
  sospecha, la forma de exponerlo sí.
- El motivo NO es el mismo que en ADR-0100. `asistencia_directa` salió
  porque llegó a un techo y se quedó ahí 27 meses — el indicador se saturó,
  no hay duda sobre lo que mide. `masa_salarial` sale por una duda abierta
  sobre la exposición de la fuente, sin que nada haya "tocado techo".
  Reutilizar la etiqueta "promesa cumplida"/`INDICADORES_CUMPLIDOS` para este
  caso sería falso: nada se cumplió. Hace falta un estado propio.
- Los tres indicadores que quedan en `reforma_estado` deben renormalizar sus
  pesos de forma DELIBERADA, no por default aritmético silencioso — mismo
  principio que ADR-0100 aplicó a `social_orden`.
- Este cambio mueve el ITCG publicado. El registro tiene que decirlo con el
  número real, no aproximado.

## Opciones consideradas

- **Ocultar la card por completo** (como los indicadores de contexto de
  ADR-0051) — descartada: `masa_salarial` SÍ mide la dimensión que dice
  medir (a diferencia de `alertas_manifestacion`/`protestas_caba`, que nunca
  midieron su dimensión); ocultarla borraría un dato válido por una duda
  sobre el índice, no sobre el dato.
- **Reusar `INDICADORES_CUMPLIDOS`** (la card se muestra con la etiqueta
  "✓ Logrado") — descartada: sería una afirmación falsa. No se cumplió nada.
- **Dejarlo en el índice con un peso reducido** (en vez de sacarlo del todo)
  — descartada: CIGOB pidió explícitamente no incluirlo, no matizarlo; un
  peso chico seguiría siendo "incluirlo".
- **Sacarlo del cálculo, mantener la card, con un estado nuevo
  (`INDICADORES_SUSPENDIDOS`) que declare el motivo real** — elegida.

## Decisión

`masa_salarial` **sale del cálculo del ITCG y se queda en el tablero**, con
un estado nuevo y distinto de "promesa cumplida":

```python
# scripts/itcg.py
INDICADORES_SUSPENDIDOS = {
    "masa_salarial": {
        "dimension": "reforma_estado",
        "desde": "2026-08",
        "desde_txt": "agosto de 2026",
        "por_que": "CIGOB pidió sacarlo del índice: la forma de exponer estos "
                   "datos genera dudas sobre las afirmaciones que permiten "
                   "sostener, y no conviene incluirlo hasta tener certeza. "
                   "La card se sigue publicando con su valor mensual — lo "
                   "que se retira es el puntaje, no el dato.",
    },
}
```

`anotar_indicadores()` en `gestion.py` marca `en_indice=False` y adjunta
`suspendido` (mismo mecanismo que `cumplido`, motivo distinto). En la web,
`[slug].astro` muestra un chip propio —"⏸ Fuera del índice desde agosto de
2026 · en revisión"— visualmente distinto del check verde "✓ Logrado" de las
promesas cumplidas, para no confundir "se logró" con "está en duda".

La dimensión `reforma_estado` pasa de 35/25/20/20 a **43,75/31,25/25** entre
`reduccion_estado`, `gasto_funcionamiento` y `reestructuracion_organismos`:
los tres conservan su proporción relativa (35:25:20 = 7:5:4), igual que
ADR-0100 hizo con `social_orden` (2:1 preservado al sacar `asistencia_directa`).

### HONESTIDAD SOBRE EL EFECTO

Este cambio mueve el ITCG publicado. Con los datos vigentes en
`output/cache/gestion.json` al momento de este ADR:

| | antes | ahora |
|---|---|---|
| `reforma_estado` (dimensión) | 90,5 | **88,1** |
| ITCG | 79,3 | **78,7** |
| tensión (0-10, redondeada a 1 decimal) | 2,1 | **2,1** (sin cambio visible) |

El ITCG baja 0,6 puntos porque `masa_salarial` puntuaba 100,0 (su banda
mejor) y salió de una dimensión que hoy promedia más alto sin él en
proporción a lo que aportaba. La tensión pública de 0-10 no se mueve en su
primer decimal por una coincidencia de redondeo — (100−79,3)/10=2,07 y
(100−78,7)/10=2,13 redondean los dos a 2,1 — pero el ITCG de base sí cambió
y queda documentado acá con el número real, no aproximado.

Sobre el fixture de ejemplo de `tests/test_itcg.py` (valores ilustrativos,
no los del snapshot real) el efecto es menor: `reforma_estado` 78,3 → 77,3,
ITCG 75,9 → 75,6 — la tensión pineada en el test (2,4) tampoco cambia por la
misma razón de redondeo.

### Consecuencias

- `masa_salarial` deja de pesar en el ITCG desde esta corrida en adelante.
  Su serie histórica en `data/historico/` no se toca — sigue existiendo,
  simplemente no vuelve a alimentar el índice hasta que alguien la reincluya.
- `scripts/validacion_externa.py::construir_serie_itcg()` reconstruye la
  serie histórica del ITCG leyendo `itcg.DIMENSIONES_ITCG` en el momento de
  ejecutarse, así que automáticamente deja de ponderar `masa_salarial` en
  próximas corridas — no hace falta tocar ese script, pero la próxima
  publicación completa debe re-correrlo para que el ITCG↔benchmarks externos
  (r de validación) refleje la fórmula nueva.
- `scripts/procedencia_anclas.py` ya no declara procedencia para
  `masa_salarial` (se retiró la entrada, mismo criterio que
  `asistencia_directa`): `_indicadores_del_indice()` deja de listarlo al no
  estar en ninguna `DIMENSIONES_ITCG`, así que declarar su procedencia
  inflaría la cobertura aparente sobre un índice que ya no lo incluye.
- **El estado es reversible y nadie lo vigila automáticamente**, misma
  limitación que ADR-0100 declaró para `asistencia_directa`: si las dudas de
  CIGOB se resuelven, alguien tiene que sacar la entrada de
  `INDICADORES_SUSPENDIDOS` y devolver el peso a mano. No hay vencimiento
  automático.

### Confirmación

`tests/test_itcg.py::test_masa_salarial_no_integra_ninguna_dimension` verifica
que la clave sigue en `BANDAS_ITCG` (la ficha puede seguir mostrando su
banda) pero en ninguna `DIMENSIONES_ITCG`, que está declarada en
`INDICADORES_SUSPENDIDOS`, y que el ITCG no cambia con o sin su valor.
`test_itcg_reproduce_ejemplo` y `test_renormalizacion_ante_faltantes` pinean
los números nuevos de `reforma_estado`/ITCG sobre el fixture de ejemplo.

El número real (79,3 → 78,7) se verificó recalculando `itcg.calcular_itcg()`
con los valores vigentes de `output/cache/gestion.json` bajo el código
anterior y el nuevo, sin regenerar ni commitear ningún snapshot — ver
`git status --short` al cierre de esta sesión: ningún archivo de
`output/`, `web/src/data/` o `data/historico/` quedó modificado.

## Pros y contras de las opciones

**Ocultar la card por completo**

- Bueno: coherente con ADR-0051 para indicadores que no aportan información.
- Malo: `masa_salarial` sí mide su dimensión — esconderla sería tratar una
  duda metodológica como si fuera irrelevancia, que no es lo que CIGOB dijo.

**Reusar `INDICADORES_CUMPLIDOS`**

- Bueno: cero código nuevo, mecanismo ya probado por ADR-0100.
- Malo: la etiqueta "✓ Logrado" sería una afirmación falsa sobre por qué el
  indicador dejó de puntuar.

**Dejarlo con peso reducido**

- Bueno: conserva algo de la señal que el indicador aporta.
- Malo: contradice el pedido explícito de CIGOB de no incluirlo.

**Estado nuevo `INDICADORES_SUSPENDIDOS` (elegida)**

- Bueno: mismo patrón probado (card adentro de su dimensión, sin puntaje) con
  la semántica correcta para este motivo.
- Bueno: renormalización declarada y verificable por test.
- Malo: agrega un segundo estado "no puntúa pero se muestra" al lado de
  `INDICADORES_CUMPLIDOS` — dos vocabularios para una idea con dos motivos
  distintos, más superficie para mantener sincronizada entre `itcg.py`,
  `gestion.py` y `[slug].astro`.

## Más información

### Por qué no es lo mismo que ADR-0100

ADR-0100 fue explícito en que su excepción es acotada: "toda cumplida debe
declarar su fecha de logro y el motivo" — un techo alcanzado, verificable,
con una fecha concreta donde el indicador dejó de moverse. `masa_salarial`
no dejó de moverse ni llegó a ningún techo: su valor sigue cambiando mes a
mes con normalidad. Lo que cambió es que CIGOB dejó de confiar en cómo se
presenta esa variación mientras no haya certeza sobre las afirmaciones que
permite sostener. Tratarlo con el mismo vocabulario que una promesa cumplida
habría sido más cómodo de implementar y más falso de leer.
