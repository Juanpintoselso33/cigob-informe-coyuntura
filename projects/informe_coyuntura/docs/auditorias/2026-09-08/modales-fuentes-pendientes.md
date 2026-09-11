# Coherencia de las explicaciones públicas con fuentes pendientes

Cotejo del 8-sep-2026 entre `descripciones.ts`, fichas metodológicas y snapshot. Las descripciones alimentan los campos «qué mide» y «qué aporta» del modal; por eso una ficha correcta no subsanaba estas afirmaciones.

- **Cobertura judicial:** la descripción omitía que es estimada, confundía todas las subrogancias con vacantes y atribuía la recuperación a acuerdos del Senado. Ahora explicita estimación, excepción del titular de licencia, diferencia entre acuerdo y toma de posesión, universo fijo y revisiones de flujos. Se retiró la narración histórica sin soporte suficiente para atribuir el movimiento.
- **Privatizaciones:** se retiró «una venta cerrada vale más que diez pliegos», incompatible con el promedio de etapas equiponderadas. Se explican etapas 4 y 2, igualdad de pesos, diferencia con cobros y alcance parcial del seguimiento. La frecuencia quincenal se identifica como prevista.
- **FAL:** la explicación remite a las fechas del registro curado y no convierte la consulta CNV en comprobación judicial. Distingue etapas del régimen de resultados como litigios o indemnizaciones pagadas.

No se modifican observaciones, puntajes, pesos ni series. SHA del snapshot conservado: `c61e523fc29ead5ee9978095697b07356347c9f135fc0725cb2887cb4a1ec899`.

Validación: cuatro pruebas de texto público aprobadas; build Astro de 81 páginas aprobado. Se comprobó en `web/dist/index.html` que las cuatro aclaraciones llegan al documento generado y que desaparece la metáfora retirada. `git diff --check` dirigido sin errores. Log de build: `/tmp/cigob-build-modales-auditados.log`. No se repite la suite integrada por cambios acotados de texto.
