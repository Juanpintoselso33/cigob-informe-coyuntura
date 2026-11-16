---
madr: 4
id: '0435'
estado: 'aceptado'
fecha: 2026-11-16
cinturon: 'politica'
indice: 'ITCP'
indicadores: [produccion_legislativa]
archivos: ['scripts/infoleg_abierto.py', 'scripts/politica.py', 'tests/test_infoleg_abierto.py', 'tests/conftest.py', 'web/src/lib/fichas.ts']
relacionado: ['0431', '0398', '0168']
ambito: 'Fuente de respaldo de `produccion_legislativa`'
origen: 'Juan, 16-nov-2026: «hay que arreglar de alguna manera, buscá fuentes alternativas».'
---

# ADR-0435 — Si el catálogo de Diputados no responde, la producción legislativa sale de la base abierta de InfoLeg

## Contexto y planteo del problema

`produccion_legislativa` cuenta las leyes sancionadas en 12 meses, sin las vetadas en su
totalidad ([[0398]]). Las leía del catálogo de leyes sancionadas de `datos.hcdn.gob.ar`, que
no responde desde el 4-nov-2026 ([[0431]]). El Ministerio de Justicia publica todos los meses
en `datos.jus.gob.ar` la base completa de InfoLeg: cada norma con su tipo, número y fecha de
sanción. Es un ZIP de unos 50 MB; la última versión es del 2-nov-2026.

## Factores de decisión

- La misma serie que con el catálogo de Diputados.
- Una fuente que responda desde GitHub. `datos.jus.gob.ar` ya se usa para la cobertura de
  jueces.

## Opciones consideradas

- **La base abierta de InfoLeg, sólo si el catálogo de Diputados falla por red (elegida).**
- El buscador de proyectos de Diputados (`estado=ley`): habría que pedir el detalle de cada
  ley para saber su fecha de sanción, cientos de pedidos.

## Decisión

`_leyes_produccion()` pide el catálogo de Diputados y, si falla por red, toma las leyes
numeradas de la base de InfoLeg con su fecha de sanción. Las vetadas en su totalidad se
siguen sacando con el mismo registro. La URL del ZIP se resuelve por la API, porque cambia
con cada publicación.

Validación (16-nov-2026): la serie de 12 meses móviles armada con la base de InfoLeg
coincide con la publicada en los 35 meses, de diciembre de 2023 a octubre de 2026. A octubre
da 31 leyes.

### Consecuencias

- La base sólo trae leyes publicadas en el Boletín Oficial, y se actualiza una vez por mes.
  Una ley sancionada y todavía no promulgada entra con la actualización siguiente: el último
  mes puede quedar corto hasta entonces.
- Las pruebas no bajan la base: `conftest.py` la corta, salvo en
  `tests/test_infoleg_abierto.py`.

### Confirmación

`tests/test_infoleg_abierto.py`.

## Pros y contras de las opciones

- Elegida: la misma serie, en un solo pedido; a cambio, rezago de promulgación y
  actualización mensual.
- Buscador: más fresco, pero cientos de pedidos por noche.

## Más información

https://datos.jus.gob.ar/dataset/base-de-datos-legislativos-infoleg
