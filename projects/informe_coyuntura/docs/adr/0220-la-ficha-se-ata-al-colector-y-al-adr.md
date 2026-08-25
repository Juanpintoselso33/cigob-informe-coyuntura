---
madr: 4
id: '0220'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'transversal'
archivos: ['tests/test_la_ficha_no_se_queda_atras.py', 'tests/test_web_declara_los_pesos_del_itvc.py']
relacionado: ['0217', '0218', '0219', '0222', '0227', '0231', '0234', '0240', '0243']
ambito: 'Verificación · cómo se evita que la prosa publicada describa un indicador que ya cambió'
origen: 'Editor, 21-ago-2026: «¿cómo podemos hacer que esto no vuelva a pasar? sí o sí»'
---

# ADR-0220 — La ficha se ata al colector y al ADR

## Contexto y planteo del problema

Tres decisiones de agosto —[[0217-puntua-el-acceso-total-a-proteina-no-la-vacuna]],
[[0218-el-cierre-de-pymes-se-mide-con-la-srt]] y
[[0219-la-contracara-del-cierre-el-trabajo-independiente]]— cambiaron qué mide un
indicador, y **el texto que lo describe se quedó donde estaba**. Lo que quedó
publicado durante días:

- La ficha técnica de `mortalidad_pymes` describía **entera** una fuente que el
  indicador ya no usaba: organismo, serie, transformaciones, limitaciones y
  rezago, todo del IPI manufacturero del INDEC, mientras el colector bajaba el
  XLSX de la SRT.
- `trabajo_independiente` puntuaba con 2,42% del ITCIS **sin ficha**: la web lo
  mostraba y no había a dónde ir a leer qué mide ni qué no cubre.
- La ficha del índice declaraba el reparto entre dimensiones anterior a
  ADR-0214 —"37% ingresos · 25% precios · 15% empleo"—, o sea cuatro de seis
  pesos mal en el párrafo que explica cómo se agrega el ITCIS, y se contaba de
  dos maneras distintas, las dos equivocadas.

El problema no es que faltara una guarda. Es **de qué forma son las guardas que
había**: todas nacieron de un incidente y todas cruzan *una frase concreta
contra un número concreto* —el peso, la dimensión, el «no puntúa»—. Cubren el
campo que alguien ya se acordó de mirar. Nadie iba a escribir a mano la guarda
del campo `fuente.organismo` antes de que ese campo se rompiera, y la siguiente
va a romperse en un campo que hoy tampoco estamos mirando.

Peor: al ir a extenderlas apareció que **62 de 73 bloques de ficha desbordaban
hasta el final del archivo**. El extractor capturaba la sangría con `\s*`, que
incluye el salto de línea, así que el cierre se buscaba con un patrón que no
existe. Las aserciones de la forma «esta frase tiene que estar en el bloque»
pasaban porque la frase estaba en cualquier otra ficha. Las guardas existían y
no podían fallar.

## Factores de decisión

- **Una guarda por incidente no escala.** Cada una cubre un campo; los campos
  son decenas y crecen.
- **La guarda tiene que engancharse al ACTO de cambiar algo**, no sólo comparar
  estado con estado: el estado se compara cuando alguien se acuerda de
  compararlo.
- **Tiene que existir una verdad de campo contra la cual medir.** Una guarda que
  cruza prosa contra prosa no verifica nada.
- **Una guarda que no puede fallar es peor que ninguna**: ocupa el lugar de la
  que sí serviría, y deja la sensación de estar cubierto.

## Opciones consideradas

1. Guardas genéricas sobre todos los indicadores, atadas al snapshot y al ADR.
2. Seguir agregando una guarda por campo a medida que cada uno se rompe.
3. Generar las fichas desde la paramétrica y los colectores, sin prosa a mano.
4. Una lista de verificación en `CLAUDE.md` para barrer al tocar un indicador.

## Decisión

**Opción 1**, en `tests/test_la_ficha_no_se_queda_atras.py`. Tres guardas que se
aplican a **todos** los indicadores a la vez y no hay que acordarse de extender
cuando entra uno nuevo, más la guarda del propio extractor.

**1 · Lo que se publica tiene ficha.** Todo indicador del snapshot —los 66, en
los cuatro cinturones— tiene que tener entrada en `fichas.ts`. Es el hueco por
el que se coló `trabajo_independiente`, y era invisible porque los tests que
cruzan fichas hacen `skip` cuando falta la entrada: la ausencia se leía como
"nada que verificar".

**2 · La ficha declara la fuente que el colector realmente usó.** El snapshot
trae, por indicador, la fuente que escribió el colector en la corrida: es la
verdad de campo, regenerada todas las noches. La ficha declara un organismo a
mano. Se cruzan. Hoy 61 de 66 cruzan por sigla directa; los otros cinco son el
mismo organismo nombrado de dos maneras legítimas ("UTDT" y "Universidad
Torcuato Di Tella") y esa equivalencia se declara en una tabla explícita, más un
caso donde el colector publica la URL de descarga y se compara el host contra el
de la ficha. **Esta guarda hubiera cantado el caso de la SRT en el acto**, sin
que nadie tuviera que preverlo.

**3 · Un ADR que toca un indicador deja rastro en su ficha.** Es la que importa
a largo plazo: las otras dos comparan estado con estado; ésta engancha al acto.
El ADR ya es el registro canónico de "cambiamos este indicador" y ya nombra los
indicadores en frontmatter legible por máquina. Un ADR aceptado que nombra un
indicador con ficha tiene que dejar en `cambios:` una entrada que lo cite o que
sea de esa fecha o posterior. **No hay nada que recordar**: no se puede aceptar
un ADR que toca un indicador sin contarlo donde el lector lo va a leer.

**Un ADR que sólo toca `tests/` o `.github/` queda exento**: cambió cómo
verificamos el indicador, no cómo se produce. La distinción no es teórica —
[[0221-un-cable-trampa-mira-la-banda-no-el-puntaje]] recalibra el cable trampa de
`litigiosidad_laboral` sin mover un dato, y la guardia disparó contra él a los
cinco minutos de escrita. La salida no fue sacarle el indicador al frontmatter
para que el test callara —eso es acomodar el registro a la herramienta— sino
separar dos cosas que de verdad son distintas. Ante la duda se exige el rastro:
un ADR sin `archivos:` entra igual.

**Rige desde el 21 de agosto de 2026 y no se retrofitea.** El frontmatter
`indicadores:` se usó con criterios distintos a lo largo del proyecto —hay ADRs
que ahí nombran funciones del colector— y aplicarla hacia atrás pedía tocar 88
fichas viejas para que un test pase, que es reescribir el registro histórico
para acomodar la herramienta.

### Consecuencias

- Cambiar la fuente de un indicador sin tocar su ficha **rompe la CI**. Antes se
  publicaba y no lo veía nadie.
- Sumar un indicador al índice sin escribirle la ficha **rompe la CI**.
- Un cambio cosmético en el string de fuente de un colector ahora obliga a pasar
  por la ficha. Es el costo deliberado: ese string es lo que el lector ve.
- Un organismo nuevo puede pedir una línea en la tabla de siglas. Que la
  equivalencia esté escrita y no adivinada es parte de la decisión.
- El extractor de bloques quedó arreglado, y tiene su propia guarda: si vuelve
  a desbordar, el test lo dice en vez de dejar todo en verde.

### Confirmación

Cada guarda se verificó **mutando el repositorio a propósito** y comprobando que
falla: volviendo el extractor a `\s*`, borrando una ficha publicada, cambiando
el organismo de la SRT de vuelta a INDEC, y borrando la entrada de cambios que
ADR-0219 dejó en su ficha. Las cuatro fallaron; con el árbol restaurado, las
cinco pasan. Una guarda que no se probó rompiéndola no se sabe si guarda.

## Pros y contras de las opciones

**1. Guardas genéricas atadas al snapshot y al ADR.** A favor: cubren
indicadores que todavía no existen, se apoyan en artefactos que ya se generan
solos, y la tercera convierte el trámite que ya se hace —escribir el ADR— en el
disparador. En contra: la del organismo necesita una tabla de siglas que hay que
mantener, y la del ADR no puede aplicarse hacia atrás.

**2. Una guarda por campo.** A favor: precisión quirúrgica, cero falsos
positivos. En contra: es lo que veníamos haciendo, y es por definición reactiva
— llega después del incidente, siempre.

**3. Generar las fichas.** A favor: elimina la clase entera de error. En contra:
la ficha vale justamente por lo que no es derivable —las limitaciones, los
supuestos, qué NO mide—; generarla la convertiría en una tabla de metadatos y
perdería su función.

**4. Lista de verificación en CLAUDE.md.** A favor: gratis. En contra: la regla
ya existía —"un indicador tiene que medir lo que su nombre dice"— y se violó de
todos modos, porque un documento no bloquea un merge.

## Más información

- La regla escrita queda en `CLAUDE.md`, en el bloque de reglas del tablero, con
  el mismo criterio: ahí va lo que se lee *antes* de escribir el código.
- Las guardas por campo que ya existían siguen vivas en
  `tests/test_web_declara_los_pesos_del_itvc.py`; éstas no las reemplazan, les
  ponen un piso genérico debajo.
