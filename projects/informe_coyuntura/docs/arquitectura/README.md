# Arquitectura del Informe de Coyuntura

Documentación técnica del sistema que produce [informe.cigob.org](https://informe.cigob.org).

**Qué manda cuando esta carpeta y otra cosa se contradicen.** Estas páginas
describen la *forma* del sistema —flujo, contratos, operación— y se revisan de
a saltos; la última pasada de estructura es de ago-2026. Lo que mide y con qué
peso cada indicador NO se lee acá: manda la **ficha** del indicador
(`/metodologia/<id>`), que es lo único atado al colector por
`tests/test_la_ficha_no_se_queda_atras.py` (ADR-0220), y el **porqué** de cada
decisión está en [`docs/adr/`](../adr/README.md).

| Doc | Qué cubre |
|---|---|
| [01 — Visión general](01-vision-general.md) | Qué es el sistema, los cuatro cinturones, las cuatro paramétricas, principios de diseño |
| [02 — Pipeline de datos](02-pipeline-datos.md) | De la fuente oficial al snapshot de la web: colectores, caches, series, stores resilientes |
| [03 — Motor paramétrico y robustez](03-motor-parametrico.md) | ITCM / ITCG / ITVC-B100 / ITCP, interpolación, winsorización, Monte Carlo, validación externa |
| [04 — Web](04-web.md) | Astro, librerías de presentación, modales, reglas editoriales |
| [05 — Operaciones y deploy](05-operaciones.md) | CI nocturno, deploy por Vercel, verificación de producción, troubleshooting |
| [06 — Catálogo de fuentes](06-catalogo-fuentes.md) | Indicador por indicador: fuente, vía, frecuencia, credenciales, resiliencia, descartes con evidencia |
| [07 — Contratos de datos](07-contratos-datos.md) | Esquemas de `informe.json`, `series.json`, stores, ajustes e invariantes |
| [08 — Decisiones abiertas](08-decisiones-abiertas.md) | La agenda metodológica CIGOB: D5-D10 con propuesta y qué falta para decidir |
| [09 — Onboarding](09-onboarding.md) | Día uno de un colaborador: setup, credenciales, corrida completa, trampas del entorno |
| [10 — Glosario](10-glosario.md) | Términos del sistema, del motor, de la robustez y siglas de fuentes |

**Complementos:**
- Las *decisiones* de diseño y metodología viven en [`docs/adr/`](../adr/README.md) (más de 230) — esta carpeta describe el *sistema*; los porqués están allá.
- El marco conceptual (cinturones, doc maestro de extracción) es **read-only**: la app deployada es la fuente de verdad de la metodología vigente.
