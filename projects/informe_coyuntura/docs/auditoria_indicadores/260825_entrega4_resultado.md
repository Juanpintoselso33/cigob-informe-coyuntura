# Entrega 4 — resultado

**Fecha:** 25 de agosto de 2026 · **Estado:** código, tests y ADR completos.
**No se corrió el pipeline ni se publicó nada.**

Los cinco constructos de esta entrega no tenían mal la aritmética, ni el
universo, ni la fuente. Le ponían al número **un nombre que sus insumos no
sostienen**. Por eso acá casi no se mueven los valores: lo que cambia es lo que
el tablero afirma.

## 16 · `idm` — «Exceso de pesos sobre la demanda» → **Brecha de crecimiento real M3–M2** (ADR-0254)

Compara el crecimiento real del M3 privado contra el del M2 privado
transaccional. **Los dos son agregados monetarios.** Una demanda de dinero es una
función estimada —variables, forma funcional, período, validación— y nada de eso
existe acá, así que la palabra «exceso» no tenía contra qué medirse.

La lectura pública pasa de «sobran pesos» a lo que efectivamente muestra: hacia
dónde se mueven los pesos dentro del sistema. Fórmula, banda y peso intactos.

> **Anotado:** la banda se calibró leyendo la brecha como exceso monetario. Sigue
> siendo defendible por otra vía, pero merece revisarse ahora que el constructo
> se llama por su nombre.

## 17 · `desequilibrio_monetario` — se elimina «fuera del sistema» (ADR-0252)

El componente B se llamaba **«fuga fuera del sistema»** en seis lugares: el
módulo, la ficha, el rótulo público, la fórmula y dos celdas de la matriz. Mide
la **compra neta de divisas** del sector privado no financiero, y el BCRA estimó
que cerca del **80% quedó depositado localmente**. Comprar divisas y sacarlas del
sistema son dos actos distintos; acá sólo se observa el primero.

Las cuatro celdas pasan a describir la combinación observada:

| Celda | Antes | Ahora |
|---|---|---|
| verde | confianza real | liquidez transaccional alta y poca compra de divisas |
| amarillo | dolarización contenida en el sistema | menos pesos transaccionales, sin presión compradora |
| naranja/rojo | **fuga oculta fuera del sistema** | presión compradora alta pese a liquidez transaccional alta |
| rojo | deterioro dentro y fuera del sistema | menos pesos transaccionales y presión compradora alta |

> **Anotado, y es lo más importante de este caso:** toda la asimetría de la
> matriz —que degradar B cueste 77,5 puntos de tensión y degradar A sólo 40— se
> justificaba con la tesis de que *la fuga fuera del sistema es la señal grave*.
> Si B no identifica fuga, esa justificación se cae aunque el número no cambie.
> La asimetría queda en pie porque viene de las celdas que fijó la ficha
> original, pero **su fundamento ya no es el que se creía**.

## 18 · `icip` — «Capitalización digital» → **Pagos de servicios digitales y productividad** (ADR-0253)

En cuentas nacionales, los pagos al exterior por informática y nube son **consumo
intermedio**, no formación bruta de capital. Pagar la licencia de la nube todos
los meses no capitaliza a nadie.

La ficha ya declaraba la ambigüedad —«admite leerse como digitalización o como
dependencia tecnológica»— y no alcanzaba, porque el **nombre** afirmaba lo
contrario. Quien ve «Capitalización digital» no va a la ficha a enterarse de que
no es capitalización.

## 19 · `judicializacion` — **fuera del score** (ADR-0255)

El 1,57% son 114 sumarios que mencionan «medida cautelar» sobre 7.273 publicados
por SAIJ. Ese corpus **no identifica causas contra el Ejecutivo**: una cautelar
entre privados cuenta igual.

La auditoría proponía como mínimo renombrarlo a «densidad de menciones
cautelares». **No alcanzaba**: para puntuar hay que decidir un signo, y más
menciones cautelares en la jurisprudencia general no dicen nada sobre el
gobierno. Es el mismo razonamiento por el que `sentimiento_digital` salió en la
Entrega 2. Renombrar habría movido el problema del título al signo.

El rótulo se corrige igual, porque el indicador se sigue relevando.

## 20 · `sentimiento_digital`

Ya salió del score en la Entrega 2 (ADR-0248). Su rediseño es un proyecto nuevo y
prospectivo; la condición de reingreso está escrita y prohíbe explícitamente
reusar la correlación favorable de una canasta anterior.

## Impacto

| Cinturón | Publicado | E1 | E1+E2 | E1+E2+E3 | E1..E4 |
|---|---:|---:|---:|---:|---:|
| Macro (ITCM) | 3,6 | 3,5 | 3,5 | 3,6 | 3,6 |
| Política (ITCP) | 3,3 | 3,2 | 2,9 | 2,9 | 2,9 |
| Vida cotidiana (ITCIS) | 6,1 | 6,1 | 6,2 | 6,2 | 6,2 |
| Gestión (ITCG) | 2,7 | 2,5 | 2,1 | 2,1 | 2,1 |
| **Score global** | **3,9** | **3,8** | **3,7** | **3,7** | **3,7** |

**Ningún índice se mueve de forma visible**, y eso merece una observación. Tres de
los cuatro casos son renombres puros, así que no podían moverlo. El cuarto sí
salió del score, y aun así el ITCP se mueve **+0,19 puntos** (70,71 → 70,90):
`judicializacion` puntuaba 54,4 y la media de su dimensión era 59,4, así que
sacarlo apenas la corre.

O sea: **el indicador cuya interpretación estaba peor fundada era casi neutro en
el número**. Aportaba 4,6 sobre 10 de tensión leído en su propia escala, y quitarlo
no cambia el tablero. Es un recordatorio útil de que el daño de un constructo mal
nombrado no se mide por cuánto mueve el score, sino por lo que hace creer.

## Verificación

- `pytest tests -q`: **3001 pasan**, 3 se saltean, **5 fallan de forma esperada**
  (las mismas de siempre: comparan contra el snapshot publicado, que no se
  regeneró). Se resuelven en la Entrega 5.
- `npx tsc --noEmit`: limpio.
- Los tres renombres se probaron **rompiéndolos**: repuestos los rótulos
  anteriores, fallan seis guardas.
- Las guardas nuevas no verifican prosa linda: verifican que **las afirmaciones
  que la auditoría marcó no puedan volver** —«fuera del sistema»,
  «capitalización», «demanda de dinero», «exceso de pesos»— en ningún archivo de
  código ni de la capa pública, aceptando sólo las líneas que las citan para
  decir que no son ciertas.

## Deudas que quedan anotadas

1. **La asimetría de la matriz de `desequilibrio_monetario`** perdió su
   fundamento declarado. Revisar en la próxima recalibración.
2. **La banda de `idm`** se calibró bajo la lectura de exceso monetario.
3. **`icip` combina dos cosas heterogéneas** —pagos al exterior y productividad
   laboral— y eso es anterior a esta corrección; no se tocó.
4. Las opciones sustantivas de los cuatro casos (estimar una demanda de dinero,
   medir activos externos fuera del sistema, usar cuentas nacionales para
   inversión digital, construir el universo de causas contra el Ejecutivo) son
   **indicadores nuevos**, no rótulos distintos. La auditoría pide no
   implementarlas sin diseño y ADR previos, y no se implementaron.
