---
madr: 4
id: '0031'
estado: 'aceptado'
fecha: 2026-07-04
cinturon: 'gestion'
archivos: ['sensibilidad.py']
relacionado: ['0075', '0078']
ambito: 'Sección Robustez de las tres paramétricas (ITCM · ITCG · ITVC) + `sensibilidad.py` + pipeline nocturno'
---

# ADR-0031 — Tercer pilar de robustez: validación cruzada (matriz discriminante)

## Contexto y planteo del problema

> **ACTUALIZADO (30-jul-2026, ADR-0154 y sus enmiendas).** La matriz sigue
> siendo el tercer pilar, pero su composición cambió dos veces desde acá:
> creció a 4×4 al entrar el ITCP, y el **riesgo país se retiró por completo**
> —del par propio del ITCM, que ahora es el Índice Líder, y de la matriz
> entera—. Con eso la observación del editor que motivó esta sección (que
> reutilizar el riesgo país para ITCM e ITCG debilitaba el discriminante) queda
> resuelta por vía distinta: ya no hay contraste compartido entre dos índices.
>
> Y hay un resultado que este ADR no anticipaba y que hoy se publica: **la
> diagonal NO es la más fuerte en todos los casos** (2 de 4 índices
> correlacionan más con un contraste ajeno que con el propio). No se corrige
> moviendo nada: la conclusión de la matriz lo declara, derivado de los
> números en cada corrida.

La batería de robustez tenía dos pilares: (1) sensibilidad interna Monte
Carlo (¿el número depende de nuestras elecciones?) y (2) validación externa
convergente (¿acompaña a un contraste independiente?), con un hallazgo
discriminante puntual en el ITCG (↔ ICG UTDT). El editor pidió evaluar una
tercera dimensión.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

1. `publicar._validacion_cruzada()` calcula la matriz 3×2 en cada corrida y
   la publica en el snapshot (`informe.validacion_cruzada`); la web la
   muestra como tercer bloque armonizado de Robustez en los tres cinturones
   con índice, con la fila propia señalada. Resultado al 04-jul-2026: ITCM
   −0,73/+0,55 · ITCG −0,89/+0,49 (patrón cumplido) · ITVC +0,52/−0,54
   (parejo — declarado en la conclusión: con ~30 meses donde macro y bolsillo
   se movieron juntos, la separación es menor).
2. **La reconstrucción de series pasa al pipeline nocturno**: se descubrió
   que `output/validacion_externa.json` solo se refrescaba corriendo el
   script a mano (las correlaciones publicadas podían quedar con métricas
   viejas tras un rediseño). `data-pipeline.yml` ahora corre
   `validacion_externa.py` entre las series y publicar — la validación quedó
   de punta a punta automática.
3. **Ruido de insumos scale-free** en la sensibilidad: la perturbación
   multiplicativa ±5% subestimaba la incertidumbre de los indicadores con
   signo o centrados en cero (IdC en σ, IDM en pp: ±5% de un valor ≈0 no
   perturba nada). Pasa a ruido ADITIVO de ±5% del ancho entre anclas
   finitas de cada indicador.

### Consecuencias

- La batería queda en tres pilares: sensibilidad interna · validación
  convergente por índice · validación cruzada discriminante — el estándar de
  validez de constructo, sin fuentes nuevas.
- Los rangos p05-p95 publicados cambian levemente por el ruido nuevo
  (más honesto para IdC/IDM).
- El bug del script standalone de sensibilidad (constante `PROB_SALTO_BANDA`
  eliminada en ADR-0021 pero referenciada en `_meta`) quedó corregido.

## Más información

### Candidatas evaluadas con datos

1. **Validación predictiva (lead-lag)** — probada y DESCARTADA como claim:
   la correlación del ITCG con el riesgo país es máxima en el mes
   contemporáneo (−0,86) y decae con el adelanto; la del ITCM mejora apenas a
   5 meses (−0,755 vs −0,731), indistinguible con n=25. Los índices
   ACOMPAÑAN, no anticipan (o la muestra es corta para afirmarlo). Publicar
   "capacidad anticipatoria" sería sobrevender. Queda documentado como
   negativo verificado; re-evaluable cuando la muestra duplique.
2. **Matriz de validación cruzada (discriminante)** — ADOPTADA: los tres
   índices reconstruidos contra los DOS contrastes externos a la vez
   (riesgo país EMBI · ICC UTDT). El patrón esperado — validez convergente y
   discriminante del canon psicométrico/JRC — es que cada índice correlacione
   más fuerte con su par teórico que con el ajeno.

### Ampliación (mismo día): tercer contraste — cada índice con su par propio

El editor observó que reutilizar el riesgo país para ITCM e ITCG debilitaba
el discriminante. Se incorporó el **Merval en dólares** (cierre mensual de
^MERV vía Yahoo Finance sobre el CCL promedio de ArgentinaDatos) como par
convergente PROPIO del ITCG: el mercado de acciones pricea la transformación
estructural. Probado antes de adoptar: ITCG ↔ Merval USD **r = +0,766**
(n=32) — el más alto de los tres índices contra ese contraste, con el signo
esperado. La matriz pasa a 3×3 con diagonal completa: ITCM ↔ riesgo país
(−0,74) · ITCG ↔ Merval USD (+0,77) · ITVC ↔ ICC (+0,55). El bloque de
validación por cinturón de gestión también migra al Merval (gráfico en modo
`minmax` sin inversión: relación positiva); el contraste ITCG ↔ riesgo país
queda visible en la matriz (−0,88: reformas y solvencia se pricean juntas —
declarado en la conclusión).
