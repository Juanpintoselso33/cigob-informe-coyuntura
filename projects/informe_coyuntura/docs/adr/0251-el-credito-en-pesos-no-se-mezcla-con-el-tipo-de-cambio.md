---
madr: 4
id: '0251'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [credito_privado]
archivos: ['scripts/macro.py', 'scripts/descargar_series.py', 'tests/test_universos_declarados.py']
relacionado: ['0022']
ambito: 'Cinturón macro · ITCM · `credito_privado` · en qué moneda se mide el crédito'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «incluye préstamos en dólares valuados en pesos; la variación mezcla crédito y efecto cambiario»'
---

# ADR-0251 — El crédito en pesos no se mezcla con el tipo de cambio

## Contexto y planteo del problema

`credito_privado` publicaba **+2,5% real interanual** y el crédito en pesos
estaba **cayendo**.

El indicador usaba la variable 26 del BCRA. El propio catálogo del BCRA la
declara `moneda: "MEyML"` — moneda extranjera **y** moneda local: es la suma del
crédito en pesos más la cartera en dólares **valuada en pesos**. Con esa serie,
una devaluación revalúa la cartera en dólares sin que se preste un peso más, y
el indicador lo publica como crecimiento real del crédito.

En julio de 2026, con el mismo corte y el mismo deflactor:

| Variable BCRA | Moneda | i.a. real |
|---|---|---:|
| **117** — préstamos al sector privado | `ML` (pesos) | **−1,5%** |
| 126 — la misma cartera en dólares, valuada en pesos | `ME` | +17,1% |
| 26 — las dos juntas *(la que se publicaba)* | `MEyML` | +2,6% |

El titular no estaba a mitad de camino entre las dos lecturas: estaba en la
frontera del signo. Publicaba expansión donde había contracción.

## Factores de decisión

- **Un indicador de crédito tiene que medir crédito**, no revaluación de
  cartera.
- **El universo tiene que ser el mismo en los dos extremos** de la comparación
  interanual; con `MEyML` el tipo de cambio entra como un tercer término.
- **La cartera en dólares no sobra**: informa, pero hay que poder leerla sin que
  se mezcle.

## Opciones consideradas

- **A — Deflactar el total también por el tipo de cambio**, para neutralizar la
  revaluación.
- **B — Usar la serie en pesos (117) como titular** y publicar la cartera en
  moneda extranjera como desglose.

## Decisión

**Opción B.** El titular pasa a la variable **117** (`ML`, sólo pesos), que tiene
la misma forma que la anterior —saldos diarios, millones de ARS— así que la
mecánica del colector y de la serie no cambia.

La cartera en moneda extranjera se publica dentro de la card, en **sus dos
unidades**: en dólares (variable 125), que es donde se ve si creció de verdad, y
valuada en pesos (variable 126), que es donde se ve el efecto cambiario. Se
publica también el total, para que quien venga de la serie anterior encuentre su
número y entienda la diferencia.

La opción A necesita elegir un tipo de cambio y defenderlo, y termina
construyendo un agregado sintético que no publica nadie. La 117 es una serie
oficial, con su propia historia desde 2002.

### Consecuencias

- El indicador pasa de **+2,5% a −1,5% real**: cambia de signo. En la escala del
  ITCM eso lo mueve del tramo «0–8 → 45» al de «−10 a 0 → 25», así que **sube la
  tensión del cinturón macro**.
- La serie histórica se reconstruye con la 117. La 26 y la 117 no son empalmables
  —una incluye un universo que la otra no— así que la serie se rehace entera, no
  se pega.
- La card queda con más números, y a propósito: el lector que quiera el total lo
  tiene, y ahora sabe qué está mirando.

### Confirmación

`tests/test_universos_declarados.py`, con un fixture sintético que es el caso de
aceptación que pidió la auditoría: **un año sin crédito nuevo, con los saldos en
pesos y en dólares quietos y una devaluación del 50%**, con inflación cero.

- el titular da **0% real** — el efecto cambiario no se cuela;
- con esos mismos saldos, el total da +16,7%, que es lo que publicaba antes (y el
  test lo verifica, para que el fixture no pueda perder la devaluación);
- la cartera en dólares aparece en el desglose: 0% en dólares, +50% en pesos;
- la unidad dice «en pesos» y la fuente nombra la variable 117, no la 26;
- card y serie leen la misma variable.

Probado rompiéndolo: repuesta la variable 26 como titular, fallan dos guardas,
incluida la de aceptación.

## Pros y contras de las opciones

### A — Deflactar también por el tipo de cambio

- Bueno, porque conserva el universo completo.
- Malo, porque obliga a elegir un tipo de cambio y a defenderlo, y produce un
  agregado que no publica ninguna fuente.

### B — Titular en pesos, dólares como desglose

- Bueno, porque las dos series son oficiales y cada una se lee en su moneda.
- Bueno, porque el criterio de aceptación es verificable: una devaluación sin
  préstamos nuevos da cero.
- Malo, porque parte la serie histórica publicada: la 26 y la 117 no se empalman.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_macro.md`.
- [[0022-credito-real-y-contexto-oculto]] define el indicador y su rol frente al
  IdC, que este ADR no toca.
