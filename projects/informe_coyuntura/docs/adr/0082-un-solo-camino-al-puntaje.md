---
madr: 4
id: '0082'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'politica'
archivos: ['parametrica.Escala']
relacionado: ['0192', '0195', '0197', '0231', '0233']
ambito: 'Motor paramétrico · `parametrica.Escala` (nuevo) · ITCM/ITCG/ITCP · todo módulo que reproduzca puntajes'
origen: 'El mismo bug, cuatro veces en una jornada'
---

# ADR-0082 — Un solo camino del valor crudo al puntaje

| **Precedentes** | ADR-0021 (puntaje interpolado) · ADR-0028 (anclas explícitas de la presión de dolarización) |

## Contexto y planteo del problema

### El problema, en su forma general

Puntuar un indicador exige saber **tres cosas**:

1. **Qué bandas** le corresponden.
2. **Si tiene anclas explícitas** que no coinciden con los puntos medios de esas
   bandas (`presion_dolarizacion`: valor 75 → 10 puntos por bandas, 35 por
   anclas).
3. **Si el valor se transforma antes** de puntuarse (`rem_ipc_12m` se publica
   como expectativa anual y se puntúa por su equivalente mensual).

Las tres vivían en lugares distintos y se pasaban por separado. **Nada obligaba
a que quien puntúa las tuviera todas.**

### Los cuatro casos

| # | Dónde | Qué faltó | Consecuencia |
|---|---|---|---|
| 1 | Reconstrucción histórica del ITCM | la lista de componentes, escrita a mano | Los indicadores nuevos no entraban: la validación externa se quedó atrás del índice **en silencio** |
| 2 | Matriz de redundancia (ADR-0075) | las **anclas** | Correlaciones publicadas sobre un puntaje que el índice nunca usa. Hasta 25 puntos de diferencia |
| 3 | Diagnóstico de bandas (ADR-0081) | la **transformación** | Mandaba a revisar una banda perfectamente calibrada: el REM anual puntuado contra bandas mensuales caía al piso siempre |
| 4 | La misma matriz, al arreglar el caso 3 | las **transformaciones**, otra vez | Llamaba a la función correcta **olvidando un argumento**. El \|r\| medio publicado pasó de 0,513 a 0,493 |

**El caso 4 ocurrió minutos después del 3, dentro de su propio arreglo.** Eso
descarta el descuido como explicación: el problema es la forma de la API.

Ninguno de los cuatro rompió nada. Los cuatro devolvieron un número plausible y
equivocado, y tres llegaron a publicarse.

## Opciones consideradas

- **Declarar las transformaciones junto a las bandas y que las aplique el motor** — elegida.
- **Que cada llamador aplique la transformación antes de invocar al índice** — descartada: es lo que permitía que existiera más de un camino al puntaje.

## Decisión

### 1. Las transformaciones se declaran junto a las bandas

`TRANSFORMACIONES_ITCM` vive al lado de `BANDAS_ITCM` y `ANCLAS_ITCM`, y **la
aplica el motor**. Antes cada llamador la aplicaba antes de invocar al índice.

Cada entrada es `(directa, inversa)`. La inversa no es decorativa: la simulación
de sensibilidad perturba el valor **crudo**, y para saber cuánto es "±5% del
ancho entre anclas" necesita ese ancho en unidades del valor crudo. Para el REM
son ~67 puntos (anual), no 4 (mensual) — un factor 17 de diferencia en el ruido.

### 2. Las tres partes se pasan como UNA: `parametrica.Escala`

```python
ESCALA_ITCM = parametrica.Escala(BANDAS_ITCM, ANCLAS_ITCM, TRANSFORMACIONES_ITCM)
...
puntaje = ESCALA_ITCM.puntaje(valor_crudo, indicador)
```

Con la escala armada una vez por índice, **olvidarse una parte deja de ser
posible: no hay parámetro que omitir.** La escala también expone `span_crudo()`
—el ancho ya convertido a unidades del valor— y `puntuable()`.

### 3. La regla queda pineada por un test

`tests/test_puntaje_unico_camino.py` verifica que, fuera de `parametrica.py`,
**ningún módulo llame a `puntaje_interpolado`, `puntaje_desde_anclas` ni
`puntaje_de`**: se usa una `Escala`. Más una prueba de fuego que toma el valor
crudo publicado de cada indicador del ITCM y reproduce su `puntaje_banda`
—cualquiera de los cuatro bugs la habría hecho fallar.

### Consecuencias

- **Ningún número cambia.** ITCM 62,2, robustez 60,4-64,0, \|r\| medio 0,513,
  correlación con riesgo país −0,767. Es una corrección de arquitectura.
- Se corrigió, de paso, una inconsistencia que nadie había visto: el bloque del
  índice publicaba el REM como **1,6917** (mensual) mientras su card mostraba
  **22,3** (anual) — dos números distintos para el mismo indicador. Ahora ambos
  publican el crudo y la transformación es interna.
- `macro.py` y `validacion_externa.py` dejan de transformar por su cuenta. El
  fixture de tests pasa el valor **crudo**, como el colector.

## Más información

### Limitaciones

- ITCG e ITCP no tienen transformaciones hoy; sus escalas se construyen igual,
  así que agregar una en el futuro no requiere tocar a los consumidores.
- El test de "nadie puntúa por fuera" es **estático**: detecta llamadas
  escritas, no construidas dinámicamente. Es suficiente para el estilo del
  repositorio.
- La `Escala` no valida que un indicador con transformación tenga inversa. Si
  se declara sólo la directa, `span_crudo` devuelve el ancho sin convertir —
  correcto para los indicadores sin transformación, silenciosamente estrecho
  para uno mal declarado.

### Por qué no alcanzaba con "prestar más atención"

Los cuatro casos los cometió la misma persona, con el problema fresco, y el
cuarto mientras arreglaba el tercero. Cuando un error se repite así, la causa no
está en quien lo comete sino en lo que el diseño permite: **una API que exige
recordar tres cosas correlacionadas garantiza que tarde o temprano falte una.**

La corrección que funciona no es un recordatorio, es hacer que el estado
incorrecto no se pueda expresar.
