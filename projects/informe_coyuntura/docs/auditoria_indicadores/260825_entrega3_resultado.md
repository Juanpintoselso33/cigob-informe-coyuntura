# Entrega 3 — resultado

**Fecha:** 25 de agosto de 2026 · **Estado:** código, tests y ADR completos.
**No se corrió el pipeline ni se publicó nada.**

Los tres casos comparten la misma forma de error, y **ninguno tenía la aritmética
mal**: el rótulo prometía un universo y el cálculo usaba otro.

## 11 · Crédito privado — pesos, no efecto cambiario (ADR-0251)

El indicador usaba la **variable 26 del BCRA**, que el propio catálogo declara
`moneda: "MEyML"`: pesos **más** la cartera en dólares valuada en pesos. Con esa
serie, una devaluación revalúa la cartera sin que se preste un peso más.

| Variable | Moneda | i.a. real (jul-2026) |
|---|---|---:|
| **117** — préstamos al sector privado | `ML` (pesos) | **−1,5%** |
| 126 — la misma cartera en dólares, valuada en pesos | `ME` | +17,1% |
| 26 — las dos juntas *(lo que se publicaba)* | `MEyML` | +2,6% |

El titular no estaba a mitad de camino: estaba **del otro lado del signo**.
Publicaba expansión donde había contracción. `+2,5% → −1,5%`.

La cartera en dólares no se descarta: se publica en el desglose, en dólares
(donde se ve si creció) y en pesos (donde se ve el efecto cambiario), junto con
el total, para que quien venga de la serie anterior encuentre su número.

## 12 · Trabajo independiente — el universo restringido se enumera (ADR-0250)

La card decía «% del empleo registrado» y dejaba afuera al **monotributo social**
de los dos lados del cociente.

Verifiqué la exclusión contra la fuente antes de tocarla, y está bien fundada: el
padrón cae de **653 a 259 mil personas entre noviembre y diciembre de 2024**, un
−60% en un mes, y es el único salto de esa magnitud en catorce años. Con ese
salto adentro, la participación independiente **cae** de 22,9% a 22,1% desde el
4T-2023; sin él, **sube** de 19,1% a 20,6%. Lecturas opuestas, y sólo una
describe la economía.

Así que se hizo lo que el propio mandato prevé para este caso: **conservar la
exclusión y arreglar el rótulo**. La unidad pasa a `% del empleo registrado SIPA,
sin monotributo social`, y la card enumera las categorías de los dos lados, nombra
el régimen excluido con el mes de su quiebre y publica **cuánto daría con él
adentro** (22,1%). El valor no cambia.

## 13 · Subocupación demandante — el nombre (ADR-0249)

`pluriempleo` nunca midió pluriempleo. Su fuente es la serie 47.2 de la EPH, que
INDEC titula «Tasa de subocupación demandante»: gente que trabaja menos horas de
las que quisiera y busca más.

Lo llamativo es que **el repo entero ya lo sabía**: la clave en `config.py` era
`subocupacion_demandante`, la fórmula de puntaje decía «(subocupación
demandante)», `procedencia_anclas` decía lo mismo, la ficha decía «aproximación
declarada del pluriempleo», y `manual.py` documenta en una entrada aparte cómo se
construiría el pluriempleo de verdad, con la nota de que la serie pública no lo
trae. El único lugar donde la confusión seguía viva era **el identificador**, que
es lo que ve el lector.

Segundo error, más fácil de propagar: la web decía **«% de ocupados»**. INDEC lo
define sin ambigüedad — «porcentaje entre la población de subocupados demandantes
y la **población económicamente activa**».

La migración es explícita: código, series, web, fichas, tests y **las 40 filas de
la serie histórica versionada**, más la declaración de sustitución para que una
corrida acotada purgue la clave vieja en vez de dejar las dos conviviendo.

## Un defecto que arrastraba la Entrega 2, corregido acá

ADR-0245 hizo que un indicador suspendido conserve su peso en `DIMENSIONES_*`.
Eso dejó a esa tabla sin poder contestar «¿esto puntúa?» — contesta «¿cuánto
pesaría si puntuara?». Y **todo lo que la leía con la primera intención quedó
mal**: el generador de manuales presentaba los tres suspendidos como componentes
vivos, con sus pesos de diseño.

Se agregó `parametrica.indicadores_vigentes()` como única respuesta a esa
pregunta, y la usan el generador y sus tests. De paso apareció un bug anterior:
`cargar_ocultos()` leía las listas de ocultos parseando `publicar.py` con una
regex de una línea, y **`GESTION_OCULTOS` venía devolviendo vacío en silencio
hace meses** porque dejó de ser un literal. Ahora se importan.

## Impacto acumulado

| Cinturón | Publicado | E1 | E1+E2 | E1+E2+E3 |
|---|---:|---:|---:|---:|
| Macro (ITCM) | 3,6 | 3,5 | 3,5 | **3,6** |
| Política (ITCP) | 3,3 | 3,2 | 2,9 | 2,9 |
| Vida cotidiana (ITCIS) | 6,1 | 6,1 | 6,2 | 6,2 |
| Gestión (ITCG) | 2,7 | 2,5 | 2,1 | 2,1 |
| **Score global** | **3,9** | **3,8** | **3,7** | **3,7** |

Macro vuelve a **3,6**: el crédito privado pasa de un puntaje de banda de 41,7 a
32,8 y compensa la mejora del costo de financiamiento. Es la primera corrección
de la remediación que **empeora** el cuadro, y por la mejor razón: el número
anterior estaba inflado por el tipo de cambio.

Los otros dos casos no mueven ningún índice — son correcciones de rótulo y de
identificador.

## Verificación

- `pytest tests -q`: **2965 pasan**, 3 se saltean, **4 fallan de forma esperada**.
- Las cuatro comparan contra el **snapshot publicado**, que sigue teniendo la
  clave `pluriempleo` y los pesos previos porque no se regeneró. Se resuelven
  solas en la Entrega 5. Son:
  `test_fichas_pesos::test_los_pesos_que_afirman_las_fichas_son_los_vigentes`,
  `test_la_ficha_no_se_queda_atras::test_todo_indicador_publicado_tiene_ficha_tecnica`,
  `test_series_registradas::test_todo_indicador_numerico_tiene_serie_registrada` y
  `test_web_declara_los_pesos_del_itvc::…_publica_la_composicion_vigente[itvc]`.
- Cada caso se probó **rompiéndolo**: repuesta la variable 26 como titular fallan
  dos guardas —incluida la de aceptación—, y devuelta la clave vieja a las
  dimensiones fallan otras dos.
- `npx tsc --noEmit`: limpio.

## Cierre de contrato de los casos 14 y 15

El handoff pedía además cerrar formalmente el universo de `iaf_transferencias` y
`cobertura_judicial`, corregidos numéricamente en la Entrega 1. Los dos ya
quedaron cerrados ahí y sus ADR lo documentan:

- **ADR-0239** declara para transferencias el universo (Provincias, C.A.B.A. y
  Fondo Compensador, con la compensación del Consenso Fiscal; afuera Tesoro
  Nacional, Seguridad Social y Fondo A.T.N.), la ventana anual, el IPC, la regla
  de agregación mes a mes y el ancla de unidad contra el CSV.
- **ADR-0240** declara para cobertura judicial el numerador, el denominador, la
  fecha de cada uno, el criterio (`cargo_vacante`, no `cargo_cobertura`) y el
  inventario de designaciones y renuncias que une los dos cortes.

No hacía falta trabajo adicional: lo que faltaba era decirlo, y está dicho.
