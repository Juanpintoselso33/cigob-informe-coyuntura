---
madr: 4
id: '0249'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'vida'
indicadores: [subocupacion_demandante]
archivos: ['scripts/itvc.py', 'scripts/publicar.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/vida_cotidiana/config.py', 'web/src/lib/datos.ts', 'web/src/lib/fichas.ts', 'output/series/vida_cotidiana.csv', 'tests/test_universos_declarados.py']
relacionado: ['0018', '0130', '0263']
ambito: 'Cinturón vida cotidiana · ITCIS · el indicador que se llamaba `pluriempleo` y medía otra cosa'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «INDEC define subocupación demandante como porcentaje de la PEA; pluriempleo es otro fenómeno»'
---

# ADR-0249 — La subocupación demandante se llama por su nombre

## Contexto y planteo del problema

El indicador `pluriempleo` publicaba **7,5%** y nunca midió pluriempleo.

Su fuente es la serie `47.2_ECTSDT_0_T_47` de la EPH, que INDEC titula «Tasa de
subocupación demandante total»: gente que **trabaja menos horas de las que
quisiera y busca más**. El pluriempleo —tener más de un empleo a la vez— es otro
fenómeno, y no está en las series públicas de la EPH.

Lo llamativo es que **el repo entero ya lo sabía**:

- `scripts/vida_cotidiana/config.py` tiene la clave `subocupacion_demandante`
  apuntando a la serie, y la llamaba «proxy pluriempleo»;
- `publicar.py` la leía de ahí y la renombraba a `pluriempleo` al publicarla;
- la fórmula de puntaje en `publicar.py` decía, textual, `(subocupación demandante)`;
- `procedencia_anclas.py` decía «subocupación demandante rebaseada a 4T-2023»;
- la ficha pública decía «aproximación declarada del pluriempleo»;
- y `collectors/manual.py` documenta, en una entrada aparte, **cómo se
  construiría el pluriempleo de verdad** desde los microdatos de la EPH, con la
  nota de que «la serie sintética pública no incluye este dato».

O sea: todo el sistema sabía que eran dos cosas distintas y publicaba una con el
nombre de la otra. El único lugar donde la confusión seguía viva era el
identificador — y el identificador es lo que ve el lector.

Había además un segundo error, más chico y más fácil de propagar: la web decía
**«% de ocupados»**. INDEC lo define sin ambigüedad: «Tasa de subocupación
demandante: calculada como porcentaje entre la población de subocupados
demandantes y la **población económicamente activa**». Sobre ocupados o sobre
PEA no da lo mismo, y decir «ocupados» invita a compararla contra la tasa de
empleo, que se calcula sobre la población total.

## Factores de decisión

- **Un identificador es la unidad de sentido más estable que tiene un
  indicador**: sobrevive a los cambios de rótulo, de banda y de peso.
- **La migración tiene que ser explícita**: dos claves conviviendo se leerían
  como dos indicadores.
- **La historia no se pierde ni se duplica.**
- **La base del porcentaje es parte de la definición**, no un detalle de
  presentación.

## Opciones consideradas

- **A — Dejar el id y arreglar sólo los rótulos.**
- **B — Migrar el id a `subocupacion_demandante`** en código, series, web,
  fichas y tests, en un solo paso.
- **C — Construir el pluriempleo de verdad** desde los microdatos de la EPH.

## Decisión

**Opción B.** El indicador pasa a llamarse `subocupacion_demandante` en todas
partes, y la unidad pasa a **`% de la PEA`**.

La migración incluye la **serie histórica versionada**: las 40 filas del CSV se
renombran en el lugar, con su unidad y su fuente corregidas. Y se declara la
sustitución en `INDICADORES_SUSTITUIDOS`, porque una corrida acotada por
indicador hace *merge* con el CSV existente: sin declararla, quedarían las dos
claves como si fueran series distintas del mismo cinturón.

La opción A deja el problema donde estaba: el id es lo que aparece en el JSON
publicado, en BigQuery y en cualquier análisis que alguien haga sobre estos
datos. La opción C es un indicador nuevo, no una corrección — y la entrada de
`manual.py` que documenta cómo se haría se conserva, ahora marcada como **«NO se
publica»** para que nadie la confunda con esta card.

### Consecuencias

- **El valor, la serie y el peso no cambian.** Cambian el nombre y la unidad
  declarada. Es una corrección de rótulo, y por eso no mueve ningún índice.
- Cualquier consulta histórica contra BigQuery o contra los snapshots
  commiteados encuentra `pluriempleo` hasta el 25-ago-2026 y
  `subocupacion_demandante` desde entonces. La ficha lo registra.
- Los ADR viejos siguen diciendo `pluriempleo` y así queda: son registro
  histórico, no documentación vigente.

### Confirmación

`tests/test_universos_declarados.py`:

- el indicador está en las dimensiones con el nombre nuevo y no con el viejo;
- **la clave vieja no sobrevive como identificador en ningún script**, con dos
  excepciones que el test acepta a propósito: la declaración de sustitución
  —que tiene que nombrarla para poder purgarla— y `manual.py`, que documenta el
  otro indicador;
- la serie histórica se migró entera, sin perder filas ni duplicarlas;
- la serie y la web declaran `% de la PEA`, y **`% de ocupados` no puede
  volver**;
- la sustitución está declarada para que una corrida acotada purgue la vieja.

Probado rompiéndolo: si la clave vieja vuelve a la tabla de dimensiones, fallan
dos guardas.

## Pros y contras de las opciones

### A — Sólo los rótulos

- Bueno, porque no toca datos versionados.
- Malo, porque el id es lo que queda en el JSON, en BigQuery y en todo análisis
  posterior: el rótulo se corrige y la confusión sigue viajando.

### B — Migrar el id

- Bueno, porque el nombre pasa a describir lo que se mide.
- Malo, porque parte la serie en dos nombres para cualquiera que consulte el
  archivo histórico. Se mitiga documentándolo en la ficha.

### C — Construir el pluriempleo real

- Bueno, porque el fenómeno es interesante y hoy no se mide.
- Malo, porque exige procesar microdatos de la EPH trimestre a trimestre: es un
  indicador nuevo con su propio diseño, no el arreglo de éste.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_impacto_social.md`.
- INDEC, «Conceptos de la EPH»: la tasa se calcula sobre la PEA.
