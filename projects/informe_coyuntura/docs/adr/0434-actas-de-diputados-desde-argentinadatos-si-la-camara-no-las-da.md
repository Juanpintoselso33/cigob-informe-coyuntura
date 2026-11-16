---
madr: 4
id: '0434'
estado: 'aceptado'
fecha: 2026-11-16
cinturon: 'politica'
indice: 'ITCP'
indicadores: [desafios_legislativos, bloqueo_sostenido, votos_sobre_bancas, cohesion_bloque]
archivos: ['scripts/argentinadatos_diputados.py', 'scripts/politica.py', 'tests/test_argentinadatos_diputados.py', 'tests/conftest.py', 'web/src/lib/fichas.ts']
relacionado: ['0431', '0432']
ambito: 'Fuente de respaldo de las actas de votación nominal de Diputados'
origen: 'Juan, 16-nov-2026: «hay que arreglar de alguna manera, buscá fuentes alternativas».'
---

# ADR-0434 — Si la Cámara no da un acta de Diputados, se lee de ArgentinaDatos

## Contexto y planteo del problema

Las actas de votación nominal de Diputados se leían del PDF de `votaciones.hcdn.gob.ar`. Desde
el 16-nov-2026 ese sitio devuelve 403 a todo, desde la Mac y desde GitHub; desde GitHub ya se
colgaba desde el 5-nov. Las usan desafíos legislativos, bloqueo sostenido, votos sobre bancas
y la cohesión del bloque.

ArgentinaDatos (`api.argentinadatos.com/v1/diputados`) es un proyecto abierto que replica las
actas de la Cámara en JSON: id, fecha, título, resultado, tipo de mayoría, totales y el voto
de cada diputado por nombre. Su padrón trae el bloque y la provincia de cada diputado.

## Factores de decisión

- Mismo dato que el PDF.
- No tocar la lógica de cada indicador.
- Que una caída de las dos fuentes siga siendo una caída.

## Opciones consideradas

- **ArgentinaDatos como respaldo, sólo cuando la Cámara no da el acta (elegida).**
- La copia del Internet Archive: no tiene las actas nuevas.
- Esperar a que la Cámara levante el bloqueo: sin fecha.

## Decisión

`_diputados_acta_pdf` pide el PDF a la Cámara. Si no lo consigue, busca el acta en
ArgentinaDatos.

- Si el acta está, devuelve un `ActaAD`. Es un `bytes` vacío que lleva el JSON, y los
  lectores de PDF (`_parsear_acta_diputados_pdf`, `_diputados_acta_fecha`,
  `_parsear_encabezado_acta_diputados`, `_cabecera_acta_diputados_pdf`) lo reconocen y leen
  los mismos campos del JSON.
- Si el acta no está pero ArgentinaDatos tiene la numeración, es un hueco.
- Si ArgentinaDatos tampoco responde, es un fallo, como antes.

La fecha se pasa de UTC a hora argentina. Al que preside se lo saca de las filas, como en el
PDF. El bloque sale del padrón, con el nombre normalizado sin apodos y, si no aparece, por
apellido y primer nombre.

### Validación (16-nov-2026)

- Las 238 actas de 2025 y 2026 son las mismas en las dos fuentes, sin una de más ni de menos.
  Los 14 ids que «no contestaban» no existen en ninguna.
- Los afirmativos coinciden en todas.
- El encabezado coincide con el del PDF en las actas guardadas en el registro de derrotas.
  Por ejemplo, la 5736 (habilitación, afirmativa 159-75) y la 5737 (insistencia de la ley
  27.791, negativa 160-83).
- El bloque tiene un límite:
  - En 2026 el padrón no tiene a un diputado (Martín Matzkin, de LLA), así que LLA da uno
    menos (93 contra 94).
  - Para 2025 el padrón fecha mal los pases de bloque: 49 contra 39.
  - Por eso los conteos por bloque de un acta leída de ArgentinaDatos pueden diferir en un
    diputado. Todas las actas existentes ya están leídas del PDF y guardadas; el respaldo sólo
    lee las nuevas.

### Consecuencias

- Desafíos legislativos y bloqueo sostenido vuelven a calcularse: sólo usan el encabezado,
  que coincide.
- Las pruebas no salen a la red: `conftest.py` corta ArgentinaDatos en todas, salvo en las
  pruebas del respaldo.

### Confirmación

`tests/test_argentinadatos_diputados.py`.

## Pros y contras de las opciones

- Elegida: el mismo dato, sin tocar los indicadores. A cambio, depende de un tercero y el
  bloque puede diferir en un diputado.
- Internet Archive: no sirve para lo nuevo.
- Esperar: los cuatro quedan congelados.

## Más información

https://argentinadatos.com · `https://api.argentinadatos.com/v1/diputados/actas/2026`
