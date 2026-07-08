# Reemplazo de `gobernadores_alineamiento` por proxy de voto de senadores por provincia

## Contexto

`gobernadores_alineamiento` está congelado en 55% desde 2026-04-01 (carga manual). Se investigaron y descartaron 4 proxies (composición partidaria de Diputados/Senado, transferencias ATN, adhesión RIGI) — ninguno automatizable con una fuente estructurada. El único camino identificado hasta hoy era NLP sobre cobertura periodística (proyecto aparte, no encarado).

Hallazgo nuevo (2026-07-08): la tabla de cada acta de votación del Senado (ya scrapeada hoy para `cohesion_bloque_senado`) trae **Provincia** como columna directa (`<th class="ocultar">Provincia</th>`, índice 3 de `<td>`, confirmado en vivo idéntico en Diputados y Senado) — no scrapeada hasta ahora, pero trivial de extraer con la infraestructura ya construida.

## Diseño

**Métrica**: para cada acta dividida del Senado en la ventana de recencia, se determina la posición del oficialismo (mayoría de votos del bloque LLA, reusando `es_bloque_lla`/`indice_rice`). Para cada provincia, se mide qué % de los votos de sus senadores **no-LLA** coincidió con esa posición. El valor final es el promedio de ese % entre las provincias que tienen al menos 1 senador no-LLA en la ventana (las provincias 100% LLA se excluyen del promedio — su alineamiento con LLA es tautológico por construcción, no aporta señal).

**Caveat honesto a documentar (no descalificante, mismo estándar que `adhesion_reformas_provincial`/RIGI)**: esto mide comportamiento de voto de **senadores**, no la postura pública del **gobernador** (Poder Ejecutivo provincial) — un senador no depende del gobernador de turno, puede responder a la estrategia nacional de su partido. Es la mejor señal automatizable disponible hoy, pero es un proxy, no una medición directa.

**Nombre nuevo**: `alineamiento_senadores_prov` (no se reusa el nombre `gobernadores_alineamiento` porque mide algo distinto — mismo criterio que llevó a crear `adhesion_reformas_provincial` como indicador aparte en vez de forzarlo dentro de `gobernadores_alineamiento`). Reemplaza a `gobernadores_alineamiento` en `DIMENSIONES_ITCP["alianzas_territoriales"]`, mismo peso interno (30%).

## Arquitectura técnica

- Extender `_parsear_acta(html)` en `politica.py` para devolver también `"provincia"` (celda índice 3 — ya confirmado en vivo, mismo índice para Diputados y Senado). Cambio aditivo a un dict, no rompe los usos existentes de `nombre`/`bloque`/`voto` en `fetch_cohesion_bloque`/`fetch_cohesion_bloque_senado`.
- Nueva función `fetch_alineamiento_senadores_prov(anio=None, dias_ventana=90)` en `politica.py`, siguiendo el mismo patrón que `fetch_cohesion_bloque_senado` (reusa `_descubrir_actas_senado`, `_paced_get`, ventana anclada a hoy/31-dic según backfill).
- Lista estática `PROVINCIAS_SENADO` (24: 23 provincias + CABA) — para saber cuántas provincias existen y detectar nombres mal escritos/inesperados en el scraping (defensivo, no bloqueante).
- Serie histórica: mismo patrón de caché persistente por año que `cohesion_bloque_senado_serie` (año cerrado no se re-pide, año en curso siempre se re-pide).

## Fuera de alcance

- No tocar `gobernadores_alineamiento` en sí (queda como placeholder manual congelado, con nota agregada explicando que fue reemplazado por `alineamiento_senadores_prov` para el peso del índice, pero se mantiene documentado como referencia histórica de lo investigado).
- No tocar `cohesion_bloque` (Diputados, bloqueado por anti-bot) — indicador separado, ya usado como fuente de este proxy solo por su tabla de actas, sin depender del scraping bloqueado de Diputados.
