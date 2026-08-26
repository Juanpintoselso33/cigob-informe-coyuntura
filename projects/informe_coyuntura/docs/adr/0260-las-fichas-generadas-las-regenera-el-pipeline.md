---
madr: 4
id: '0260'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'transversal'
indicadores: [consumo_supermercados, desequilibrio_monetario]
archivos: ['.github/workflows/data-pipeline.yml', 'scripts/fichas/generar.py', 'scripts/fichas/comun.py', 'scripts/fichas/verificar.py', 'scripts/fichas/README.md', 'tests/test_fichas_generadas_al_dia.py', 'output/fichas/']
relacionado: ['0220', '0256', '0257']
ambito: 'Artefacto `output/fichas/*.md` · quién lo regenera y qué lo verifica'
origen: 'Discrepancia 10 de la reauditoría del 25-ago-2026: la ficha del supermercado publicaba mayo (83,2) mientras la card, la serie y el colector publicaban junio (82,1)'
---

# ADR-0260 — Las fichas generadas las regenera el pipeline

## Contexto y planteo del problema

`output/fichas/*.md` son las fichas metodológicas de cada cinturón: una por
indicador, más una portada con el índice, las dimensiones y la tabla de todos
los indicadores con su valor, su color y su peso. Las escribe
`scripts/fichas/generar.py` leyendo `web/src/data/informe.json`, o sea el mismo
snapshot que alimenta la web.

**Ese script no estaba en `.github/workflows/data-pipeline.yml`.** El snapshot
se regeneraba todas las noches y las fichas se quedaban donde las hubiera
dejado la última persona que se acordó de correrlo a mano. Nada las comparaba
con nada, así que la deriva no rompía ninguna corrida: se publicaba.

La reauditoría del 25 de agosto de 2026 lo encontró en `consumo_supermercados`:
la ficha decía **mayo de 2026 = 83,2** —índice base-100 91,2— mientras la card,
la serie y el colector ya publicaban **junio = 82,1**, índice 90,1 (ADR-0256).
La ficha *web* de `/metodologia`, que se arma en tiempo de build desde
`web/src/lib/fichas.ts`, estaba correcta: lo viejo era el artefacto generado.

Al regenerar los cuatro cinturones aparecieron dos casos más que la auditoría
no había mirado:

| Qué | Decía la ficha | Dice el snapshot |
|---|---|---|
| `consumo_supermercados` | mayo-2026 · 83,2 · índice 91,2 | junio-2026 · 82,1 · índice 90,1 |
| `desequilibrio_monetario` | 50,86 pts · AMARILLO | 38,69 pts · VERDE (ADR-0257) |
| ITCM (índice del cinturón) | 64,1 · 9 verde / 6 amarillo / 2 naranja | 64,8 · 10 / 5 / 2 |
| Dimensión *Estabilidad monetaria* | 65,3 | 67,8 |
| Dimensión *Ingresos y consumo* (ITCIS) | 112,4 | 112,2 |

Dos de las tres son de la misma jornada de remediación, lo que dice cuál es el
régimen normal: **el artefacto queda viejo el mismo día en que se toca un
indicador**, no cada tanto.

No es un archivo decorativo. `CLAUDE.md` nombra a `output/informe.md` y
`output/fichas/*.md` como el material de ingesta para modelos —son 2.627 y
121.507 tokens, contra los 1,5 millones del HTML autocontenido—, así que un
número viejo ahí se propaga a cualquier análisis que los lea, y llega con el
aspecto de un dato publicado.

## Factores de decisión

- **Que el artefacto no pueda estar viejo sin que algo lo diga.** Es el
  problema; todo lo demás es cómo.
- **Costo en el nocturno.** El job tiene una cota dura de 45 minutos y ya se
  comió los 30 anteriores más de una vez.
- **Alcance de la guarda.** El hallazgo era un indicador; el arreglo no puede
  serlo, o el siguiente vuelve a aparecer por auditoría.
- **Que la guarda no se vuelva ruido.** Si falla por una coma editada en la
  prosa de `fichas.ts`, se la empieza a ignorar y deja de proteger.

## Opciones consideradas

1. **Sólo la guarda**, y marcar el artefacto como derivado bajo demanda: quien
   lo necesite lo regenera.
2. **Regenerar en el pipeline, después de los gates**, junto al commit.
3. **Regenerar en el pipeline entre `publicar.py` y los gates**, más la guarda.

## Decisión

Se toma la **opción 3**.

`generar.py --todos` corre como paso propio **después de `publicar.py`** —que
es lo que escribe el snapshot del que las fichas leen— y **antes de
`gate_calidad.py` y del pytest**, y `output/fichas/*.md` entra en el `git add`
de la corrida. La guarda es `tests/test_fichas_generadas_al_dia.py`.

El orden importa en las dos direcciones y por el mismo motivo que el paso de
Slack (`output/estado_slack.json`) va antes de commitear: un artefacto que se
escribe fuera de la ventana entre el snapshot y los gates es un artefacto que
nadie miró. Si se generara **después** de los gates, se commitearía sin
verificar y el pytest de cada noche fallaría contra las fichas de la noche
anterior. Si se generara y no se agregara al `git add`, el runner las
reescribiría cada noche y las descartaría cada noche.

La opción 1 se descartó por lo que ya se sabe de este repo: un artefacto
versionado que hay que acordarse de regenerar es un artefacto viejo. El
generador **ya existía** y llevaba meses fuera del pipeline; agregar una guarda
sin agregar el paso convertiría cada corrida manual en una falla a resolver a
mano, que es la forma lenta de que alguien la desactive. Y el costo del paso no
es un argumento: **0,2 segundos los cuatro cinturones juntos**, medido tres
veces contra un job que dura media hora. No hay nada que ponderar.

### Consecuencias

- Las fichas generadas dejan de ser un artefacto de fecha incierta y pasan a
  tener la misma fecha que el snapshot, todas las noches.
- Una corrida manual que publique sin regenerar las fichas **ya no pasa**: la
  guarda corre dentro de `python -m pytest tests -q`, que `CLAUDE.md` exige
  después de cualquier corrida a mano. El mensaje de falla dice el comando.
- Los `.docx` de `output/fichas/` **siguen siendo manuales, a propósito**: son
  la última versión *enviada* al equipo, no un espejo del snapshot de hoy.
  Pasan por pandoc y `estilar.py`, y `verificar.py` los cruza contra el
  snapshot antes de mandarlos. Hoy acumulan 57 fallas contra el snapshot
  vigente, que es exactamente lo que significan: se enviaron hace tiempo.
- Se borra `output/fichas/fichas-espiritu_epoca.md`. Espíritu de época dejó de
  ser cinturón (ADR-0205) y `test_publicar.py` guarda que no vuelva; la ficha
  quedó huérfana, sin generador que la escribiera —`generar.py` no lo tiene en
  su mapa y reventaría con un `KeyError`— y sin nadie que la leyera. El `.docx`
  se conserva por la misma razón que los otros cuatro: es lo que se envió.
- El formateador de números (`coma`) y los mapas de color, rótulos y cinturones
  se mudan a `scripts/fichas/comun.py`, que ahora comparten el generador, el
  verificador de los `.docx` y la guarda. Eran dos copias con firmas distintas
  y la guarda habría sido la tercera; tres copias de un formateador son tres
  oportunidades de que el verificador busque un texto que el generador ya no
  escribe — y un verificador que no encuentra lo que busca **no falla: pasa**.

### Confirmación

`tests/test_fichas_generadas_al_dia.py`, tres tests. Para cada indicador de
cada cinturón cruza contra el snapshot:

- el **período** del dato, en el banner «Hoy:» y en «Dato vigente:»;
- el **valor** y su unidad, en el banner, en la tabla resumen de la portada y
  en «Dato vigente:»;
- el **puntaje**: el color del semáforo en sus tres apariciones, el peso
  efectivo en el índice y el índice base-100 del ITCIS donde corresponde;
- y en la portada, el valor, el color, la banda y el recuento por color del
  índice del cinturón, más el puntaje, el color y el peso de cada dimensión.

Son ~470 comparaciones sobre 65 indicadores. Un tercer test verifica que el
parser no se haya quedado sin matchear —cuenta comparaciones, rótulos y fichas
parseadas—, porque un parser que no encuentra nada no falla, pasa.

Doce mutaciones, doce fallas. Nueve sobre el artefacto: el valor viejo del
supermercado en el banner; sólo el período; sólo el color; el índice base-100;
el valor del índice del cinturón; el peso de una dimensión; la fila de la tabla
resumen con el banner correcto; el recuento por color de la portada; y una
ficha entera borrada. Tres sobre el parser mismo —el rótulo del banner, el del
identificador técnico y el localizador de tablas—, que fallan además por el
lado de «la guarda no miró nada».

## Pros y contras de las opciones

### 1 · Sólo la guarda, artefacto bajo demanda

- Bueno: no toca el nocturno; deja explícito que el `.md` es derivado.
- Malo: convierte cada corrida manual en una falla a resolver a mano; el
  artefacto sigue viejo en `main` hasta que alguien lo note; el generador ya
  llevaba meses demostrando que nadie se acuerda.

### 2 · Regenerar después de los gates

- Bueno: el paso no puede hacer fallar la corrida.
- Malo: se commitea un artefacto que ningún gate miró, y el pytest de cada
  noche cruzaría las fichas de la noche anterior contra el snapshot de hoy —una
  falla diaria garantizada, que es como se entrena a ignorar un gate.

### 3 · Entre `publicar.py` y los gates, más la guarda *(elegida)*

- Bueno: las fichas de esta corrida las verifica esta corrida; el artefacto
  entra al mismo commit que el snapshot del que sale; cuesta 0,2 s.
- Malo: un paso más en un job con cota dura, y la lista de cinturones vive en
  un solo lugar (`comun.CINTURONES`) del que el workflow depende.

## Más información

### Por qué la guarda no compara la prosa

Sería la comparación más completa posible —regenerar en un temporal y comparar
byte a byte— y se descartó. Las fichas también interpolan texto de
`web/src/lib/fichas.ts` y `descripciones.ts`, así que una coma editada ahí haría
fallar la guarda entera, y eso ya lo cubre `test_la_ficha_no_se_queda_atras.py`
(ADR-0220), que exige que la ficha describa el indicador que realmente se está
midiendo. Acá se cuidan los **números**: período, valor y puntaje. Cada
comparación falla con el nombre del indicador y los dos textos, que es lo que
hace falta para arreglarlo sin abrir el archivo.

### El espacio de no separación

`generar.py` escribe «ITCIS 93,8» y «10,4 %» con U+00A0 a propósito, para que
Word no parta el número de su unidad. Es una decisión tipográfica del
artefacto, no un dato: la guarda lo normaliza a los dos lados de cada
comparación, igual que `verificar.py` ya normaliza lo que Word agrega por su
cuenta al guardar. Sin eso la guarda fallaba en 40 comparaciones mostrando dos
textos idénticos, que es la peor clase de falso positivo.

### Qué queda pendiente

`generar.py --todos` se re-ejecuta a sí mismo una vez por cinturón en vez de
exponer una función: el cuerpo del script son 400 líneas de nivel de módulo que
dependen de la variable `CINT`, y envolverlas para ahorrar tres arranques de
intérprete no se paga a 0,2 segundos. Si alguna vez hace falta importarlo —por
ejemplo para generar a un directorio temporal— ahí sí conviene el refactor.
