---
madr: 4
id: '0248'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'vida'
indicadores: [sentimiento_digital]
archivos: ['scripts/itvc.py', 'scripts/publicar.py', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'tests/test_itvc.py', 'tests/test_suspension_libera_el_peso.py']
relacionado: ['0222', '0245']
ambito: 'Cinturón vida cotidiana · ITVC · `sentimiento_digital` · por qué un volumen de búsquedas no mide ánimo'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «el volumen de búsquedas no identifica valencia ni bienestar»'
---

# ADR-0248 — El volumen de búsquedas no tiene valencia

## Contexto y planteo del problema

`sentimiento_digital` promediaba las búsquedas de seis términos —inflación,
precios, dólar, empleo, inseguridad y corrupción— contra su propio 4T-2023, y el
ITCIS lo puntuaba **invertido**: más búsquedas, peor ánimo.

La aritmética nunca estuvo en discusión. El problema es el salto de sentido:
**buscar «inflación» no dice si a uno le preocupa, le conviene o le da
curiosidad**. Un volumen de búsquedas mide atención, y la atención no tiene
signo.

Eso sería una objeción conceptual discutible si la validación externa
acompañara. No acompaña, y por márgenes que no dejan lugar a interpretación:

| Contraste | Resultado |
|---|---|
| Ipsos, post-base | **r = −0,788** |
| ICC UTDT, 59 meses, en niveles | r = −0,126 |
| ICC UTDT, en cambios | r = **+0,082** |
| Ventanas móviles de 18 meses | **34 de 42 con el signo opuesto al esperado** |

El primero es el más elocuente: contra la encuesta que el indicador dice
aproximar, la correlación es **fuerte y del signo contrario**. No es ruido — es
que mide otra cosa, o la misma dada vuelta.

Vale decir que el indicador ya venía siendo trabajado en serio:
[[0222-la-canasta-de-busquedas-pesa-por-termino-no-por-volumen]] arregló la
ponderación para que un término popular no dominara el promedio. Ese arreglo era
correcto y no toca el problema de fondo, que es qué representa el número.

## Factores de decisión

- **Un constructo tiene que medir lo que su nombre dice.** «Sentimiento» promete
  valencia; el insumo no la tiene.
- **La validación externa es adversa y consistente** en cuatro cortes distintos.
- **Pesaba poco (1,5% del ITCIS)**, pero entraba invertido y winsorizado: su
  índice crudo de 171,8 se recortaba a 140, o sea que empujaba el cinturón hacia
  arriba con un techo puesto a mano.

## Opciones consideradas

- **A — Renombrarlo** a «Atención de búsquedas en seis términos», sin inversión
  ni lectura afectiva, y dejarlo puntuando.
- **B — Sacarlo del score** y tratarlo como proyecto de rediseño.
- **C — Ajustar la canasta** de términos hasta que correlacione.

## Decisión

**Opción B.** Sale del ITCIS por el mecanismo de
[[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]]: libera su 18,18%
de la dimensión de percepción y `icc_utdt` queda como su único componente, con el
8,25% que la dimensión ya tenía.

La opción A es tentadora porque el rótulo corregido sería honesto. Pero un
indicador renombrado sigue **puntuando**, y para puntuar hay que decidir en qué
dirección: más atención, ¿es mejor o peor? Esa pregunta es justamente la que no
tiene respuesta fundada, así que renombrar mueve el problema del título al signo.

La opción C es el peor camino: ajustar la canasta contra la correlación que se
quiere obtener es optimizar sobre la muestra de validación. Por eso la condición
de reingreso lo prohíbe explícitamente.

**Condición de reingreso**: términos o topics predeclarados, varios vintages
congelados, encuesta objetivo definida y validación temporal **fuera de muestra**.
No vale reusar la correlación favorable de una canasta anterior para validar la
actual: la historia que devuelve hoy una consulta retroactiva no equivale a
vintages históricos.

### Consecuencias

- La dimensión de percepción queda con `icc_utdt` solo, que pasa de 81,82% a
  100% interno y de 6,75% a 8,25% del índice. La ficha lo declara.
- El ITVC **baja** levemente: `sentimiento_digital` entraba en 140 —por encima de
  la base 100— así que empujaba el cinturón hacia arriba. En el ejemplo de
  referencia, 87,5 → 87,6; sobre los valores publicados el efecto es del mismo
  orden.
- La serie se sigue publicando y el colector sigue corriendo: si el rediseño
  prospera, la historia va a estar.
- Queda una fragilidad declarada: la dimensión de percepción depende ahora de una
  sola fuente, y es una que ya se congeló cuatro días sin que nada fallara
  ([[0175-el-ancla-icg-vuelve-a-actualizarse]]).

### Confirmación

`tests/test_suspension_libera_el_peso.py` cubre la suspensión, el reparto y que
no se muestre. `tests/test_itvc.py` actualiza el ejemplo de referencia.
`tests/test_web_declara_los_pesos_del_itvc.py` compara la ficha contra los pesos
**post-suspensión**, que es lo que hizo aparecer que `icc_utdt` declaraba un
reparto que ya no existía.

## Pros y contras de las opciones

### A — Renombrarlo y dejarlo puntuando

- Bueno, porque el rótulo pasaría a describir el insumo.
- Malo, porque puntuar exige un signo, y el signo es exactamente lo que no está
  fundado. Mueve el problema, no lo resuelve.

### B — Sacarlo del score

- Bueno, porque deja de puntuar un constructo que la validación externa
  contradice en cuatro cortes.
- Malo, porque la dimensión de percepción queda con una sola fuente.

### C — Ajustar la canasta

- Bueno, porque conserva el indicador.
- Malo, porque elegir términos contra la correlación buscada es optimizar sobre
  la validación: el resultado se vería bien y no significaría nada.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_impacto_social.md`.
