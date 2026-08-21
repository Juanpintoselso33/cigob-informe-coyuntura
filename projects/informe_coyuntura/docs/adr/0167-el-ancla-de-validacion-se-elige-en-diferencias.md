---
madr: 4
id: '0167'
estado: 'aceptado'
fecha: 2026-07-31
cinturon: 'transversal'
archivos: ['scripts/validacion_externa.py']
cierra: ['0154']
relacionado: ['0045', '0155', '0158', '0159', '0161', '0162', '0169', '0175', '0225']
ambito: 'Validación externa de los cuatro índices · criterio de elección del ancla'
origen: 'Al recorrer las decisiones editoriales abiertas de vida y macro, ésta era la única que fijaba una regla general'
---

# ADR-0167 — El ancla de validación se elige por diferencias, no por niveles

## Contexto y planteo del problema

ADR-0154 dejó anotado un pendiente que nunca se resolvió como regla:

> si el criterio del proyecto para elegir ancla es «la que valida en
> diferencias» o «la que más correlaciona en niveles». Acá se eligió la primera
> por decisión del editor; son criterios distintos y llevan a anclas distintas.

El criterio se aplicó una vez, para un índice, sin escribirse. Cada ancla nueva
volvía a plantear la misma pregunta desde cero, y la respuesta dependía de quién
la mirara.

## Factores de decisión

- **La tendencia compartida está medida, no supuesta.** ADR-0162 lo estableció
  para todo el proyecto: en estos años casi todas las series argentinas
  comparten la tendencia del período, así que una correlación alta en niveles
  puede ser sólo eso. Por eso ese ADR reporta el aporte incremental de R² sobre
  una tendencia, en vez del R² a secas.
- **Elegir por niveles es elegir el resultado.** El ancla que "más correlaciona"
  es, en este contexto, la que mejor comparte la tendencia. Optar por ella es la
  misma clase de decisión que ADR-0045 prohíbe con las anclas de banda: mover un
  criterio para que un test dé mejor.
- **La práctica ya iba por ahí.** El ancla del ITCM reemplazó a un indicador de
  mercado que *"correlacionaba fuerte en niveles y ~0 en primeras diferencias"*,
  y el ITVC pasó al consumo medido por el mismo motivo (ADR-0155). Lo que
  faltaba era la regla, no el comportamiento.
- El costo es real y hay que decirlo: los r publicados bajan.

## Opciones consideradas

- **La que valida en primeras diferencias** — elegida.
- **La que más correlaciona en niveles** — descartada: choca con lo que el
  propio proyecto midió en ADR-0162 y con el patrón de ADR-0045.
- **No elegir: publicar los dos y que el lector vea la brecha** — no como
  criterio de elección, aunque sí como forma de publicación (ver decisión 2).

## Decisión

### 1. El ancla se elige por su correlación en primeras diferencias

Cuando un índice necesita un ancla de validación externa, la candidata se juzga
por cuánto correlaciona **fuera de la tendencia común**. Una candidata que
valida en niveles y se cae en diferencias no es un ancla: es una serie que
comparte el período.

### 2. Se publican los dos números, siempre

Elegir por diferencias no autoriza a esconder el nivel. La validación publica
ambos —como ya hace hoy: ITVC contra consumo medido da **0,596** en niveles y
**0,246** en primeras diferencias— porque la brecha entre los dos *es* el dato
sobre cuánta de la correlación es tendencia compartida. Es el mismo criterio con
el que ADR-0159 publica convergente, discriminante y la brecha.

### Consecuencias

- **No requiere cambiar nada hoy.** Verificado al decidir: las anclas vigentes
  del ITCM y del ITVC ya se eligieron con este criterio y ya publican los dos
  números. Este ADR codifica la práctica y le pone nombre; el trabajo que evita
  es el de la próxima ancla, no el de las actuales.
- Los r que el informe publica son y van a seguir siendo más bajos que los que
  saldrían eligiendo por niveles. Es deliberado.
- Cierra el pendiente de ADR-0154, que era la última decisión editorial de
  método abierta en el cinturón de vida cotidiana.

### Confirmación

`output/validacion_externa.json` publica hoy `niveles` y `primeras diferencias`
para cada par, y `tests/test_validacion_externa.py` cubre el módulo. Una ancla
nueva que sólo reporte niveles es, por este ADR, una ancla sin justificar.

## Más información

### Limitaciones

- En primeras diferencias el ruido pesa más, así que los r caen para todos —
  incluso para un ancla buena. La regla dice **cómo comparar candidatas entre
  sí**, no fija un umbral de aprobación: un r de 0,246 en diferencias no es
  "malo" en abstracto, es lo que hay que leer contra las alternativas.
- Con series cortas la estimación en diferencias es inestable. Donde la historia
  todavía no alcanza, corresponde decirlo al publicar antes que elegir por
  niveles porque el número se ve mejor.
