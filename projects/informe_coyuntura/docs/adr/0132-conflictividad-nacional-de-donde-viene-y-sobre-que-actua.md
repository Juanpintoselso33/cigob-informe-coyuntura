---
madr: 4
id: '0132'
estado: 'aceptado'
nota_estado: 'Aceptado — se mantiene en el ITCP, con la evidencia declarada'
fecha: 2026-07-25
cinturon: 'politica'
indicadores: [conflictividad_nacional, conflicto_social]
complementa: ['0052']
cierra: ['0094']
ambito: 'ITCP · `conflictividad_nacional` · dimensión `conflicto_social`'
origen: 'Pendiente editorial abierto desde ADR-0052'
---

# ADR-0132 — Conflictividad nacional: de dónde viene y sobre qué actúa

| **Complementa** | ADR-0052 (entrada del indicador), ADR-0064 |

## Contexto y planteo del problema

### La pregunta

Desde que `conflictividad_nacional` reemplazó a `movilizacion_cepa` (ADR-0052)
quedó anotado como pendiente editorial si el indicador **corresponde al cinturón
político** o si describe condiciones sociales y debería vivir en vida cotidiana.

Se resolvió con evidencia en vez de con criterio a secas.

## Opciones consideradas

- **Dejar `conflictividad_nacional` en el ITCP** — elegida, y resuelta con evidencia en vez de con criterio a secas.
- **Moverlo a vida cotidiana** — descartada: dejaría al ITCP sin ninguna medida de presión de calle. El cinturón mediría Congreso, gobernadores, empresarios y Justicia, y quedaría ciego al único actor que no pasa por una institución.

## Decisión

### Decisión: se queda en el ITCP

La correlación dice **de dónde viene** el conflicto, no sobre qué actúa.

Que la conflictividad se explique mejor por la brecha salario/canasta que por
cualquier variable legislativa es esperable: **el conflicto social se origina en
las condiciones materiales**. Pero lo que el ITCP mide es la capacidad de
gobernar y avanzar la agenda, y la calle es una restricción sobre esa capacidad,
no una consecuencia de ella.

Un índice debe ubicar un indicador **por lo que restringe, no por lo que lo
causa**. Con el criterio inverso, media macroeconomía habría que mudarla a vida
cotidiana porque explica mejor el humor social.

Queda como está: dimensión `conflicto_social`, 10% del ITCP, un solo indicador.

## Más información

### Qué dicen los datos

Correlación de la serie mensual (31 puntos, dic-2023 → jun-2026) contra los
indicadores de los dos cinturones candidatos:

| | \|r\| medio |
|---|---|
| contra los 11 indicadores del ITCP | **0,425** |
| contra los indicadores de vida cotidiana | **0,407** |

**Prácticamente iguales. El test de pertenencia por correlación agregada no
resuelve nada**, y conviene decirlo antes que forzar una lectura.

Pero mirando los pares individuales aparece algo que sí ordena:

| par | r |
|---|---|
| **brecha_salario_cbt** (vida) | **−0,859** |
| empleo_registrado (vida) | +0,716 |
| desafios_legislativos (ITCP) | −0,597 |
| cobertura_judicial (ITCP) | +0,592 |
| veto_quorum (ITCP) | −0,578 |
| icc_utdt (vida) | −0,578 |

**La relación más fuerte de todo el análisis —por bastante— es con el poder
adquisitivo del salario, y es de vida cotidiana.** Ningún indicador del cinturón
político llega a 0,60.

### Lo que esto sí obliga a declarar

- **El indicador es en buena medida endógeno a las condiciones materiales.** Con
  r = −0,859 contra la brecha salario/canasta, una parte grande de su movimiento
  no informa sobre decisiones políticas sino sobre el poder adquisitivo. Al leer
  el ITCP conviene tenerlo presente: cuando la dimensión de conflicto social se
  mueve, puede no haber pasado nada en el tablero político.
- **Hay solapamiento informativo entre cinturones.** No es doble conteo —son
  índices separados que no se suman— pero sí significa que un deterioro salarial
  empeora dos cinturones por dos caminos. Está declarado acá y no en una nota al
  pie.
- **La dimensión sigue colgando de un solo indicador**, igual que
  `cohesion_interna`, `imagen_voto`, `sector_privado` y `poder_judicial`.

### Alternativa que se descartó

**Moverlo a vida cotidiana.** Se descartó por el argumento de arriba, y porque
dejaría al ITCP sin ninguna medida de presión de calle: el cinturón mediría
Congreso, gobernadores, empresarios y Justicia, y sería ciego al único actor que
no tiene representación institucional en el tablero.

### Cómo se llegó acá

El análisis está en el propio ADR y es reproducible: serie mensual de
`conflictividad_nacional` contra las series publicadas de ambos cinturones,
Pearson sobre los meses comunes, mínimo 10 puntos. Sin recorte de ventana ni
selección de pares.
