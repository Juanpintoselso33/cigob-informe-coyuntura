# Alquiler: discrepancia confirmada y corrección aplicada

La [planilla original de aperturas INDEC](https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_aperturas.xls)
enlazada por el portal vigente llega a julio de 2026. En la hoja «Índices
aperturas», región GBA, «Alquiler de la vivienda» da 11.728,8484 en julio y
11.285,9597 en junio: variación de 3,9242%. La hoja de variaciones mensuales
publica 3,9%, consistente con ese cálculo.

La API usada por el monitor da 12.449,235 y 12.268,2793: 1,4750%. Ambas
series valen 100 en diciembre de 2016 y sus cocientes posteriores no son
constantes, por lo que la diferencia no se explica por un simple rebase.
El nivel general GBA sí coincide. La evidencia y comparación histórica están
en [cotejo-alquiler-discrepancia.json](cotejo-alquiler-discrepancia.json).

El componente relativo calculado con ambos niveles originales da 50,3189
para julio, contra la base media de octubre–diciembre de 2023. No alcanza
con cambiar la tarjeta mensual: hay que sustituir la historia de alquiler y
reconstruir su componente, el ITCIS y los contrastes derivados.

Corrección aplicada (ADR-0291): lector compartido del original que identifica
hoja, región, concepto y meses, valida continuidad y niveles positivos finitos.
No mezcla partes de la API discrepante con el original. Tarjeta 3,92%,
componente 50,3 e ITCIS 93,3, frente a 94,0 antes de esta revisión.
Se reconstruyeron los contrastes mensuales y las correlaciones.

La ficha ya corrige la afirmación de que sólo existe alquiler GBA: el libro
publica otras cinco regiones. Cambiar la cobertura geográfica del indicador
es una decisión metodológica distinta de reparar su fuente GBA.
