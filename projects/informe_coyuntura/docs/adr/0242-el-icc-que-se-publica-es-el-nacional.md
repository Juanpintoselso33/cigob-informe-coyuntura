---
madr: 4
id: '0242'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'vida'
indicadores: [icc_utdt]
archivos: ['scripts/vida_cotidiana/collectors/utdt_icc.py', 'scripts/descargar_series.py', 'tests/test_utdt_icc_columna_nacional.py', 'tests/fixtures/utdt_icc_regiones.json']
relacionado: ['0175']
ambito: 'Cinturón vida cotidiana · ITVC · `icc_utdt` · qué columna del cuadro de la UTDT es el índice que se publica'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «39,87 corresponde a CABA; el total nacional del mismo corte es 40,23»'
---

# ADR-0242 — El ICC que se publica es el nacional

## Contexto y planteo del problema

El tablero publicaba **39,9** como Índice de Confianza del Consumidor de la
UTDT, rotulado total nacional. 39,87 es el ICC de **la Ciudad de Buenos Aires**.
El nacional del mismo corte es **40,23**.

El colector leía **la columna 1 por posición**. En el cuadro de la UTDT —hoja
«Desagregación por regiones»— las columnas son:

| col | serie |
|---:|---|
| 0 | fecha |
| **1** | **ICC Capital** ← la que se leía |
| 3 | ICC Interior |
| 5 | ICC GBA |
| **7** | **ICC Nacional** ← la que corresponde |

Las columnas 2, 4, 6 y 8 son las variaciones mensuales de cada una.

Lo que hizo el error invisible: **la card y la serie leían la misma columna
equivocada**. Coincidían entre sí, así que el gate G3 —que compara la card
contra el último punto de la serie— no tenía nada que marcar. Dos cosas mal de
la misma manera se ven bien, y no hay gate que compare un rótulo con la columna
de la que sale el número.

La solución obvia —ubicar la columna por nombre, buscando «nacional» en el
encabezado— **elige Capital**. El encabezado ocupa tres filas y la primera trae
el banner `ICC Nacional - Desagregación por regiones` **encima de la columna de
Capital**. Sería el mismo error, ahora con aire de estar ubicado por nombre.

## Factores de decisión

- **Una columna se ubica por su encabezado, no por su posición**: el cuadro
  ganó las regionales en algún momento y las puede volver a mover.
- **El encabezado a leer es el de la columna, no el banner del bloque.**
- **Una ambigüedad tiene que fallar**, no resolverse eligiendo la primera.
- **La serie histórica se rehace entera**: la columna nacional existe desde
  marzo de 2001, así que no hace falta empalmar con la de Capital.

## Opciones consideradas

- **A — Cambiar la posición de 1 a 7.**
- **B — Ubicar por encabezado buscando «nacional».**
- **C — Ubicar por encabezado, descartando el banner del bloque y excluyendo
  explícitamente los rótulos regionales y las columnas de variación.**

## Decisión

**Opción C.** `columna_icc_nacional()` recorre las columnas, arma el encabezado
de cada una con sus celdas de texto **descartando el banner** (todo lo que diga
«desagreg» o «series»), y se queda con la única que dice «icc» y «nacional» sin
nombrar una región ni ser una variación. Si hay cero o más de una candidata,
falla: un colector que adivina publica CABA sin decirlo.

La misma función la usan la card y la serie, así que no pueden volver a
desalinearse en silencio.

Las dos guardas —descartar el banner y excluir las regionales— son **redundantes
contra el cuadro de hoy**: cualquiera de las dos alcanza. Están las dos porque
cubren derivas distintas, y cada una tiene su test:

- si la UTDT renombrara `Capital` a `CABA`, lo único que evita volver a elegir
  esa columna es haber descartado el banner;
- si el rótulo de la columna regional pasara a decir `ICC Nacional - Capital`
  —que es literalmente el texto del banner una fila más abajo—, lo único que la
  excluye es que además nombre una región.

### Consecuencias

- El valor pasa de **39,9 a 40,2**. La serie del ITVC se reconstruye entera con
  la columna nacional (306 puntos desde marzo de 2001; el ITVC arranca en
  dic-2023, así que la cobertura sobra).
- `validacion_externa.py` correlaciona el ITVC contra el ICC: esa correlación se
  recalcula sobre la serie nacional, que es la que corresponde comparar con un
  índice nacional.
- El Índice Líder de la UTDT usa el mismo parser, pero tiene una sola serie: se
  le pasa la columna explícitamente en vez de buscar una que no existe.
- La card declara `cobertura: "total nacional"`.

### Confirmación

`tests/test_utdt_icc_columna_nacional.py` contra
`tests/fixtures/utdt_icc_regiones.json` —los encabezados reales, con el banner
adentro, y 30 períodos de las cuatro series—:

- ubica la columna 7;
- **no elige Capital pese al banner** que dice «Nacional» encima;
- el valor es 40,23 y **39,87 no puede volver**;
- no confunde una columna de variación (daría 0,01 y el semáforo lo leería como
  confianza en piso);
- un cuadro sin columna nacional falla, y uno con dos también;
- Capital y Nacional difieren de verdad en la ventana: si coincidieran, el error
  no habría tenido efecto.

Las dos guardas se probaron rompiéndolas **por separado**: cada mutación hace
fallar exactamente el test de su escenario.

## Pros y contras de las opciones

### A — Cambiar la posición

- Bueno, porque es un carácter.
- Malo, porque el problema no era el número 1 sino leer por posición: el próximo
  cambio de cuadro repite el error, y en silencio.

### B — Buscar «nacional» en el encabezado

- Bueno, porque parece resolver la causa.
- Malo, porque **elige Capital**: el banner del bloque dice «ICC Nacional» y
  está encima de esa columna. Es peor que A, porque además parece correcta.

### C — Encabezado sin banner, regiones y variaciones excluidas

- Bueno, porque sobrevive a que el cuadro gane o mueva columnas.
- Bueno, porque falla ante la ambigüedad en vez de elegir.
- Malo, porque depende de los rótulos de la UTDT: si renombra las series, falla.
  Es el modo de falla que se prefiere — ruidoso, no silencioso.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_impacto_social.md`.
- [[0175-el-ancla-icg-vuelve-a-actualizarse]] es el antecedente de esta misma
  fuente congelándose sin que nada fallara.
