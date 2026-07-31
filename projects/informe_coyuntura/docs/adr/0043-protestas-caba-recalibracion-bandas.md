---
madr: 4
id: '0043'
estado: 'aceptado'
fecha: 2026-07-09
cinturon: 'politica'
parametros: ['BANDAS_ITCP["protestas_caba"]']
archivos: ['scripts/itcp.py', 'tests/test_itcp.py']
ambito: '`scripts/itcp.py` (`BANDAS_ITCP["protestas_caba"]`) · `tests/test_itcp.py`'
---

# ADR-0043 — protestas_caba: recalibración de bandas ITCP con la serie ACLED ya existente

## Contexto y planteo del problema

De los cinco indicadores del ITCP con banda propia, dos seguían
PROVISIONALES (ver ADR-0036): `adhesion_reformas_provincial` y
`protestas_caba`. El primero sigue bloqueado — la fuente (MAGyP) no tiene
fecha de adhesión por provincia, y la alternativa con fecha
(trivia.consejo.org.ar) devuelve "Request Rejected" (WAF), sin una vía
alternativa legítima encontrada todavía (a diferencia de `cohesion_bloque`
Diputados, ADR-0040).

`protestas_caba` es distinto: no le faltaba backfill — `gestion.py` ya
mantiene 102 meses de datos ACLED en `output/series/gestion.csv` desde
2017, usados para el valor live (conteo rolling 12 meses) pero nunca
usados para chequear si las anclas del ITCP (-30/-10/10/30, simétricas,
nunca validadas) tenían sentido contra la métrica real que puntúa:
`var_vs_2023` (`gestion.fetch_protestas_caba()`: rolling 12m / total 2023
− 1, en %).

Reconstruyendo esa fórmula mes a mes sobre la serie ya existente (30 puntos
válidos, dic-2023 a may-2026 — el primer mes en que la ventana de 12m ya no
se solapa con el propio 2023 parcial), el rango real es −10,0% a +25,4%.
Con las anclas viejas, **22 de 30 meses (73%) caían en la misma banda
"moderado" (65 puntos)** — no una saturación en un extremo como en los
otros cuatro indicadores recalibrados hoy, sino un aplanamiento en el medio
de la escala: las anclas eran demasiado anchas (±30 y ±10) para un rango
real que nunca superó ±25,4.

## Opciones consideradas

- **Dejar las anclas simétricas (±X) pero angostarlas** (ej. ±20/±7) — se
  descartó a favor de anclas asimétricas basadas en los cuantiles reales:
  la distribución observada no es simétrica (cola más larga hacia valores
  positivos, reflejando el aumento de protesta en 2025-2026), forzar
  simetría hubiera repetido el mismo error de origen (anclas elegidas por
  estética en vez de por datos).
- **Esperar más meses de recorrido antes de recalibrar** — descartada por
  la misma regla de proyecto que las otras cuatro recalibraciones de hoy
  (lanzamiento público agosto 2026, no sentarse sobre gaps PROVISIONAL
  cuando ya hay datos suficientes).

## Decisión

Anclas nuevas: **−6,0 / −3,0 / 0,0 / 10,0** (antes −30/−10/10/30),
chequeadas contra los 30 puntos reales: 5/5/7/6/7 por banda (de la más
favorable a la más desfavorable), todas con datos reales, sin bandas
vacías. Tramos extremos siguen abiertos (`INF`/`-INF`), mismo criterio que
las otras recalibraciones de hoy.

A diferencia de `alineamiento_senadores_prov`/`cohesion_bloque_senado`/
`cohesion_bloque` (ADR-0038/0039/0042), esta recalibración no requirió
ningún backfill nuevo ni scraping adicional — toda la información ya
estaba en disco, solo hacía falta aplicarle la fórmula de puntuación que
ya usa el valor live.

### Consecuencias

- `protestas_caba` sale de PROVISIONAL. De los cinco indicadores con banda
  propia del ITCP, solo `adhesion_reformas_provincial` sigue sin
  recalibrar (ver Contexto — no es un problema de espera, es de fuente).
- El puntaje de `protestas_caba` ahora discrimina de verdad dentro del
  rango 2024-2026 en vez de aplanarse en 65 durante la mayor parte de ese
  período — afecta el 40% de la dimensión "conflicto social" del ITCP
  (los otros 60% son `movilizacion_cepa`).
- Si la serie ACLED se extiende con meses fuera del rango −10,0/+25,4 ya
  observado, el motor de interpolación (`parametrica.puntaje_interpolado`,
  ADR-0021) sigue funcionando correctamente sin tocar las anclas — mismo
  criterio de "no recalibrar ante un punto aislado" ya establecido en
  ADR-0042.
