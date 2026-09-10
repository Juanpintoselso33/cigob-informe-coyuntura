# Alcance de las explicaciones frente a las fórmulas

Cotejo del 8-sep-2026. Se encontraron contradicciones entre las explicaciones breves del modal, los textos de dimensión y las limitaciones metodológicas ya publicadas. No son cambios de signo, peso ni diseño: se retiran conclusiones que las operaciones del monitor no identifican.

| Componente | Afirmación retirada o precisada | Evidencia de alcance |
|---|---|---|
| IAI | La caída interanual demostraba descapitalización; un aumento superaba reposición. | Sus insumos son variaciones de construcción y bienes importados; no contiene depreciación ni stock de capital. |
| Brecha de construcción | Restar expectativas aislaba al Estado y eliminaba el ciclo; cero probaba ausencia de incertidumbre diferencial. | Dos saldos de encuesta no identifican un efecto causal ni controlan diferencias entre submuestras. |
| Sesiones disciplinarias | Las reuniones demostraban funcionamiento o parálisis del control. | La operación cuenta reuniones publicadas, no decisiones ni resultados. |
| Recaudación | Un valor menor que la base demostraba menor economía formal. | Ingresos cobrados también cambian por normativa, vencimientos y reasignaciones. |
| Cortes y protestas | La caída era atribuible al Gobierno y probaba reconversión de las mismas protestas. | Las series tienen universos distintos; no enlazan los mismos eventos ni identifican causalidad. |
| Apertura | El cociente medía directamente desmantelamiento impositivo. | También varía con composición, valoración y pagos del comercio. |
| Producción legislativa | Se atribuía un cambio porcentual a menos leyes del Congreso a partir de una supuesta estabilidad histórica. | El indicador computa leyes totales; no permite deducir origen ni contenido. |
| Reforma laboral | La dimensión y la leyenda de fórmula llamaban a la litigiosidad SRT resultado del FAL o «industria del juicio». | Son universos de reclamos distintos y la serie no evalúa mérito. |
| Dimensión social y orden | TDPS se presentaba como asistencia sin intermediarios. | El devengado clasificado no acredita cobro ni implementación. |
| Dimensión judicial | Se hablaba de velocidad de la Corte. | La medida es una tasa de resueltos/ingresados, no duración. |

Archivos: `web/src/lib/descripciones.ts`, `formulas.ts`, `fichas.ts` y fichas Markdown regeneradas. Los cambios alcanzan descripciones de indicadores y dimensiones; el desarrollo adicional de límites de IAI y brecha se incorpora también a sus fichas.

Validación: nueve pruebas dirigidas de texto y fichas aprobadas; build Astro de 81 páginas correcto. Se verificaron cuatro límites principales dentro del HTML generado. `git diff --check` dirigido sin errores. El SHA-256 del snapshot sigue siendo `c61e523fc29ead5ee9978095697b07356347c9f135fc0725cb2887cb4a1ec899`; no se modificaron datos ni resultados. Log: `/tmp/cigob-build-alcance-indicadores.log`.

El rediseño de proxies, sus signos o referencias permanece en `mejoras-potenciales.md`; estas correcciones no lo ejecutan. Los pendientes de fuentes del estado vigente siguen abiertos.
