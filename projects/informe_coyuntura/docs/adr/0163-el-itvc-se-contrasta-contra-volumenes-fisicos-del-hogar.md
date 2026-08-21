---
madr: 4
id: '0163'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'vida'
archivos: ['scripts/desestacionalizar.py']
relacionado: ['0225']
ambito: 'panel y factor común del ITVC; `scripts/desestacionalizar.py`,'
---

# ADR-0163 — El ITVC se contrasta contra volúmenes físicos consumidos por los hogares

`panel_validacion.FACTOR`, nuevas series en `validacion_externa.py`
- **Relacionados**: ADR-0161 (el factor común), ADR-0159 (el panel), ADR-0160
  (el ITVC casi no se mueve en neto), ADR-0045 (no mover nada para que un test
  dé mejor)

## Contexto y planteo del problema

ADR-0161 dejó el ITVC como el caso que **no** funcionaba: su factor común daba
+0,211 en niveles y +0,029 en los cambios, por debajo de lo que lograba el
consumo en supermercados solo. El diagnóstico quedó escrito ahí y es el punto de
partida de esta decisión: **las tres estadísticas de su familia eran tres
variantes de venta minorista**, y lo que tres canales de comercio comparten es el
ciclo del comercio, no la condición material de los hogares. Con un panel de un
solo tipo de fuente, el factor mide el ciclo de esa fuente.

## Opciones consideradas

- **Las cuatro series de volumen físico** — elegida.
- **Cualquier índice salarial** — descartado: `brecha_salario_cbt` *es* RIPTE/CBT, así que el RIPTE sería el índice validándose contra una parte de sí mismo.
- **Consumo de carne y patentamiento** — afuera por la misma regla.
- **Las tres series de comercio** — descartadas por insumo compartido: las ventas «a precios constantes» se deflactan con el mismo índice.

## Decisión

### 1. Se amplía la familia a cuatro canales de fuente

La familia del ITVC pasa de 3 a 7 estadísticas, agregando registros operativos
que no son ventas de comercio:

| canal | estadística | fuente | historia |
|---|---|---|---|
| energía del hogar | electricidad consumida por los hogares | CAMMESA | desde 2005 |
| energía del hogar | gas consumido por los hogares | Secretaría de Energía | desde 1996 |
| movilidad | viajes en transporte público | INDEC | desde 2012 |
| combustible | naftas vendidas en el mercado interno | Secretaría de Energía | desde 1994 |

**Regla de exclusión aplicada**: queda afuera lo que sea *la misma medición* que
un componente del índice, no lo que esté causalmente relacionado — si se
excluyera todo lo causalmente relacionado no quedaría nada en una economía. Por
eso se descartó **cualquier índice salarial**: `brecha_salario_cbt` *es*
RIPTE/CBT, así que el RIPTE sería el índice validándose contra una parte de sí
mismo. Por la misma regla quedaron afuera consumo de carne y patentamiento de
motos, que son componentes.

### 2. El factor se arma sólo con los volúmenes físicos

`panel_validacion.FACTOR` declara explícitamente qué estadísticas arman el factor
de cada índice, que puede ser **un subconjunto de la familia**. Para el ITVC son
las cuatro físicas y no las tres de comercio, por dos razones:

- **Insumo compartido.** Las ventas «a precios constantes» se deflactan con
  índices de precios del INDEC, y `ipc_alimentos` es componente del ITVC. Un
  volumen físico no necesita deflactor. Es la misma regla del punto anterior.
- **Concepto.** Los autoservicios mayoristas abastecen también a revendedores y
  los centros de compras son gasto discrecional: ninguno de los dos es «cómo vive
  el hogar promedio».

Las tres de comercio **siguen en el panel y en la familia**: se publican sus
correlaciones, sólo que no arman el factor.

**Sobre el orden en que pasó, que hay que declarar**: el criterio es
independiente del resultado y ya se venía aplicando, pero **se lo aplicó después
de medir el panel ancho**. Eso no lo invalida y tampoco lo convierte en un
hallazgo confirmado — la prueba real son los meses que vienen, con el corte ya
fijado en el código.

### 3. Ajuste estacional obligatorio (`desestacionalizar.py`)

Los volúmenes físicos traen estacionalidad fuerte y las de comercio ya vienen
ajustadas por el INDEC. Mezclarlas crudas haría que el primer componente sea **la
estación del año**. Se aplica a todas por igual un factor multiplicativo fijo por
mes calendario (cociente sobre media móvil), que sobre una serie ya ajustada es
casi la identidad — verificado: supermercados 3,7% → 0,3%.

| serie | amplitud estacional antes | después |
|---|---|---|
| gas residencial | 188,0% | 14,5% |
| electricidad residencial | 37,7% | 2,9% |
| transporte de pasajeros | 23,7% | 1,8% |
| naftas | 19,1% | 1,5% |

El residuo del gas **no es chico y se declara**: depende de cuán crudo viene cada
invierno, no sólo de que sea invierno, y un factor fijo por mes no captura eso.

**Detalle de implementación con su error**: la primera versión usó una media
móvil simple de 13 meses, que **cuenta dos veces el mismo mes calendario** y
sobreestimaba la amplitud (47,4% donde el patrón verdadero era 44,0%). Se corrigió
a la media móvil **2×12** —extremos con peso mitad—, que es la forma estándar de
centrar una media de período par. Hay test que lo fija.

### 4. El gráfico muestra el plano donde se apoya el veredicto

El ITVC pasa la prueba en los cambios mes a mes y no en niveles. Graficar niveles
mientras el encabezado informa el resultado de los cambios deja una figura que
contradice a su propio titular — el mismo defecto que ADR-0161 corrigió por otra
puerta. `plano_del_veredicto()` elige: niveles por defecto (más legibles), cambios
sólo cuando el veredicto descansa exclusivamente ahí.

### Consecuencias

| | niveles | mes a mes |
|---|---|---|
| **factor de 4 volúmenes físicos** | 0,043 | **+0,478** |
| mejor estadística sola del factor | 0,364 | 0,406 |
| factor anterior (3 de comercio) | 0,211 | 0,029 |

**El compuesto le gana a las cuatro por separado en los cambios mes a mes**, que
es la prueba exigente: la que no se puede satisfacer con la tendencia que en
estos años arrastró a casi todas las series argentinas. Aguanta dejando una
afuera por vez (0,419 – 0,460).

**En niveles queda en 0,04, y la razón es sustantiva, no un defecto**: el ITVC se
movió 5,0 puntos netos en 32 meses porque sus componentes se compensan entre sí
(ADR-0160), mientras que las estadísticas del contraste tienen tendencia propia.
Comparar niveles de una serie casi plana contra series que suben o bajan no dice
demasiado en ninguna dirección. El texto público lo explica en esos términos en
lugar de dejar que un 0,04 se lea como «el índice no mide nada».

Las cargas: electricidad 0,724 · naftas 0,666 · gas 0,163 · transporte −0,072. El
transporte queda con carga casi nula, que es el comportamiento esperado del
método con una serie mayormente idiosincrásica: se la baja de peso en vez de
dejar que cancele señal ajena.

- El ITVC deja de ser el caso que falla y pasa a validar en el plano exigente.
- El ITCG sigue sin factor: tiene **una sola** estadística de su familia. Es
  ahora el pendiente principal de validación externa.
- El panel del ITVC pasa a 7 propias y la brecha en niveles queda en −0,004: las
  físicas correlacionan ~0 en niveles por la misma razón de arriba. Se publica.
