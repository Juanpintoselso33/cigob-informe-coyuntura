---
madr: 4
id: '0245'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'transversal'
archivos: ['scripts/parametrica.py', 'scripts/itcp.py', 'scripts/itcg.py', 'scripts/itvc.py', 'tests/test_suspension_libera_el_peso.py']
relacionado: ['0186', '0189', '0246', '0247', '0248']
ambito: 'Transversal · qué le pasa al peso de un indicador cuando se lo saca del score'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «Un indicador suspendido libera su peso y los restantes se renormalizan automáticamente dentro de su dimensión. No asignar pesos nuevos a mano para preservar el score anterior»'
---

# ADR-0245 — Suspender libera el peso, y el índice renormaliza solo

## Contexto y planteo del problema

La Entrega 2 de la remediación saca tres indicadores del score a la vez
—[[0246-el-saldo-empresario-se-calculaba-sobre-un-corpus-abierto]],
[[0247-un-porcentaje-entre-normas-y-una-meta-documental]] y
[[0248-el-volumen-de-busquedas-no-tiene-valencia]]—. El riesgo de una suspensión
no está en el indicador que sale: está en qué pasa con su peso.

Hay dos formas de hacerlo mal, y las dos dejan el índice pareciendo sano:

1. **Reasignar pesos a mano** para que el índice quede donde estaba. Eso no es
   una suspensión, es una recalibración disfrazada de una.
2. **Borrar el indicador de la tabla de pesos** y reescribir los de sus pares.
   Es lo que se hizo en agosto de 2026 con `masa_salarial`
   ([[0186-masa-salarial-sale-del-itcg]]): los tres que quedaban en Reforma del
   Estado pasaron de 35/25/20 a 43,75/31,25/25. Funciona y conserva la
   proporción, pero tiene dos costos. Los pesos renormalizados quedan escritos
   **como si fueran de diseño**, así que seis meses después nadie distingue un
   peso elegido de uno derivado. Y reponer el indicador obliga a recalcular de
   memoria los originales.

Con tres suspensiones simultáneas, la opción 2 significaba reescribir a mano
los pesos de tres dimensiones en tres módulos distintos. Es mucha superficie
para un error que ninguna guarda mira.

Lo que hizo evidente la salida: **el motor ya sabía hacer esto**. `calcular_indice`
renormaliza dentro de la dimensión cada vez que un indicador no tiene dato. Un
indicador suspendido es, para el cálculo, exactamente eso.

## Factores de decisión

- **El peso de diseño tiene que seguir visible.** Es lo que distingue una
  suspensión de una baja.
- **Reponer el indicador tiene que ser trivial**, o la suspensión se vuelve
  permanente por inercia.
- **El reparto tiene que ser proporcional y mecánico**: nadie elige a quién
  darle el peso liberado.
- **El peso liberado se queda en su dimensión.** Derramarlo hacia afuera
  cambiaría el reparto editorial entre dimensiones, que es otra decisión.

## Opciones consideradas

- **A — Reescribir los pesos de la dimensión**, como en ADR-0186.
- **B — Sacar el indicador del CÁLCULO** y dejar la tabla intacta, apoyándose en
  la renormalización que el motor ya hace ante faltantes.

## Decisión

**Opción B.** Cada índice declara `INDICADORES_SUSPENDIDOS` —dimensión, desde
cuándo, por qué y **condición de reingreso**— y su punto de entrada filtra esas
claves antes de calcular, con `parametrica.sin_suspendidos()`. La tabla de pesos
no se toca.

Un indicador suspendido, además, **no se muestra**: se suma a los ocultos del
cinturón. Es la regla del tablero, cerrada tres veces
([[0051-gestion-contexto-oculto]], [[0153-pobreza-entra-al-itvc-y-no-hay-cards-de-contexto]],
[[0189-si-no-puntua-no-se-muestra]]) y vale también acá. El handoff de la
auditoría pedía conservar «una card de contexto claramente marcada *no integra
el índice*»; eso reabriría una excepción que el proyecto ya cerró dos veces,
porque una card sin semáforo se lee como componente igual. El valor informativo
del indicador sobrevive donde corresponde: en su serie, que se sigue publicando,
y en el motivo documentado en la constante y en la ficha.

`masa_salarial` queda como está —ya está fuera de la tabla— y su entrada en
`INDICADORES_SUSPENDIDOS` sigue sirviendo para documentar el motivo. No se
reescribe hacia atrás: sería tocar pesos publicados sin necesidad.

### Consecuencias

- Suspender es agregar una entrada; reponer, sacarla. Los pesos de diseño no se
  tocan en ninguno de los dos casos.
- Los pares absorben el hueco en proporción exacta a sus pesos relativos.
- El reparto entre dimensiones no se mueve.
- La reconstrucción histórica de `validacion_externa` usa el mismo punto de
  entrada, así que la serie del índice queda homogénea con la card: no hay un
  camino que puntúe el suspendido y otro que no.
- **Aparece un efecto de segundo orden que conviene no perder de vista.** El
  test del piso de cobertura afirmaba que un mes incompleto siempre da **por
  debajo** del valor real, y era cierto en los 31 meses de la serie. Dejó de
  serlo al suspender `reestructuracion_organismos`: era el único componente de
  Reforma del Estado que llegaba temprano, y puntuaba bajo. Sin él, la dimensión
  entera desaparece del subconjunto rápido y lo que queda puntúa alto. El piso
  sigue justificado —el desvío es grande y sistemático, con mediana de ~10
  puntos— pero **el signo dependía de una composición que cambió**, y el test
  ahora afirma lo que es estable en vez de lo que era cierto en agosto.

### Confirmación

`tests/test_suspension_libera_el_peso.py`, contra los tres casos reales:

- cada suspendido declara dimensión, fecha, motivo y **condición de reingreso**;
- no puntúa ni pesa, y **no se muestra como card**;
- su peso de diseño sigue en la tabla;
- los pesos de la dimensión suman 1, y los efectivos del cinturón también;
- los pares absorben el hueco **en proporción**;
- la renormalización **no toca las otras dimensiones**;
- el índice es el promedio ponderado de los que quedan, rehecho a mano;
- **sacar la suspensión devuelve el reparto original**, que es la prueba de que
  no se reasignó nada.

Probado rompiéndolo de las dos formas: si el filtro no saca al suspendido, o si
la renormalización deja de dividir por la suma, fallan seis y siete guardas.

## Pros y contras de las opciones

### A — Reescribir los pesos de la dimensión

- Bueno, porque el archivo de pesos dice exactamente lo que se usa.
- Malo, porque el peso de diseño se pierde y reponer obliga a reconstruirlo.
- Malo, porque con tres suspensiones son tres dimensiones editadas a mano en
  tres módulos, sin ninguna guarda que compare el resultado con la proporción
  original.

### B — Sacarlo del cálculo

- Bueno, porque reutiliza la renormalización que ya existía y estaba probada.
- Bueno, porque la suspensión es una línea y es reversible.
- Malo, porque la tabla de pesos ya no se lee sola: hay que mirar también la
  lista de suspendidos para saber qué pesa qué. Lo compensa que los pesos
  vigentes se publican en cada card (`peso_efectivo`) y en la ficha.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_handoff_claude_remediacion_17_discrepancias.md`,
  Entrega 2.
