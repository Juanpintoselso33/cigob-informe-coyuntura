---
madr: 4
id: '0247'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'gestion'
indicadores: [reestructuracion_organismos]
archivos: ['scripts/itcg.py', 'scripts/publicar.py', 'web/src/lib/descripciones.ts', 'tests/test_itcg.py', 'tests/test_piso_cobertura.py']
relacionado: ['0245', '0259', '0265']
ambito: 'Cinturón gestión · ITCG · `reestructuracion_organismos` · por qué su porcentaje no es un porcentaje'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «11 cuenta normas que afectan aproximadamente 18 entidades; 45 es una convención documental»'
---

# ADR-0247 — Un porcentaje entre normas y una meta documental

## Contexto y planteo del problema

`reestructuracion_organismos` publicaba **24,4% de avance**, que es `11 / 45`.
Ninguno de los dos números es lo que el porcentaje necesita.

- **El 11 son NORMAS**, no entidades. La auditoría del 25-ago-2026 verificó que
  esas once normas afectan **unas 18 entidades**: una sola norma puede disolver
  varias, y varias normas pueden tocar la misma.
- **El 45 es una convención documental**, no una meta oficial publicada. Nadie
  fijó 45 organismos a reestructurar en un acto verificable.
- **El buscador se saltea cierres conocidos**, entre ellos el del ENOHSA.

Dividir normas por una meta documental no da un porcentaje de avance: da un
cociente entre dos cosas que no comparten unidad. Y como el denominador no está
fijado por ninguna fuente, el indicador no tiene forma de estar bien.

El propio colector tiene un registro cuidadoso de exclusiones —falsos positivos
identificados uno por uno, con su motivo— que muestra que el numerador se venía
depurando en serio. El problema no era el rigor del conteo. Era que el conteo y
el denominador miden cosas distintas.

## Factores de decisión

- **Numerador y denominador tienen que compartir unidad.** Es la condición
  mínima de un porcentaje.
- **El denominador tiene que venir de algún lado verificable.** Una convención
  interna no es una meta.
- **El universo tiene que estar cerrado**, o el avance depende de qué encuentre
  el buscador.
- **Corregirlo con otro porcentaje improvisado sería peor**: el 18/45 tampoco
  cierra, porque 45 sigue sin ser una meta.

## Opciones consideradas

- **A — Cambiar el numerador a entidades** (18) y conservar el 45.
- **B — Sacarlo del score** y conservar el inventario de entidades y actos, sin
  porcentaje de avance.
- **C — Redefinir el denominador** con un universo cerrado y publicado.

## Decisión

**Opción B.** `reestructuracion_organismos` sale del ITCG por el mecanismo de
[[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]]: libera su 25% de
la dimensión de Reforma del Estado, y `reduccion_estado` y
`gasto_funcionamiento` pasan de 43,75/31,25 a 58,33/41,67 conservando su
proporción 7:5, sin que se toque la tabla de pesos.

La opción A arregla la unidad del numerador y deja el denominador igual de
inventado. La C es el rediseño, y es adonde hay que ir — pero es trabajo de
definición, no una corrección: mientras tanto el indicador no debe puntuar.

**Condición de reingreso**: numerador y denominador en la misma unidad
—preferentemente entidades—, universo cerrado y publicado, regla explícita para
fusiones, absorciones y disoluciones, y una fuente que un tercero pueda
reproducir.

### Consecuencias

- La dimensión de Reforma del Estado queda con dos componentes en vez de tres.
  El ITCG del ejemplo de referencia pasa de 73,3 a 75,4.
- **Cambia el sesgo del piso de cobertura, y no de forma obvia.**
  `reestructuracion_organismos` era el **único componente de su dimensión que
  llegaba temprano**, y puntuaba bajo. Mientras estuvo, un mes incompleto daba
  siempre por debajo del valor real —en los 31 meses de la serie—. Sin él, la
  dimensión entera desaparece del subconjunto rápido y lo que queda puntúa alto:
  desde may-2025 el recorte da **por encima**. El piso sigue justificado, porque
  el desvío es grande y sistemático (mediana ~10 puntos, más de 3 en 30 de 31
  meses), pero el test que lo respaldaba afirmaba el signo y ahora afirma la
  magnitud, que es lo que se sostiene.
- El inventario de entidades y actos se conserva como seguimiento: es el insumo
  del rediseño.

### Confirmación

`tests/test_suspension_libera_el_peso.py` cubre la suspensión y el reparto.
`tests/test_itcg.py` actualiza el ejemplo de referencia y agrega el caso
compuesto —una fuente caída sobre una dimensión ya suspendida—, que deja la
dimensión con un solo indicador sin que se pierda su peso.
`tests/test_piso_cobertura.py` mide el sesgo en vez de suponer su signo.

## Pros y contras de las opciones

### A — Numerador en entidades, denominador igual

- Bueno, porque arregla la mitad del problema con poco trabajo.
- Malo, porque el 45 sigue sin ser una meta observable, así que el porcentaje
  sigue sin significar nada.

### B — Sacarlo del score

- Bueno, porque deja de publicar como avance algo que no lo mide.
- Bueno, porque el inventario sobrevive y es el insumo del rediseño.
- Malo, porque el ITCG pierde el único componente que mide reestructuración de
  organismos, y la dimensión queda más angosta.

### C — Redefinir el denominador ahora

- Bueno, porque es la solución de fondo.
- Malo, porque exige fijar un universo que hoy no existe publicado; hacerlo
  apurado produciría otra convención interna, que es el problema original.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_gestion.md`, caso 12.
