---
madr: 4
id: '0161'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'politica'
ambito: 'validación externa del ITVC y el ITCP; módulo'
---

# ADR-0161 — El contraste externo es un factor común, no una variable suelta

`scripts/factor_comun.py`, integrado en `scripts/panel_validacion.py`
- **Relacionados**: ADR-0159 (el panel, que esto encabeza), ADR-0158 (el régimen
  del ITCM), ADR-0045 (no mover pesos para que un test dé mejor)

## Contexto y planteo del problema

ADR-0159 respondió a la objeción de "peras con manzanas" comparando cada índice
contra un panel de estadísticas. Quedó viva la parte más incómoda: **lo que el
tablero mostraba seguía siendo la correlación contra una sola variable.** Un
índice de seis dimensiones contrastado contra el EPU, o contra las ventas de
supermercados, mide una faceta y se publica como si midiera el todo.

La salida obvia —promediar las estadísticas de la familia— exige dos decisiones
a mano: **qué serie entra invertida** (la incertidumbre sube cuando las otras
bajan) y **con qué peso**. Ahí está el problema: quien elige los signos ya vio
los resultados. En la primera prueba a mano el autor de este cambio se equivocó
de signo en el EPU y midió el compuesto como peor de lo que era; corregirlo lo
volvió mejor. Un procedimiento donde equivocarse mejora o empeora el resultado
según quién lo arme no es una validación, es un ajuste.

## Opciones consideradas

- **Primer componente principal del panel de la familia** — elegida: se adopta el método establecido en vez de inventar uno.
- **Construir un compuesto eligiendo signos y pesos a mano** — descartada: dejaría esas decisiones en manos de quien ya vio los números. Con el factor común, las cargas fijan signo y peso solas.

## Decisión

Se adopta el método establecido en vez de inventar uno: el contraste es el
**primer componente principal** del panel de la familia — la construcción con la
que la Reserva Federal de Chicago arma el **CFNAI** a partir de 85 series, cada
una llevada a estacionariedad, centrada y estandarizada antes de entrar, y que
Stock y Watson formalizaron como **modelo de factor** (cada serie = una parte
común más una parte propia).

Lo que resuelve, y es la razón de elegirlo:

- **Las cargas ponen el signo y el peso.** A la serie que se mueve al revés que
  el factor le sale carga negativa sola; a la que es sobre todo ruido propio le
  sale carga chica en vez de cancelar la señal ajena. Ninguna de las dos
  decisiones queda en manos de quien ya vio los números.
- **No es circular.** Las cargas se estiman **con el panel externo solamente**;
  el índice no participa del cálculo y recién aparece cuando se lo correlaciona
  contra el factor ya armado. Hay un test que lo fija: cambiar el índice no puede
  cambiar ni las cargas ni la varianza explicada.

Decisiones de implementación:

- **Mínimo de tres series.** Con dos, el "factor" es un promedio con el signo de
  una única correlación: no hay nada que estimar y basta que una falle para darlo
  vuelta. El ITCG, con una sola estadística propia, no recibe factor.
- **Se diagonaliza por rotaciones de Jacobi**, exacto y determinista. La
  iteración de potencia —el atajo habitual, y lo primero que se escribió acá— **no
  sirve**: arrancando del vector (1,1,…) queda clavada cuando ese vector ya es un
  autovector, y devuelve todas las cargas positivas aunque las series estén
  correlacionadas negativamente entre sí. Con dos series pasaba **siempre**, y el
  síntoma era que todo par devolvía exactamente 0,707/0,707. Hay test de
  regresión.
- **El gráfico del tablero muestra el factor**, no una estadística suelta: el
  titular informa el r contra el factor y un número que no se corresponde con la
  curva que tiene debajo es peor que no publicarlo. La escala se fuerza a rango
  (el factor es un puntaje estandarizado, cruza el cero).
- **El desarrollo va a la ficha metodológica, no al tablero.** En el tablero
  queda una línea; las cargas, la varianza explicada y la comparación contra la
  mejor estadística sola se publican en `/metodologia/<índice>`.

### Consecuencias

- El tablero deja de contrastar contra una variable en los dos cinturones que
  tienen tres o más estadísticas propias.
- Queda declarada la limitación que ordena el trabajo siguiente: **el ITCG
  necesita más estadísticas de su familia** (hoy tiene una y no puede tener
  factor), y **el ITVC necesita estadísticas que no sean todas ventas
  minoristas**. Con un panel de un solo tipo de fuente, el factor mide el ciclo
  de esa fuente.
- No se toca ningún peso ni ninguna ancla para mejorar estos números: hacerlo
  sería exactamente lo que ADR-0045 prohíbe.

## Más información

### Resultado, incluido el que no confirma

| índice | factor (niveles / mes a mes) | mejor estadística sola | varianza explicada |
|---|---|---|---|
| **ITCP** | **+0,523 / +0,493** | 0,493 / 0,42 | 51,5% |
| **ITVC** | +0,211 / +0,029 | **0,596 / 0,246** | 59,2% |

**El ITCP es el caso que el método promete**: el compuesto acompaña al índice más
que *cualquiera* de sus tres componentes por separado, en los dos planos. Y el
cálculo dedujo por su cuenta que el EPU entra invertido (carga **−0,511**, contra
+0,709 de confianza en el gobierno y +0,487 de clima electoral).

**El ITVC es el caso que no**, y se publica igual. Las tres cargas salen
positivas (supermercados 0,707 · mayoristas 0,667 · shoppings 0,234): el factor
común de los tres canales es **el ciclo del comercio minorista**, y eso no es lo
que el índice mide. Mayoristas correlaciona **−0,114** con el ITVC mientras carga
**+0,667** en el factor. La lectura sustantiva es que el ITVC sigue la canasta
cotidiana del hogar —que supermercados aproxima— y no el ciclo del comercio, que
incluye reventa y consumo discrecional. Es un límite del panel disponible —corto
y de un solo tipo de fuente— antes que un veredicto sobre el índice.

Publicar el caso que falla es el mismo criterio de ADR-0159: el estándar pide
explicar las diferencias, no informar sólo las que confirman.
