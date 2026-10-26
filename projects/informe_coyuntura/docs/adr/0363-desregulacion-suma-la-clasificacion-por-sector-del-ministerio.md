---
madr: 4
id: '0363'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [desregulacion_normativa]
archivos: ['scripts/gestion.py', 'web/src/lib/fichas.ts', 'tests/test_desregulacion_sectores.py', 'tests/fixtures/desregulacion_sectores_ago2026.json']
relacionado: ['0143', '0361']
ambito: 'Cinturón de gestión · ITCG · desregulación normativa'
origen: 'Observación #7 de la auditoría externa del cinturón de Gestión (23-oct-2026) y decisión de Juan del 26-oct-2026.'
---

# ADR-0363 — Desregulación suma la clasificación por sector del Ministerio

## Contexto y planteo del problema

`desregulacion_normativa` cuenta artículos modificados o eliminados
([[0143-la-desregulacion-se-mide-en-articulos]]). La auditoría externa
([[0361-respuesta-a-la-auditoria-del-cinturon-de-gestion]]) objetó que un
artículo menor cuenta igual que uno que transforma un régimen, y propuso
mantener el conteo y sumar una clasificación complementaria por sectores,
tipos de normas y naturaleza de los cambios.

## Factores de decisión

- Sólo datos publicados y verificables; nada de etiquetado propio permanente.
- El puntaje no cambia: la clasificación acompaña, no reemplaza.

## Opciones consideradas

- Sólo aclarar en el rótulo que mide volumen (ya hecho el 24-oct).
- Etiquetar a mano cada norma por sector, tipo y naturaleza (más de 770 normas,
  ~36 nuevas por mes, con un criterio nuestro).
- **Tomar la clasificación por sector que publica el propio informe mensual
  (elegida).**

## Decisión

El colector lee la tabla «Cantidad de normas de desregulación, por sector» de
cada informe (formato desde mayo de 2026: cifra y rótulo en la misma fila) y la
publica en la tarjeta como `normas_por_sector` y en el detalle. Agosto de 2026:
770 normas en once sectores, de Agroindustria (125) a Sector Inmobiliario (16).

- **Control:** la tabla se publica sólo si sus sectores suman el total de normas
  del mismo informe; si no, se omite y se avisa en el log.
- **Tipo de norma y naturaleza del cambio:** el Ministerio no los publica (ni una
  lista norma por norma), así que no se agregan.
- **No puntúa.**

### Consecuencias

- El lector ve en qué sectores se concentró la desregulación, con la fuente
  oficial y sin trabajo manual.
- Es la clasificación del Ministerio: hereda la limitación ya declarada de que
  el organismo mide su propio programa.

### Confirmación

`tests/test_desregulacion_sectores.py` lee el informe real de agosto de 2026
(fixture) y verifica los once sectores, la suma 770 y que una cifra mal leída o
un total distinto anulen el desglose.

## Pros y contras de las opciones

- Rótulo solo: no agrega información.
- Etiquetado propio: cubre tipo y naturaleza, pero es un trabajo permanente y un
  criterio discutible.
- Sector oficial: automático y verificable; cubre sólo una de las tres
  dimensiones pedidas.

## Más información

Informe «Análisis de la desregulación implementada», agosto 2026, página 2.
