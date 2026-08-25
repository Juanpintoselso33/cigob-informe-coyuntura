---
madr: 4
id: '0252'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [desequilibrio_monetario]
archivos: ['scripts/desequilibrio_monetario.py', 'scripts/itcm.py', 'scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'tests/test_constructos_no_prometen_de_mas.py']
relacionado: ['0055', '0192', '0257']
ambito: 'Cinturón macro · ITCM · `desequilibrio_monetario` · qué observa realmente su componente B'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «la compra neta de divisas del sector privado no identifica dinero fuera del sistema»'
---

# ADR-0252 — La compra de divisas no dice adónde fue el dinero

## Contexto y planteo del problema

El indicador cruza dos componentes en una matriz. El **componente B** era, según
todo lo que el sistema decía de él, la **«fuga fuera del sistema»**: el módulo lo
titulaba así, la ficha lo llamaba «flujo, fuera del sistema», el rótulo público
era «Dolarización dentro y fuera del sistema», la fórmula lo describía como «la
que se va» y la celda peor de la matriz se leía **«fuga oculta fuera del
sistema»**.

Lo que B mide es la **compra neta de billetes y divisas del sector privado no
financiero** en el mercado de cambios. Comprar divisas y sacarlas del sistema
financiero **son dos actos distintos**, y el segundo no se observa acá: el BCRA
estimó que cerca del **80%** de esas compras quedó depositado localmente.

El error no era de matiz, porque la interpretación estaba **cableada en la
lectura de la matriz**. Toda la asimetría del indicador —que degradar B cueste
77,5 puntos de tensión y degradar A sólo 40— se justificaba con la tesis de que
la fuga fuera del sistema es la señal grave. Si B no identifica fuga, esa
justificación se cae aunque el número no cambie.

## Factores de decisión

- **Lo que se observa es la compra, no el destino.**
- **La aritmética y la calibración son correctas** y no hay razón para tocarlas:
  el problema es lo que se afirma sobre el resultado.
- **La afirmación estaba en seis lugares distintos**, así que corregir uno no
  alcanza.

## Opciones consideradas

- **A — Sacar el indicador del score** hasta rediseñar el componente.
- **B — Renombrar el componente** como presión compradora de divisas y eliminar
  toda afirmación de «fuera del sistema».
- **C — Reemplazar B** por una medida observable de activos externos fuera del
  sistema.

## Decisión

**Opción B**, que es la mínima que la auditoría propuso para este caso. El
componente B pasa a llamarse **presión compradora de divisas** y desaparece toda
afirmación sobre el destino del dinero:

| Celda | Antes | Ahora |
|---|---|---|
| verde | confianza real | liquidez transaccional alta y poca compra de divisas |
| amarillo | dolarización contenida en el sistema | menos pesos transaccionales, sin presión compradora |
| naranja/rojo | **fuga oculta fuera del sistema** | presión compradora alta pese a liquidez transaccional alta |
| rojo | deterioro dentro y fuera del sistema | menos pesos transaccionales y presión compradora alta |

El rótulo público pasa de «Dolarización dentro y fuera del sistema» a
**«Liquidez en pesos y presión compradora de divisas»**.

La opción C es el rediseño de fondo y necesita una serie que hoy no está
identificada; la auditoría misma la deja como opción sustantiva, no como
corrección. La A sería desproporcionada: lo que el indicador observa sigue
siendo informativo y su calibración no está en discusión — lo que sobraba era la
inferencia.

### Consecuencias

- **El valor, la matriz, los pesos y las bandas no cambian.** Cambia lo que se
  afirma.
- **Queda una deuda declarada**: la asimetría 77,5 contra 40 se justificaba con
  la tesis de la fuga. Sigue en pie porque viene de las celdas que fijó la ficha
  original, pero **su fundamento ya no es el que se creía** y merece revisarse
  cuando se recalibre el indicador. Está anotado en el módulo.
- El detalle de la card describe la combinación observada, no el destino.

### Confirmación

`tests/test_constructos_no_prometen_de_mas.py`:

- **la frase «fuera del sistema» no puede afirmarse** en ningún archivo de
  código ni de la capa pública — el test acepta sólo las líneas que la citan
  para decir que no es cierta;
- las cuatro celdas de la matriz describen la combinación y ninguna dice «fuga»;
- el rótulo público ya no promete dolarización fuera del sistema.

Probado rompiéndolo: repuesta la etiqueta «fuga oculta fuera del sistema»,
fallan dos guardas.

## Pros y contras de las opciones

### A — Sacarlo del score

- Bueno, porque elimina de raíz la lectura equivocada.
- Malo, porque el dato observado —composición de la liquidez y compra de
  divisas— es correcto y útil; el problema era el nombre.

### B — Renombrar el componente

- Bueno, porque el indicador pasa a decir lo que observa, sin tocar el cálculo.
- Malo, porque la asimetría de la matriz queda apoyada en una tesis que ya no se
  sostiene tal como estaba escrita. Queda declarado.

### C — Reemplazar B por activos externos fuera del sistema

- Bueno, porque mediría el fenómeno que el nombre prometía.
- Malo, porque no hay hoy una serie identificada que lo haga de forma
  defendible: es un proyecto, no una corrección.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_macro.md`.
