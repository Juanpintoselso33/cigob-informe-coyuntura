---
madr: 4
id: '0331'
estado: 'rechazado'
nota_estado: 'Rechazado construir un indicador de inversión tecnológica: ninguna serie pública mensual lo sostiene. La dimensión `inversion` sigue con `iai` solo y `icip` sigue fuera del índice (ADR-0262).'
fecha: 2026-09-19
cinturon: 'macro'
indice: 'ITCM'
indicadores: [icip, iai]
relacionado: ['0253', '0262']
ambito: 'Cinturón macro · ITCM · dimensión `inversion` · si existe una serie que mida inversión tecnológica sin duplicar el componente BK del IAI'
origen: 'Apuntes de Juan del 15-sep-2026 (#monitor-de-proyecto-de-gobierno): «Revisar Indicador de inversión tecnológica diferenciada de la IAI». Es la opción B que ADR-0253 aplazó explícitamente.'
---

# ADR-0331 — La inversión tecnológica no tiene serie que la sostenga: o es ruido, o es el BK del IAI

## Contexto y planteo del problema

ADR-0253 renombró `icip` a «Pagos de servicios digitales y productividad»
porque el nombre anterior —«Índice de Capitalización Inteligente y
Productividad»— prometía formación de capital sobre un insumo que es consumo
intermedio. Eligió la opción mínima y **aplazó la opción B**: medir inversión
digital de verdad, lo que exigía «elegir una fuente de cuentas nacionales,
resolver su frecuencia y su rezago, y recalibrar la banda entera». ADR-0262
después sacó `icip` del índice por un defecto más profundo: sus dos insumos
necesitan signos opuestos y el compuesto los suma con el mismo.

Resultado al 19-sep-2026: **no existe ningún indicador de inversión
tecnológica**. La dimensión `inversion` (12% del ITCM) la sostiene `iai` solo,
con peso 1,0 — ISAC 65% + bienes de capital importados 35%.

El pedido de Juan tiene dos mitades y la segunda es la que manda. «Diferenciada
de la IAI» no es un problema pendiente entre los indicadores que ya existen:
`iai` e `icip` no comparten **ninguna** serie. Es una restricción para el
indicador nuevo, porque el componente BK del IAI es
`74.3_IIBCA_0_M_32`, el agregado de bienes de capital importados, y el hardware
informático importado está adentro. Cualquier serie de equipamiento TIC
importado duplica contra el 35% del único indicador que se queda con la
dimensión entera.

## Factores de decisión

- La serie tiene que ser **mensual y fresca**: una card del tablero no se
  alimenta con un dato trimestral de tres trimestres atrás.
- Tiene que **discriminar**: si la banda no separa meses distintos, el
  indicador no aporta puntaje, aporta ruido.
- Tiene que ser **independiente del BK del IAI**, o la dimensión puntúa dos
  veces lo mismo.
- No puede medir otra cosa que la que su nombre dice. El repo ya pagó dos veces
  esa cuenta (ADR-0218 con `mortalidad_pymes`, ADR-0217 con la proteína animal).

## Opciones consideradas

1. **Cuentas nacionales (la opción B de ADR-0253)** — la FBCF con apertura por
   software, bases de datos y equipos TIC.
2. **`184.1_BIENES_PAGICA_0_M_24` — «Bienes Pagos Informática»** (BCRA, balance
   cambiario): pagos al exterior por *bienes* del sector informática. Es
   hardware, no suscripciones, así que está más cerca del capital que el insumo
   actual de `icip`. Único candidato vivo y mensual.
3. **No construir el indicador** y registrar por qué — elegida.

## Decisión

**No se construye.** La dimensión `inversion` sigue con `iai` solo e `icip`
sigue en `INDICADORES_CONTEXTO`. No se toca código: este ADR registra una
medición, no un cambio.

Las dos opciones sustantivas se descartaron por evidencia, no por criterio.

### Evidencia 1 — la fuente que pedía ADR-0253 no existe

Barrido del catálogo de `apis.datos.gob.ar` por «informática», «TIC»,
«computación», «intangible», «formación bruta de capital» y «equipo durable»:

- **No hay apertura de FBCF por software, bases de datos ni equipos TIC.**
  Ninguna serie.
- Las líneas específicas de informática que existen están **muertas**:
  `125.1_MOI_1993_0_28` («Máquinas de oficina e informática») termina en
  **2014**; `326/327.x` («Fabricación de maquinaria de oficina, contabilidad e
  informática») en **2016** — y ésa mide producción, no inversión.
- La FBCF agregada (`166.2_F_BRUTAIJO_0_0_19`) es **trimestral, en pesos
  corrientes, y su último punto es 4T-2025**: unos tres trimestres de atraso
  contra un tablero mensual.

La opción B de ADR-0253 no es difícil: es **inaplicable** con datos públicos.

### Evidencia 2 — la serie funciona; lo que mide ya está medido

Conviene decirlo al derecho, porque el motivo del rechazo depende de eso: **el
candidato no es una serie mala.** Tiene 283 meses sin huecos, llega a 2026-07
(dos meses de rezago, mejor que varios indicadores que sí puntúan) y, en su forma
suavizada —acumulado móvil de 12 meses, el mismo recurso que ADR-0322 usó con la
faena—, es una serie limpia y legible: sube a +143,2% en octubre 2025 y baja
ordenadamente a +39,8% en julio 2026. **Ocupa los cinco tramos de una banda**
(38,7% de los meses en el más bajo, 41,9% en el más alto), o sea discrimina.

El problema es otro: en su forma usable, **es el componente BK del IAI**.

| | i.a. mensual crudo | i.a. del acumulado móvil 12m |
|---|---|---|
| Desvío del candidato | 558,5 | 69,7 |
| Desvío del BK del IAI (referencia) | 40,0 | 26,5 |
| Recorrido | −96,5% a +3.052,4% | −60,5% a +143,2% |
| Correlación con el BK del IAI (2024+) | +0,343 | **+0,984** |

Crudo no se puede bandear: desvío 558 contra 40 del componente que pretendía
complementar. Suavizado sí, y ahí aparece el +0,984.

**Ese +0,984 no es un artefacto de la ventana, y se verificó.** La sospecha
razonable era que dos series suavizadas que comparten el rebote post-cepo
correlacionen por construcción. Tres controles dicen que no:

- **Se replica en la otra ventana de cambio libre.** 2016-2019, sin quiebre
  cambiario: **r = +0,974** (n=48). Misma duplicación, otro período.
- **Sobrevive a las primeras diferencias**, que matan la tendencia común:
  r = +0,785 en la ventana de calibración (+0,429 en todo el histórico).
- **El BK explica el 96,8% de su varianza** en la ventana de calibración
  (R² = 0,968, n=31; regresión `candidato = −5,6 + 2,59·BK`). El desvío del
  residuo —lo único propio— es de **12,4 puntos contra 69,7 de la serie
  entera: 3,2%**.

Sumarlo a la dimensión `inversion` sería darle un segundo indicador cuyo
contenido independiente es del orden del 3%.

### Evidencia 3 — cuándo sí se despega: mide el régimen cambiario

El patrón por subperíodo es el que cierra el caso, porque la duplicación **no**
es constante:

| Ventana | r (acumulado 12m) | Régimen |
|---|---|---|
| 2016-2019 | **+0,974** | cambio libre |
| 2024-2026 | **+0,984** | cambio libre |
| 2012-2015 | −0,118 | cepo |
| 2020-2023 | +0,210 | cepo |

**Se despega del BK exactamente cuando hay cepo, y converge cuando el dólar es
libre.** Eso es lo contrario de lo que se necesita: la serie aporta información
propia sólo en los períodos en que las restricciones cambiarias la distorsionan,
y es redundante justo cuando el dato es limpio. Lo que su parte independiente
mide no es inversión en tecnología: es **acceso a divisas**.

Los niveles lo confirman. El candidato pesa entre **1,0% y 2,7% de los BK
importados** (julio 2026: 14,5 MUSD contra 1.167,2): unas pocas operaciones por
mes. El +3.052,4% de enero 2025 sale de comparar 15,4 MUSD contra **0,5 MUSD** en
enero 2024; el +979,0% de diciembre 2024, de 10,6 contra 1,0. El salto de nivel de
10× a 30× entre 2023-24 y 2025-26 deja además la historia previa a 2025 inservible
para calibrar una banda, y hace que la corrida de +100% a +143% de 2025 sea el
escalón cambiario, no más inversión en tecnología.

### Consecuencias

- La dimensión `inversion` sigue descansando en un solo indicador. Eso ya estaba
  decidido (ADR-0262) y este ADR no lo mejora: lo confirma como el estado
  alcanzable con datos públicos.
- **Queda registrado que el pedido no está pendiente por olvido.** Sin esto, la
  próxima revisión del tablero vuelve a proponer lo mismo — que es exactamente
  lo que este repo evita escribiendo un ADR rechazado en vez de no escribir nada
  (mismo patrón que ADR-0313).
- Si alguna vez INDEC publica FBCF con apertura TIC, o el BCRA abre los BK
  importados por subpartida, la decisión se revisa: lo que falta es la serie, no
  el diseño.

### Confirmación

No hay código nuevo que probar. Lo que sostiene este ADR es reproducible:
`scripts/macro.py` ya trae las dos series con
`_indec_nivel_mensual(INDEC_BK_IMPO_ID)` y el mismo `HTTP_HEADERS`; las
correlaciones de la tabla salen de comparar su i.a. contra el i.a. de
`184.1_BIENES_PAGICA_0_M_24`, crudo y sobre acumulado móvil de 12 meses.

Las guardas que ya cubren el perímetro y tienen que seguir en verde:

- `tests/test_idm_e_icip_no_puntuan.py` — `icip` no vuelve al índice.
- `tests/test_constructos_no_prometen_de_mas.py` — no se puede afirmar
  «capitalización» ni «inversión digital» en la capa pública.

## Más información

- ADR-0253 — por qué pagar la nube no es capitalizar, y la opción B que aplazó.
- ADR-0262 — por qué ninguna dimensión arregla un compuesto de signos opuestos.
- La otra mitad del pedido del 15-sep ya está: el rótulo de `iai` perdió la
  sigla «(IAI)» en ADR-0311, y su texto público dice «inversión
  física/tradicional», sin prometer nada tecnológico.
