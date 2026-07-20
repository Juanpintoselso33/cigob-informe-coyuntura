# ADR-0085 — La redundancia interna se mide en los tres índices, y en cambios además de niveles

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITCM · ITCG · ITCP · `validacion_externa.matriz_redundancia` · card pública "Consistencia interna" |
| **Fecha** | 2026-07-18 |
| **Amplía** | ADR-0075 (matriz de redundancia, sólo ITCM) |
| **Origen** | Pedido editorial de extender la card a los demás cinturones |

## Contexto

ADR-0075 publicó la matriz de redundancia sólo para el ITCM, dejando anotado
que "extender la medición a los otros tres índices no requiere cambios de
estructura". Se extiende ahora a **ITCG e ITCP**.

El ITVC queda afuera: es un índice base-100 continuo, sin bandas ni puntajes de
componente, así que la pregunta "cuánto se parecen los puntajes" no aplica en
los mismos términos.

## El problema que apareció al extenderla

La primera corrida sobre el **ITCG** devolvió un resultado imposible:

| par | r | n |
|---|---|---|
| protocolo antipiquetes × RIGI inversiones | **+1,000** | 24 |
| libertad de opción de salud × RIGI | +0,995 | 23 |
| privatizaciones × reestructuración de organismos | +0,993 | 32 |

Una correlación **exactamente 1,000** casi siempre es un artefacto, y lo era.
Esos indicadores son **contadores acumulados**:

- `libertad_opcion_salud`: 0 → 31,8
- `protocolo_antipiquetes`: 52,7 → 74,2, monótono

> **Corrección (ADR-0086, mismo día).** Los dos pares que involucran a
> `rigi_inversiones` no eran contadores acumulados: eran un **bug**. Su serie
> guardaba millones de dólares y sus bandas están calibradas en porcentaje, así
> que la reconstrucción le asignaba 10 durante todo 2024 y 100 desde ene-2025 —
> un escalón binario, que correlaciona 1,000 con cualquier otra serie monótona.
> El indicador salió de la matriz y el par desapareció.
>
> La explicación original era plausible, estaba bien argumentada y era falsa.
> Vale registrarlo: **el mecanismo correcto para el resto de los pares sirvió de
> tapadera para uno que no lo era**. Un número imposible admitía dos causas y se
> publicó la primera que encajaba, sin descartar la otra.

**Dos series que sólo suben correlacionan cerca de 1 aunque no compartan
ninguna información.** Es el artefacto clásico de correlacionar tendencias.
Publicar "34% de los pares se mueven muy juntos" en gestión habría presentado
como redundancia lo que era, sobre todo, el paso del tiempo.

## Decisión

La matriz se calcula **también sobre primeras diferencias**, y la card publica
las dos medidas. Correlacionar los cambios mes a mes cancela la tendencia común
y deja el co-movimiento real, que es el que efectivamente se cuenta dos veces al
promediar.

Es el test que la revisión adversarial de esta misma jornada había señalado como
disponible y no hecho — `_difs()` ya existía en el archivo.

### El resultado, en los tres índices

| índice | niveles \|r\| | % altos | **cambios \|r\|** | **% altos** |
|---|---|---|---|---|
| ITCM | 0,496 | 25% | **0,182** | **0%** |
| ITCG | 0,492 | 31% | **0,137** | **2%** |
| ITCP | 0,371 | 9% | **0,215** | **3%** |

(Las cifras del ITCG son las posteriores a ADR-0086; la corrida original, con el
indicador defectuoso adentro, daba 0,514 / 34% / 0,154 / 4%.)

**Al quitar la tendencia común, la redundancia prácticamente desaparece.** En el
ITCM ningún par supera el umbral.

Esto convierte en **medición** lo que ADR-0075 sólo podía afirmar como salvedad
cualitativa: decía que el co-movimiento "refleja sobre todo el proceso
macroeconómico, no necesariamente un defecto de construcción". Ahora está
contrastado: los componentes suben y bajan con el ciclo, pero sus movimientos
mensuales son en buena medida propios.

La card lo publica como el número decisivo, destacado junto a los otros tres.

### Lo que no cambia

La advertencia práctica al lector se mantiene intacta: **cuando varias
dimensiones coinciden en el diagnóstico, eso no son varias confirmaciones
independientes**. Que el acoplamiento sea tendencia y no información repetida
explica *por qué* ocurre, no lo vuelve inocuo para leer el índice.

## Consecuencias

- `matriz_redundancia()` es genérica: recibe escala, dimensiones y valores por
  mes. Las tres variantes por índice son envoltorios de tres líneas.
- Se extrajeron `_valores_itcg_por_mes()` y `_valores_itcp_por_mes()`, que ahora
  comparten reconstrucción y matriz — la misma corrección estructural de
  ADR-0082, para que no puedan divergir en qué componentes miran. La máscara de
  era de la eficacia legislativa (ADR-0070) queda dentro del helper.
- Un fallo en la matriz de un índice no tumba la corrida: se registra y sigue.
- **Política es el índice más sano de los tres**: \|r\| medio 0,371 en niveles y
  sólo 9% de pares acoplados, contra 25-34% de macro y gestión.

## Limitaciones declaradas

- Las primeras diferencias son más ruidosas que los niveles: con 24-32 meses,
  las correlaciones de cambios tienen intervalos amplios y se publican como
  orden de magnitud, no como estimación fina.
- Que el acoplamiento sea tendencia **no lo vuelve irrelevante**: si dos
  componentes comparten tendencia durante todo el período disponible, el índice
  sigue sin poder distinguirlos en ese tramo.
- El ITVC no se mide. Su equivalente sería correlacionar los índices base-100 de
  sus componentes, que es una pregunta parecida pero no la misma.
