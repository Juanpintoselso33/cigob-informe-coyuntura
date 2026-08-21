---
madr: 4
id: '0153'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'vida'
relacionado: ['0223', '0224']
extendido_por: ['0216']
ambito: 'cinturón vida cotidiana (ITVC-B100), dimensión ingresos y consumo;'
---

# ADR-0153 — La pobreza entra al ITVC, y la categoría «card de contexto» queda cerrada

y una regla transversal de publicación
- **Descarta**: ADR-0113 (el nowcast se publica pero no puntúa)
- **Relacionados**: ADR-0022 y ADR-0051 (patrón `*_OCULTOS`), ADR-0115 (qué mide
  la dimensión de ingresos), ADR-0018/0024/0067 (base 100 = 4T-2023), ADR-0045
  (cuándo se puede calibrar contra lo observado)

## Contexto y planteo del problema

El editor venía con una lista de indicadores a mover entre cinturones. Sobre la
pobreza no tenía decidido el destino («no sé a dónde iba, ¿a macro?, ¿en algún
lado?») y resolvió: **vida cotidiana**.

La pobreza estaba desde ADR-0113 como **card visible que no puntuaba**. Ese
estado no era una opción de diseño: es la categoría «indicador de contexto» que
el editor **dio de baja expresamente**, y dejarla viva era el problema de fondo
a resolver, no un detalle de implementación.

## Opciones consideradas

- **La pobreza entra al ITVC y puntúa** — elegida.
- **Dejarla publicada sin puntuar**, como en ADR-0113 — descartada: ese estado no era una opción de diseño, sino la categoría «indicador de contexto» que el editor dio de baja expresamente, y dejarla viva era el problema de fondo.

## Decisión

1. `pobreza_nowcast` **integra el ITVC** con 25% de la dimensión de ingresos y
   consumo. `itvc.INDICADORES_CONTEXTO` queda vacía, con guard.
2. La serie `itvc_pobreza` se registra rebaseada e invertida contra el 2º
   semestre de 2023 del INDEC, con el desvío del empalme declarado en la ficha.
3. El fechado del nowcast sale del enunciado de resultados, no del título.

### Consecuencias

- **ITVC 94,4 → 96,4** y tensión del cinturón **6,1 → 5,7**. La dimensión de
  ingresos pasa de **105,1 a 110,5**, porque el componente que entra vale 126,9:
  la pobreza cayó mucho respecto del 2º semestre de 2023, que fue un pico. El
  índice mejora, y hay que decir con qué criterio se aceptó: el peso se fijó
  antes de ver este número.
- La lectura contra la transición y no contra un óptimo queda explícita en la
  ficha: superar 100 no significa una situación buena, significa mejor que un
  punto de partida muy malo.
- Peso efectivo de la pobreza en el ITVC: **9,31%**.
- Validación externa ITVC↔ICC: **sube**. Medido sobre los mismos datos, sacando y
  poniendo el componente: **0,526 → 0,558** sin ICC y **0,647 → 0,674** completo
  (n = 31 en los cuatro).

  Esto **corrige una lectura anterior**. Antes de arreglar el fechado de la
  sección 5, la misma comparación daba que la validación **bajaba**, y ya estaba
  escrita la explicación de por qué era aceptable que bajara —el ICC es
  expectacional y la pobreza es material, la anti-fase ya documentada—. Era una
  racionalización sobre un dato malo: con abril en su valor y mayo en su lugar, el
  componente mejora el ajuste contra el ICC. Se deja anotado porque el argumento
  «baja pero se justifica» es exactamente el que hay que desconfiar cuando todavía
  no se auditó el insumo.

  Que suba no autoriza a tocar nada tampoco: mover un peso para que un r mejore
  está prohibido por ADR-0045, y el peso ya estaba fijado antes de mirar.
- El componente arranca en enero de 2025: los meses anteriores del ITVC no lo
  incluyen y la dimensión renormaliza. La comparación de un ITVC de 2024 contra
  uno de 2026 mide, en esa fracción, composiciones distintas.
- Si un mes no publica informe, el componente mantiene el último valor y la
  dimensión renormaliza.

## Más información

### 1. La categoría «card de contexto» está cerrada, y ahora hay un guard

La regla queda escrita sin ambigüedad: **un indicador entra al índice de su
cinturón, o va a los ocultos del snapshot** (patrón `*_OCULTOS`, ADR-0022 y
ADR-0051 — se sigue relevando, cacheando y serializando, pero no se publica como
tile). No hay tercera opción.

`itvc.INDICADORES_CONTEXTO` queda **vacía y con un test que exige que siga
vacía**. No es celo: el camino de vuelta es agregar un nombre a una lista de una
línea, y mientras `pobreza_nowcast` estuvo ahí, `publicar.py` le estampaba
`en_indice: false` más la nota «Indicador de contexto — no integra el ITVC» sin
que ningún gate se quejara. El guard vale más que la limpieza puntual: el que
falla la próxima vez es el test, no el editor leyendo el tablero.

### 2. Por qué vida cotidiana y no macro

Las seis dimensiones del ITCM son **condiciones de la economía** —estabilidad
monetaria, viabilidad fiscal-comercial, financiamiento, actividad,
competitividad, inversión— y la pobreza no es ninguna de ellas: es el
**resultado social**, que es precisamente lo que mide este cinturón. Ponerla en
macro habría obligado a abrir una séptima dimensión de naturaleza distinta a las
otras seis.

### 3. El peso: 25% de la dimensión, fijado antes de mirar el efecto

El razonamiento se escribió en el código **antes** de calcular el impacto sobre
el índice, que es la única forma de que el peso no sea un ajuste al resultado
deseado (ADR-0045).

La pobreza **cubre lo que el indicador de salario no puede ver**:
`brecha_salario_cbt` compara salario **registrado** contra canasta, así que sólo
alcanza al empleo formal; la pobreza cuenta personas, incluidos los hogares
informales y los que no viven de un sueldo. Esa población es del orden de la que
mide `informalidad` (32,9% de la dimensión antes del cambio), así que el peso va
en esa banda y por debajo del ancla salarial: **25%**, el número redondo del
tramo. Los cuatro componentes previos ceden proporcionalmente (×0,75) y
conservan su orden relativo; el peso **nominal** de la dimensión no se toca.

| componente | antes | después |
|---|---|---|
| `brecha_salario_cbt` | 0,6107 | 0,4580 |
| `informalidad` | 0,3289 | 0,2467 |
| **`pobreza_nowcast`** | — | **0,2500** |
| `consumo_carne` | 0,0403 | 0,0302 |
| `patentamiento_motos` | 0,0201 | 0,0151 |

**No es redundante con la brecha salarial, y está medido**: r = **+0,150** en la
matriz publicada (n = 19). Era el solapamiento que había que descartar —los dos
comparan ingreso contra canasta— y no aparece.

Dos salvedades, las dos incómodas y las dos van escritas.

La primera: **el número que casi publiqué estaba contaminado por el bug de la
sección 5.** Antes de corregir el fechado, la misma correlación daba **−0,265**;
con abril devuelto a su valor y mayo en su lugar da **+0,150**. Un punto mal
fechado en diecisiete dio vuelta el signo de la métrica con la que se justificaba
el peso. No cambia la conclusión —en los dos casos |r| es chico y el
solapamiento conceptual no aparece— pero sí cambia qué se puede afirmar con
cuánta firmeza sobre una serie de este largo.

La segunda: **la matriz marca un acoplamiento que este razonamiento no
anticipaba.** En niveles la pobreza supera el umbral de 0,7 con cuatro
componentes de **otras** dimensiones:

| par | r | n |
|---|---|---|
| `mora_familias` | −0,897 | 19 |
| `patentamiento_motos` | +0,892 | 19 |
| `empleo_registrado` | −0,821 | 19 |
| `indice_lider` | −0,748 | 19 |

No es una anomalía suya: el cinturón muestra **24 pares altos en niveles y
ninguno al destendenciar** (r absoluto medio **0,413 → 0,199**), y eso ya está
documentado como época en común (ADR-0108) y se publica junto al dato. Lo que sí
es propio de la pobreza es que sus pares se miden sobre **19 meses y no 32**, así
que son los menos asentados de la matriz. No se toca ningún peso por esto: la
lectura en diferencias es la que el proyecto ya decidió que viaja con el número.

Por eso entra a **esta** dimensión, donde el solapamiento queda explícito y los
pesos lo absorben, y no como dimensión aparte fingiendo independencia.

### 4. El empalme de dos fuentes, y su costo declarado

El nowcast mensual de la UTDT **arranca en enero de 2025** y no llega al período
base, así que el rebase toma la base de la **serie oficial del INDEC**:
`100 × pobreza(2º sem. 2023) / pobreza(mes)`, invertido —más pobreza es peor, así
que la base va arriba y por encima de 100 hay menos pobreza que en la transición.
Base = **40,1%**.

Las dos fuentes no coinciden, y el desvío **no tiene signo constante**, así que
no se puede corregir con una constante:

| semestre | INDEC | nowcast | desvío |
|---|---|---|---|
| 1er sem. 2025 | 38,1 | 35,8 | −2,3 pp |
| 2º sem. 2025 | 31,6 | 31,1 | −0,5 pp |
| 1er sem. 2026 | 28,2 | 30,2 | +2,0 pp |

Sobre una base de 40,1 puntos, el desvío mayor implica hasta un **5,7%** de error
que se traslada a **todos** los valores del componente. Se acepta porque la
alternativa —usar sólo la medición semestral— renuncia al dato mensual, que es
la razón de ser de la fuente. Va a las limitaciones de la ficha pública.

**Lo que se verificó antes de aceptar el empalme**, para no declarar un
imposible: la página del autor lista **23 informes**, y el nowcast propio **no
alcanza** el 2º semestre de 2023 — los cinco más viejos no traen el par
tasa-semestre (uno es la nota metodológica de 2022, otro es una publicación
distinta sobre evolución entre semestres, y dos no tienen capa de texto), y entre
julio de 2022 y noviembre de 2024 la página no lista ningún informe. El gráfico
de evolución del informe más reciente sólo cubre siete semestres móviles, y
ninguno de los informes leídos menciona 2023. **Queda un camino sin recorrer y se
deja anotado, no cerrado**: la app Shiny del autor
(`mrozada.shinyapps.io/shinynowcast`) sirve la serie completa y podría contener
la base propia del nowcast; si la tuviera, el empalme desaparece. No se intentó
acá porque exige mantener un websocket (ver el docstring del colector), no porque
se haya comprobado que no está.

### 5. Un bug de fechado que apareció al RENDERIZAR el informe

Buscando si el nowcast llegaba a 2023 apareció otra cosa. La serie tenía **un
hueco en mayo de 2026** y el primer reflejo era «la fuente no publicó ese mes».
No era eso.

Cada informe nombra su semestre **dos veces** —el título de RESULTADOS y el
enunciado que trae la tasa— y las dos las escribe el autor a mano. El parser se
fechaba por el título. El informe publicado el 16 de junio de 2026 dice
`RESULTADOS Semestre Noviembre 2025 - Abril 2026` —el del mes anterior— y a
renglón seguido «una tasa de pobreza de **29,6 por ciento para el semestre
diciembre 2025 - mayo 2026**». El gráfico de evolución del propio informe rotula
ese 29,6 como **Dic25May26**, que es lo que adjudicó el caso.

El daño era doble y silencioso:

- **pisaba abril**: el dedupe por período se queda con el informe más nuevo, así
  que abril pasó de 29,2 a 29,6 y el error se veía como una revisión legítima del
  autor;
- **dejaba mayo sin dato**, que es el hueco que disparó la búsqueda.

**El arreglo obvio estaba mal, y lo mostró revisar los 18 informes uno por uno.**
Cambiar la preferencia al enunciado arregla junio de 2026 y rompe noviembre de
2025, donde el informe dice título `Semestre Mayo 2025 - Octubre 2025` y
enunciado «abril 2025 - septiembre 2025»: acá el viejo es el **enunciado**, y se
sabe porque el informe del mes anterior ya había estimado abril-septiembre.
Cualquiera de los dos campos puede quedar atrasado.

La regla que resuelve los dos casos no prefiere una fuente sobre la otra: **gana
el semestre más nuevo de los dos declarados.** Lo que queda viejo es siempre el
mes anterior, nunca el siguiente, así que la desactualización sólo apunta hacia
atrás. Con esa regla los 18 informes dan **18 meses consecutivos, sin huecos ni
duplicados**; fechando sólo por el título se perdía mayo-2026 y se pisaba abril,
y sólo por el enunciado se perdía octubre-2025.

Además: la tasa se toma del **mismo enunciado** que da el semestre, para que no
puedan venir de oraciones distintas (los informes traen una segunda tasa, la del
mismo semestre del año anterior); se cubre la variante que cierra semestre
calendario, en sus dos redacciones («de 2026» y «del 2025»); y cuando los dos
campos discrepan queda un **warning** en el log en vez de una elección muda.

Se agrega un control de serie: el autor publica un informe por mes y cada uno
corre el semestre móvil un mes, así que **un hueco no es un mes sin publicar, es
un informe mal fechado**. `fetch_nowcast_pobreza(historico=True)` ahora devuelve
`huecos` y avisa. Ocho tests sin red pinean los cuatro formatos reales, los dos
sentidos de desactualización, el caso de dos tasas en el mismo texto y el
control de huecos.

Vale registrar **cómo** se encontró, porque ninguna de las vías habituales lo
veía: no hay test que compare un PDF contra su propio gráfico, y el hueco de un
mes en una serie de 18 puntos no disparaba ningún gate. Apareció al **renderizar
el PDF y mirarlo** — la misma disciplina que ya está anotada para no cerrar
negativos apurado.
