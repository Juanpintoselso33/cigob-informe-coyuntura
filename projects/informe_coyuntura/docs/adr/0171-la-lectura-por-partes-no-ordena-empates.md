---
madr: 4
id: '0171'
estado: 'aceptado'
fecha: 2026-07-31
cinturon: 'politica'
indice: 'ITCP'
archivos: ['scripts/publicar.py']
continua: ['0094']
relacionado: ['0045', '0160', '0166', '0168']
ambito: 'Cinturón político (ITCP) · card «lectura por partes»'
origen: 'ADR-0168 anotó como limitación que la familia tensión podía moverse por composición; al medirlo, se movió sólo por eso'
---

# ADR-0171 — La lectura por partes no ordena empates

## Contexto y planteo del problema

ADR-0168 dejó anotado que los cuatro indicadores nuevos entraban todos a la
familia `tension` de ADR-0094, y que **parte del movimiento de esa familia
sería composición y no señal**. Medido, no es parte: es todo.

| Familia | Antes | Hoy, sólo miembros viejos | Hoy publicado |
|---|---:|---:|---:|
| Tensión externa | 65,0 (n=7) | **65,0** (n=7) | **63,2** (n=11) |
| Capacidad propia | 59,8 (n=5) | 63,5 | 63,5 |
| Recursos | 74,9 (n=2) | 74,9 | 74,9 |

Los siete miembros previos de `tension` valen hoy exactamente lo mismo que
antes: el aporte de la señal es **0,0** y los −1,8 son íntegramente por los
cuatro que entraron. Además el **peso de la familia saltó de 41% a 52%** del
índice, mientras `capacidad` cayó de 45% a 33%.

El problema concreto es lo que la card estaba **afirmando en texto público**:

> "lo más flojo del cinturón es «tensión externa» (63,2)"

Con `capacidad` en 63,5. **Tres décimas de diferencia**, presentadas como un
hallazgo. Antes de ADR-0168 la brecha era real —65,0 contra 59,8, cinco
puntos— y la frase se sostenía; hoy ordena dos números indistinguibles.

## Factores de decisión

- El guard que ya existía comparaba **el peor contra el mejor**: con 63,2 y
  74,9 la brecha daba 11,7 y pasaba el umbral de 5 puntos. No miraba el empate
  de abajo, que es donde estaba el problema.
- Publicar un ranking construido sobre 0,3 puntos es leer ruido, y es la misma
  familia de error que ADR-0160 evitó al negarse a mover la escala para que un
  número "se viera mejor".
- El reparto entre familias se mueve cuando entran o salen indicadores. Si el
  lector no lo ve, atribuye a la realidad lo que fue un cambio de composición.

## Opciones consideradas

- **No nombrar un "más flojo" cuando las dos peores están empatadas, y declarar
  cuánto del índice carga cada familia** — elegida.
- **Rebalancear los pesos para que las familias vuelvan a repartos parecidos** —
  descartada: mover pesos para que una lectura quede prolija es exactamente lo
  que ADR-0045 prohíbe.
- **Dejarlo y anotar la limitación** — descartada: la limitación ya estaba
  anotada en ADR-0168 y aun así se publicó la afirmación.

## Decisión

### 1. Si las dos familias más flojas están dentro de 2 puntos, no se ordenan

La card las nombra a las dos como empatadas en lugar de coronar a una. El umbral
de 2 puntos es deliberadamente grosero: la escala es un puntaje interpolado
entre anclas y una diferencia menor no distingue estados del mundo.

### 2. El subtítulo declara que el reparto entre familias se mueve

Cada familia ya publicaba su `share`; ahora el texto dice que ese reparto cambia
cuando entran o salen indicadores y que explica parte de lo que se mueve entre
lecturas. Es el mismo criterio con el que ADR-0137 obliga a publicar el `n` de
la ventana junto al porcentaje.

### Consecuencias

- El texto publicado pasa a decir: *"las dos partes más flojas del cinturón
  —«tensión externa» (63,2) y «capacidad propia» (63,5)— están hoy empatadas"*.
- No cambia ningún puntaje ni ningún peso. Es un cambio de qué se afirma.

### Confirmación

`tests/test_publicar.py::test_familias_no_ordenan_empates` verifica que, cuando
las dos familias más flojas están dentro de 2 puntos, la conclusión no corone a
ninguna.

## Más información

### Limitaciones

- El umbral de 2 puntos es una convención, no una medida de error. No hay
  intervalo de confianza sobre estos puntajes que permita derivarlo; se eligió
  grosero a propósito, para errar del lado de no afirmar.
- La composición de las familias va a seguir moviéndose cada vez que entre o
  salga un indicador. Este ADR hace que la card no mienta cuando eso pasa; no
  evita que el lector que compara dos lecturas separadas en el tiempo atribuya a
  la realidad un cambio de reparto. Publicar la serie histórica de cada familia
  resolvería eso y no está hecho.
