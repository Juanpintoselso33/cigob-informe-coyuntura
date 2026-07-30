# ADR-0154 — Endeudamiento e Índice Líder salen del ITVC; el líder pasa a validar el ITCM

- **Estado**: Aceptado
- **Fecha**: 2026-07-30
- **Ámbito**: cinturón vida cotidiana (ITVC-B100), dimensiones vulnerabilidad
  financiera y prospectivas de empleo; validación externa del ITCM
- **Descarta**: ADR-0112 (el líder integra el ITVC) y el reparto 50/50 de
  ADR-0067, que estaba declarado provisorio
- **Relacionados**: ADR-0022 y ADR-0153 (patrón `*_OCULTOS`, no hay cards de
  contexto), ADR-0108 (matriz de redundancia), ADR-0045 (no mover pesos para que
  un número quede mejor), ADR-0020 (flag de dimensión crítica), ADR-0033 (techo
  de winsorización)

## Contexto

Apunte del editor: «pobreza, endeudamiento e índice líder se va (este último
probar como validador de macro)». La pobreza se resolvió en ADR-0153. Acá van
los otros dos, que **se van por motivos distintos** — conviene no mezclarlos,
porque el argumento que sirve para uno no sirve para el otro.

## 1. `endeudamiento_familiar`: redundante, en el techo, y de signo equívoco

Los tres motivos, en orden de peso creciente:

**Es redundante.** Participaba en **6 de los 24 pares altos** del cinturón, y su
tope es r = **+0,943 contra `brecha_salario_cbt`**, que es el componente más
pesado del índice (17,06%). También +0,919 con alimentos y −0,858 con alquiler.
Al salir, los pares altos del ITVC bajan de **24 a 17** y el r absoluto medio de
0,413 a 0,391.

**Estaba clavado en el techo.** Era el único componente tocando el tope de
winsorización de ADR-0033: índice crudo **171,5** recortado a 140. Y no es un
detalle de un mes — cruzó el techo en **diciembre de 2024** y quedó ahí, así que
durante **18 de los 31 meses** de la serie aportó una constante, es decir
varianza cero.

**Y el signo es equívoco, que es lo que decide.** El índice **no** está
invertido: mide el stock real de crédito de consumo de familias y lee que crezca
como *acceso al crédito* — así lo dice el propio fetcher. Con la deuda real
**+71,5% sobre la base** y la morosidad **multiplicada por más de cinco** en el
mismo período, esa lectura no se sostiene: no es más acceso, es consumo
financiado con crédito que no se paga.

El efecto sobre el tablero era concreto: el componente en 140 promediaba contra
la mora en **17,2** y dejaba la dimensión en **78,6**. O sea que el componente
**tapaba exactamente la señal que la dimensión existe para dar.**

La dimensión queda con la mora sola. Precedente de dimensión con un solo
indicador: `seguridad`. El peso **nominal** de la dimensión no se toca —bajarlo
porque el ITVC cae sería mover un peso para que el número quede mejor, prohibido
por ADR-0045.

## 2. `indice_lider`: no es redundante, mide otra cosa

Acá el argumento empírico **no** aplica y hay que decirlo: el líder participa en
apenas **2 de los 24 pares altos**, y uno de los dos es justamente con
endeudamiento, que se va en este mismo cambio. No sale por redundante.

Sale porque mide otra cosa. Es un índice de **ciclo de la actividad**, construido
para anticipar puntos de giro macroeconómicos, no una condición de la vida
cotidiana de los hogares. El argumento de ADR-0112 para incorporarlo —«el único
componente del cinturón que mira adelante»— sigue siendo cierto; lo que cambió
es la conclusión: mirar adelante no lo vuelve parte de este cinturón.

Los cuatro componentes que quedan en prospectivas de empleo **absorben
proporcionalmente** (÷0,87), regla simétrica de la que rige las altas, y
conservan su orden relativo:

| componente | antes | después | efectivo |
|---|---|---|---|
| `empleo_registrado` | 0,35 | 0,4023 | 6,03% |
| `mortalidad_pymes` | 0,23 | 0,2644 | 3,97% |
| `despacho_cemento` | 0,21 | 0,2414 | 3,62% |
| `indice_lider` | 0,13 | — | — |
| `pluriempleo` | 0,08 | 0,0919 | 1,38% |

## 3. El líder como validador del ITCM: funciona, y cubre un hueco real

Lo que el editor pidió probar. Resultado, sobre 31 meses:

| | r | n |
|---|---|---|
| niveles (ITCM vs líder) | **+0,698** | 31 |
| **primeras diferencias** | **+0,419** | 30 |
| líder adelantado 1 mes vs ITCM | +0,394 | 31 |
| líder adelantado 3 meses vs ITCM | −0,166 | 31 |
| ITCM adelantado 1 mes vs líder | +0,740 | 30 |

**Cubre un hueco real.** El ITCM tenía un solo validador, el riesgo país, que da
r = −0,819 en niveles pero **−0,083 en primeras diferencias**: fuera de la
tendencia común no valida nada. El **+0,419 en diferencias** del líder es el más
alto de todo el proyecto — por encima del EPU contra el ITCP (−0,397), del
Merval contra el ITCG (+0,135) y del ICC contra el ITVC (+0,167).

**Y hay un resultado que va en contra del nombre del índice, y no se puede
publicar al revés: el que adelanta es el ITCM, no el líder.** Con el ITCM
adelantado un mes el ajuste **mejora** (+0,740 contra +0,698 contemporáneo);
con el líder adelantado un mes **empeora** (+0,394), y a tres meses cambia de
signo (−0,166). Los cinco pares se publican justamente para que la lectura no se
pueda invertir: sirve como validación **contemporánea**, no como alerta
temprana. Escribir «el líder anticipa al ITCM» sería falso, y era la frase que
salía sola.

## 4. Lo incómodo: la validación del ITVC baja mucho, y el número honesto es el nuevo

El ITVC↔ICC cae de **+0,558 a +0,337** sin ICC (y de +0,674 a +0,458 completo).
Es una caída grande y no se resuelve con una explicación cómoda, así que se
atribuyó componente por componente sobre los mismos datos:

| escenario | r (sin ICC) |
|---|---|
| estado anterior | +0,558 |
| sacando **sólo el líder** | +0,557 |
| sacando **sólo endeudamiento** | +0,339 |
| hoy (sin los dos) | +0,337 |

**Toda la caída es endeudamiento.** Y el mecanismo está medido, no supuesto: la
pérdida se concentra en **niveles (−0,221)** y casi no aparece en **primeras
diferencias (−0,023)**, diez veces menos. Lo que se perdió era **tendencia
compartida, no co-movimiento**: endeudamiento era una rampa que sube 64,6 puntos
y no baja en 20 de 31 meses, y encima estuvo pegada al techo desde dic-2024, así
que la correlación que aportaba venía del tramo de 2024.

Dicho de frente: **el +0,558 anterior estaba en buena medida fabricado por la
tendencia de un componente de signo equívoco y varianza nula en más de la mitad
de la serie.** El +0,337 es el número honesto, y deja al ITVC con la validación
externa más débil de los cuatro cinturones. Eso es información para el editor,
no una objeción al cambio: un validador que se satisface con un componente que
lee el endeudamiento creciente como mejora estaba midiendo peor de lo que su
número sugería.

Se registra también **por qué no se cerró con la explicación fácil**. La primera
redacción de esta sección decía que la baja era aceptable porque el ICC es
expectacional y la pobreza/mora son materiales. Puede ser cierto y no alcanza:
es el mismo argumento —«baja pero se justifica»— que en ADR-0153 resultó ser una
racionalización sobre un dato mal fechado. Por eso acá se midió la atribución
antes de escribir la conclusión.

## Decisión

1. `endeudamiento_familiar` e `indice_lider` **salen del ITVC** y van a
   `VIDA_OCULTOS`: se siguen relevando y sus series se siguen publicando, pero no
   son cards. Es el quinto cinturón en tener lista de ocultos, con lo que los
   cinco usan el mismo patrón (ADR-0153: no hay cards de contexto).
2. Vulnerabilidad financiera = `mora_familias` al 100%. Prospectivas de empleo
   renormaliza sobre los cuatro que quedan.
3. El **Índice Líder REEMPLAZA al riesgo país (EMBI) como ancla de validación
   externa del ITCM** — ver la enmienda de abajo. Se publican los cinco pares,
   incluidos los adelantos en las dos direcciones, para que la lectura no pueda
   invertirse.

## Consecuencias

- **ITVC 96,4 → 90,2** y tensión del cinturón **5,7 → 7,0**. La banda pasa de
  «sin cambios» a **deterioro moderado**, que es un cambio de titular del
  tablero público. Casi todo el movimiento (−6,1 de −6,2) es la dimensión de
  vulnerabilidad, que pasa de 78,6 a **17,2** al quedar apoyada en la mora sola.
- **Eso no es deterioro nuevo**: la mora ya estaba en 17,2 y el número anterior
  la promediaba con un componente en el techo. El cinturón venía informando
  «sin cambios» sobre una morosidad casi seis veces la de la transición.
- La dimensión sigue marcada como **crítica** (ADR-0020), que es el mecanismo
  previsto para señalizar una caída sin recortarla: el techo de winsorización es
  sólo hacia arriba.
- El ITVC queda con **16 componentes** puntuando y la matriz de redundancia con
  120 pares, 17 altos.
- Las dos fichas metodológicas se dan de baja, siguiendo el patrón de los
  ocultos ya existentes (`badlar`, `protestas_caba`, `rotacion_gabinete`): sin
  ficha, con rótulo y con entrada en `formulas`/`descripciones`.
- Queda **una dimensión con un solo componente** y sin margen de
  renormalización: si la planilla del BCRA falla, vulnerabilidad se queda sin
  dato y su 10% se reparte entre las otras cinco. Antes el endeudamiento la
  cubría. Es el costo de la decisión y va declarado en la ficha de la mora.

## Enmienda (2026-07-30, mismo día): el líder REEMPLAZA al EMBI, no lo acompaña

La primera implementación entendió mal la decisión del editor y sumó el líder
como **segundo** contraste del ITCM, dejando al EMBI como ancla graficada. La
decisión era **cambiar la fuente de validación**: el ancla del cinturón macro es
el líder y el EMBI pasa a segundo plano.

Corregido: la sección de validación de macro grafica ITCM contra el líder
(correlación positiva esperada), y el EMBI se reporta en la conclusión —con su
−0,819 en niveles y su −0,083 mes a mes— como explicación de por qué se cambió.
En la matriz de validación cruzada el par propio del ITCM pasa a ser la
actividad, y el EMBI se conserva como **quinta columna** porque sigue aportando
poder discriminante (la nota publicada sobre la celda ITCP×riesgo depende de él).

Detalle de implementación que hay que recordar si se vuelve a mover un ancla: la
matriz cruzada **derivaba sus series externas de los pares graficados de cada
cinturón**. Con el ancla cambiada, la columna «riesgo país» habría traído los
valores del líder bajo la etiqueta del EMBI, sin fallar nada. Ahora el riesgo
país se lee de su propia serie (`riesgo_pais_mensual`).

### El costo del cambio, medido: el ITCM deja de pasar su prueba discriminante

Con el EMBI como par propio, la correlación más fuerte del ITCM era con su
propio par. Con el líder, no:

| índice | par propio | mayor correlación ajena |
|---|---|---|
| ITCM | +0,70 (actividad) | **−0,82 riesgo país**, +0,75 Merval |
| ITCG | +0,75 (Merval) | **−0,87 riesgo país** (ya fallaba antes) |
| ITVC | +0,34 (ICC) | **+0,51 actividad** (falla nueva, por la columna nueva) |
| ITCP | −0,49 (EPU) | −0,27 actividad — el único que pasa |

O sea: el líder es el contraste que valida **mes a mes** (+0,419 contra −0,083
del EMBI), y a la vez **no** es el correlato más fuerte del ITCM en niveles. Las
dos cosas son ciertas y las dos se publican. La frase de la matriz que antes
decía que las celdas cruzadas eran «del mismo orden en más de un caso» —con un
ejemplo escrito a mano— pasa a **derivarse de los números en cada corrida**, para
que no pueda sobreafirmar separación que la muestra no da.

Queda anotado como pendiente editorial: si el criterio del proyecto para elegir
ancla es «la que valida en diferencias» o «la que más correlaciona en niveles».
Acá se eligió la primera por decisión del editor; son criterios distintos y
llevan a anclas distintas.