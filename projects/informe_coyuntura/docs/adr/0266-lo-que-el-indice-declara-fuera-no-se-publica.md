---
madr: 4
id: '0266'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'transversal'
archivos: ['scripts/publicar.py', 'tests/test_ocultos_derivan_de_la_fuente.py']
relacionado: ['0216', '0153', '0022', '0245']
ambito: 'Publicación · los cuatro cinturones · de dónde sale la lista de indicadores que no se publican como card'
origen: 'Descubierto el 25-ago-2026 al sacar `idm` e `icip` del ITCM: la lista de macro era un literal y la baja no los habría ocultado'
---

# ADR-0266 — Lo que el índice declara fuera no se publica

## Contexto y planteo del problema

`publicar.py` decide qué indicadores **no** se publican como card, con un
conjunto por cinturón. Tres de los cuatro lo **derivaban** de las listas que
declara el módulo del índice:

```python
POLITICA_OCULTOS = set(itcp.INDICADORES_CONTEXTO) | set(itcp.INDICADORES_SUSPENDIDOS)
GESTION_OCULTOS  = set(itcg.INDICADORES_CONTEXTO) | … CUMPLIDOS | … SUSPENDIDOS
VIDA_OCULTOS     = {...} | set(itvc.INDICADORES_SUSPENDIDOS)
```

Y macro **repetía la lista como literal**:

```python
MACRO_OCULTOS = {"badlar", "prestamos_privados", "base_monetaria", "tc_mayorista"}
```

Los cuatro nombres coincidían con `itcm.INDICADORES_CONTEXTO`, así que la copia
no hacía daño **mientras nadie agregara nada a esa lista**.

El 25 de agosto de 2026 alguien agregó algo: `idm` e `icip` salieron del ITCM y
se anotaron en `itcm.INDICADORES_CONTEXTO`. Con el literal, esa anotación **no
los habría ocultado**. Los dos habrían seguido publicándose como card, sin
puntaje y sin peso, cayendo en el `else` de `_scoring_indice` que les pone la
nota de contexto — con el mismo aspecto que un indicador vigente.

Eso es exactamente lo que ADR-0153 dio de baja y ADR-0216 tuvo que volver a
aplicar: **o integra el índice, o no es card**. `CLAUDE.md` la lista entre las
reglas que «se rompen solas», y el motivo es este: la card no vuelve porque
alguien la reponga, vuelve **por omisión**.

## Factores de decisión

- **Una sola fuente de verdad** por cinturón sobre qué no puntúa.
- **Que la próxima baja no dependa de acordarse de dos lugares.**
- **Que la guarda sea genérica**: una que nombrara `idm` e `icip` habría que
  extenderla en la próxima baja, que es justo lo que no pasa.

## Opciones consideradas

1. **Agregar `idm` e `icip` al literal** de macro.
2. **Derivar `MACRO_OCULTOS`** de `itcm.INDICADORES_CONTEXTO`, como los otros
   tres, y agregar una guarda que exija esa derivación en los cuatro.

## Decisión

**Opción 2.** `MACRO_OCULTOS = set(itcm.INDICADORES_CONTEXTO)`, y
`tests/test_ocultos_derivan_de_la_fuente.py` verifica, para los **cuatro**
cinturones, que todo lo que el módulo del índice declara fuera esté oculto, y
que nada oculto conserve peso vigente.

La opción 1 arreglaba el caso y dejaba la trampa armada para el siguiente. Es
la reparación que ya se hizo dos veces con este mismo error.

### Consecuencias

- Sacar un indicador del score y anotarlo en la lista del módulo **ahora
  alcanza** para que desaparezca de la web. Antes, en macro, eran dos pasos y
  el segundo no estaba escrito en ningún lado.
- La guarda no exige la recíproca —que todo lo oculto esté declarado—, porque
  `VIDA_OCULTOS` y `MACRO_OCULTOS` esconden además insumos que **nunca**
  puntuaron (`indice_lider`, `endeudamiento_familiar`) y que no tienen por qué
  figurar en una lista de bajas.
- La segunda guarda se mide contra los **pesos vigentes**
  (`parametrica.indicadores_vigentes`) y no contra la tabla `DIMENSIONES_*`:
  ADR-0245 conserva a propósito el peso y la banda de un suspendido, así que
  mirar la tabla cruda marcaría a los cuatro suspendidos de hoy como intrusos.

### Confirmación

`tests/test_ocultos_derivan_de_la_fuente.py`, nueve casos. Probado
rompiéndolo: reponer el literal de macro falla un test; sacarle los suspendidos
a política, otro.

**Una tercera mutación no falló y queda declarado**: sacar
`INDICADORES_CUMPLIDOS` de la derivación de gestión no rompe nada, porque esa
lista está **vacía** en los cuatro cinturones. La rama existe para el día que
vuelva a poblarse; hoy no está probada contra datos reales y el test lo dice.

## Pros y contras de las opciones

### 1 · Agregar los dos nombres al literal

- Bueno: una línea.
- Malo: dejaba dos fuentes de verdad y la misma trampa para la próxima baja.

### 2 · Derivar y vigilar *(elegida)*

- Bueno: una fuente por cinturón, y la guarda cubre a los cuatro sin que haya
  que extenderla.
- Malo: acopla `publicar.py` a la forma de los módulos de índice. Ya estaba
  acoplado en tres de los cuatro; esto lo completa en vez de agregarlo.

## Más información

El literal venía de ADR-0022, que fue el primero en ocultar contexto y es
anterior a que existieran `INDICADORES_CONTEXTO` como concepto compartido. Los
otros tres cinturones se escribieron después y ya nacieron derivando. Macro
quedó como el resto de una convención vieja que nadie volvió a mirar porque
nunca había fallado.
