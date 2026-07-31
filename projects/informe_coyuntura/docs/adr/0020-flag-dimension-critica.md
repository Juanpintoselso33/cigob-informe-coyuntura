---
madr: 4
id: '0020'
estado: 'aceptado'
nota_estado: 'aceptada (resuelve la Decisión 2 del ADR-0019 por la opción b)'
fecha: 2026-07-03
cinturon: 'transversal'
---

# ADR-0020 — Flag de dimensión crítica: la compensabilidad se señaliza, no se corrige

## Contexto y planteo del problema

Las tres paramétricas agregan dimensiones con **promedio ponderado lineal**,
que implica sustituibilidad perfecta: un colapso en una dimensión queda
compensado por el exceso de otra. Es la crítica que llevó al IDH a abandonar
la media aritmética en 2010 (pasó a geométrica para que "vivir mucho Y sano Y
educado" no fuera intercambiable). Casos vivos en este informe: en el ITCG la
reforma laboral (10/100 — cero materialización del Fondo de Cese) queda tapada
por el componente cambiario (~90); en el ITVC el colapso crediticio
(vulnerabilidad 31,7 — mora de familias ×5,5) queda amortiguado por motos e
ingresos.

## Opciones consideradas

- **(a) Status quo silencioso**: dejar la lineal sin señal. Descartada: es el
  punto débil comunicacional exacto que un lector crítico ataca ("el índice
  esconde el colapso crediticio detrás de las motos").
- **(b) Flag visible (elegida)**: fórmula intacta, compensación explícita.
  Costo cero sobre las series y la comparabilidad.
- **(c) Media geométrica** (IDH 2010): castiga desequilibrios pero cambia
  todos los valores publicados, rompe la comparabilidad y complica la
  comunicación ("¿por qué bajó si nada empeoró?"). Queda disponible como
  evolución futura si CIGOB la adopta en el doc — este flag no la bloquea.

## Decisión

**Mantener la agregación lineal** (comunicable, comparable con la historia
publicada, y el linaje ICRG también es lineal) **y señalizar la compensación
en vez de corregirla**: toda dimensión por debajo de un umbral crítico se
publica con `critica: true` y la web la marca de forma visible — borde y
barra en rojo + chip "Dimensión crítica: el promedio del índice no la
compensa" en la card de la dimensión.

**Umbrales** (`publicar.py`):
- Índices 0-100 por bandas (ITCM/ITCG): **puntaje < 30** — la dimensión está
  en la peor banda de su escala (los puntajes de banda son ~10/35/60/85/100).
- Índice base-100 (ITVC): **puntaje < 85** — la banda de "deterioro
  sustancial" de la escala del propio doc 260702.

El flag se recalcula en cada corrida de `publicar.py` (pineado en
`tests/test_publicar.py::test_dimensiones_criticas_marcadas`).

### Consecuencias

- Hoy quedan señaladas: **reforma laboral (10/100)** en el ITCG y
  **vulnerabilidad financiera (31,7)** en el ITVC. El ITCM no tiene
  dimensiones críticas (la peor, fiscal-comercial, está sobre el umbral).
- La señal es binaria y por umbral fijo — hereda el efecto escalón de las
  bandas (Decisión 3 del ADR-0019, pendiente); si se adopta la interpolación,
  el umbral crítico se revisa en el mismo acto.
- El leave-one-out del análisis de sensibilidad (ADR-0019) cuantifica lo que
  este flag señala cualitativamente: sin el Fondo de Cese el ITCG sería 78,8
  (+10,3); sin el endeudamiento el ITVC sería 98,8 (+6,7).
