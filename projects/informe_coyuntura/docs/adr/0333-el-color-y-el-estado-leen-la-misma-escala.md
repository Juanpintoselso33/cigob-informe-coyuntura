---
madr: 4
id: '0333'
estado: 'aceptado'
fecha: 2026-09-20
cinturon: 'transversal'
archivos: ['config.py', 'scripts/parametrica.py', 'tests/test_color_y_estado_no_se_contradicen.py']
relacionado: ['0181', '0195']
ambito: 'Umbral `ESTABLE_MAX` y `CORTES_SEMAFORO` — cómo se nombra la tensión 0-10, no cómo se calcula'
origen: 'Juan, 20-sep-2026: «¿por qué macro pasó a tensión?». Macro no había pasado a nada —está en `en_tension` desde agosto— pero al ir a explicarlo apareció que el titular decía «3,7 — Sin tensión relevante» y el cinturón, con el mismo 3,7, decía «en tensión».'
---

# ADR-0333 — El color y el estado leen la misma escala y tienen que decir lo mismo

## Contexto y planteo del problema

La tensión 0-10 de un cinturón se publica **dos veces, con palabras distintas**:

- como **color de semáforo**, que la web enuncia «Sin tensión relevante» /
  «Tensión moderada» / «Tensión alta» / «Tensión crítica»;
- como **estado del cinturón**: «estable» / «en tensión» / «tensionado».

Cada uno tenía su propia tabla de cortes, y no coincidían en el primero:

| | primer corte | segundo | tercero |
|---|---|---|---|
| `CORTES_SEMAFORO` (ADR-0181) | verde hasta **4,0** | amarillo 6,0 | naranja 8,0 |
| `UMBRALES` (ADR-0195) | estable hasta **3,0** | en tensión 6,0 | tensionado > 6 |

Resultado: **todo lo que caía entre 3,0 y 4,0 se publicaba con dos etiquetas
opuestas**. Le pasaba a macro. Su ITCM es 63,1, que da tensión
(100 − 63,1) / 10 = **3,69**: el titular lo mostraba verde con la leyenda «Sin
tensión relevante» y la card del cinturón, con el mismo número, decía «en
tensión». Un lector no tiene forma de saber que son dos tablas.

No era un caso de borde raro: al medirlo sobre el snapshot del 20-sep-2026,
**10 de los 94 elementos con semáforo** caían en esa franja.

## Factores de decisión

- Las dos lecturas describen **el mismo número en la misma escala**. Que una
  diga tensión y la otra no es un defecto, no un matiz.
- Uno de los dos cortes tiene que ceder, y la pregunta es **cuál está
  anclado a algo**.
- No se puede arreglar dejando las dos tablas escritas por separado: volverían a
  separarse en el próximo cambio.
- El cambio no puede tocar `es_tensionado` ni la alerta multicinturón, que
  dependen del segundo corte y no del primero.

## Opciones consideradas

1. **Mover el corte del color de 4,0 a 3,0**, para que siga al estado.
2. **Mover `ESTABLE_MAX` de 3 a 4**, para que el estado siga al color — elegida.
3. Dejar las dos tablas y explicar la diferencia en la metodología.

## Decisión

**Opción 2**, y además `CORTES_SEMAFORO` pasa a **derivarse de `UMBRALES`** en
vez de repetir los números.

Lo que decide entre la 1 y la 2 es de dónde sale cada valor:

- El **4,0 del color está anclado y documentado**. ADR-0181 eligió los cortes
  60/40/20 —los bordes de `BANDAS_INTERPRETACION`— después de descartar
  alternativas (85/55/25, y las cinco tablas distintas que traían los documentos
  de CIGOB), con el criterio explícito de que «los cortes tienen que derivarse de
  algo que el informe **ya publica**». En un índice 0-100, tensión 4 es el
  puntaje 60: el límite entre «moderadamente aflojado» y «moderadamente
  apretado».
- El **3 del estado no sale de ningún lado**. ADR-0195 lo arrastró al unificar
  tres criterios que estaban dando resultados distintos, y su texto se ocupa de
  esa unificación, no de justificar el valor. No corresponde a ningún borde de
  banda: tensión 3 es el puntaje 70, que no separa nada.

O sea: el estado era **más estricto que el método que resume**. Con ITCM 63,1 el
propio informe lee «moderadamente aflojado» y el semáforo pinta verde, mientras
el estado decía «en tensión». Mover el 3 al 4 no afloja un criterio: lo alinea
con la interpretación que el índice ya publica.

La opción 1 se descartó porque rompía el anclaje de ADR-0181 —el primer corte
dejaría de coincidir con un borde de banda— y hacía fallar las once pruebas que
verifican esa correspondencia. La opción 3 se descartó porque la contradicción
la ve el lector en la portada, no en la metodología.

### Consecuencias

Medido sobre el snapshot del 20-sep-2026, antes y después:

| Cinturón | score | antes | después |
|---|---|---|---|
| **macro** | 3,7 | `en_tension` | **`estable`** |
| política | 2,9 | estable | estable |
| vida cotidiana | 6,3 | tensionado | tensionado |
| gestión | 2,0 | estable | estable |

- **Cambia un solo cinturón.** El score global sigue en 3,7 y la alerta
  multicinturón sigue en `false`: depende de `es_tensionado`, que mira el
  segundo corte (6) y no se tocó.
- Los colores **no cambian**: los cortes son los mismos 4/6/8 de siempre, ahora
  derivados en vez de repetidos.
- `detectar_barbarismo` elige el riesgo dominante entre los cinturones «en
  tensión o más», así que macro deja de ser candidato. Hoy no mueve el
  resultado —vida cotidiana, en 6,3, ya dominaba— pero es un cambio de
  mecanismo y queda dicho.
- Un cinturón entre 3 y 4 va a leerse «estable» donde antes decía «en tensión».
  Es lo que el método siempre dijo de él; lo que cambió es que ahora las dos
  capas lo dicen igual.

### Confirmación

`tests/test_color_y_estado_no_se_contradicen.py`, cuatro casos, y el que hace el
trabajo **barre las 1.001 centésimas de 0,00 a 10,00** y exige que color y
estado coincidan en todas. No comprueba un número: comprueba que las dos tablas
sigan atadas.

Los otros tres cierran los flancos: que los cortes del color salgan de
`UMBRALES` y no estén escritos aparte, que el caso que lo destapó (tensión 3,69)
ya no se contradiga, y que los bordes exactos caigan del mismo lado en las dos
tablas.

Probado rompiéndolo, con el bytecode borrado: al volver a cablear el primer
corte en 4,0 con `ESTABLE_MAX` en 3, **caen los cuatro**.

Las once pruebas de `tests/test_semaforo.py` que verifican la correspondencia
entre los cortes y los bordes de `BANDAS_INTERPRETACION` siguen en verde: esta
decisión las respeta, es justamente por eso que cedió el otro lado.

## Pros y contras de las opciones

**Opción 2 (elegida).** Bueno: deja las dos capas diciendo lo mismo, respeta el
anclaje documentado de ADR-0181 y ata las tablas para que no vuelvan a
separarse. Malo: reclasifica como «estable» una franja que el tablero venía
llamando «en tensión», y un lector que siga la serie de estados va a ver el
salto sin que haya cambiado ningún dato.

**Opción 1.** Bueno: erraría hacia mostrar más tensión, que en un monitor es el
lado seguro. Malo: rompe el criterio con el que ADR-0181 eligió los cortes y
deja el primer borde sin correspondencia con nada.

**Opción 3.** Bueno: no cambia ningún número publicado. Malo: pide que el lector
lea la metodología para entender por qué la portada se contradice sola.

## Más información

- ADR-0181 — por qué el color es la tensión ya publicada y de dónde salen
  60/40/20.
- ADR-0195 — la unificación que dejó `ESTABLE_MAX` en 3 sin justificarlo.
- El hallazgo no salió de ningún gate: salió de ir a explicar por qué macro
  estaba «en tensión» y encontrar que, según qué parte de la misma página se
  mirara, no lo estaba.
