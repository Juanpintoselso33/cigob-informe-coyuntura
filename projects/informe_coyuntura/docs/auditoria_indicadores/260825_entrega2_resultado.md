# Entrega 2 — resultado

**Fecha:** 25 de agosto de 2026 · **Estado:** código, tests y ADR completos.
**No se corrió el pipeline ni se publicó nada.**

## Los tres indicadores suspendidos

| Indicador | Índice | Aportaba | Por qué sale |
|---|---|---:|---|
| `apoyo_empresario` | ITCP · sector privado (50%) | 6,4/10 de tensión | Saldo −0,429 sobre **7 textos codificados con 14 pendientes**, y entre los pendientes había apoyos y críticas de peso. Mide qué se alcanzó a codificar, no la postura del sector. |
| `reestructuracion_organismos` | ITCG · reforma del estado (25%) | 5,5/10 | `11/45` divide **normas** (que afectan ~18 entidades) por una **convención documental** que nadie fijó. El buscador además se saltea cierres conocidos (ENOHSA). |
| `sentimiento_digital` | ITCIS · percepción (18,18%) | empujaba el índice **arriba** | El volumen de búsquedas mide atención, y la atención no tiene signo. Validación externa adversa en cuatro cortes: r = −0,788 contra Ipsos, +0,082 en cambios contra el ICC, 34 de 42 ventanas con el signo opuesto. |

Los tres siguen relevándose y sus series se siguen publicando. Ninguno se muestra
como card: es la regla del tablero, cerrada tres veces (ADR-0051/0153/0189).

## La regla de pesos: qué se decidió y por qué

El handoff pedía renormalización **automática**, sin pesos escritos a mano. El
patrón anterior del repo (ADR-0186, `masa_salarial`) era **borrar el indicador de
la tabla de pesos y reescribir los de sus pares**. Funciona, pero con tres
suspensiones simultáneas significaba editar a mano tres dimensiones en tres
módulos, y deja los pesos renormalizados escritos como si fueran de diseño.

ADR-0245 cambia el mecanismo: el indicador sale del **cálculo**, la tabla no se
toca, y los que quedan absorben el hueco solos — que es lo que el motor ya hacía
con un indicador sin dato. Suspender es agregar una línea; reponer, sacarla.

| Dimensión | Antes | Después |
|---|---|---|
| ITCP · sector privado | brecha 50% · apoyo 50% | brecha **100%** |
| ITCG · reforma del estado | dotación 43,75% · gasto 31,25% · organismos 25% | dotación **58,33%** · gasto **41,67%** |
| ITCIS · percepción | ICC 81,82% · sentimiento 18,18% | ICC **100%** |

Ninguna dimensión cambió su peso frente a las otras.

## Impacto acumulado

| Cinturón | Publicado | Tras Entrega 1 | Tras Entrega 1+2 |
|---|---:|---:|---:|
| Macro (ITCM) | 3,6 | 3,5 | 3,5 |
| Política (ITCP) | 3,3 | 3,2 | **2,9** |
| Vida cotidiana (ITCIS) | 6,1 | 6,1 | **6,2** |
| Gestión (ITCG) | 2,7 | 2,5 | **2,1** |
| **Score global** | **3,9** | **3,8** | **3,7** |

Vida cotidiana **sube** su tensión: `sentimiento_digital` entraba en 140 sobre
una base de 100, o sea que empujaba el cinturón hacia arriba. Sacarlo quita una
mejora que no estaba fundada. Los otros dos bajan porque los suspendidos
aportaban tensión alta.

**Cuidado al leer esto.** Ninguno de estos movimientos describe la realidad
cambiando: describen dejar de puntuar tres mediciones mal fundadas. Que política
mejore 0,4 puntos no dice nada sobre la relación del Gobierno con el sector
empresario — dice que ya no se puntúa un saldo calculado sobre un tercio del
corpus.

## Un efecto de segundo orden que no estaba previsto

El test del piso de cobertura afirmaba que un mes incompleto del ITCG siempre da
**por debajo** del valor real, y era cierto en los **31 de 31** meses de la serie.
Dejó de serlo con esta entrega: `reestructuracion_organismos` era el **único
componente de Reforma del Estado que llegaba temprano**, y puntuaba bajo. Sin él,
la dimensión entera desaparece del subconjunto rápido y lo que queda puntúa alto,
así que desde may-2025 el recorte da **por encima** (ahora 17 de 31).

El piso sigue justificado: el desvío es grande y sistemático —mediana ~10 puntos,
más de 3 puntos en 30 de 31 meses—. Lo que cambió es que el **signo** dependía de
una composición que se movió. El test ahora afirma la magnitud, que es lo que se
sostiene, en vez del signo, que era cierto sólo hasta ayer.

## Verificación

- `pytest tests -q`: **2936 pasan**, 3 se saltean, **1 falla de forma esperada**.
- La falla es `test_fichas_pesos::test_los_pesos_que_afirman_las_fichas_son_los_vigentes`:
  compara el texto de la ficha contra el **snapshot publicado**, que todavía
  tiene los pesos viejos porque no se regeneró. La ficha de `icc_utdt` ya declara
  100% interno · 8,25% del índice, que es lo que calcula el código. **Se resuelve
  sola al regenerar en la Entrega 5**; es el orden que usa la CI (colectores →
  publicar → gate → pytest). Dejarla en verde exigiría escribir en la ficha un
  reparto que ya no existe.
- El mecanismo se probó **rompiéndolo de las dos formas**: si el filtro no saca
  al suspendido, fallan 7 guardas; si la renormalización deja de dividir por la
  suma, fallan 6.
- `npx tsc --noEmit`: limpio.

## Riesgos anotados

- **Dos dimensiones quedan con un solo componente**: sector privado (ITCP) y
  percepción (ITCIS). Si esa fuente única se cae, la dimensión desaparece y su
  peso se derrama al resto del cinturón. En percepción la fuente es la UTDT, que
  ya se congeló cuatro días sin que nada fallara (ADR-0175).
- **Las tres suspensiones tienen condición de reingreso escrita**, y los tests la
  exigen no vacía. Sin eso, una suspensión es una baja encubierta.
