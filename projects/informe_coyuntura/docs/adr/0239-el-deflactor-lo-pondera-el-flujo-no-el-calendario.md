---
madr: 4
id: '0239'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'politica'
indicadores: [iaf_transferencias]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'tests/test_politica_iaf_deflactor.py', 'tests/fixtures/ron_transferencias_2024_2025.json']
supersede: ['0065']
relacionado: ['0066', '0263']
ambito: 'Cinturón política · ITCP · `iaf_transferencias` · cómo se deflacta una suma anual de flujos mensuales'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «IARAF +1,6%; Politikon +1,7% para el agregado anual comparable. El crecimiento nominal local, +43,1%, sí es consistente»'
---

# ADR-0239 — El deflactor lo pondera el flujo, no el calendario

## Contexto y planteo del problema

`iaf_transferencias` publicó **+0,8% real** para 2025. IARAF informó **+1,6%** y
Politikon **+1,7%** para el mismo agregado y el mismo período. La auditoría del
25-ago-2026 verificó además que el **nominal sí coincidía**: +43,1% acá, +43%
en las dos fuentes externas. Con el numerador y el denominador nominales bien,
el error sólo podía estar en el deflactor.

Lo estaba. El cálculo era:

```
var_real = (Σ flujos 2025 / Σ flujos 2024) / (1 + IPC promedio 2025) − 1
```

El IPC promedio anual le da a **cada mes el mismo peso**. Los flujos no se
reparten así: mayo y diciembre giran mucho más que febrero, y en 2025 el grueso
cayó en meses ya más baratos, con la inflación en descenso. El deflactor
ponderado por el flujo real es **40,78%**; el promedio de calendario, **41,92%**.
Poco más de un punto de deflactor, y el indicador se corre de +1,6% a +0,8% —la
mitad—.

Vale la pena decir que [[0065-iaf-transferencias-deflactor-promedio]] ya había
corregido este mismo indicador en la misma dirección, cambiando el dic-dic por
el promedio anual, y validándolo contra IARAF. El promedio es mejor que el
dic-dic, pero sigue siendo **un solo número para doce flujos distintos**. La
corrección de julio se quedó a mitad de camino.

El obstáculo era de datos: el CSV anual de Hacienda —el que usaba el
colector— trae una fila por año, sin apertura mensual, así que con esa fuente la
deflación mes a mes es imposible. Resulta que la **misma sección publica una
planilla con una hoja por mes**, y su consolidado reconcilia con el CSV anual
peso por peso: 42.133.458 contra 42.133.458 en 2024.

## Factores de decisión

- **Una suma de flujos no tiene un deflactor, tiene doce.** El agregado correcto
  se arma llevando cada flujo a precios de una base común y recién ahí sumando.
- **La validación externa ya existía y estaba disponible**: dos organismos
  independientes publican el mismo agregado.
- **El universo no se toca.** El nominal estaba bien; cambiar de fuente no puede
  cambiar qué se está midiendo.
- **La serie histórica entera se rehace**, no sólo el último punto.

## Opciones consideradas

- **A — Dejar el promedio anual y anotar la diferencia** con IARAF como brecha
  metodológica conocida.
- **B — Ponderar el IPC promedio por el flujo de cada mes**, siguiendo con el
  CSV anual para los montos.
- **C — Cambiar a la planilla mensual y deflactar cada flujo por el IPC de su
  propio mes.**

## Decisión

**Opción C.** Los montos salen de la planilla mensual consolidada de Hacienda
—una hoja por mes, mismo universo que el CSV anual (ADR-0066: Provincias,
C.A.B.A. y Fondo Compensador, incluida la compensación del Consenso Fiscal;
afuera Tesoro Nacional, Seguridad Social y Fondo A.T.N.)— y cada flujo se divide
por el índice IPC de su mes antes de sumarse.

La opción B es aritméticamente casi equivalente, pero requiere igual la apertura
mensual del flujo para armar la ponderación: si hay que bajar la planilla
mensual, conviene usarla entera.

Tres cosas del cuadro que no son obvias y que el colector resuelve
explícitamente:

- **La columna del total se ubica por encabezado, no por posición.** El cuadro
  fue ganando columnas con los años. Hasta 2017 se llamaba sólo `T O T A L`, y
  hay dos columnas `Sub-total` antes: quedarse con una de ellas dejaría afuera
  media planilla sin que nada fallara.
- **Los rótulos de fila vienen espaciados letra por letra** en los años viejos
  (`P R O V I N C I A S`), así que se comparan sin espacios.
- **Las planillas cambiaron de miles a millones de pesos entre 2022 y 2023 y no
  lo declaran en ningún lado.** Sin corregirlo, 2023 daba **−99,9% real**: tres
  órdenes de magnitud leídos como derrumbe. El CSV anual, que cubre 2003-2025 en
  una sola unidad, hace de ancla: el factor tiene que ser exactamente una
  potencia de mil y el residuo, menor al 1%. Si no lo es, el colector falla en
  vez de publicar una variación armada sobre dos unidades distintas.

### Consecuencias

- 2025 pasa de **+0,8% a +1,6% real**, dentro del rango de las dos fuentes
  externas.
- La serie 2018-2025 se rehace entera con la misma fórmula. Se mueve poco en los
  años de inflación pareja (2019: −1,4 → −1,4) y bastante en los de inflación
  cambiante (2023: −5,8 → −4,4; 2024: −8,3 → −9,8).
- `_ipc_promedio_indec()` deja de existir: no quedaba nadie usándolo.
- El rótulo de la fuente decía `(dic-dic)` desde antes de ADR-0065 —o sea,
  describía un método que ya se había abandonado dos veces—. Ahora dice cómo se
  deflacta y hay un test que lo verifica.
- La card viaja con el deflactor efectivamente aplicado, así que la diferencia
  con cualquier otra estimación pública es reproducible sin abrir el código.

### Confirmación

`tests/test_politica_iaf_deflactor.py` contra
`tests/fixtures/ron_transferencias_2024_2025.json` —24 flujos mensuales reales y
el índice IPC de cada mes—:

- deflactado mes a mes cae **entre IARAF y Politikon**, a menos de 0,1 de IARAF;
- el método anterior **sigue reproduciendo el +0,8% publicado**, que es lo que
  confirma que el diagnóstico de la auditoría era el correcto, y el método nuevo
  no puede dar ese número;
- el nominal (+43,1%) no se mueve;
- card y serie devuelven el mismo valor;
- un año incompleto no entra;
- el localizador de columnas no confunde el total con un `Sub-total`;
- sumar la fila `Total` en vez de las tres de jurisdicción se detecta;
- el cambio de unidad de 2023 se detecta y un desvío que **no** es de unidad
  hace fallar.

Probado rompiéndolo: revertido el colector al IPC promedio, fallan el test del
colector y el de card-contra-serie.

## Pros y contras de las opciones

### A — Dejar el promedio anual

- Bueno, porque no cambia nada y la serie histórica queda quieta.
- Malo, porque publica la mitad de la variación real que informan dos fuentes
  independientes, en un indicador cuyo nominal ya coincide con ellas.

### B — Ponderar el promedio por el flujo mensual

- Bueno, porque da prácticamente el mismo resultado que C.
- Malo, porque necesita igual la apertura mensual: el trabajo de datos es el
  mismo y el resultado es una construcción intermedia más difícil de explicar.

### C — Planilla mensual y deflación mes a mes

- Bueno, porque es la definición de la variación real de un flujo, y reproduce a
  IARAF y a Politikon sin ajustar nada.
- Bueno, porque abre la puerta a una serie mensual, hoy anual.
- Malo, porque agrega una fuente con tres trampas de formato (columna, rótulo,
  unidad), las tres cubiertas por tests.
- Malo, porque depende del CSV anual como ancla de unidad, así que un año sin
  CSV no puede entrar a la comparación.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_politica.md`.
- [[0066-iaf-transferencias-solo-provincias]] define el universo, que este ADR
  no toca.
- [[0065-iaf-transferencias-deflactor-promedio]] es la corrección anterior del
  mismo deflactor, que este ADR reemplaza.
