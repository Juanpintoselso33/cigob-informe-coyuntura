---
madr: 4
id: '0170'
estado: 'aceptado'
fecha: 2026-07-31
cinturon: 'politica'
indice: 'ITCP'
indicadores: [judicializacion, paralisis_denuncias]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py']
continua: ['0168']
relacionado: ['0131', '0134', '0135', '0139', '0191']
ambito: 'Cinturón político (ITCP) · dimensión `poder_judicial`'
origen: 'ADR-0168 dejó declarado que tres de los cuatro indicadores leían un relevamiento versionado en vez de la fuente'
---

# ADR-0170 — Judicialización y parálisis de denuncias pasan a fuente viva

## Contexto y planteo del problema

ADR-0168 incorporó cuatro indicadores al ITCP y dejó declarado que **tres de
los cuatro leían un relevamiento versionado y no la fuente**. Un store curado
que no se refresca es un indicador viejo sin que ningún gate lo note: la card
y la serie salen del mismo archivo, así que la comprobación de coherencia
entre ambas pasa siempre.

De los tres, dos son automatizables. `velocidad_resolucion` no lo es: su fuente
son tableros que no admiten consulta y un anuario en documento (ADR-0140).

## Factores de decisión

- Las dos consultas ya estaban **verificadas y documentadas** en sus propios
  relevamientos; no había que descubrirlas, había que ejecutarlas.
- El sitio del Consejo no publica `robots.txt` —404—, así que no hay
  restricción declarada por el operador. Y expone la **API REST de WordPress**,
  que es una interfaz de datos y no scraping de HTML.
- La numeración secuencial de las sesiones es lo que valida la cobertura: si el
  Consejo sesionara sin publicar la nota, el número siguiente delataría el
  hueco.

## Opciones consideradas

- **Automatizar las dos** — elegida.
- **Dejarlas leyendo el store** — descartada: es lo que ADR-0168 declaró como
  deuda.
- **Scrapear el HTML del Consejo** — descartada: la API REST devuelve fecha y
  slug estructurados, con la numeración de sesión incluida en el slug.

## Decisión

### 1. `judicializacion` consulta SAIJ en cada corrida

Dos consultas por año al buscador —una con el término y otra sin él—, ambas
restringidas a jurisdicción Federal + Nacional por la faceta. El conteo sale de
`categoriesResultList`, no de `totalSearchResults`, que viene topeado por el
pageSize: es la corrección que el relevamiento de ADR-0135 ya le había hecho a
ADR-0131.

### 2. `paralisis_denuncias` consulta la API del Consejo

Posts de las categorías de Acusación y Disciplina; el número de sesión sale del
slug y la fecha del campo `date`. La ventana es de 12 meses **calendario**
terminados en el mes informado.

### Consecuencias

- Los dos indicadores dejan de depender de una pasada manual. El bloque
  judicial queda con dos fuentes vivas de tres.
- Los valores cambian: `judicializacion` 1,78 → **1,65** y
  `paralisis_denuncias` 6 → **7**. El primero porque SAIJ siguió indexando 2026
  desde el relevamiento del 26-jul; el segundo por el defecto que sigue.

### Confirmación

**SAIJ reproduce el relevamiento en 10 de sus 11 años, exacto.** El único que
difiere es 2026, el año en curso, donde el valor vivo es el fresco. Los conteos
crudos también coinciden: 2024 da 233/11.962 y 2025 da 215/12.575, idénticos a
los que el relevamiento había registrado a mano.

**El colector del Consejo reproduce los eventos crudos del propio store en 32
de 32 meses.**

## Más información

### Un defecto del relevamiento, encontrado al automatizar

La serie `serie_12m` publicada en `denuncias_comisiones_universo.json` **no se
reproduce desde su propio universo de eventos**. Reconstruida a partir de las
listas `sesiones_ordinarias` del mismo archivo, difiere en nueve meses:
2024-09, 2024-12, 2025-05, 2025-06, 2025-08, 2025-10, 2025-11, 2026-05 y
2026-07. El colector en vivo coincide con los eventos crudos en los 32 meses,
así que el defecto está en la derivación manual, no en la consulta.

Es el patrón de siempre: el universo estaba bien relevado y la serie derivada de
él no. Auditar los registros crudos uno por uno es lo que lo muestra.

### La serie corregida valida PEOR, y se publica igual

Medido con el contrafáctico, aislando el cambio: la `paralisis_denuncias`
**defectuosa** daba ITCP↔EPU en diferencias de **−0,405**; la corregida da
**−0,378**. La serie mala correlacionaba mejor.

Se publica la corregida. Quedarse con el insumo que hace que un test dé mejor
es exactamente lo que ADR-0045 prohíbe, y no cambia de naturaleza porque acá el
test sea una validación externa en vez de una banda. La correlación mejor era
un artefacto de una serie que no reproducía su propia fuente.

El costo está medido y es 0,027 de correlación. Lo que se compra es una serie
que coincide con sus registros crudos en 32 de 32 meses.

### La sesión que estaba mal fechada

El relevamiento anotaba que el número 7 de Acusación era *"un solo número sin
identificar, que muy probablemente sea el post sin numerar del 20-dic-2023"*.
La API encuentra la nota numerada real: **06-dic-2023**. La conjetura era
razonable y era incorrecta.

### Limitaciones

- La normalización de SAIJ divide el volumen editorial de la base, pero no un
  eventual cambio en su **mezcla**. Sigue siendo la limitación declarada de
  ADR-0135 y no la resuelve este cambio.
- El punto del año en curso se recalcula en cada corrida y sube a medida que
  SAIJ indexa. Al ser un cociente, numerador y denominador se recortan juntos,
  así que el punto es comparable — pero se mueve.
- `velocidad_resolucion` sigue leyendo el store, y no hay camino de salida
  conocido: la fuente no admite consulta automática.
