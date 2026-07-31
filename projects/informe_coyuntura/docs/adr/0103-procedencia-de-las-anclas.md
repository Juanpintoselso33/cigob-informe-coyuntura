---
madr: 4
id: '0103'
estado: 'aceptado'
fecha: 2026-07-20
archivos: ['scripts/procedencia_anclas.py']
continuado_por: ['0104', '0105', '0123']
cerrado_por: ['0120', '0121']
ambito: 'Los cuatro índices paramétricos · `scripts/procedencia_anclas.py`'
origen: 'Auditoría del cinturón de gestión, punto 3.2 (circularidad de las bandas)'
---

# ADR-0103 — Cada ancla declara de dónde sale, y el sesgo se vuelve contable

## Contexto y planteo del problema

La auditoría planteó un riesgo que no es un bug de ningún indicador en
particular sino una propiedad del método entero:

> "Las bandas se fijan mirando lo que el gobierno ya logró. Si el ancla se
> acomoda al dato, el puntaje tiende a ser alto por construcción."

Y pidió algo concreto: **distinguir en la documentación pública qué bandas están
ancladas a un criterio normativo externo y cuáles son convenciones internas.**

El reclamo es correcto y el proyecto ya lo había tropezado varias veces por
separado —ADR-0045 fijó cuándo se puede recalibrar contra el rango observado,
ADR-0059 revirtió una recalibración que blanqueaba señal real— pero nunca se
había medido **cuánto** del puntaje descansa en anclas de cada tipo.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

`scripts/procedencia_anclas.py` clasifica los 42 indicadores que puntúan y
calcula qué fracción del peso de cada índice viene de cada tipo de ancla.

| categoría | qué significa |
|---|---|
| `externa` | referencia verificable fuera del proyecto y ajena al período medido |
| `documento` | fijada en el documento de diseño **antes** de ver los datos |
| `conceptual` | anclada a un valor con significado propio (el cero, la paridad, el 100%) |
| `historia_larga` | calibrada con serie propia que incluye gobiernos anteriores |
| `convencion` | calibrada mirando el rango observado desde dic-2023 |
| `sin_declarar` | el código no dice de dónde sale |

Las dos últimas son las que la auditoría señala. Su suma es el número que el
script publica como **riesgo de circularidad**.

### Consecuencias

| índice | circular | externa | detalle |
|---|---|---|---|
| **ITCM** | **83%** | **0%** | 38% convención + 45% sin declarar |
| ITCP | 61% | 18% | 40% convención + 21% sin declarar |
| ITCG | 51% | 0% | 35% convención + 16% sin declarar, 34% del documento |

Dos hallazgos que no estaban en la auditoría:

**1. El índice más expuesto es el que nadie auditó.** La auditoría revisó
gestión; la del cinturón político cerró la semana pasada con siete ADRs. El
ITCM —el índice más "duro", el de inflación y reservas— nunca se auditó y es el
más circular de los tres, sin una sola ancla externa. El caso más claro es
`iai`, cuyo comentario dice textualmente que *"el umbral ±2% del doc no
sobrevive al dato"* y lo reemplaza por bandas calibradas a 2024-2026: se
descartó el ancla anterior a los datos y se la reemplazó por una posterior.

**2. Existe una categoría peor que "convención interna": la convención no
declarada.** El 45% del peso del ITCM está en bandas cuyo comentario sólo dice
la unidad —`ipc_total` dice "% mensual" y nada más—. No es que el criterio sea
malo: es que no hay criterio escrito que discutir. La auditoría pedía separar
externas de convenciones y asumía que toda banda tenía alguna justificación
declarada; una porción grande no la tiene.

**3. Una parte del sesgo no es irreducible: es trabajo pendiente.** El
argumento cómodo es que con 30 de los 42 indicadores sin serie anterior a
dic-2023 no hay contra qué otra cosa calibrar. Es cierto para la mayoría, pero
no para todos. Cinco indicadores **tienen historia previa sustancial y aun así
su ancla es circular o no está declarada**:

| indicador | serie desde | categoría hoy |
|---|---|---|
| `iaf_transferencias` | dic-2018 | sin declarar |
| `emae_ia` | may-2021 | sin declarar |
| `ipc_total` | ago-2021 | sin declarar |
| `recaudacion` | sep-2021 | sin declarar |
| `saldo_comercial_12m` | may-2022 | sin declarar |

(`iai`, `icip` e `idm` figuran con historia previa, pero arrancan entre
septiembre y noviembre de 2023: uno a tres meses no alcanzan para anclar nada.)

Ahí la circularidad no es una limitación del dato disponible — es que nadie
escribió el criterio. Es la lista de trabajo concreta que sale de este ADR.

- `tests/test_procedencia_anclas.py` (46 casos) impide que el registro se
  desactualice: un indicador nuevo sin procedencia declarada rompe la suite. El
  test espejo —declarar algo que ya no puntúa— disparó en la primera corrida con
  `asistencia_directa`, que había salido del índice por ADR-0100.
- Cada entrada guarda el **motivo**, no sólo la categoría: sin la referencia
  citada, `externa` sería una afirmación sin respaldo, que es el problema que
  este ADR viene a resolver.
- Trabajo futuro, en orden de prioridad: (a) los **cinco** indicadores con
  historia previa desaprovechada del hallazgo 3, donde se puede anclar contra
  gobiernos anteriores y hoy no se hace; (b) las **7** bandas `sin_declarar` del
  ITCM, que no requieren recalibrar nada — requieren escribir de dónde salieron,
  y si no se puede reconstruir, decirlo.

## Más información

### Limitaciones

**No corrige el sesgo, lo vuelve contable.** Para los 30 indicadores sin
historia previa, calibrar contra el período medido es en buena medida
irreducible. La respuesta honesta no es declarar externas unas anclas que no lo
son, sino publicar cuánto del puntaje descansa en cada tipo y dejar que el
lector lo pondere.

**La clasificación es una primera pasada y es de criterio.** Se llenó leyendo
uno por uno los comentarios de `BANDAS_*`. Los casos `convencion` son los que
conviene que el editor revise: algunos pueden ser reclasificables si se
encuentra la referencia externa que falta, y ése es justamente el trabajo que
el registro habilita.
