---
madr: 4
id: '0144'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
indicadores: [cobertura_judicial]
ambito: 'cinturón político (ITCP) · `cobertura_judicial` · validación'
origen: 'piloto propuesto por la revisión externa del cinturón político'
---

# ADR-0144 — El piloto de concursos corrobora la cobertura judicial

- **Relacionados**: ADR-0126 (`cobertura_judicial`), ADR-0134 (archivo del Consejo)

## Opciones consideradas

- **No crear un indicador nuevo** — elegida: con 32 posts en cuatro años y un hueco de veinte meses, el archivo no sostiene una serie mensual.
- **Usarlo como corroboración** — es lo que sí aporta, y es exactamente lo que le faltaba a un indicador de fuente única.

## Decisión

1. **No se crea un indicador nuevo.** Con 32 posts en cuatro años y un hueco de
   veinte meses, el archivo no sostiene una serie mensual. Lo que aporta es
   corroboración, y eso es exactamente lo que le faltaba a un indicador de fuente
   única.
2. **El relevamiento queda versionado** en
   `data/politica/concursos_consejo_relevamiento.json`, con los 32 posts, sus
   números de concurso y sus URLs.
3. **La corroboración se declara en la ficha de `cobertura_judicial`**: que el
   quiebre de junio de 2026 aparece también en una fuente independiente.

## Más información

### Qué era y por qué faltaba

La revisión externa del cinturón político incluía un piloto técnico:

> "se validó un piloto de scraper contra el archivo de «Concursos» del Consejo
> de la Magistratura, que extrae fecha, número de concurso, tribunal mencionado
> y URL de cada entrada de forma automática. El script no pudo ejecutarse en
> vivo desde este entorno por restricción de red del sandbox (no incluye
> dominios .gov.ar), pero su lógica de parseo fue validada offline contra HTML
> real del sitio. Queda listo para correr en el entorno de CIGOB."

`cobertura_judicial` terminó saliendo por otro camino —el padrón de magistrados
de `datos.jus.gob.ar`, con reconstrucción por designaciones y renuncias
(ADR-0126)—, así que el piloto quedó sin correr. **Correrlo era lo que faltaba,
y valía la pena.**

### Lo que devolvió

Categoría `concursos` del sitio del Consejo, recorrida hasta agotarla: **4
páginas, 32 posts**, del 9-may-2022 al 7-jul-2026. **29 de 32 traen número de
concurso identificable**, del 436 al 511. La lógica de parseo del piloto
funciona tal como su autor la describió.

Y aparece un hecho que no estaba buscado:

| año | 2022 | 2023 | 2024 | **2025** | 2026 |
|---|---|---|---|---|---|
| posts | 3 | 14 | 8 | **0** | 7 |

**Veinte meses sin una sola publicación**: el último post es del 23-oct-2024 y el
siguiente del 4-jun-2026. Después, siete concursos con entrevistas personales
concentrados entre junio y julio de 2026 (481, 511, 508, 471, 497, 457, 464).

### Por qué esto importa: corrobora un indicador de fuente única

`cobertura_judicial` es de **fuente única**. El archivo de concursos es del
Consejo de la Magistratura, no comparte ni fuente ni método con el padrón del
Ministerio de Justicia, y marca **el mismo quiebre en el mismo mes**:

| | oct-2025 → may-2026 | jun-2026 |
|---|---|---|
| `cobertura_judicial` (padrón datos.jus) | cae de 67,12 a **64,08** | salta a **70,16** |
| concursos con entrevistas (archivo del Consejo) | **cero en 20 meses** | **siete** |

Y agrega lectura sobre lo que ya publicamos: el salto de junio **no fue sólo el
Senado aprobando un lote de pliegos**. La maquinaria de selección del Consejo
también se reactivó después de veinte meses sin publicar una entrevista. Son dos
cosas distintas —el flujo de selección y el stock de cargos cubiertos— y las dos
se movieron a la vez.

### Salvedad, y en qué se diferencia de ADR-0134

La ausencia de posts en 2025 **puede ser falta de actividad o falta de
publicación**, y acá —a diferencia del archivo de comisiones de ADR-0134— **no
hay numeración secuencial de posts que lo delate**: los números son de concurso,
no de entrada.

Lo que sí se observa es que los concursos entrevistados en 2026 llevan números
altos (hasta el 511), o sea que se seguían convocando durante el hueco. **El
freno estuvo en la etapa de entrevistas, no en la de llamado.** Eso acota la
lectura sin resolverla del todo, y queda dicho como tal.
