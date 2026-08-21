---
madr: 4
id: '0228'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'gestion'
indicadores: [fal_modernizacion_laboral]
archivos: ['scripts/gestion.py', 'scripts/itcg.py', 'scripts/descargar_series.py', 'data/gestion/fal_hitos.json', 'tests/test_gestion_fal_actos.py', 'tests/test_descargar_series_fal.py', 'tests/test_itcg.py']
supersede: ['0142']
revierte: ['0142']
relacionado: ['0042', '0068', '0098', '0121', '0128', '0218', '0221', '0226']
ambito: 'ITCG · `fal_modernizacion_laboral` · bandas · serie · card · ficha · `fal_hitos.json`'
origen: 'Evidencia externa de tres terceros independientes, revisada a pedido del editor el 21-ago-2026 («¿te parece que hay que incorporarlo?» → «dale, mandá 3 agentes a hacerlo»)'
---

# ADR-0228 — El FAL puntúa lo que rige, no lo que se dictó

**Esto revierte una decisión editorial previa.** [[0142-el-fal-mide-sus-dos-actos-fundamentales]]
decidió, con el efecto a la vista y por decisión explícita del editor, que
sancionar y reglamentar la ley agotaba lo que el Gobierno podía cumplir hasta la
vigencia del régimen. No se revierte porque haya cambiado el criterio: se
revierte porque apareció evidencia que aquella decisión **no tuvo a la vista**,
y que contradice su premisa. Qué cambió está en «Factores de decisión».

## Contexto y planteo del problema

`fal_modernizacion_laboral` es la mitad de la dimensión de reforma laboral del
ITCG (50% interno, dimensión 15% del índice). Desde ADR-0142 medía
`100 × actos_cumplidos / 2` sobre dos actos fechados —la Ley 27.802, publicada
el 6-mar-2026, y el Decreto 408/2026, publicado el 1-jun-2026— y por lo tanto
valía **100**, puntuaba **100** y no volvía a moverse.

El propio código lo decía, en el comentario de las bandas:

> «Y EL INDICADOR YA NO DISCRIMINA: los dos actos ocurrieron y no se deshacen,
> así que queda fijo en 100 para siempre. Va contra ADR-0042 y se publica igual
> por decisión del editor.»

Hasta acá era una tensión de coherencia interna, asumida y declarada. Lo que la
convierte en un problema de medición es que **el hecho central del período que
el indicador dice medir no cabía en su escala**: entre el 30-mar y el
23-abr-2026 la ley que crea el Fondo estuvo **suspendida con efecto general**, y
el indicador publicó 100 esos días.

## Factores de decisión

### Lo que ADR-0142 no tuvo a la vista: tres terceros, tres métodos

**1. La base de desregulaciones de Chequeado y elDiarioAR (FOPEA).** 160 normas
publicadas entre el 10-dic-2023 y el 31-may-2025, clasificadas por impacto con
un criterio cualitativo de cuatro niveles y unos treinta especialistas
consultados. Reproducida acá desde la planilla pública que alimenta la
visualización: 160 filas, distribución 62 moderado / 43 alto / 35 bajo / 20 nulo
— que es el 38 / 28 / 22 / 12 por ciento publicado.

| sector | normas | de impacto NULO |
|---|---|---|
| **Trabajo y Seguridad Social** | **12** | **12** |
| Economía y Finanzas | 43 | 4 |
| Otros sectores | 11 | 2 |
| Administración Pública y Reforma del Estado | 35 | 1 |
| Transporte | 30 | 1 |
| Energía y Minería · Salud | 28 | 0 |

**Ningún otro sector se acerca.** Y hay que leer el 12 con cuidado, porque el
número solo exagera: las doce filas son **la misma norma** —el capítulo laboral
del DNU 70/2023, desagregado en doce medidas— y el motivo es uno solo, escrito
igual en las doce: *«El capítulo laboral del DNU 70/23 fue frenado por la
Justicia»*. No son doce observaciones independientes; es un evento contado doce
veces. Sirve igual, y por otra razón: dice que **en política laboral argentina
el sector entero de la base es una norma dictada que no rigió**.

La base **no habla del FAL**: se cierra en may-2025 y la Ley 27.802 es de
mar-2026. Es evidencia sobre la clase, no sobre el caso.

**2. Heritage, subíndice Labor Freedom de Argentina.** Extraído de los PDF de
país del Índice de Libertad Económica y contrastado contra la tabla de puntajes
de la edición 2026:

| edición del Índice | datos de | Labor Freedom |
|---|---|---|
| 2024 | 2022 | 53,5 |
| 2025 | 2023 | 55,2 |
| **2026** | **2025** | **53,5** |

**Variación neta cero** entre la edición que retrata el año anterior a esta
gestión y la que retrata su segundo año completo, mientras el índice general de
Argentina subía 7,5 puntos (49,9 → 57,4) y el propio informe la nombra como el
país que más mejoró en la edición 2026. El texto de Heritage lo dice sin
rodeos: *«Argentina's business and labor freedom scores in the 2026 Index are
below the world averages»*.

Dos advertencias que corresponde declarar. La primera: el valor **55,1 para
2023** que motivó la revisión **no se pudo reproducir contra fuente primaria**
—Heritage no publica el PDF de país de esa edición en la misma ruta— y sólo hay
corroboración secundaria (un agregador que registra 55 como máximo de la serie,
alcanzado en 2023). Los tres valores de la tabla sí salen del documento
original. La segunda: Labor Freedom se construye con seis factores del *Doing
Business* del Banco Mundial, **discontinuado en 2021**, así que su movimiento
año a año es más pobre de lo que parece. Por eso entra como corroboración y
**no** como componente ni como validador — donde además chocaría con las cuatro
condiciones de [[0226-el-itcg-se-queda-sin-validacion-externa-y-lo-declara]]:
es anual y aporta a lo sumo tres puntos desde dic-2023.

**3. La propia Ley 27.802, que es la evidencia decisiva.** No es sobre la clase:
es sobre los dos actos que el indicador cuenta.

| fecha | qué pasó |
|---|---|
| 06-mar-2026 | se publica la Ley 27.802 |
| **30-mar-2026** | el Juzgado Nacional del Trabajo N° 63 dicta una cautelar innovativa en *«CGTRA c/ Estado Nacional s/ Acción Declarativa»* y **suspende con efecto general unos 82 artículos, entre ellos los del Fondo de Asistencia Laboral** |
| 06-abr-2026 | el mismo juzgado revoca la suspensión del art. 55 |
| **23-abr-2026** | la Cámara Nacional de Apelaciones del Trabajo, Sala VIII, concede efecto suspensivo a la apelación del Estado y **la ley vuelve a regir** |
| 01-jun-2026 | se publica el Decreto 408/2026, que reglamenta el Título II y difiere el arranque al 1-nov-2026 |
| 08-may · 08-jul-2026 | el Juzgado CAF 12 y la Sala IV de la Cámara CAF ratifican que la ley rige mientras tramita la causa |
| **abierta** | la acción declarativa de inconstitucionalidad **sigue en trámite** |

Que la cautelar alcanzaba al FAL está en dos coberturas independientes del
mismo día: *«el fallo frena el Fondo de Asistencia Laboral (FAL), las
limitaciones al derecho a huelga…»* y *«suspendió, con efecto general, una parte
sustancial de la ley 27.802… incluyendo normas sobre contrato de trabajo,
tercerización, solidaridad, jornada, indemnizaciones, huelga, ultraactividad,
negociación colectiva, tutela sindical, teletrabajo y el Fondo de Asistencia
Laboral»*.

**Durante veinticuatro días el indicador publicó el máximo puntaje posible
mientras un juez tenía frenada la ley que le da sentido.** Y no había forma de
que se notara: la escala de ADR-0142 era monótona por construcción.

### El error de categoría, nombrado

Es el mismo de [[0218-el-cierre-de-pymes-se-mide-con-la-srt]] —`mortalidad_pymes`
midiendo producción industrial durante trece meses— en su versión cara: un
indicador llamado **modernización laboral** puntuando cien porque se firmaron
dos papeles, con el rótulo público correcto y el contenido no. Ningún gate
compara un nombre con lo que mide.

### Y el argumento editorial de ADR-0142, dicho con justicia

Sigue teniendo una parte de razón, y por eso no se lo descarta entero: sancionar
y reglamentar **sí** es progreso real sobre la promesa, y **sí** es el grueso de
lo que el Gobierno podía hacer antes de la vigencia. Lo que la evidencia niega
no es eso: es que **agote** la promesa. Por eso los dos actos conservan la mayor
parte del indicador y pierden el resto.

## Opciones consideradas

- **Medir el FAL en tres etapas por lo que RIGE**: construcción normativa
  vigente 50% + vigencia del régimen 20% + adopción efectiva 30%, con cada acto
  gateado por su estado judicial — **elegida**.
- **Dejar el indicador como está** — descartada: publica el máximo mientras la
  norma que cuenta estuvo suspendida, y su serie no puede bajar.
- **Volver literalmente al compuesto de ADR-0098** (40/20/40, con adopción por
  menciones del Boletín Oficial) — descartada: no tenía gate judicial, que es
  justo lo que falló, y su etapa de adopción se apoyaba en un pleno provisorio
  (420 menciones, [[0068-fal-regimen-ley-27802]]).
- **Reemplazar el FAL por un indicador de reforma laboral efectivamente
  vigente** — descartada por alcance: exige una fuente de supervivencia judicial
  de normas que no existe todavía en el proyecto, y dejaría la dimensión sin su
  mitad de instrumento durante el desarrollo.
- **Recomponer la dimensión con otro reparto** (bajarle peso al FAL y subírselo
  a la litigiosidad) — descartada: mueve el número sin arreglar el indicador. El
  50/50 de [[0128-fuerzas-en-la-dotacion-y-peso-del-fal]] no se toca.
- **Sumar el Labor Freedom de Heritage como componente o como ancla** —
  descartada: anual, con insumos de una fuente discontinuada, y a lo sumo tres
  observaciones desde dic-2023. No cumple las condiciones de ADR-0226.

## Decisión

El indicador pasa a medir, en tres etapas fechadas:

```
FAL = 100 × ( 0,50 · actos fundamentales VIGENTES / 2
            + 0,20 · régimen en vigencia
            + 0,30 · adopción efectiva )
```

- **Construcción vigente (0,50).** Los dos actos de ADR-0142, cada uno por la
  mitad de la etapa. Un acto cuenta sólo si está **dictado y no suspendido**: si
  un tribunal frena su vigencia con alcance general, deja de sumar mientras dure
  la suspensión.
- **Vigencia (0,20).** Mismo peso que le dio ADR-0098. Es un hecho fechado y es
  un hecho de gestión: el art. 27 del propio decreto reglamentario **difirió el
  arranque cinco meses**, del 1-jun al 1-nov-2026. Premiar la reglamentación con
  cien puntos cuando esa misma reglamentación posterga el comienzo es perverso.
- **Adopción (0,30).** Al menos un Fondo inscripto en el registro de la CNV bajo
  la denominación de la Ley 27.802. Menos que el 0,40 de ADR-0098 porque aquella
  etapa se apoyaba en un pleno provisorio y ésta en un hecho duro.

Los pesos son **una convención declarada**, igual que el 40/20/40 de ADR-0098 y
el 100/0/0 de ADR-0142.

### Lo que se implementó

- **`data/gestion/fal_hitos.json`** suma un bloque `judicial`: las suspensiones
  de alcance general con su órgano, sus fechas, su alcance y la resolución que
  las levanta, más la causa de fondo con su estado. Mismo patrón que
  `privatizaciones_fechas.json`: hechos fechados y verificables, no juicio.
  **Sólo entran suspensiones de alcance general** — una cautelar individual no
  cambia si el régimen rige para todos.
- **`gestion.py`**: `fal_estado_actos()` y `fal_indice()` — una sola regla, que
  usan la card y la serie. ADR-0098 y ADR-0142 se desincronizaron dos veces
  entre las dos; ahora hay un test que lo impide.
- **`gestion.py`**: el conteo de la CNV se parte en dos. El que **puntúa** busca
  sólo `ASISTENCIA LABORAL`; el ancho —que suma `CESE`— queda como contexto. El
  «fondo de cese laboral» es el régimen de la industria de la construcción
  (Ley 22.250), la misma contaminación que ADR-0068 sacó de la consulta al
  Boletín Oficial y que había quedado viva por este lado: un fondo de la
  construcción registrado mañana valdría treinta puntos del indicador.
- **`itcg.py`**: bandas nuevas `(90, INF, 100) · (62,5, 90, 80) ·
  (37,5, 62,5, 55) · (10, 37,5, 30) · (-INF, 10, 10)`, con los cortes en los
  huecos de la escalera realizable y no en el rango observado
  ([[0121-itce-e-itcp-declaran-el-origen-de-sus-bandas]]).
- **`descargar_series.py`**: la serie se reconstruye con la misma regla, evaluada
  **al cierre de cada mes**. No toca la red mientras el régimen no rija.
- **Web**: `fichas.ts`, `datos.ts`, `descripciones.ts`, `formulas.ts` y
  `charts.ts` — los cinco archivos del checklist.
- **Tests**: `tests/test_gestion_fal_actos.py` (16 casos) y
  `tests/test_descargar_series_fal.py`.

### El efecto, sin maquillaje y en el sentido incómodo

| | ADR-0142 | ADR-0228 |
|---|---|---|
| valor del indicador | 100 | **50** |
| puntaje | 100 | **55,0** |
| dimensión `reforma_laboral` | 80,4 | **57,9** |
| **ITCG** | 76,7 | **73,3** |

**El cambio EMPEORA el número, y eso no lo hace correcto por sí solo.** La
simetría es el punto: ADR-0142 subió el ITCG 5,2 puntos con una justificación
editorial y lo dejó escrito; éste lo baja 3,4 con una justificación de categoría
y lo deja escrito igual. La dirección no es argumento en ninguno de los dos
sentidos.

La serie cambia de forma, que es la corrección de fondo:

| mes | ADR-0142 | ADR-0228 | por qué |
|---|---|---|---|
| feb-2026 | 0 | 0 | no hay ley |
| **mar-2026** | **50** | **0** | ley publicada el 6, **suspendida el 30** |
| abr-2026 | 50 | 25 | cautelar levantada el 23 |
| may-2026 | 50 | 25 | ley firme, sin reglamentar |
| jun-2026 → hoy | 100 | 50 | reglamentada; el régimen todavía no rige |
| desde 1-nov-2026 | 100 | 70 | con el régimen vigente |
| con el primer fondo | 100 | 100 | adopción efectiva |

### Consecuencias

- **El indicador vuelve a discriminar**, que es lo que [[0042-cohesion-bloque-diputados-recalibracion-bandas]]
  exige: puede bajar si un tribunal vuelve a suspender un acto, y le quedan
  cincuenta puntos de recorrido hacia arriba en vez de cero.
- **La dimensión de reforma laboral vuelve a ser la parte más floja del ITCG**,
  empatada con privatizaciones e inversión (57,9 contra 57,5), que es donde
  estuvo desde ADR-0098 hasta ADR-0142.
- `validacion_externa.py` reconstruye el ITCG con estas bandas y esta serie: se
  corre en el mismo cambio, como pide el checklist que ya falló dos veces
  (`bloqueo_sostenido` y `mora_familias`).
- **La guardia de [[0221-un-cable-trampa-mira-la-banda-no-el-puntaje]] no se
  toca**: mira la litigiosidad, no el FAL.

### Confirmación

`tests/test_gestion_fal_actos.py` fija las cuatro propiedades que se pueden
perder por separado: que un acto suspendido no cuente, que el índice **pueda**
bajar, que la adopción no se contamine con el régimen de la construcción y que
la reversión editorial esté dicha en el texto público. Cada una se verificó
rompiéndola a propósito.

La guarda de la caída **no mira la serie publicada**, y eso es deliberado: la
suspensión de marzo cayó sobre un mes que ya valía cero —la ley se publicó el 6
y se frenó el 30—, así que la serie real no muestra ningún descenso. Una guarda
escrita contra la serie habría pasado con un indicador otra vez monótono. Mira
la regla: inyectada una suspensión posterior, el índice tiene que bajar.

## Pros y contras de las opciones

**A favor de las tres etapas.** Es la única opción que representa el hecho que
motivó la revisión. Conserva lo defendible del argumento editorial —los dos
actos siguen siendo la mitad del indicador— y le devuelve recorrido sin inventar
una fuente nueva: las tres etapas salen de datos que el colector ya traía.

**En contra, dicho de frente.** La etapa de adopción es **binaria y gruesa**: no
distingue un fondo de doscientos. Se prefirió así antes que volver a un pleno
provisorio, pero es una pérdida de resolución real y habrá que refinarla cuando
existan fondos. Y el registro de la CNV publica el stock del día, sin historia,
así que esa etapa no se puede reconstruir hacia atrás; hoy no cambia ningún
valor porque no hay ningún fondo, y cuando lo haya habrá que fechar el alta como
están fechadas las normas.

**Contra el indicador, en general.** Sigue siendo un contador de hitos con
saltos, no una serie continua, y eso es inherente a medir una reforma por sus
actos. Lo que cambió es que ahora los saltos van en los dos sentidos.

## Más información

### Lo que queda abierto

- **La causa de fondo sigue en trámite.** Si la acción declarativa de
  inconstitucionalidad prospera, el bloque `judicial` de `fal_hitos.json` tiene
  que registrar la suspensión nueva **a mano**: no hay colector que vigile los
  fallos. Es el mismo régimen manual con que se mantienen
  `privatizaciones_fechas.json` y `concesiones_fechas.json`, con la misma
  fragilidad — si nadie mira, el indicador se queda con el último estado
  conocido y nada avisa.
- **La suspensión se asienta por norma completa, no por artículo.** La cautelar
  alcanzó a unos 82 de más de doscientos artículos y acá cuenta como suspensión
  de la Ley 27.802 porque los del FAL estaban adentro. Si en el futuro se
  suspendieran artículos que **no** son los del Fondo, el registro tendría que
  distinguirlo y hoy no puede.
- **El 1-nov-2026 el indicador sube solo de 50 a 70** sin que nadie toque nada,
  igual que en ADR-0098. Es correcto —la vigencia es un hecho fechado— y hay que
  saberlo de antemano para no leerlo como una mejora de gestión de ese mes.

### Cómo se verificó cada cosa

| afirmación | cómo se comprobó |
|---|---|
| distribución de impactos de la base FOPEA | planilla pública de la visualización, exportada a CSV y contada: 160 filas, 62/43/35/20 — coincide con el 38/28/22/12 publicado |
| 12 de 12 medidas laborales en NULO | agrupación por `Sector` de esa misma planilla; las doce citan el mismo motivo |
| Labor Freedom 53,5 · 55,2 · 53,5 | PDF de país de las ediciones 2024, 2025 y 2026 del Índice; el orden de los doce subíndices se validó contra la fila de Argentina de la tabla de puntajes de la edición 2026 |
| Labor Freedom 55,1 en 2023 | **no reproducido** contra fuente primaria; sólo corroboración secundaria |
| suspensión del 30-mar y su alcance sobre el FAL | dos coberturas independientes del mismo día + análisis doctrinario de la cautelar (RC D 141/2026), que confirma el efecto general del proceso colectivo |
| levantamiento del 23-abr y ratificaciones | coberturas del 23-abr, 08-may y 08-jul-2026 |

### Precedentes directos

[[0098-fal-en-tres-etapas]] (la estructura de tres etapas, que vuelve con el gate
que le faltaba) · [[0142-el-fal-mide-sus-dos-actos-fundamentales]] (lo que se
revierte) · [[0218-el-cierre-de-pymes-se-mide-con-la-srt]] (el error de
categoría) · [[0068-fal-regimen-ley-27802]] (la contaminación del «fondo de cese
laboral» de la construcción, que acá se corrige por el lado de la CNV)
