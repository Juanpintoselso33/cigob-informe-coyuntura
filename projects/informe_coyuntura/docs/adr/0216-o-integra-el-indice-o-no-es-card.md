---
madr: 4
id: '0216'
estado: 'aceptado'
fecha: 2026-08-20
cinturon: 'vida'
indicadores: [consumo_carnes_total, consumo_carne]
archivos: ['scripts/publicar.py', 'tests/test_carne_dos_fuentes.py']
extiende: ['0153']
relacionado: ['0119', '0223', '0224']
cerrado_por: ['0217']
ambito: 'ITCIS · qué se publica como card · Componente B de proteína animal'
origen: 'Editor, agosto de 2026: "no se pueden mostrar indicadores como cards que no integran el índice"'
---

# ADR-0216 — O integra el índice, o no es card

## Contexto y planteo del problema

[[0153-pobreza-entra-al-itvc-y-no-hay-cards-de-contexto]] eliminó la categoría
"card de contexto" y dejó la regla: **o el indicador entra al índice, o no se
publica como card** — se releva, su serie se publica, y no ocupa un lugar en la
vidriera. `itvc.INDICADORES_CONTEXTO` quedó vacía con un guard.

`consumo_carnes_total` la violaba desde el 12 de agosto de 2026. Se publicaba
como card, no puntuaba, y no estaba en `VIDA_OCULTOS`: caía en el `else` de
`publicar.py` que le pone la nota *"Indicador de contexto — no integra el
ITCIS"*. O sea, exactamente la categoría dada de baja, resucitada por omisión.

No es un detalle de vidriera. Una card sin color y sin peso al lado de quince
que sí puntúan enseña al lector que hay dos clases de indicador, cuando la
decisión del proyecto es que hay una sola.

## Factores de decisión

- **La regla ya estaba tomada.** Esto no la revisa: la aplica a un caso que se
  le escapó.
- **El dato del total no puede perderse**: es lo que distingue sustitución de
  empobrecimiento, que es todo el aporte de la ficha de proteína animal.
- **Sacarlo antes de tiempo rompe la explicación.** La matriz A×B lee el total
  dentro de `_semaforos()` para escribir el `por_que` de la carne.

## Opciones consideradas

1. Sacarlo de las cards después de calcular los semáforos.
2. Meterlo a `VIDA_OCULTOS`.
3. Hacerlo puntuar con peso propio.
4. Dejarlo como card de contexto.

## Decisión

**Opción 1.** `consumo_carnes_total` deja de publicarse como card. Su serie se
sigue publicando y su dato se sigue leyendo **dentro de la card de carne**, en
la matriz A×B que explica el color — que es el único lugar donde significa algo.

El descarte va **después** de `_semaforos()`, no en `VIDA_OCULTOS`: los ocultos
se aplican antes, y sacarlo ahí deja a la carne sin su explicación **sin que
nada falle en voz alta**. Verificado: al hacerlo en el lugar equivocado, el
campo `semaforo.por_que` quedó vacío y el gate pasó igual.

La opción 3 se descarta acá por una razón acotada —el peso del compuesto es
3,02% y no hay nada que repartir— pero el fondo del asunto queda abierto abajo.

### Consecuencias

- El cinturón publica **16 cards y las 16 puntúan**. No hay ninguna en el limbo.
- La regla de ADR-0153 vuelve a valer sin excepciones en este cinturón.
- El lector pierde el número del total como card y lo conserva como
  explicación. Es un cambio de lugar, no una pérdida.

### El problema de fondo, que esto NO arregla

Ordenar la vidriera dejó a la vista algo peor: **el indicador que puntúa es la
carne vacuna sola.**

La ficha de proteína animal existe porque leer la caída de la vacuna como
pérdida de poder adquisitivo es un falso positivo: buena parte es sustitución
hacia pollo y cerdo. Para desarmar eso propuso un indicador **compuesto** —A
vacuna, B total, C ratio— tratados, en sus palabras, como *"un único indicador
compuesto"*.

Se implementó la explicación y no el compuesto:

| | Hoy |
|---|---|
| Puntúa | la vacuna sola, 89,3 rebaseado, 3,02% del índice |
| El total | se releva, no entra al cálculo |
| El ratio | no existe como número; vive dentro del texto del color |

Y la decisión del 12 de agosto —*"no hay nada que repartir, el compuesto
conserva el 3,02%"*— da por hecho un compuesto que no existe. El resultado es
que se suman cerdo y pollo para nada: el número que mueve el índice sigue
mirando una sola carne.

**Lo que corresponde es que puntúe el acceso total a proteína cárnica**, no la
vacuna. El bloqueo era de datos: el tablero de SAGYP es una foto mensual y no
tiene historia contra la cual rebasear al 4T-2023 (ver
[[0215-la-carne-se-mide-con-dos-fuentes-y-se-declara]]).

Ese bloqueo se levantó. INDEC publica las tres faenas mensuales en toneladas,
verificado el 2026-08-20 contra su API:

| Serie | id | Desde |
|---|---|---|
| Faena pecuaria, vacunos | `40.3_VT_0_M_17` | 1998-01 |
| Faena pecuaria, porcinos | `40.3_PT_0_M_18` | 2006-01 |
| Faena pecuaria, aves | `40.3_AT_0_M_14` | 1991-01 |

Las tres llegan a 2026-06. Con eso se reconstruye la serie del total —promedio
móvil de 12 meses, corregida por crecimiento de población— hasta el 4T-2023 y
más atrás, y el compuesto puede puntuar. Queda como el trabajo siguiente, con
su propio ADR: mueve el puntaje del componente y cambia qué mide una card.

### Confirmación

`tests/test_carne_dos_fuentes.py` verifica las tres cosas: que el total no
vuelva a publicarse como card, que su serie se siga publicando, y que la matriz
A×B siga escribiendo el `por_que` de la carne — que es el guard que faltaba
cuando el descarte se hizo en el lugar equivocado.

## Pros y contras de las opciones

**1. Sacarlo después de los semáforos.** A favor: cumple la regla sin perder el
dato ni la explicación. En contra: el descarte queda en un punto del pipeline
que hay que explicar, y por eso está comentado en el código.

**2. `VIDA_OCULTOS`.** A favor: es el mecanismo previsto para esto. En contra:
se aplica antes de los semáforos y rompe la matriz en silencio. Probado.

**3. Que puntúe con peso propio.** A favor: sería una card legítima. En contra:
duplicaría el peso de "carne" dentro del cinturón, que es lo que la propia
ficha pide evitar. El camino correcto no es sumarle peso al total: es que el
compuesto reemplace a la vacuna como lo que puntúa.

**4. Dejarlo.** A favor: ninguno. En contra: es la categoría que ADR-0153 dio
de baja, publicada igual.

## Más información

- [[0119-pendientes-de-baja-prioridad-vida]] midió que la vacuna sigue al total
  con r=0,970 en niveles y r=0,987 en cambios, y por eso decidió no cambiar el
  indicador. Ese argumento sostiene la **dirección**, no el **nivel**: la propia
  medición dice que la vacuna sola exagera el deterioro en unos 7 puntos.
