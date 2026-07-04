# Arquitectura del Informe de Coyuntura

Documentación técnica del sistema que produce [informe.cigob.org](https://informe.cigob.org).
Fotografía al 04-jul-2026 (post barridos macro y vida cotidiana, ADR-0027 a 0034).

| Doc | Qué cubre |
|---|---|
| [01 — Visión general](01-vision-general.md) | Qué es el sistema, los cinco cinturones, las tres paramétricas, principios de diseño |
| [02 — Pipeline de datos](02-pipeline-datos.md) | De la fuente oficial al snapshot de la web: colectores, caches, series, stores resilientes |
| [03 — Motor paramétrico y robustez](03-motor-parametrico.md) | ITCM / ITCG / ITVC-B100, interpolación, winsorización, Monte Carlo, validación externa |
| [04 — Web](04-web.md) | Astro, librerías de presentación, modales, reglas editoriales |
| [05 — Operaciones y deploy](05-operaciones.md) | CI nocturno, deploy dual, verificación de producción, troubleshooting |
| [06 — Catálogo de fuentes](06-catalogo-fuentes.md) | Indicador por indicador: fuente, vía, frecuencia, credenciales, resiliencia, descartes con evidencia |
| [07 — Contratos de datos](07-contratos-datos.md) | Esquemas de `informe.json`, `series.json`, stores, ajustes e invariantes |
| [08 — Decisiones abiertas](08-decisiones-abiertas.md) | La agenda metodológica CIGOB: D5-D10 con propuesta y qué falta para decidir |
| [09 — Onboarding](09-onboarding.md) | Día uno de un colaborador: setup, credenciales, corrida completa, trampas del entorno |
| [10 — Glosario](10-glosario.md) | Términos del sistema, del motor, de la robustez y siglas de fuentes |

Los cinturones **política** y **espíritu de época** están pre-barrido: su
documentación de detalle crecerá cuando pasen por la revisión uno-por-uno.

**Complementos:**
- Las *decisiones* de diseño y metodología viven en [`docs/adr/`](../adr/README.md) (34 ADRs) — esta carpeta describe el *sistema*; los porqués están allá.
- El marco conceptual (cinturones, doc maestro de extracción) es **read-only**: la app deployada es la fuente de verdad de la metodología vigente.
