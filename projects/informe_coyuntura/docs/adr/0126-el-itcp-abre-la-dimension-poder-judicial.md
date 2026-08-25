---
madr: 4
id: '0126'
estado: 'aceptado'
fecha: 2026-07-25
cinturon: 'politica'
indicadores: [poder_judicial, cobertura_judicial]
relacionado: ['0168', '0240']
complementado_por: ['0131']
ambito: 'ITCP · dimensión `poder_judicial` (nueva) · `cobertura_judicial` (nuevo) · pesos entre dimensiones · banda · serie'
origen: 'Aporte externo sobre el cinturón político (doc 260724), decisión del editor'
---

# ADR-0126 — El ITCP abre la dimensión del Poder Judicial

## Contexto y planteo del problema

El aporte externo propuso ampliar el cinturón con dos bloques —Poder Judicial y
Poder Económico— y listó nueve indicadores candidatos con su nivel de
automatización y su limitación principal. El bloque económico ya había entrado
como `sector_privado` (ADR-0088); este ADR abre el judicial.

El hueco era real y del mismo tipo que el que cerró ADR-0088: **el índice medía
en detalle al Congreso, de forma indirecta a los gobernadores, y no medía en
absoluto al Poder Judicial**, que es un actor de veto de primer orden sobre la
agenda de un gobierno.

## Opciones consideradas

- **`cobertura_judicial`**: porcentaje de cargos de juez habilitados que tienen juez designado — elegida entre los nueve indicadores candidatos que se listaron con su nivel de viabilidad.
- **Contar como cubierto el cargo con subrogante** — descartada: la subrogancia es una solución transitoria.

## Decisión

Entra `cobertura_judicial`: **porcentaje de cargos de juez habilitados que tienen
juez designado**.

| | |
|---|---|
| cargos de juez habilitados | 955 |
| con titular designado | **604** |
| con subrogante a cargo | **282** |
| sin cubrir | **69** |
| cobertura (jul-2026) | **69,95%** → 52,4 puntos |

Un cargo con subrogante **cuenta como no cubierto**: la subrogancia es una
solución transitoria, no un juez designado para ese tribunal. La composición se
publica en la card para que el lector pueda hacer la lectura contraria.

### Por qué en este cinturón y no en el de gestión

Designar jueces **exige acuerdo del Senado**. Es una capacidad negociada, no una
decisión administrativa del Ejecutivo — que es justamente lo que el ITCP mide.

### Los pesos

La dimensión entra con **0,15**, igual que `sector_privado`, y las seis
existentes ceden **proporcionalmente (×0,85)**, de modo que su orden relativo no
se toca. Es el segundo cambio de pesos entre dimensiones desde ADR-0036 y sigue
el precedente de ADR-0088.

| dimensión | antes | ahora |
|---|---|---|
| poder_legislativo | 0,25 | 0,21 |
| alianzas_territoriales | 0,22 | 0,19 |
| cohesion_interna | 0,18 | 0,15 |
| **poder_judicial** | — | **0,15** |
| sector_privado | 0,15 | 0,13 |
| conflicto_social | 0,12 | 0,10 |
| imagen_voto | 0,08 | 0,07 |

**ITCP 69,0 → 66,6** (tensión 3,1 → 3,3). El Poder Judicial entra como la
dimensión más floja del cinturón.

## Más información

### Limitaciones

- **Un solo indicador, y mide capacidad, no comportamiento.** Cobertura de
  cargos no dice nada sobre cómo falla la Justicia, con qué velocidad resuelve
  ni en qué sentido. Los cinco indicadores que faltan cubren eso y todos
  esperan el protocolo de codificación.
- **El total de cargos se mantiene constante** en la reconstrucción. Habilitar
  tribunales nuevos movería el denominador; la serie es más confiable cerca de
  la fecha del padrón que en su extremo inicial.
- **Descontar las subrogancias por completo es discutible**: un juzgado con
  subrogante funciona, aunque precariamente. Por eso la composición se publica.
- **Los traslados no se procesan como evento propio.** Un traslado deja una
  vacante y cubre otra y en el agregado se compensan, pero puede introducir
  diferencias de un cargo en meses puntuales.
- La reconstrucción hacia atrás **no se validó contra una foto histórica del
  padrón**, porque no hay ninguna publicada. Las juras del padrón vigente no
  sirven de contraste: ninguna es posterior a dic-2023.

### Por dónde se empieza

De los seis indicadores judiciales propuestos, **cinco dependen de un protocolo
de codificación de contenido que todavía no existe** —clasificar un fallo como
favorable o adverso, decidir qué causa es "sensible"—. El propio aporte lo
señala como su recomendación principal. Publicarlos sin ese protocolo dejaría el
puntaje colgado del criterio de quien arme el informe cada mes.

**Tasa de Cobertura de Vacantes es el único que es un conteo y no un juicio**, y
por eso es el que entra.

### La fuente que el aporte no tenía

El aporte proponía scrapear el archivo de "Concursos" del Consejo de la
Magistratura y adjuntaba un piloto de parser validado offline. **No hace falta.**

El Ministerio de Justicia publica en `datos.jus.gob.ar`, en CSV estructurado:

| dataset | filas | qué aporta |
|---|---|---|
| Magistrados de la Justicia Federal y Nacional | 1.002 | padrón de cargos con `cargo_vacante` SI/NO |
| Designaciones de magistrados | 3.509 | eventos fechados desde 1976 |
| Renuncias de magistrados | 1.676 | eventos fechados |

El padrón trae exactamente la magnitud que el indicador necesita, sin scraping y
sin HTML. **El scraper del Consejo sigue siendo útil para los otros cinco
indicadores del bloque**, que sí necesitan datos de concursos.

### La serie: 32 puntos, dic-2023 → jul-2026

El padrón es una **foto fechada**, no una serie. Se reconstruye moviéndose desde
esa foto con los registros de designaciones y renuncias:

```
hacia atrás    vacantes(t) = vacantes(P) + designaciones(t,P] − renuncias(t,P]
hacia adelante vacantes(t) = vacantes(P) − designaciones(P,t] + renuncias(P,t]
```

| mes | cobertura | |
|---|---|---|
| dic-2023 | **72,77%** | punto de partida |
| dic-2024 | 70,68% | |
| dic-2025 | 65,24% | |
| **may-2026** | **64,08%** | piso de la serie |
| **jun-2026** | **70,16%** | 60 jueces designados el 11-12 de junio |
| jul-2026 | 69,95% | |

**La forma dice algo que ningún valor puntual diría:** la cobertura se erosionó
casi nueve puntos en dos años y medio, no por un conflicto sino por aritmética
—las renuncias siguieron y las designaciones se detuvieron casi por completo,
con un solo nombramiento en todo 2024—, y se recuperó de golpe cuando el Senado
aprobó un conjunto de pliegos.

**El padrón vigente (05-jun-2026) es anterior a ese lote**, así que la cifra que
publica el Ministerio hoy —61,8% sobre el total, 63,9% sobre habilitados— está
desactualizada respecto de la realidad. La serie lo corrige con los registros de
designaciones, que sí están al día.

### Las anclas

Cortes conceptuales por nivel de cobertura de un cuerpo: **>90 completa · 80-90
buena · 70-80 aceptable · 60-70 deficitaria · ≤60 crítica**.

**No se calibraron contra el rango observado**, y la consecuencia se asume: en
los 32 meses reconstruidos sólo se pueblan dos bandas. Eso **no es un defecto de
calibración, es el hallazgo** — la cobertura de la justicia argentina no estuvo
cerca del 80% en todo el período. Bajar los umbrales para poblar las bandas
altas convertiría un desempeño bajo en un puntaje alto, que es exactamente lo
que ADR-0045 prohíbe.

El puntaje interpolado igual discrimina en todo el recorrido: **34,5 en el piso
de may-2026 y 59,4 en dic-2023**, 25 puntos de amplitud.
