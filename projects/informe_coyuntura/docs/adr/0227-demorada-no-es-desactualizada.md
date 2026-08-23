---
madr: 4
id: '0227'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'transversal'
archivos: ['scripts/gate_calidad.py', 'tests/test_gate_no_afirma_lo_que_el_snapshot_no_cumple.py', '.github/workflows/data-pipeline.yml']
continua: ['0133']
relacionado: ['0191', '0210', '0220', '0231', '0234']
ambito: 'Gate G2 · flag `desactualizado` · el resumen que imprime el gate'
origen: 'El gate decía que marcaba los indicadores demorados y no marcaba ninguno'
---

# ADR-0227 — «Demorada» no es «desactualizada»

## Contexto y planteo del problema

`gate_calidad.py` cerraba toda corrida con demoras así:

    → 2 fuente(s) demorada(s), ninguna falla de integridad. El snapshot SE
      PUBLICA: los indicadores atrasados van marcados como desactualizados.

**Y no los marcaba.** El 21-ago-2026 reportó `macro/icip` (142 días) y
`vida_cotidiana/mora_familias` (112 días), y las dos cards salieron publicadas
con `desactualizado: false`. Un tercer caso, `macro/emae_difusion`, había
aparecido en una corrida anterior del mismo día.

No es un bug de datos: el flag estaba bien. Lo que estaba mal era la frase, y
detrás de la frase había **dos conceptos que nadie había separado por escrito**.

### Las dos condiciones

|  | `desactualizado: true` | demora G2 |
|---|---|---|
| **quién lo escribe** | el COLECTOR | lo calcula el gate, en memoria |
| **qué significa** | el fetch falló y estoy sirviendo caché (o es carga manual) | la fuente publica con más rezago que su tope `MAX_DIAS` |
| **el fetch** | falló | anduvo perfecto |
| **el valor publicado** | arrastrado de una corrida anterior | el último que existe |
| **qué estado describe** | el del PIPELINE | el de la FUENTE |

Ninguna implica la otra. El flag lo escriben los colectores en tres formas, y
ninguna es «la fuente publica tarde»:

- **carry-forward tras un fetch fallido** — `{**anterior, "desactualizado":
  True}` (`macro.py:_sellar`, `gestion.py:213`, `vida_cotidiana.py:144`,
  `politica.py:4559`);
- **carga manual** — `gestion.py:_manual_entry`, con el comentario «Manual ⇒
  desactualizado=True (badge honesto)»;
- **antigüedad del EVENTO** en las fuentes esporádicas — el votómetro y la
  conflictividad comparan contra su propio `STALE_*_DAYS`
  (`politica.py:422`, `:895`, `:2197`).

Y hay dos razones estructurales por las que el gate **no puede** hacer cierta esa
frase aunque quisiera: es de **sólo lectura** —no tiene una sola escritura— y
corre **después** de `publicar.py` en `data-pipeline.yml`. Para cuando calcula la
demora, el snapshot ya está escrito.

### Por qué nadie lo vio

La frase era falsa desde que se escribió, en [[0133-una-fuente-demorada-no-tira-abajo-el-pipeline]],
cuyo razonamiento la da por buena textualmente («el indicador **ya queda marcado
`desactualizado`**, `publicar.py` hace carry-forward del último valor bueno y el
tablero lo muestra como viejo»). De ahí se copió al comentario del gate y al de
`data-pipeline.yml`.

Sobrevivió trece meses porque **ningún test miraba la salida del gate**.
`test_gate_bloqueante_vs_demora.py` verifica el código de retorno y la
clasificación; `test_gate_frescura_fetch.py` busca subcadenas de una falla
concreta. Nadie cruzaba lo que el gate *dice* del snapshot contra lo que el
snapshot *tiene*. Es la misma familia que
[[0220-la-ficha-se-ata-al-colector-y-al-adr]] —prosa publicada que afirma algo
que el sistema no hace— del lado del operador en vez del lector.

## Factores de decisión

- La conducta actual es **correcta**: una card demorada con el fetch sano
  publica el último dato que existe, y ése es el dato que corresponde publicar.
  El que miente es el texto.
- La distinción no está escrita en ningún ADR. Peor: ADR-0133 la confunde, así
  que la fuente de verdad que alguien iría a consultar reproduce el error.
- El aviso del gate lo lee un operador a las 3 de la mañana buscando si hay algo
  que hacer. «Ya está marcado» le dice que no hay nada que hacer; la verdad
  —«el organismo todavía no publicó»— también, pero por el motivo correcto.
- Una frase que *afirma* algo del snapshot se rompe otra vez. Una línea
  *derivada* del snapshot no puede divergir de él.

## Opciones consideradas

- **Corregir el mensaje para que el resumen lea el estado real de cada card
  demorada** — elegida.
- **Corregir el mensaje por otra afirmación universal más prudente** (p. ej.
  «las demoradas NO encienden el flag») — descartada: sigue siendo un universal
  que el snapshot puede no cumplir. Una card puede estar demorada **y** en
  carry-forward al mismo tiempo, y entonces la frase nueva volvería a mentir.
- **Implementar lo que la frase prometía**: que una demora G2 encienda
  `desactualizado` y el lector vea una marca de «dato viejo» — descartada, y no
  por costo. Rompe la semántica del flag y **empeora la web**: ver abajo.
- **Dejarlo como está y anotar el matiz en un comentario** — descartada: la
  distinción no estaba escrita en ningún lado y el ADR que se consultaría la
  tiene mal. Un comentario no corrige a ADR-0133.

## Decisión

### 1. Las dos condiciones quedan separadas por escrito

La tabla de arriba es la definición canónica. **Corrige el razonamiento de
ADR-0133**, cuya decisión operativa —que una demora no bloquee la publicación—
sigue vigente y no cambia: cambia el motivo por el que es correcta. No es que el
indicador quede marcado, es que **el dato publicado es el último que existe**.

### 2. El resumen del gate deriva en vez de afirmar

`gate_calidad.py` guarda `(nombre, rezago, tope, fecha_dato, desactualizado)` de
cada card que G2 reporta demorada, leyendo el flag del snapshot, y el resumen
imprime una línea por card:

    → 2 fuente(s) demorada(s), ninguna falla de integridad. El snapshot SE PUBLICA.
      2 card(s) con la fuente demorada. «Demorada» es que el organismo todavía no
      publicó nada más nuevo, NO que el fetch haya fallado: eso es `desactualizado`,
      lo escribe el colector y lo vigila G2b. Son cosas distintas y el estado del
      flag va abajo, leído del snapshot:
        · macro/icip: 2026-04-01, 142d contra un tope de 140d · desactualizado=false
          — publica el último dato que existe, no un valor arrastrado
        · vida_cotidiana/mora_familias: 2026-05, 112d contra un tope de 110d ·
          desactualizado=false — publica el último dato que existe, no un valor arrastrado

El caso mixto —demorada y además en caché— se imprime con `desactualizado=true`
y remite a G2b, que es quien lo vigila.

El mismo texto falso se corrigió en el comentario de `data-pipeline.yml`.

### Consecuencias

- El log nombra las fuentes demoradas con su rezago contra su tope, que antes
  había que ir a buscar a las líneas `[DEMORA]` de arriba.
- El resumen se alarga. Es a propósito: el mensaje corto era el que mentía.
- Nada cambia en el snapshot, en la web ni en el comportamiento de publicación.
  Ninguna corrida cambia de resultado.

### Confirmación

`tests/test_gate_no_afirma_lo_que_el_snapshot_no_cumple.py`, en dos capas:

- **A — lo derivado no puede divergir.** Cada campo de cada línea del resumen se
  re-deriva del `informe.json`: `fecha_dato` textual, rezago recalculado contra
  `date.today()`, tope contra `MAX_DIAS`, y el flag contra el del snapshot.
  Además cruza en los dos sentidos que ninguna demora reportada sea falsa y que
  ninguna demora real se calle.
- **B — una afirmación universal obliga al hecho.** Si la salida del gate vuelve
  a decir que las cards demoradas *están marcadas* como desactualizadas,
  entonces todas tienen que estarlo. No prohíbe la frase: la ata. Es la capa que
  habría agarrado el bug original, y si algún día el comportamiento cambia y las
  demoras sí encienden el flag, el test pasa solo sin tocarlo.

Probado rompiéndolo, con `__pycache__` borrado entre mutaciones:

| mutación | resultado |
|---|---|
| vuelve la frase original textual | **falla** (capa B) |
| el flag se cablea en `false` en vez de leerse | **falla** (capa A) |
| el rezago impreso se corre 3 días del real | **falla** (capa A) |
| el gate deja de reportar una demora real | **falla** (completitud) |

Los tres snapshots sintéticos cubren la card demorada con el fetch sano (el caso
del 21-ago), la demorada que además está en caché, y la que no está demorada.

## Más información

### La opción que se descartó, y por qué empeoraría la web

Valía preguntarse si la frase describía una intención correcta que nunca se
implementó: que el lector vea una marca de «dato viejo» en una card de 142 días.
La respuesta es que no, porque **la capa de display no usa `desactualizado` para
decir «dato viejo» sino para decir de dónde salió el dato**:

- `web/src/lib/datos.ts:627` — `badgeEstado()`: `if (ind.desactualizado) return
  "Carga manual"`.
- `web/src/lib/datos.ts:326` — `bucketDeIndicador()`: `if (ind.desactualizado)
  return "manual"`, y `indicadoresOrdenados()` manda ese bucket al fondo.
- `web/src/components/IndicadorTile.astro:26` — `const chip = badge ===
  "Automático" ? periodoDato(ikey, ind) : badge;`

Encender el flag en `icip` haría que su card diga **«Carga manual»** —falso: es
automática y se bajó esa mañana— y, por esa última línea, **reemplazaría el chip
que hoy muestra «abr 2026»** por ese rótulo. O sea: la marca de dato viejo se
implementaría destruyendo la única marca de dato viejo que hay.

### Qué ve hoy el lector de un dato de 142 días

- **El chip de la card muestra el período del dato** (`periodoDato`): «abr 2026»
  para `icip`, «may 2026» para `mora_familias`. El dato viejo se ve; hay que
  restarlo mentalmente contra la fecha de hoy.
- **El hero cuenta los rezagados** —«N indicadores con rezago declarado»
  (`indicadoresRezagados`)—, pero cuenta `desactualizado`, así que **no incluye
  a las cards demoradas**. Hoy dice 1 (`judicializacion`) mientras hay 2 cards
  con la fuente atrasada. No es falso —el rótulo dice «declarado»— pero tampoco
  es lo que un lector entendería.
- **No hay ningún realce cuando el período se pasó del tope de su propia
  fuente.** El lector puede ver que un dato es de abril; no puede ver que abril
  es más viejo de lo que esa fuente suele estar.

Eso último es una mejora de display posible y **queda sin hacer a propósito**:
es una decisión editorial (¿se realza?, ¿con qué umbral?, ¿el tope técnico
`MAX_DIAS` es el umbral que le sirve al lector?) y no se toma desde el gate. Va
anotada acá para que exista, no como pendiente comprometido.

### Limitaciones de la guarda

- La capa B es una regex sobre prosa: reconoce la familia
  «demorada/atrasada … marcada … desactualizada». Alguien puede escribir la
  misma mentira con otras palabras y pasar. La capa A no tiene esa debilidad
  —es aritmética contra el JSON— pero sólo cubre las líneas derivadas.
- El resto de la salida del gate no está cubierto. Este archivo audita el
  resumen de las demoras, no los mensajes de G1, G3, G6, G7 ni G8.
