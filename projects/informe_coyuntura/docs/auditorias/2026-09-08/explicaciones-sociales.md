# Explicaciones sociales y composición

Cotejo del 8-sep-2026 contra el snapshot, el motor y las fichas.

- Pobreza: la explicación conservaba 9,31% del índice, frente a 7,3% efectivo en el snapshot. Se remite a la composición dinámica y se retira la afirmación no sustentada de que sea la única estimación mensual del país.
- Construcción: la dimensión decía cemento, pero el componente usa ISAC desestacionalizado. Se identifica ISAC y se distingue actividad de cantidad de puestos.
- Empleadores: se retira «cierre neto» en la dimensión; el universo 1–50 trabajadores puede cambiar por otras causas.
- Carnes: toneladas de faena no miden gramos de proteína, consumo de hogares ni sustituciones individuales. La ficha afirmaba erróneamente que el rebase impedía que la diferencia faena/consumo afectara al puntaje. Se explicita ese riesgo, conservando el cálculo; el rediseño se anota como mejora potencial.
- Autos: el desglose ya no afirma que puntúe por separado ni que identifique descenso de categoría dentro de hogares. El componente vigente es motorización total.
- ICC: no se afirma que prediga voto o consumo. Victimización: se distingue el hecho reportado en encuesta de un censo de delitos. Búsquedas: se mantiene su alcance de atención, sin deducir preocupación.
- Empleo y supermercados: se retiran narraciones históricas fijas y exclusividades no necesarias para explicar sus operaciones.

Archivos: `web/src/lib/descripciones.ts`, ficha de carnes en `fichas.ts` y Markdown regenerado. Nueve pruebas dirigidas aprobadas; build Astro de 81 páginas correcto; cuatro textos confirmados en HTML y peso obsoleto ausente. La primera comprobación literal buscó «no demuestra» donde el texto dice «ni demuestra»; corregida la búsqueda, el contenido esperado se confirmó. Sin cambios de datos, pesos ni índices. Log: `/tmp/cigob-build-explicaciones-sociales.log`.
