---
madr: 4
id: '0257'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [desequilibrio_monetario]
archivos: ['scripts/desequilibrio_monetario.py', 'scripts/itcm.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'tests/test_desequilibrio_monetario.py']
relacionado: ['0252', '0192', '0082']
ambito: 'Cinturón macro · ITCM · `desequilibrio_monetario` · ventana de calibración de A y esquinas cruzadas de la matriz'
origen: 'Deuda declarada en ADR-0252: la asimetría de la matriz se justificaba con la tesis de la fuga y quedó sin fundamento'
---

# ADR-0257 — Los dos componentes, el mismo régimen y el mismo peso

## Contexto y planteo del problema

ADR-0252 dejó una deuda escrita: la asimetría de la matriz —degradar B cuesta
**77,5** puntos de tensión y degradar A sólo **40**— se apoyaba en la tesis de
que la fuga fuera del sistema es la señal grave. Como B no observa fuga sino
**compra neta de divisas**, la asimetría quedó en pie sin el argumento que la
sostenía.

Al ir a saldarla apareció un segundo defecto, más grande, que la escondía.

### Los dos componentes no se calibran en el mismo régimen

ADR-0192 fijó la ventana de **B** en la apertura del cepo a personas humanas,
con un argumento explícito: *«bajo cepo este flujo daba ~0 por falta de acceso,
no por confianza»*. Y calibró **A** contra **2021-01 / 2026-08**, donde **51 de
esos 68 meses son de cepo**.

El argumento vale igual para A. Un ratio alto de pesos transaccionales bajo cepo
no mide confianza en el peso: mide que no había dónde ir. La regla se aplicó a
un componente y no al otro.

Las dos distribuciones casi no se tocan:

| | mínimo | p25 | mediana | p75 | máximo |
|---|---:|---:|---:|---:|---:|
| con cepo (51 meses) | 33,14 | 37,26 | **40,29** | 45,10 | 49,96 |
| régimen abierto (17 meses) | 30,60 | 32,05 | **32,83** | 34,46 | **37,65** |

El **máximo** del régimen abierto cae por debajo de la **mediana** del cepo. Con
los cortes viejos, A quedaba clavada contra su piso: posición media **0,15**, y
**11 de 15 meses por debajo de 0,25**. La matriz A × B era, en los hechos, casi
unidimensional — el 94% de la varianza de la tensión publicada venía de B.

Y de ahí la trampa: **con A clavada, la asimetría parecía inerte**. Aplanarla
movía el último mes 1,15 puntos. Esa lectura era un artefacto de la ventana mal
puesta, no una propiedad del indicador.

## Factores de decisión

- **La misma regla para los dos componentes**, o el argumento de ADR-0192 no es
  un argumento sino una preferencia.
- **No reponer una justificación por decreto.** La asimetría perdió su
  fundamento; inventarle otro para conservar el número sería peor que el error.
- **Reproducibilidad**: los cortes van congelados, como los de B.
- **No confundir severidad con diagnóstico**, que es lo que el esquema de
  colores hacía.

## Opciones consideradas

Sobre la ventana de A:

1. **Dejarla en 2021-01** y anotar la inconsistencia.
2. **Llevarla a 2025-04**, la misma que B.

Sobre las esquinas cruzadas:

- **A — Conservar 40 / 77,5** y buscarle un fundamento nuevo.
- **B — Ordenarlas con evidencia**, midiendo cuál componente sigue mejor al
  estrés macro.
- **C — Igualarlas**, y con eso no afirmar ningún orden.

## Decisión

**Ventana: opción 2.** `CORTES_A` pasa a los percentiles de **2025-04 / 2026-08**
(17 meses): `(30,60 · 32,05 · 32,83 · 34,46 · 37,65)`. Congelados, igual que los
de B. Con ellos A se reparte —posición media 0,51, desvío 0,27, sólo 3 de 15
meses por debajo de 0,25— y la matriz vuelve a ser de dos dimensiones.

**Esquinas: opción C.** Las dos cruzadas pasan a valer **58,75 cada una**, que
es el promedio de las que fijó la ficha: se reparte en partes iguales la **misma
severidad total** que ella les había asignado a las dos juntas (40 + 77,5 =
117,5). Cambia el **orden**, no el **nivel** — que es exactamente lo que ADR-0252
invalidó y nada más. Las dos puras no se tocan: nada degradado sigue en 0 y todo
degradado en 90.

La opción B se **intentó y falló**, y ese es el resultado que justifica la C.
Contra tres referencias externas del propio proyecto, con los 15 meses
disponibles:

| referencia | r con la degradación de A | r con B |
|---|---:|---:|
| EPU (incertidumbre, ↑ = peor) | 0,046 | **0,360** |
| Merval en dólares (↑ = mejor) | **+0,415** ⚠ | −0,571 |
| índice líder (↑ = mejor) | −0,454 | **+0,126** ⚠ |

Cada componente sale con el **signo invertido** contra al menos una referencia
(⚠), dos referencias ordenan al revés que la tercera, y con n=15 sólo uno de los
seis coeficientes llega a ser significativo. **El dato no puede ordenarlos.**
Cuando no se puede determinar un orden, lo honesto es no codificarlo.

La opción A quedaba descartada por lo mismo: cualquier fundamento nuevo sería
elegido para conservar un número que ya estaba escrito.

### Consecuencias

- **La forma de la matriz queda intacta.** La suma de las dos cruzadas es lo
  único que fija el término de interacción de la bilineal
  (`tensión = c·d_A + c·B + (90−2c)·d_A·B`), así que conservarla en 117,5 deja
  la interacción en los mismos **−27,5** que tenía. Se redistribuye, no se
  recalibra.
- **El valor publicado se mueve, y la mayor parte es la ventana.** Junio de 2026
  pasa de **50,86 a 38,69** puntos de tensión (puntaje ITCM 49,1 → 61,3).
  Atribuido:

  | cambio | jun-2026 | media de los 15 meses |
  |---|---:|---:|
  | punto de partida | 50,86 | 61,77 |
  | sólo la matriz simétrica | 60,56 | 68,15 |
  | sólo la ventana de A | 37,19 | 52,87 |
  | los dos | **38,69** | **52,59** |

  O sea: lo que se vino a arreglar mueve **+9,70**; el defecto que apareció en
  el camino mueve **−13,67**. Van declarados por separado a propósito, y que se
  compensen en parte no es diseño: la ventana vieja tenía a A clavada en
  degradado, así que encarecer esa esquina pesaba justo donde el indicador ya
  estaba.
- **Los cuadrantes dejan de llamarse por colores.** Pasan a
  `sin_tension · solo_liquidez · solo_presion · liquidez_y_presion`. Con las
  cruzadas iguales, un cuadrante llamado «naranja/rojo» que puntúa lo mismo que
  uno llamado «amarillo» sería una etiqueta que miente.
- **Las bandas del ITCM siguen siendo cuatro y con los mismos cortes**, pero
  dejan de pretender una esquina por tramo. Eran una escala de severidad
  haciéndose pasar también por el mapa de la matriz; ahora la severidad la dice
  la banda y el diagnóstico lo dice el cuadrante, que viajan aparte en el
  snapshot.
- **Lo que el indicador existe para exponer no cambia**: que un componente esté
  en su mejor valor no puede leerse como confianza si el otro está en el peor.
  Las dos esquinas cruzadas siguen a 45 puntos del verde.

### Confirmación

`tests/test_desequilibrio_monetario.py`. Cuatro mutaciones, cuatro fallas:
reponer la asimetría, volver los cortes de A a la era del cepo, volver sólo la
ventana declarada, y volver un nombre de color.

La guarda de la simetría **no pide el número 58,75**: pide que las dos cruzadas
valgan lo mismo. Recalibrar el nivel es legítimo; volver a afirmar un orden
entre ellas es volver a afirmar lo que no se puede sostener.

**Una guarda vieja atrapó una sobrecorrección de esta misma entrega**, y vale la
pena dejarlo escrito porque es el argumento de por qué el nivel se conserva. La
primera versión igualó las cruzadas en **45**, el punto medio de las dos puras.
Ahí la bilineal se vuelve `45·d_A + 45·B`, que es **exactamente el promedio** de
las dos degradaciones — y no promediar es la premisa fundacional del indicador
(ADR-0192: «el resultado sale de CRUZARLOS, no de promediarlos»), que ADR-0252
no tocó. Con 45, un componente en su mejor valor y el otro en el peor daba 45
sobre 100: media tabla. Quitar el orden se habría llevado puesta, de contrabando,
la razón de ser del indicador. Lo agarró `test_web_labels.py`, que exigía que la
fórmula pública no pareciera un promedio. Quedó como guarda propia:
`test_cruzar_sigue_sin_ser_promediar`, escrita contra el 45 y no contra el
58,75.

## Pros y contras de las opciones

### Ventana 1 — dejar A en 2021-01

- Bueno: 68 meses en vez de 17, percentiles más estables, y no cambia ningún
  número ya publicado.
- Malo: mide el presente contra una distribución de otro régimen monetario, que
  es exactamente lo que ADR-0192 rechazó para B. Deja A clavada contra el piso y
  el indicador reducido a uno solo de sus dos componentes.

### Ventana 2 — llevarla a 2025-04 *(elegida)*

- Bueno: una sola regla para los dos componentes, y A vuelve a discriminar.
- Malo: 17 meses es una ventana corta y los percentiles se van a mover cuando se
  recalibre. Es la misma limitación que B ya tiene y que el proyecto aceptó por
  la misma razón.

### Esquinas A — conservar 40 / 77,5

- Bueno: no cambia nada publicado.
- Malo: conserva una afirmación cuyo fundamento ADR-0252 anuló.

### Esquinas B — ordenarlas con evidencia

- Bueno: sería la respuesta más fuerte de todas.
- Malo: con 15 meses el dato no alcanza, y lo poco que dice se contradice.
  Volvería a intentarse con más muestra.

### Esquinas C — igualarlas *(elegida)*

- Bueno: no afirma lo que no se puede sostener y no toca nada más — ni el nivel
  de las cruzadas, ni la interacción, ni las dos esquinas puras.
- Malo: pierde la lectura de cuatro colores, que era cómoda. Se recupera
  separando severidad de diagnóstico, que además estaban confundidos.

## Más información

Queda **abierto y declarado**: si en algún momento hay muestra suficiente para
ordenar los componentes con evidencia, la simetría es lo primero que hay que
volver a mirar. La guarda está escrita para permitir esa revisión —pide igualdad,
no un número— y este ADR deja la medición con la que se comparará.

- ADR-0252, que dejó la deuda: `0252-la-compra-de-divisas-no-dice-adonde-fue-el-dinero.md`
- ADR-0192, que fijó la matriz y las ventanas originales.
