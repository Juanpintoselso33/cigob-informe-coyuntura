---
madr: 4
id: '0149'
estado: 'aceptado'
fecha: 2026-07-27
cinturon: 'politica'
indicadores: [sector_privado, apoyo_empresario]
ambito: 'cinturón político (ITCP) · `sector_privado` · herramienta interna'
---

# ADR-0149 — Detector de postura empresaria

- **Relacionados**: ADR-0148 (el registro que esto protege), ADR-0129 y ADR-0141
  (mismo patrón), ADR-0131 (protocolo de codificación)

## Contexto y planteo del problema

### Por qué, y por qué ahora

ADR-0148 dejó el indicador de postura empresaria funcionando, con **103
comunicados de AEA y UIA codificados a mano**. Falta la segunda pasada con otro
codificador para publicarlo.

El problema es el intervalo: **sin vigilancia, ese registro se queda viejo apenas
una cámara publica el siguiente comunicado.** Si pasan semanas hasta que alguien
haga el kappa, lo codificado ya no cubre el período y el trabajo se pierde justo
cuando la métrica empezaba a servir.

## Opciones consideradas

- **Marcar los comunicados nuevos como pendientes de codificar** — elegida.
- **Codificar la postura automáticamente** — descartada, por el mismo criterio de ADR-0129 y ADR-0141: se automatiza la vigilancia, no el juicio.

### Consecuencias

- `apoyo_empresario_novedades.json` entra al `git add` de `data-pipeline.yml`
  **en este mismo cambio**, con test que lo verifica
  (`feedback_cache_persistence_cron`: tres cachés se perdieron por olvidarlo).
- Siete tests, todos con dobles: no tocan la red.
- Va envuelto en `try` dentro de `main()`: si una cámara no responde se pierde un
  aviso, no un dato del índice. Y hay test de que una cámara caída no tumba a la
  otra.
- **Lo que sigue bloqueado no cambia**: la segunda pasada con otro codificador.
  Este detector no la reemplaza — la hace posible sin que el registro envejezca
  mientras tanto.

## Decisión

### Qué hace

`detectar_novedades_empresarias()` corre con el colector político y marca los
comunicados nuevos como **pendientes de codificar** en
`data/politica/apoyo_empresario_novedades.json`.

- **UIA**: se sondean los ids por encima del último conocido en
  `uia.org.ar/prensa/{id}/`. Las notas se sirven **sin JavaScript** aunque el
  listado sea una app, así que el corpus se recorre por id. Los ids se comparten
  con otras secciones del sitio, de modo que la mayoría del barrido devuelve
  nada — es esperable y no es un error.
- **AEA**: se lee la página de prensa completa; no numera sus comunicados.

Los 103 ya codificados entran como **revisados de arranque**, leídos del propio
registro de ADR-0148, así que no se re-avisan.

### Un detalle que hubiera roto el detector en silencio

**AEA no numera sus comunicados y publica más de uno el mismo día.** Con la fecha
sola como clave, dos comunicados del 7-mar-2021 colapsan en uno: el registro de
103 casos generaba **100 claves**, y los tres perdidos habrían aparecido como
«nuevos» en cada corrida, para siempre.

La clave lleva ahora fecha **más título normalizado**, y hay un test que contrasta
contra el registro real: si la construcción de claves se desalinea, falla.

### Primera corrida

46 comunicados vistos, **0 nuevos**, 103 revisados, 0 pendientes — correcto,
porque todo está codificado. Un detector que devuelve cero puede estar andando o
estar roto en silencio, así que se verificó aparte: el parser de UIA lee bien 3
de 3 ids conocidos y el barrido arranca en 4245 desde el último conocido (4244).

## Más información

### Lo que NO hace

- **No clasifica.** La postura y el destinatario los asigna una persona con las
  reglas de `apoyo_empresario_reglas.json`. Automatizar eso sería exactamente lo
  que ADR-0131 prohíbe.
- **No puntúa ni entra al ITCP.** Hay un test que además verifica que
  `apoyo_empresario` no aparezca en `itcp.py`, para que nadie lo conecte por
  descuido cuando ya nadie recuerde por qué.
