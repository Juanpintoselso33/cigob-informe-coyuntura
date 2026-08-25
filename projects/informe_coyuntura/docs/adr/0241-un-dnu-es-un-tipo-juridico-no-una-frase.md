---
madr: 4
id: '0241'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'politica'
indicadores: [ratio_dnu]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'tests/test_politica_ratio_dnu.py', 'tests/fixtures/infoleg_dnu_ventana_365.json']
relacionado: ['0058', '0059']
ambito: 'Cinturón política · ITCP · `ratio_dnu` · cómo se identifica un DNU y con qué convención se cuenta cada lado del cociente'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «sólo 37 registros están tipificados como DNU»'
---

# ADR-0241 — Un DNU es un tipo jurídico, no una frase

## Contexto y planteo del problema

`ratio_dnu` publicaba **1,92**: 48 DNU sobre 25 leyes en una ventana móvil de
365 días. Los 48 no eran DNU. Eran **los decretos cuyo texto contiene la frase
«necesidad y urgencia»**, que es otra cosa.

El numerador salía de una búsqueda de texto completo en InfoLeg
(`tipoNorma=2` + `texto="necesidad y urgencia"`). Esa frase la dicen también:

- los decretos que **prorrogan** una intervención dispuesta por un DNU
  (79/2026, 82/2026, 615/2025);
- los **reglamentarios** de una ley o un decreto que la mencionan
  (Decreto Reglamentario 58/2026);
- los **vetos** que la citan al fundarse (651/2025);
- decretos ordinarios que modifican una norma dictada en su momento por DNU
  (710/2026, 605/2026, 27/2026, 931/2025, 812/2025, 696/2025).

Once de los 48. El indicador puntuaba **8,4 sobre 10 de tensión** —el aporte más
alto de todo el ITCP— con un numerador inflado un 30%.

El tipo jurídico estaba a la vista todo el tiempo: InfoLeg rotula la norma en la
propia grilla de resultados, `Decreto DNU 771 / 2026` frente a `Decreto 710 /
2026`. El colector nunca miraba la grilla: leía sólo el «Encontradas: N» del
encabezado.

Del lado del denominador había un segundo problema, más chico y más silencioso.
En la misma ventana hubo **25 leyes publicadas y 22 sancionadas**. Son dos
momentos distintos del trámite, y elegir mal un lado mueve el ratio de 1,48 a
1,68 sin que nada falle.

## Factores de decisión

- **Una coincidencia textual no es una tipificación.** Buscar la frase que
  define una figura jurídica no equivale a encontrar los actos de esa figura.
- **La fuente ya publica el tipo**; no hace falta inferirlo.
- **Los dos lados del cociente tienen que usar la misma convención temporal.**
- **El inventario tiene que quedar publicado**: un numerador de 37 sin las 37
  normas es tan poco auditable como el de 48.

## Opciones consideradas

- **A — Refinar la búsqueda de texto** con frases más específicas
  («decreto de necesidad y urgencia», «artículo 99 inciso 3»).
- **B — Filtrar por el tipo que declara la grilla de InfoLeg.**
- **C — Cambiar de fuente** a la Comisión Bicameral Permanente de Trámite
  Legislativo, que recibe todos los DNU.

## Decisión

**Opción B**, con la convención de **publicación en el Boletín Oficial en los
dos lados**: `37 / 25 = 1,48`.

La búsqueda de texto se conserva, pero degradada de criterio a **filtro previo**:
acota la grilla para no tener que traer todos los decretos del año. Quien decide
es el rótulo, con `^Decreto\s+DNU\b`. El más traicionero de los falsos positivos
es `Decreto Reglamentario`, que empieza igual que `Decreto DNU` y obliga a que el
patrón sea anclado.

La card publica ahora la ventana (`ventana_desde`, `ventana_hasta`) y el
**inventario completo de los DNU contados**, norma por norma y con su fecha de
publicación.

Apareció en el camino algo que no estaba en la auditoría: **la grilla devuelve 50
filas por página** y la ventana de 365 días trae 48. El techo estaba a dos normas
de distancia, y quedarse con la primera página no habría fallado — habría
contado 50. El listado ahora pagina con `desplazamiento=AP` e `irAPagina`, y si
el acumulado no llega al total declarado, falla en vez de devolver un conteo
corto.

### Consecuencias

- El ratio pasa de **1,92 a 1,48**. El puntaje de banda sube de 16,0 y la tensión
  del indicador baja desde 8,4/10; era el aporte más alto del ITCP.
- La serie mensual se rehace con el mismo filtro: card y serie comparten la
  función y la ventana.
- La unidad pasa a decir `DNUs publicados por ley publicada`, que es la
  convención que efectivamente usa.
- El indicador queda expuesto a un cambio de rotulación de InfoLeg. Es un riesgo
  real y preferible al anterior: si el rótulo cambia, el conteo cae a cero y se
  nota; una frase que deja de coincidir baja el conteo de a poco y no se nota.

### Confirmación

`tests/test_politica_ratio_dnu.py` contra
`tests/fixtures/infoleg_dnu_ventana_365.json` —las 48 filas reales de la ventana
auditada, con las 11 que sobran incluidas a propósito—:

- el filtro por tipo da 37, y `37/25 = 1,48`;
- **1,92 sigue siendo lo que daba el método viejo** —o sea que el diagnóstico de
  la auditoría era correcto— y el nuevo no puede darlo;
- los seis rótulos reales se clasifican bien, `Decreto Reglamentario` incluido;
- los 11 falsos positivos se pueden **nombrar**, no sólo descartar, y entre ellos
  está el veto;
- `37/22` (leyes sancionadas) no da 1,48: las convenciones no se mezclan;
- todas las filas caen dentro de la ventana;
- un listado truncado hace fallar.

Probado rompiéndolo: relajado el patrón a `^decreto`, fallan ocho guardas.

## Pros y contras de las opciones

### A — Refinar la búsqueda de texto

- Bueno, porque no cambia la mecánica del colector.
- Malo, porque sigue infiriendo el tipo del texto. Un DNU que no use la frase
  exacta desaparece, y un decreto que la cite entra igual.

### B — Filtrar por el tipo de la grilla

- Bueno, porque usa la tipificación de la propia fuente.
- Bueno, porque deja publicar el inventario de lo contado.
- Malo, porque depende del rótulo de InfoLeg, que podría cambiar.

### C — Comisión Bicameral

- Bueno, porque es el registro institucional de los DNU.
- Malo, porque su publicación es irregular y no expone las leyes, así que el
  denominador seguiría viniendo de InfoLeg: dos fuentes para un cociente.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_politica.md`.
- [[0058-ratio-dnu-ventana-movil-12m]] fijó la ventana móvil, que este ADR
  no toca.
