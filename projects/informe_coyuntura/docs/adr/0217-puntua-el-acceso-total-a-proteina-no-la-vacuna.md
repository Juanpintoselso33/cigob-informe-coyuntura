---
madr: 4
id: '0217'
estado: 'aceptado'
fecha: 2026-08-20
cinturon: 'vida'
indicadores: [consumo_carnes_total, consumo_carne]
archivos: ['scripts/itvc.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'scripts/gate_calidad.py', 'tests/test_carne_compuesto.py']
supersede: ['0215']
cierra: ['0216']
relacionado: ['0018', '0119']
ambito: 'ITCIS · componente de proteína animal · qué puntúa y con qué serie'
origen: 'Editor, agosto de 2026: "el indicador tiene que cruzar los tres tipos de consumo, y la card termina diciendo vacuna — al pedo lo que estamos haciendo"'
---

# ADR-0217 — Puntúa el acceso total a proteína, no la carne vacuna

## Contexto y planteo del problema

La ficha de proteína animal existe por un motivo preciso: **leer la caída del
consumo de carne vacuna como pérdida de poder adquisitivo es un falso
positivo.** Buena parte de esa caída es sustitución hacia pollo y cerdo, que es
un cambio de hábito y de precios relativos, no empobrecimiento. Para
distinguirlo propuso tres componentes —A vacuna, B total, C ratio— tratados,
textual, como *"un único indicador compuesto"*.

Se implementó la explicación y no el compuesto. Hasta hoy:

| | Antes |
|---|---|
| Puntuaba | la vacuna sola, 89,3 rebaseado |
| El total | card al lado, sin entrar al cálculo |
| El ratio | sin número propio; sólo dentro del texto del color |

O sea: se sumaron cerdo y pollo, se escribió la matriz que explica la
sustitución, y **el número que mueve el índice siguió mirando una sola carne**.
La decisión del 12 de agosto —*"no hay nada que repartir, el compuesto conserva
el 3,02%"*— da por hecho un compuesto que nunca existió.

El bloqueo era de datos, no de criterio.
[[0215-la-carne-se-mide-con-dos-fuentes-y-se-declara]] lo dejó escrito: el
tablero de SAGYP publica el per cápita del total ya calculado, pero es **una
foto del mes** que se pisa en cada edición, así que no tiene historia contra la
cual rebasear al 4T-2023. La vacuna, en cambio, tenía CICCRA con serie mensual
desde octubre de 2023. Se puntuaba lo que se podía medir, no lo que se quería
medir.

## Factores de decisión

- **El componente tiene que medir lo que la ficha dice que mide**: acceso a
  proteína cárnica, no consumo de una carne.
- **La base del índice es el 4T-2023.** Cualquier serie que entre necesita
  llegar hasta ahí; una base distinta se lee distinto que los otros quince
  componentes.
- **El nivel per cápita oficial es lo que le sirve al lector.** "114,45
  kg/hab/año" dice algo; "95,0 de índice" no.
- **Una reconstrucción propia tiene que poder contrastarse contra la fuente
  oficial**, o es una cuenta nuestra sin control.

## Opciones consideradas

1. Reconstruir la serie del total desde la faena del INDEC y puntuar eso.
2. Acumular el per cápita de SAGYP mes a mes y esperar a tener historia.
3. Combinar A, B y C en un puntaje sintético con una fórmula propia.
4. Dejar que siga puntuando la vacuna.

## Decisión

**Opción 1.** El componente que puntúa pasa a ser **`consumo_carnes_total`**, y
la carne vacuna deja de puntuar y deja de ser card.

**La serie se reconstruye desde la faena mensual en toneladas del INDEC**,
verificadas contra su API el 2026-08-20:

| Serie | id | Desde |
|---|---|---|
| Faena pecuaria, vacunos | `40.3_VT_0_M_17` | 1998-01 |
| Faena pecuaria, porcinos | `40.3_PT_0_M_18` | 2006-01 |
| Faena pecuaria, aves | `40.3_AT_0_M_14` | 1991-01 |

Se suman las tres, se toma el promedio móvil de 12 meses —la misma ventana con
la que SAGYP publica su per cápita, y la que saca la estacionalidad fuerte de la
faena—, se divide por población y se rebasea al promedio del 4T-2023. La serie
resultante tiene 42 puntos y arranca en enero de 2023.

**La vacuna sigue relevándose**: es el Componente A y la mitad de la matriz A×B
que explica el color. Su valor se lee ahí adentro, no como card — porque una
card que no puntúa es la categoría que ADR-0153 dio de baja
([[0216-o-integra-el-indice-o-no-es-card]]).

**La card publica el nivel oficial de SAGYP** (114,45 kg/hab/año), que es el
número con significado para el lector; el color y el puntaje salen del índice
reconstruido. Card y serie quedan por lo tanto en unidades y fuentes distintas,
así que el componente entra a `G3_EXCEPCIONES` con ese motivo escrito.

### Los dos supuestos, declarados

- **La faena es PRODUCCIÓN.** Sin netear exportaciones, el nivel no es consumo
  aparente. No importa para el puntaje: el índice se lee contra su propia base,
  así que lo que pesa es la evolución. Y el nivel per cápita que ve el lector
  no sale de acá, sale de SAGYP.
- **El pasaje a per cápita usa la población urbana total del INDEC**
  (`461.3_POBLACION_ANO_AEA_T_28_3`), trimestral, interpolada a meses y
  extendida con su propia pendiente. Es una proyección en línea recta de la
  fuente —crece exactamente 100 mil por trimestre—, no una estimación nuestra.

### Consecuencias

- **El componente pasa de 89,3 a 95,0.** La vacuna sola exageraba el deterioro:
  cae 10,7% contra el arranque del mandato, y el acceso total a proteína cae
  5,0%. Es exactamente la brecha que [[0119-pendientes-de-baja-prioridad-vida]]
  había medido en unos 7 puntos y decidido no corregir.
- **El ITCIS no se mueve: 90,7, tensión 6,9.** El componente pesa 1,12%, así
  que 5,7 puntos de mejora suya son 0,06 en el índice. La dimensión de ingresos
  sí sube, de 116,9 a 117,1.
- El cinturón mantiene **16 cards y las 16 puntúan**.
- La matriz A×B ahora cuelga del total, que es el que tiene card, y lee la
  vacuna. El descarte de la vacuna va **después** de `_semaforos()` por eso.
- El indicador queda con dos fuentes por diseño —INDEC para la evolución, SAGYP
  para el nivel— y eso es lo que supersede a ADR-0215: aquel declaraba una
  divergencia accidental entre card y serie; ésta es deliberada y tiene otro
  motivo.

### Confirmación

La prueba de que la reconstrucción mide lo que dice es contrastarla contra la
fuente oficial: **la variación interanual reconstruida da −2,86% y SAGYP publica
−1,69% para el total**, 1,17 pp de brecha, mismo signo y mismo orden. La
diferencia es esperable —la faena no netea exportaciones— y
`tests/test_carne_compuesto.py` falla si supera 3 pp, con un mensaje que dice
que no es un bug de código sino que la faena dejó de aproximar el consumo.

El mismo test cuida que puntúe el total y no la vacuna, que la vacuna no vuelva
como card, que la matriz siga explicando el color, y que la serie llegue al
4T-2023.

## Pros y contras de las opciones

**1. Reconstruir desde faena.** A favor: da historia real hasta antes del
mandato, viene de una fuente oficial con API estable, y se puede contrastar
contra SAGYP mes a mes. En contra: mide producción y no consumo aparente, y
necesita el supuesto de población.

**2. Acumular SAGYP y esperar.** A favor: es el per cápita oficial, sin
supuestos. En contra: la acumulación empezó el 12-ago-2026 y **por construcción
nunca va a contener el 4T-2023**. Esperar no resuelve: no hay contra qué
rebasear, ahora ni dentro de tres años.

**3. Fórmula sintética A+B+C.** A favor: usaría los tres componentes. En contra:
la ficha propone la matriz para el **color**, no una fórmula para el
**puntaje** — inventarla y publicarla como si el documento la dijera sería
atribuirle a la Fundación una decisión que no tomó.

**4. Dejar la vacuna.** A favor: cero trabajo. En contra: es el falso positivo
que la ficha vino a desarmar, publicado en el índice.

## Más información

- [[0119-pendientes-de-baja-prioridad-vida]] midió que la vacuna sigue al total
  con r=0,970 en niveles y r=0,987 en cambios, y por eso decidió no tocar el
  indicador. Ese argumento sostenía la **dirección**; el **nivel** quedaba
  exagerado en ~7 puntos, y es el nivel lo que puntúa.
- [[0018-itvc-parametrica-vida-cotidiana]] fijó el componente original `I_CC` en
  la carne vacuna de CICCRA, que es lo que este ADR reemplaza.
