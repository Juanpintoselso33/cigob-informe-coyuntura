---
madr: 4
id: '0265'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'politica'
indicadores: [apoyo_empresario, judicializacion, sentimiento_digital, reestructuracion_organismos, masa_salarial]
archivos: ['web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'web/src/pages/metodologia/[id].astro', 'tests/test_contrato_publico_dice_lo_que_corre.py']
relacionado: ['0186', '0245', '0246', '0247', '0248', '0255', '0261', '0262']
ambito: 'Capa pública · descripciones de dimensión y fichas de indicadores suspendidos · que ningún texto prometa una vía o un peso que ya no existe'
origen: 'Reauditoría post-cambios, 25-ago-2026: discrepancias 7 y 8 y los «residuos transversales» de composición de dimensiones'
---

# ADR-0265 — Una dimensión no promete vías que ya no puntúan

## Contexto y planteo del problema

Cuatro indicadores se suspendieron en agosto de 2026 —`apoyo_empresario`
(ADR-0246), `judicializacion` (ADR-0255), `sentimiento_digital` (ADR-0248) y
`reestructuracion_organismos` (ADR-0247)—, más `masa_salarial` en ADR-0186. El
mecanismo funcionó como está diseñado: salen del cálculo, liberan su peso y los
que quedan lo absorben (ADR-0245).

Lo que no salió es el texto. Quedaron dos clases de afirmación falsa:

**La composición de la dimensión, contada de más.** «Sector privado» prometía dos
vías cuando queda una; «Poder judicial», cuatro cuando quedan tres; «Percepción»
seguía siendo el ICC más las búsquedas; «Reforma del Estado», tres medidas cuando
puntúan dos. Un lector que quiera reconstruir el índice desde la web reconstruye
otro.

**El peso y la escala del indicador suspendido, en presente.** La ficha de
`apoyo_empresario` decía «pesa la mitad de la dimensión de sector privado (13%
del total)». La de `brecha_obra_publica` decía lo mismo del otro lado —«la otra
mitad es la postura pública de las cámaras empresarias»— cuando hoy es el 100% de
su dimensión. La de `sentimiento_digital` declaraba «18,2% interno · 1,5% del
ITCIS». Y las fichas de `judicializacion`, `reestructuracion_organismos` y
`masa_salarial` publican su tabla de bandas bajo el encabezado «Cómo entra al
índice», precedida de una línea que dice que «el motor los lee como anclas y el
puntaje se interpola»: la tabla es correcta como registro histórico y falsa como
descripción de lo que pasa hoy.

Dos residuos más viejos del mismo tipo aparecieron en el camino:
`derrotas_legislativas`, fuera del índice desde julio de 2026, seguía diciendo
«integra la dimensión de poder legislativo (25% del total), donde pesa 20%»; y
`gobernadores_alineamiento`, retirado en el mismo mes, seguía explicando su
incidencia con el esquema anterior al ITCP («el score del cinturón es el promedio
simple de las tensiones»).

## Factores de decisión

- **Suspender no es borrar la historia**, pero tampoco puede dejar el indicador
  descrito como vigente. Son dos cosas distintas y el texto tiene que decir cuál.
- **El peso de diseño se conserva a propósito** (ADR-0245): la ficha lo tiene que
  publicar como de diseño, no como efectivo.
- **La tabla de bandas de un indicador suspendido sigue siendo útil**: es la
  regla con la que se construyó la serie que se sigue publicando. Sacarla haría
  ilegible el histórico.
- **Ningún gate compara la prosa de una dimensión con su tabla de pesos.**

## Opciones consideradas

- **A — Reescribir los textos y marcar cada escala suspendida como histórica**,
  con una guarda que cuente las vías prometidas contra los indicadores que
  efectivamente puntúan.
- **B — Borrar de la capa pública todo rastro de los indicadores suspendidos.**
- **C — Generar la descripción de cada dimensión desde la tabla de pesos.**

## Decisión

**Opción A.**

- Las cuatro descripciones de dimensión pasan a nombrar sólo las vías que
  puntúan, y a decir en una frase cuál salió, cuándo y por qué. La baja explicada
  es más informativa que la baja silenciosa: un lector que vuelva en seis meses
  entiende por qué la dimensión tiene un componente menos.
- Las fichas de los indicadores suspendidos abren su sección de puntaje con una
  frase que dice que la escala ya no se aplica y que la tabla es histórica, y
  declaran su peso como **de diseño**, nombrando quién lo absorbió.
- La ficha del indicador que **quedó** también se corrige: `brecha_obra_publica`
  pasa a declarar 100% interno · 13% efectivo del ITCP. Es el mismo error del
  otro lado del par y no lo marcó ninguna auditoría.
- La página de ficha metodológica deja de afirmar que el motor interpola cuando
  el indicador no integra ningún índice, y suprime el ejemplo resuelto con el
  dato vigente para esos casos.
- **Y sobre todo: la ficha de un retirado deja de renderizarse vacía.** El
  cuerpo entero de la página estaba condicionado a que el indicador tuviera fila
  en el snapshot, y un retirado no la tiene. La página existía —el enlace desde
  la serie funciona— y mostraba un único callout de «sin dato vigente»: 7,7 kB
  contra los 15,6 de una ficha viva, sin fuente, sin método, sin escala, sin
  limitaciones y sin changelog. Todo lo que este ADR y los cinco que retiran
  indicadores escriben para «conservar la ficha histórica» era invisible. Ahora
  el cuerpo se publica siempre y se ocultan, uno por uno, sólo los bloques que
  leen un campo de la corrida: el valor concreto, el color del semáforo, el
  aporte al índice.

La opción B destruye el registro: la serie se sigue publicando y sin la escala no
se puede leer. La opción C es correcta para la lista de componentes y no para el
resto —una descripción de dimensión dice qué mide, no sólo quiénes la integran—,
así que quedaría un texto generado y otro a mano, con el mismo problema.

### Consecuencias

- **Ningún valor, peso ni banda cambia.** Cambia lo que el texto afirma.
- Quedan alineadas las cuatro dimensiones tocadas: sector privado (una vía),
  poder judicial (tres), percepción (una) y reforma del Estado (dos).
- La ficha del ITCP decía que «tres indicadores retirados conservan ficha
  histórica»; con las dos suspensiones de hoy son cuatro.
- Un indicador que vuelva al índice tiene que sacar estas frases: el texto no
  vuelve solo. Es el costo aceptado de conservar el peso de diseño.

### Confirmación

`tests/test_contrato_publico_dice_lo_que_corre.py`, contra las tablas de
dimensiones de `itcm`/`itcp`/`itcg`/`itvc` y sus listas de suspendidos:

- ninguna descripción de dimensión promete más componentes de los que puntúan:
  se cuentan los numerales en palabras («dos vías», «tres medidas») contra los
  indicadores vivos de esa dimensión;
- ninguna ficha de indicador suspendido afirma en presente que pesa o que
  integra una dimensión;
- toda ficha de indicador suspendido que publica tabla de bandas dice que la
  escala ya no se aplica;
- la ficha del único componente que queda en una dimensión no nombra a un
  compañero suspendido como si siguiera aportando;
- el cuerpo de la ficha metodológica no vuelve a depender de la fila del
  snapshot. Se verifica sobre el código y no sobre el HTML para que la guarda
  corra sin build.

Probado rompiéndolo, una mutación por guarda: repuesto «por cuatro vías» en la
descripción de poder judicial, repuestas «cuatro señales» en estabilidad
monetaria, «pesa la mitad de la dimensión» en la ficha de `apoyo_empresario`, la
escala de `judicializacion` como vigente, un peso efectivo que el índice no
calculó, y el gate contra `ind` en la página de ficha. Las seis fallan, cada una
en su propia guarda.

## Pros y contras de las opciones

### A — Reescribir y marcar como histórico

- Bueno, porque conserva la serie legible y deja dicho el estado real.
- Malo, porque el texto de la baja hay que sacarlo a mano si el indicador vuelve.

### B — Borrar el rastro

- Bueno, porque no puede quedar desactualizado lo que no está.
- Malo, porque la serie histórica queda publicada sin la escala con la que se
  construyó, y la baja deja de ser auditable.

### C — Generar la descripción desde los pesos

- Bueno, porque la lista de componentes no podría divergir.
- Malo, porque una descripción de dimensión dice qué mide y por qué, y eso no
  sale de una tabla de pesos.

## Más información

- Reauditoría post-cambios, 25-ago-2026:
  `docs/auditoria_indicadores/260825_reauditoria_post_cambios_completa.md`.
- [[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]] define el
  mecanismo de suspensión que este ADR termina de hacer visible.
