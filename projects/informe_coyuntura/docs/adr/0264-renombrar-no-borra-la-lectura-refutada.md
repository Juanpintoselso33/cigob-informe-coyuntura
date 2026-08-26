---
madr: 4
id: '0264'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [idm, icip, desequilibrio_monetario]
archivos: ['web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'web/src/lib/charts.ts', 'web/src/lib/descripciones.ts', 'web/src/pages/[slug].astro', 'tests/test_contrato_publico_dice_lo_que_corre.py', 'tests/test_web_labels.py']
relacionado: ['0189', '0253', '0254', '0257', '0261', '0262']
ambito: 'Cinturón macro · ITCM · el texto activo de un indicador que se renombró, se recalibró o se retiró tiene que seguirlo'
origen: 'Reauditoría post-cambios, 25-ago-2026: discrepancias 4 y 6 — «constructos macro renombrados, pero no rediseñados»'
---

# ADR-0264 — Renombrar no borra la lectura refutada

## Contexto y planteo del problema

ADR-0253 y ADR-0254 cambiaron el nombre de dos indicadores porque afirmaban más
de lo que sus insumos observan. Los rótulos cambiaron y la descripción del modal
también. La **fórmula pública**, en cambio, siguió diciendo exactamente lo que se
acababa de refutar:

- La fórmula de **`idm`** rotulaba sus dos términos como «pesos que HAY» menos
  «pesos que la gente QUIERE», y su leyenda cerraba con «positivo = **sobran
  pesos** → presión sobre precios y brecha». M2 no es lo que la gente quiere: es
  un stock observado. La ficha repetía la misma frase en `transformaciones` y
  hablaba del «pico de **excedente**» en sus limitaciones.
- La fórmula de **`icip`** decía «variaciones interanuales de la **inversión
  intangible**», y la página de metodología del cinturón macro presentaba el
  indicador como «ICIP (**capitalización digital**: servicios tech y
  productividad)» — el rótulo que ADR-0253 acababa de retirar.

`tests/test_constructos_no_prometen_de_mas.py` no los agarró, y por dos motivos
que conviene dejar escritos: su lista de frases prohibidas cubre «exceso de
pesos» y «excedente de pesos» pero no «sobran pesos», y su corpus son los cuatro
archivos de `web/src/lib` más `scripts/*.py` — las páginas `.astro` quedaban
afuera. Una guarda por frase sólo cubre las frases que alguien escribió.

## Factores de decisión

- **Una fórmula es la capa que más se lee y la más literal**: si el `\underbrace`
  dice «pesos que la gente QUIERE», el nombre nuevo no alcanza.
- **La decisión estructural es de otro ADR y este no la espera.** Mientras se
  resolvía la banda de `idm` y el lugar de `icip` —ADR-0261 y ADR-0262, que los
  sacaron del ITCM—, el texto que la web mostraba seguía siendo el refutado. La
  corrección de texto es correcta haga lo que haga el rediseño.
- **Este ADR no toca `scripts/itcm.py`.** Ni bandas, ni pesos, ni dimensiones.

## Opciones consideradas

- **A — Sacar las afirmaciones causales de los textos activos** y esperar la
  decisión metodológica para el resto.
- **B — Esperar la decisión sobre banda y dimensión** y corregir todo junto.

## Decisión

**Opción A.** Los textos activos pasan a decir lo que se observa:

- `idm`: los dos términos del `\underbrace` pasan a llamarse «agregado amplio» y
  «agregado transaccional». La lectura del signo pasa a ser direccional —positivo
  = el agregado amplio corre más rápido que el transaccional, o sea que los pesos
  se mueven hacia plazo e instrumentos remunerados en vez de quedarse en
  transacciones— y se dice explícitamente que la brecha no es oferta menos
  demanda de dinero. Lo mismo en `transformaciones` de la ficha, en la
  limitación que hablaba del «pico de excedente» y en el comentario de
  `charts.ts` que justificaba la polaridad del área.
- `icip`: la fórmula pasa a nombrar sus dos insumos —pagos al exterior por
  servicios de informática y productividad laboral— y a decir que en cuentas
  nacionales esos pagos son consumo intermedio. La página de metodología del
  cinturón macro deja de llamarlo «capitalización digital».

La opción B es la que produjo esta discrepancia: en julio se cambió dos veces el
método del deflactor del IAF y el rótulo siguió diciendo `(dic-dic)` porque el
rediseño «venía después».

Y una tercera pieza del mismo tipo, encontrada al barrer `formulas.ts` entero:
la matriz de **`desequilibrio_monetario`** publicaba sus dos esquinas cruzadas
en **40** y **77,5** cuando ADR-0257 las había igualado en **58,75**. La leyenda
del mismo objeto, dos líneas más abajo, ya decía 58,75: **la fórmula pública se
contradecía consigo misma**. Es el residuo típico de una recalibración —se
corrige la prosa, que es lo que uno lee, y el LaTeX queda—, y ningún gate mira
el LaTeX.

### Consecuencias

- **Este ADR no cambia ningún valor, banda, peso ni dimensión**: cambia lo que
  el texto afirma. Los dos textos que quedaban dependiendo de una decisión ajena
  —por qué la banda de `idm` castiga el positivo y por qué `icip` integra la
  dimensión de inversión— dejaron de necesitarse: ADR-0261 y ADR-0262 sacaron a
  los dos del ITCM mientras esto se escribía, y la respuesta pública pasó a ser
  la misma que se le da a cualquier indicador retirado. Sus fichas conservan la
  tabla de bandas, declarada como escala histórica, y dicen por qué salieron.
- La descripción de `estabilidad_monetaria` pasa de cuatro señales a tres —el
  20% de `idm` va **entero al IPC**, que queda en 60%— y la de `inversion`
  conserva su 12% con el IAI al 100%; la página de metodología del cinturón
  macro se corrige en los dos lugares.
- **Los bloques de `idm` e `icip` salen de `formulas.ts` y de `fichas.ts`.** La
  regla es de ADR-0189 y estaba escrita: lo que no puntúa no se muestra, ni en
  el tablero ni en las fichas metodológicas, que salen del mismo snapshot. Los
  cuatro indicadores de contexto que macro ya tenía —`badlar`,
  `prestamos_privados`, `base_monetaria` y `tc_mayorista`— la venían cumpliendo:
  conservan etiqueta en `datos.ts` y descripción, y no tienen ni ficha ni
  fórmula. `idm` e `icip` quedan igual que ellos; su historia vive en ADR-0261 y
  ADR-0262, que es el registro canónico.
- La matriz del LaTeX de `desequilibrio_monetario` pasa a `58,75` en las dos
  esquinas cruzadas, término por término contra las constantes del motor.
- **Dependencia de orden, no de criterio**: mientras el snapshot en disco siga
  publicando `idm` e `icip` como cards, la guarda «todo indicador publicado
  tiene ficha» falla. `publicar.py` ya los descarta —`MACRO_OCULTOS` se deriva
  de `itcm.INDICADORES_CONTEXTO`—, así que se resuelve solo en la primera
  regeneración. Simulado ese snapshot: 63 cards, ninguna sin ficha y ninguna que
  rompa `getStaticPaths`.
- `tests/test_constructos_no_prometen_de_mas.py` seguía verde con las cinco
  afirmaciones puestas. La guarda nueva agrega «sobran pesos», «pesos que la
  gente» e «inversión intangible» al vocabulario vigilado y suma las páginas
  `.astro` al corpus.

### Confirmación

`tests/test_contrato_publico_dice_lo_que_corre.py`:

- ni la capa pública de `web/src/lib` ni las páginas `.astro` afirman «sobran
  pesos», «pesos que la gente», «inversión intangible» ni «capitalización
  digital». La exención de las líneas que citan la afirmación para negarla se
  evalúa por **cláusula** y no por línea: en `fichas.ts` una línea es un párrafo
  entero, y alcanzaba con que negara la tesis al final para poder afirmarla al
  principio. Tres mutaciones se colaban así —el deflactor promedio del IAF,
  «sobran pesos» en la leyenda del IDM e «inversión intangible» en la del
  ICIP—, y las tres las agarra ahora. La entrada de `cambios:` sigue exenta
  entera, porque contar lo que el texto decía es exactamente su trabajo;
- ningún indicador declarado de contexto conserva ficha ni fórmula, y todos
  conservan etiqueta y descripción — la guarda recorre
  `itcm.INDICADORES_CONTEXTO`, así que el próximo retiro la hereda sin que nadie
  la extienda;
- las cuatro esquinas de la matriz de `desequilibrio_monetario` son las cuatro
  constantes del motor, **término por término**: dos esquinas valen lo mismo, de
  modo que comparar el conjunto de números dejaría pasar un intercambio;
- cuando una fórmula reparte pesos, el reparto suma 1. No se compara contra el
  colector —cada compuesto lo calcula el suyo— pero un reparto que no cierra
  está mal sin necesidad de saber cuál era el bueno.

Probado rompiéndolo, una mutación por guarda: «pesos que la gente QUIERE» y
«sobran pesos» en firme, «inversión intangible», «capitalización digital» en la
página de metodología, la matriz vuelta a 40/77,5, dos esquinas del mismo valor
intercambiadas con las otras dos, un peso del IdC recalibrado a medias, `idm`
recuperando ficha e `icip` perdiendo su etiqueta. Las nueve fallan, cada una en
su propia guarda.

## Pros y contras de las opciones

### A — Sacar ahora las afirmaciones causales

- Bueno, porque lo que queda dicho es cierto haga lo que haga el rediseño.
- Malo, porque deja la ficha sin explicar por qué la banda castiga el positivo.
  Es preferible un hueco a una explicación falsa.

### B — Esperar el rediseño

- Bueno, porque el texto se escribiría una sola vez.
- Malo, porque mientras tanto la web afirma lo que dos ADR aceptados el mismo día
  declararon insostenible.

## Más información

- Reauditoría post-cambios, 25-ago-2026:
  `docs/auditoria_indicadores/260825_reauditoria_post_cambios_completa.md`.
- [[0253-pagar-la-nube-no-es-capitalizar]] y
  [[0254-la-brecha-m3-m2-no-es-oferta-menos-demanda]] son los renombres que este
  ADR termina de aplicar.
