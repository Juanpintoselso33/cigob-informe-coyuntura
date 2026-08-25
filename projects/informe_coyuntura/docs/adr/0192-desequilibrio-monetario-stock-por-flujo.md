---
madr: 4
id: '0192'
estado: 'aceptado'
fecha: 2026-08-11
cinturon: 'macro'
indicadores: [desequilibrio_monetario, presion_dolarizacion]
parametros: ['BANDAS_ITCM["desequilibrio_monetario"]', 'ANCLAS_ITCM["desequilibrio_monetario"]', 'CORTES_A', 'CORTES_B']
archivos: ['scripts/desequilibrio_monetario.py', 'scripts/itcm.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'tests/', 'datos.ts', 'descripciones.ts', 'formulas.ts', 'fichas.ts', 'astro.config.mjs']
supersede: ['0055']
relacionado: ['0009', '0021', '0053', '0054', '0057', '0082', '0083', '0120', '0193', '0252', '0257']
continuado_por: ['0193']
ambito: 'Cinturón macro · ITCM · dimensión estabilidad monetaria · colector BCRA · series históricas · validación externa · web metodológica'
origen: 'Ficha "Desequilibrio Monetario" (Diego, 10-ago-2026), a partir de una observación de un economista consultado por Luis'
---

# ADR-0192 — Desequilibrio monetario: cruzar el stock que se ve con el flujo que se va

## Contexto y planteo del problema

Llegó una ficha de indicador nueva para el cinturón macro. Su punto de partida
es una objeción al IDM vigente ([[0009-idm-y-tcrm-en-el-itcm]]): **M2 y M3 son
agregados de oferta** y no dicen con claridad cuánta demanda de dinero ni cuánta
confianza en el peso hay detrás. La ficha propone medir eso con dos componentes:

- **A (stock)** — `M2 transaccional privado ÷ M3' ampliado × 100`, donde el M3'
  ampliado suma los depósitos privados en dólares. Mide qué proporción de la
  liquidez privada total sigue en pesos de uso transaccional.
- **B (flujo)** — la formación de activos externos mensual del sector privado no
  financiero, en millones de dólares.

Y —éste es el aporte real— pide **cruzarlos en una matriz** en lugar de
promediarlos, con el argumento de que cada uno por separado miente: si la fuga
hacia el colchón es fuerte, A puede mostrarse estable o hasta mejorando, porque
esos dólares nunca entraron al denominador, mientras el fondo es lo peor posible.

La ficha se declara preliminar y deja tres cosas abiertas en su sección 7: armar
las series, recalcular los cortes de banda por percentiles reales y fijar el peso.

### Lo que la auditoría del dato encontró antes de implementar

Cuatro hallazgos cambiaron el diseño respecto de la letra de la ficha.

**1. El componente B duplica un indicador que ya está en el índice.** La presión
de dolarización de carteras ([[0055-presion-dolarizacion-carteras-itcm]]) mide la
misma fuga cambiaria, desde la misma planilla del BCRA y con la misma ventana
desde abril de 2025. Incorporar B sin retirarla dejaba la misma señal contada dos
veces dentro de `estabilidad_monetaria`.

**2. La serie que la ficha nombra no se publica con ese nombre.** El anexo del
balance cambiario reserva «formación de activos externos» para el sector
financiero y el público; lo del privado no financiero sale bajo el concepto
«03- Compra-venta de billetes y divisas sin fines específicos», que es el que ya
parseaba la presión de dolarización. Además la ficha describe B como si excluyera
los dólares que quedan depositados localmente, y ninguna serie publicada hace esa
distinción: lo que se excluye es el consumo con tarjeta.

**3. Los cortes preliminares de B no cierran contra el dato.** La ficha propone
verde <500, amarillo 500-1.500, naranja 1.500-3.000 y rojo >3.000, anclando el
último en «comparable a jul-2025». Julio de 2025 fueron **5.436** millones, un
error de ancla de ~80%. Con esos cortes, **ninguno** de los quince meses de la
ventana da verde y sólo uno da amarillo: el semáforo nace saturado, el mismo modo
de falla por el que se rechazó la fórmula literal del IDM en
[[0009-idm-y-tcrm-en-el-itcm]]. Peor: «verde <500» sólo se cumplió **con cepo**,
cuando el flujo daba ~0 por falta de acceso, no por confianza.

**4. La ventana de A no puede empezar en 2016.** El M2 transaccional del sector
privado (var. 197) se publica desde enero de 2021. Reconstruirlo hacia atrás con
las series sueltas que la propia ficha enumera (circulante 17 + cuentas corrientes
94 + cajas de ahorro 95) no sirve: esa suma corre **+22,8%** por encima de la 197
en promedio y hasta +57% en un mes, porque no puede excluir la vista remunerada de
personas jurídicas. Sobre el ratio eso son **+8,7 pp**, más que el rango entero
del indicador.

### Precedente sobre el denominador

[[0053-transparencia-y-agregados-monetarios-del-idm]] ya había auditado y
rechazado el M3 ampliado **dentro del IDM**, porque convertía una comparación
pesos/pesos en otra entre liquidez bimonetaria y demanda en pesos, y porque el
68,7% del crecimiento de los depósitos en dólares era valuación cambiaria. Ese
rechazo no se traslada mecánicamente acá: la ficha propone un **ratio de nivel**,
no una brecha de crecimiento, y el nivel es justamente el constructo que
interesa. La objeción por valuación sí sobrevive y queda declarada como
limitación.

## Factores de decisión

- No contar la misma fuga cambiaria dos veces dentro de la misma dimensión.
- Respetar el diseño de la ficha —dos componentes, cruzados en matriz— y no
  reducirlo a un promedio, que es lo que la ficha explícitamente no quiere.
- Un solo camino del valor crudo al puntaje ([[0082-un-solo-camino-al-puntaje]]).
- Cortes reproducibles: el puntaje de un mes no puede cambiar hacia atrás porque
  llegó un dato nuevo.
- No inyectar en la reconstrucción histórica del ITCM una lectura que se sabe
  invertida.

## Opciones consideradas

- **Incorporar el indicador y retirar `presion_dolarizacion`** — elegida.
- **Incorporarlo y dejar los tres** (lectura literal de la ficha). Descartada:
  deja la fuga contada dos veces.
- **Incorporarlo en reemplazo del IDM.** Descartada: el IDM mide otra cosa
  (oferta contra demanda real de pesos) y sigue siendo válido.
- **Publicar A y B como dos indicadores separados.** Descartada: la matriz —el
  aporte de la ficha— desaparece.
- **Resolver la matriz con el mínimo de los dos puntajes.** Descartada:
  reproduce tres celdas pero da naranja donde la ficha dice amarillo.
- **Conservar los cortes preliminares de la sección 4.** Descartada: cero meses
  verdes en la ventana entera.

## Decisión

### 1. Entra `desequilibrio_monetario` y sale `presion_dolarizacion`

Este ADR **supersede [[0055-presion-dolarizacion-carteras-itcm]]**. El nuevo
indicador ocupa su lugar como cuarto componente de `estabilidad_monetaria` y
**hereda su peso de 10%** (2,6% nominal del ITCM). La ficha pide «un peso similar
al de los indicadores cambiarios/de reservas» pero deja el número final a definir
con Diego: hasta entonces se conserva el del indicador que sale, que es el cambio
mínimo y no inventa una ponderación.

El IDM ([[0009-idm-y-tcrm-en-el-itcm]]) **se queda**: mide la brecha entre el
crecimiento real de la oferta amplia de pesos y el de la demanda transaccional,
que no es lo que mide este indicador.

### 2. Los dos componentes

```text
A = M2 transaccional privado (var. 197)
    ÷ (circulante 17 + depósitos privados en pesos 100
       + depósitos privados en USD expresados en pesos 104) × 100

B = compra neta de billetes y divisas sin fines específicos del sector
    privado no financiero, en USD millones (concepto 03 del Mercado de
    Cambios, excluido el sector público). Positivo = salida.
```

B se lee de la hoja **tabular** del anexo y no de la matricial: la matricial
obliga a contar columnas —el neto de cada concepto vive en la columna anterior a
su título— y se rompe sola en cuanto el BCRA agregue un rubro. Las dos reconcilian
dentro de 0,5% en 14 de los 15 meses (3,2% en diciembre de 2025).

### 3. La matriz se resuelve por interpolación bilineal

Cada componente se lleva a una posición 0-1 interpolando entre los percentiles de
su ventana, con saturación. La tensión sale de interpolar entre las cuatro
esquinas de la matriz de la ficha:

| | B bajo (poca fuga) | B alto (fuga fuerte) |
|---|---:|---:|
| **A alto** (poca dolarización visible) | verde → **0** | naranja/rojo → **77,5** |
| **A bajo** (mucha dolarización visible) | amarillo → **40** | rojo → **90** |

La celda que la ficha dejó escrita como «naranja/rojo» se resuelve como el punto
medio entre naranja (65) y rojo (90).

La matriz **no es simétrica**, y eso no es una ponderación inventada acá: que se
degrade A cuesta 40 puntos y que se degrade B cuesta 77,5, porque son las celdas
que fijó la ficha. Refleja su tesis de que la fuga fuera del sistema es la señal
grave.

### 4. Un solo camino al puntaje

El motor puntúa **un** valor crudo por indicador ([[0082-un-solo-camino-al-puntaje]]),
así que la matriz se resuelve en `desequilibrio_monetario.py` y el indicador
publica una **tensión 0-100**. Las cuatro esquinas caen exactamente sobre
`puntaje = 100 − tensión`, de modo que `ANCLAS_ITCM` es esa inversión lineal
—dos anclas— y no hay una segunda escala que pueda desincronizarse. Las bandas
declaradas son los cuatro colores de la matriz y sirven a la lectura categórica;
el motor usa las anclas, como en todo indicador con anclas explícitas.

### 5. Cortes por percentiles, congelados

Se recalculan por percentiles reales, como pide la sección 7, y quedan **fijos en
el código**:

| Posición | 0 | 0,25 | 0,50 | 0,75 | 1 |
|---|---:|---:|---:|---:|---:|
| **A** (%), ventana 2021-01 a 2026-08, 68 meses | 31,62 | 34,48 | 38,27 | 44,34 | 49,96 |
| **B** (USD M), ventana 2025-04 a 2026-06, 15 meses | 1.122 | 1.954 | 2.363 | 3.644 | 6.545 |

No se recalculan en cada corrida a propósito: si el corte se moviera con el último
dato, el puntaje de un mes dejaría de ser reproducible y la serie histórica
cambiaría hacia atrás sin que nadie tocara nada.

La ventana de B es la de la ficha (apertura del cepo a personas humanas). La de A
arranca en 2021-01 y no en 2016 por el hallazgo 4.

### 6. La serie empieza en abril de 2025

B se puede calcular desde 2003, pero bajo cepo daba ~0 y la matriz lo leería como
«poca fuga» —verde— justo en los meses de control de cambios: la lectura invertida
que [[0055-presion-dolarizacion-carteras-itcm]] había resuelto haciendo el
indicador sensible al régimen. Antes de abril de 2025 el indicador no se publica y
el ITCM renormaliza los componentes disponibles.

Es una pérdida real frente a la presión de dolarización, que tenía serie desde
diciembre de 2023 gracias al canal de precio del régimen restringido. Se acepta
porque el constructo de la ficha necesita los dos componentes y uno de ellos no
existe con sentido antes de la apertura.

### Consecuencias

- La dimensión `estabilidad_monetaria` conserva 40/25/25/10 y su 26% del ITCM.
- Con el dato de junio de 2026 el indicador marca **50,9 de tensión → 49,1 de
  puntaje**, contra 64,5 que daba la presión de dolarización. El ITCM baja unos
  **0,4 puntos** por el cambio.
- La reconstrucción histórica del ITCM pierde este componente antes de abril de
  2025 y renormaliza; la validación externa correlaciona sobre 15 puntos.
- Las URLs `/metodologia/dolarizacion_depositos/` y
  `/metodologia/presion_dolarizacion/` redirigen **directo** a la ficha vigente,
  sin encadenarse, y quedan fuera del sitemap.
- El choque de nombres con el IDM se resuelve renombrando LOS DOS en la web, no
  poniéndole un paréntesis aclaratorio a uno. El IDM pasa a «Exceso de pesos
  sobre la demanda (IDM)» y este indicador a «Dolarización dentro y fuera del
  sistema». Los dos nombres nuevos dicen qué mide cada uno y, además, van en la
  misma dirección que su número: en ambos, más alto es peor. «Confianza en el
  peso» tenía el defecto opuesto — la confianza baja cuando el valor sube.
  Las claves internas no se tocan: se citan desde series, histórico, BigQuery y
  ADRs.

### Confirmación

- `tests/test_desequilibrio_monetario.py` fija las cuatro esquinas de la matriz,
  la saturación de `posicion()`, el parseo del anexo con el sector público
  excluido y el arranque de la serie en abril de 2025.
- `tests/test_itcm.py` fija bandas, anclas y el peso dentro de la dimensión.
- `tests/test_validacion_externa.py` verifica que la matriz de redundancia puntúe
  con la misma escala que el índice.
- `tests/test_web_labels.py` exige la capa pública completa y los redirects.

## Pros y contras de las opciones

**Incorporar y retirar `presion_dolarizacion`** (elegida)

- Bueno, porque la fuga cambiaria se cuenta una sola vez.
- Bueno, porque suma el nivel de dolarización de la liquidez, que no se medía.
- Malo, porque la serie se acorta de diciembre de 2023 a abril de 2025.

**Incorporar y dejar los tres**

- Bueno, porque es la lectura literal de la ficha y conserva la serie larga.
- Malo, porque duplica la señal de fuga dentro de una dimensión de 26%.

**Dos indicadores separados en vez de la matriz**

- Bueno, porque cada componente puntúa con su propia banda, sin agregación.
- Malo, porque pierde el punto central de la ficha: A solo puede mejorar
  mientras la situación empeora, y sólo el cruce lo expone.

## Más información

- Ficha «Desequilibrio Monetario», Diego, 10-ago-2026.
- BCRA, anexo estadístico del mercado de cambios y balance cambiario.
- [[0053-transparencia-y-agregados-monetarios-del-idm]] auditó el M3 ampliado
  dentro del IDM; acá se usa como denominador de un ratio de nivel, que es un
  constructo distinto.
- El peso definitivo dentro de la dimensión queda pendiente de definir con Diego.
