---
madr: 4
id: '0431'
estado: 'aceptado'
fecha: 2026-11-16
cinturon: 'politica'
indice: 'ITCP'
indicadores: [eficacia_legislativa, votos_sobre_bancas]
archivos: ['config.py', 'tests/test_gate_cache_esperable.py', 'web/src/lib/fichas.ts']
relacionado: ['0062', '0191', '0210', '0432', '0434', '0435', '0436']
ambito: 'Tolerancia de días sin fetch (G2b) de las dos cards que leen el portal de datos abiertos de Diputados'
origen: 'Corrida nocturna del 16-nov-2026: 8 de 14 indicadores políticos desactualizados; Juan: «hay que ver esos 8», y «a y b» (ventana y migración).'
---

# ADR-0431 — Sin el portal de datos de Diputados, eficacia y votos sobre bancas toleran 45 días

## Contexto y planteo del problema

`datos.hcdn.gob.ar`, el portal de datos abiertos de la Cámara de Diputados, está caído para
todos desde el 4-nov-2026: desde una IP argentina responde 503 con una página «Application
Blocked … company policy» (la de la Mac y la de la torre), y desde afuera no contesta (los
runners de GitHub y un lector externo agotan el tiempo). El último fetch exitoso de
`eficacia_legislativa` y `votos_sobre_bancas` es del 4-nov a la 1:55. Con la tolerancia por
defecto de 14 días ([[0191]]), G2b corta la publicación de todo el Monitor desde la corrida
del 19-nov.

Diputados no sesiona desde el 21-oct-2026 (índice de sesiones de hcdn.gob.ar), así que el
último valor sigue describiendo la situación: no hubo votaciones ni sanciones que cambien las
dos cards.

## Factores de decisión

- Una fuente caída que no depende de nosotros no puede frenar todo el Monitor.
- Que la excepción no quede callada para siempre.
- El dato que se publica sigue marcado como desactualizado y con su fecha.

## Opciones consideradas

- **Ventana declarada de 45 días para las dos cards (elegida, Juan, 16-nov, junto con la
  migración).** Es el mecanismo de [[0210]], el mismo de SAIJ.
- Sacar las dos cards del índice hasta que vuelva la fuente: cambia el ITCP por una caída
  técnica.
- No hacer nada: desde el 19-nov no se publica nada.

## Decisión

`DIAS_SIN_FETCH` de `config.py` suma `eficacia_legislativa` y `votos_sobre_bancas` con 45
días. Vence sola: a los 45 días del último fetch (19-dic-2026 para el del 4-nov) G2b vuelve a
cortar. En paralelo se migran las dos al buscador nuevo de proyectos de Diputados
(`www.hcdn.gob.ar/proyectos/buscador`), que trae los mismos expedientes con datos hasta el
5-nov; cuando la migración o el portal vuelvan, las dos entradas se sacan.

### Consecuencias

- Mientras dure, las dos cards no cuentan como arrastre en G2 y no cortan en G2b.
- Si el portal sigue caído y la migración no llega antes del 19-dic, la corrida vuelve a
  cortar: es la alarma.

### Confirmación

`tests/test_gate_cache_esperable.py::test_diputados_sin_portal_tolera_45_dias`.

## Pros y contras de las opciones

- Elegida: no toca el índice y tiene vencimiento; a cambio, durante semanas las dos cards
  pueden quedar con el dato del 4-nov.
- Sacarlas del índice: el número sería fresco pero movería el ITCP por una razón técnica.
- No hacer nada: un corte total por dos cards.

## Más información

Diagnóstico del 16-nov-2026: `curl https://datos.hcdn.gob.ar/` → 503 «Application Blocked»;
`r.jina.ai` → timeout; `www.hcdn.gob.ar/sesiones/` → última sesión 21/10/2026.
