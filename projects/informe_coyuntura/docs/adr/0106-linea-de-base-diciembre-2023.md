# ADR-0106 — El ITCM publica su punto de partida

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITCM · card pública "Punto de partida" · `publicar._linea_base` · `validacion_externa.linea_base_itcm` |
| **Fecha** | 2026-07-20 |
| **Origen** | Auditoría de consistencia del cinturón macro, sección IV.1 (prioridad alta) |

## Contexto

La auditoría de macro señaló una brecha entre lo que el índice mide y lo que el
producto promete:

> "El objetivo declarado incluye avanzar respecto de lo recibido en la
> transición de 2023, pero el ITCM puntúa el estado actual contra anclas fijas:
> un mes de diciembre de 2023 y un mes de hoy se evalúan con la misma tabla. Eso
> es correcto para medir tensión vigente, pero deja sin responder la mitad de la
> pregunta original."

Y marcó la salida: **no hace falta tocar el índice.** Basta publicar el ITCM del
mes del traspaso como referencia permanente y una lectura de brecha contra ese
punto. *"Es un cambio de presentación, no de método, y alinea el producto con su
promesa."*

Era el último punto de prioridad alta sin implementar de las cuatro auditorías
de julio.

## Decisión

El bloque del ITCM publica una card con el índice de **diciembre de 2023**, el
valor de hoy y la distancia entre ambos.

| | |
|---|---|
| diciembre 2023 | **26,3** |
| hoy | **62,1** |
| distancia | **+35,8 puntos** |

El valor de base **no es un cálculo nuevo**: sale de la misma reconstrucción
que ya se usaba para validar el índice contra el riesgo país
(`construir_serie_itcm`). Si fuera un cómputo aparte, con el tiempo diría un
número distinto del que el propio informe usa para validarse, y no habría forma
de saber cuál está bien. El test lo ata: base y serie tienen que coincidir.

## La cobertura se publica junto al número

Diciembre de 2023 es **el mes peor cubierto de toda la serie**: varias series
arrancan con el mandato. La base se calcula sobre el **83% del peso** del
índice — faltan reservas netas, IAI e ICIP —, y eso se dice en el texto público,
no sólo en la ficha.

Hay además un piso: si la cobertura del mes de base cae por debajo del 60% —el
mismo umbral que ya usa la reconstrucción del ITCP—, la card **no se publica**.
Una distancia recorrida calculada sobre media docena de componentes parecería
medida sin estarlo.

Que la reconstrucción es confiable se verificó de otra forma: en mayo de 2026,
con 79% de cobertura, da 61,4 contra 62,1 del índice publicado — **0,7 puntos**.
La diferencia grande que aparecía en junio (52,4 vs 62,1) no era un problema de
método sino de cobertura: ese mes todavía tiene la mitad del índice sin dato.

## Por qué sólo el ITCM

Se evaluó extenderlo a los otros cinturones y **no corresponde**:

- **ITCG**: la reconstrucción llega a diciembre de 2023 y daría una brecha de
  +58,5 puntos, pero **seis de sus catorce componentes valen exactamente 0,0 en
  esa fecha por construcción** (reducción del Estado, reestructuración de
  organismos, FAL, privatizaciones, concesiones, libertad de opción en salud).
  Son contadores del avance de este gobierno: no podían valer otra cosa el día
  que asumió. Su brecha diría "el gobierno hizo cosas", no "la situación mejoró
  58 puntos", y publicada al lado de la del ITCM invitaría a leerlas como
  comparables.
- **ITCP**: su reconstrucción arranca en enero de 2024. No hay línea de base.

El ITCM es distinto porque sus componentes son variables macro que en diciembre
de 2023 tenían valores reales y malos: su 26,3 mide una situación, no un
contador en cero.

## Consecuencias

- `linea_base_itcm` se persiste en `output/validacion_externa.json` junto a la
  serie, con su cobertura y la lista de componentes sin dato — calculada, no
  escrita a mano, para que no quede vieja cuando una serie gane historia.
- La card hereda entera la familia visual de las cards de robustez del ITCP
  (marco, hero, rótulo en versalita, separador punteado). Se comparó por
  captura contra la card de rezago antes de publicar.
- `tests/test_linea_base.py` (5 casos) cubre lo que puede pudrirse en silencio:
  que base y reconstrucción no diverjan, que el piso de cobertura frene, que el
  número del texto público sea el mismo que el del dato, y que el texto no tenga
  siglas internas ni números de ADR.

## Lo que esta card no dice

No dice que la mejora sea atribuible al gobierno, ni que 35,8 puntos sean
"mucho". Dice dónde estaba el índice al inicio del mandato y dónde está hoy,
medidos con la misma vara. La interpretación es del lector, y la salvedad de
cobertura está en el mismo párrafo para que no la lea como una medición exacta.
