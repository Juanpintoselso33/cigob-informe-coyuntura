---
madr: 4
id: '0125'
estado: 'aceptado'
fecha: 2026-07-25
cinturon: 'gestion'
indicadores: [desregulacion_normativa]
archivos: ['desregulacion_oficial.json']
modifica: ['0096']
relacionado: ['0229']
modificado_por: ['0143']
ambito: 'ITCG · `desregulacion_normativa` · fuente · unidad · banda · serie · `desregulacion_oficial.json`'
origen: 'Aporte de la revisión externa del cinturón de gestión (doc 260723), decisión del editor'
---

# ADR-0125 — La desregulación pasa a medirse con la fuente oficial

| **Modifica** | ADR-0096 (conteo propio sobre InfoLeg) |

## Contexto y planteo del problema

La revisión externa propuso reemplazar nuestro conteo sobre InfoLeg por el
tablero del **Ministerio de Desregulación y Transformación del Estado**, que
informa 689 normas de desregulación, 2.699 normas anteriores modificadas o
eliminadas y 16.178 artículos afectados a junio de 2026.

**La Figura 1 de cada informe es un gráfico de barras mensual desde dic-2023.**
No aparecía en la extracción de texto porque el PDF trae las etiquetas
convertidas a curvas. Pero las barras son rectángulos vectoriales, así que sus
alturas se miden y se calibran con la cifra de portada del propio informe.

El informe de **abril-2026** es el último del formato que incluye ese gráfico y
cubre dic-2023 → abr-2026 (29 barras). Los dos meses siguientes salen de la
cifra de portada de los informes de mayo y junio.

## Opciones consideradas

- **Publicar las normas de desregulación acumuladas según el informe mensual del ministerio** — elegida.
- **El conteo propio sobre InfoLeg de ADR-0096** — reemplazado por la fuente oficial.

## Decisión

El indicador pasa a publicar **normas de desregulación acumuladas desde el
10-dic-2023, según el informe mensual del ministerio**.

| | antes (ADR-0096) | ahora |
|---|---|---|
| fuente | conteo propio sobre InfoLeg | informe oficial del ministerio |
| unidad | normas completas derogadas | normas de desregulación acumuladas |
| valor | 47 | **689** |
| puntaje | 72,0 | **73,3** |
| ITCG | 72,5 | **72,6** |
| serie | 31 puntos | 31 puntos |

**El puntaje casi no se mueve, y es deliberado.** Las anclas se eligieron para
que el cambio de fuente no cambiara el resultado: lo que cambia es de dónde
sale el número, no cuánto vale. Mover el puntaje al cambiar de fuente habría
sido indistinguible de recalibrar para que diera mejor (ADR-0045).

### La serie

31 puntos mensuales, dic-2023 → jun-2026:

| | | |
|---|---|---|
| dic-23 **4** · jul-24 **49** | dic-24 186 · jun-25 346 | dic-25 474 · jun-26 **689** |

Describe bien el programa: casi nada hasta jul-2024 (49 normas en siete meses),
salto con la Ley Bases y la creación del ministerio, y aceleración en 2026
(+40, +52, +53 en los últimos tres meses).

### Validación

La reconstrucción del gráfico se contrasta contra las cifras de portada de los
informes, que son **independientes del gráfico**: error máximo **3 normas**,
medio 1,4 sobre 10 puntos de comparación.

## Más información

### Limitaciones

**La escala sigue siendo una convención propia.** Era la limitación principal
que ADR-0096 dejó declarada, y cambiar de fuente **no la resuelve**: el
ministerio publica el conteo pero **no publica ninguna meta**. Los 300 que
proponía la revisión externa como objetivo ya estaban superados en jul-2025
(396), así que habrían dejado el indicador clavado en 100 desde su primer dato.
Los cortes 100/300/600/1200 los ponemos nosotros y así queda dicho en la ficha.

**Es el Gobierno midiendo su propio programa.** El criterio de qué norma cuenta
como "de desregulación" lo fija el ministerio responsable. Se planteó como
objeción y **el editor decidió que la condición de fuente oficial pesa más**:
el número deja de ser una construcción nuestra —que ya había tenido dos errores
documentados de definición (ADR-0096)— y pasa a ser verificable contra un
documento público del organismo. Queda declarado en la ficha, no escondido.

- **El ministerio revisa su serie hacia atrás, y de forma sustantiva.** El
  informe de junio de 2025 declaraba **212 normas** al 6-jun-2025; el gráfico
  publicado en abril de 2026 ubica ese mismo momento **por encima de 310**. Se
  usa siempre la última vintage, igual que con el EMAE. Conviene saberlo antes
  de que alguien compare una card vieja con una nueva y lo tome por un bug.
- **El backfill sale de medir un gráfico**, no de cifras publicadas como texto.
  Está calibrado y contrastado, pero es una reconstrucción geométrica y hay un
  test que la vigila.
- **Es un trinquete**: sólo sube. Con los cortes actuales satura al llegar a
  1.200, que al ritmo de 2026 ocurre hacia mediados de 2027. **Revisar ahí.**
- El conteo **no pondera por peso económico**.
- Los nombres de archivo de los informes son irregulares —`_junio`, `_junio_1`,
  `_mayo_2026`, `_agos`, `_diciembre_enero` y un typo oficial (`analsisi`)—, así
  que los enlaces **se resuelven leyendo la página**. Nunca construirlos a mano.
- El período se toma de la **fecha de corte**, no del mes de portada: hay
  informes cuya tapa dice "JUNIO 2025" y cuyo corte es el 4 de julio.

### Lo que la primera búsqueda no encontró

La primera revisión concluyó que la fuente servía como contexto pero no como
indicador, por dos razones: que empezaba en jul-2025 y que no había forma de
reconstruir la serie hasta dic-2023. **Las dos eran producto de haber buscado
poco.** Queda anotado acá para que el negativo sea auditable, que es lo que
exige el criterio de no declarar fuentes inexistentes:

| se probó | resultado |
|---|---|
| `package_search` en datos.gob.ar (4 consultas) | 0 datasets |
| página de informes del ministerio | 5 PDFs temáticos, ninguno de la serie |
| extracción de texto del PDF (pypdf) | sólo las cifras de portada |
| **archivo web (CDX) de las páginas del ministerio** | **1 informe no listado en la web** |
| **sondeo de nombres de archivo** | **18 PDFs accesibles, 6 no listados** |
| **render del PDF a imagen** | **la Figura 1 es la serie mensual completa** |
| iframes / tableros embebidos (Power BI, Tableau, etc.) | no hay |

### Caché

`data/gestion/desregulacion_oficial.json` guarda cada informe leído y el
backfill del gráfico. Es permanente: un informe publicado no cambia. **Se
agregó al `git add` del workflow nocturno en el mismo cambio** — un caché que
no se commitea no sobrevive al cron.

`desregulacion_normas.json` (el análisis por norma de InfoLeg) **no se borra**:
es el respaldo de la serie anterior y de ADR-0096.
