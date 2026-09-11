# Estado vigente de la auditoría

Corte del 8-sep-2026. **Etapa cerrada con reservas por indicación de Juan («cerrá con lo que te parezca»).** Véase [conclusión y decisiones de cierre](cierre.md). Las limitaciones de fuente permanecen explícitas; este cierre no las convierte en hechos verificados. Cambios locales sin push ni despliegue. El [balance por requisito](balance-requisitos.md) distingue evidencia y límites; los cotejos y validacion.md conservan la secuencia histórica.

| Cinturón | Índice | Tensión |
|---|---:|---:|
| Macro | 64,1 | 3,6 |
| Política | 73,0 | 2,7 |
| Gestión | 79,1 | 2,1 |
| Impacto social | 93,1 | 6,4 |

Cada tarjeta tiene la fecha de sus componentes; no representan un mismo mes completo. Snapshot generado a las 19:22:19 ART, con correcciones posteriores de metadatos y contraste externo. SHA-256 vigente: `5e048a7d5eca458ed61d8d4171437f2af7e94cb08f0a8463cdc92319f5638c84`.

## Evidencia de coherencia

- Censo: cuatro cinturones, 24 dimensiones, 63 indicadores publicados; 62 observados para puntuar y bloqueo sostenido sin universo. Cero fallos estructurales/aritméticos. No convertir falta de universo en cero.
- Matriz de fuentes: 63 filas, correspondencia exacta de claves y fechas con el snapshot. 57 comprobados, tres con salvedad, uno reproducido, uno con corrección pendiente y uno parcial. [Detalle](cobertura-fuentes.csv).
- Suite integrada: 3.694 pruebas aprobadas, cuatro omitidas por comparar períodos diferentes y cinco avisos de deprecación. Después se añadió una guarda de pesos nominales: cinco pruebas del archivo aprobadas. Build de 81 páginas correcto. [Verificación](verificacion-integrada.md).
- Gate de publicación: aprobado en el corte actual; único aviso G8 por ausencia de lectura editorial publicada de septiembre. La portada usa la síntesis automática. Log: `/tmp/cigob-gate-final.log`.
- Explicaciones de los modales judicial, FAL y privatizaciones alineadas con el alcance de sus fuentes; cuatro pruebas de texto y build de 81 páginas aprobados. [Cotejo](modales-fuentes-pendientes.md).
- Portada, bandas y gráficos verificados; fechas, denominadores, pesos nominales y efectivos explicados en fichas. [Presentación](portada-coherencia.md). Los Word conservan entregas históricas; manuales y fichas Markdown son la documentación vigente. [Alcance documental](documentacion-vigente-y-word.md).

El cotejo posterior de explicaciones retiró inferencias no identificadas por las fórmulas (inversión neta, causalidad de la brecha, resultados del FAL y otros alcances). Nueve pruebas dirigidas y build de 81 páginas aprobados; fichas regeneradas. [Detalle](alcance-explicaciones.md).

También se corrigieron explicaciones sociales: peso fijo obsoleto de pobreza, ISAC en lugar de cemento, alcance de faena, patentamientos y encuestas. Nueve pruebas y build de 81 páginas aprobados. [Cotejo](explicaciones-sociales.md).

La lectura generada de carnes también fue corregida; comparación completa confirma que sólo cambió ese texto del snapshot. 43 pruebas de publicación aprobadas y build correcto. [Evidencia](carne-lectura-generada.md).

## Contraste externo vigente

El contraste mensual enero-agosto conserva convergencias y discrepancias; no acredita validez causal o predictiva ni justifica ajustar pesos para coincidir con encuestas. [Lectura cualitativa](contraste-politico-cualitativo.md).

Se corrigieron el calendario de diferencias/adelantos y el mes de julio omitido por el colector ICG. El panel completo fue recalculado con insumos guardados. Brechas en diferencias: ITCIS 0,025, ITCG −0,028, ITCP 0,164. Las correlaciones del factor siguen siendo parciales. [Corrección ICG e insumos](icg-julio-corregido.md). Las afirmaciones anteriores sobre falta de insumos quedan superadas por este cotejo.

Las propuestas de rediseño permanecen separadas de las correcciones: [mejoras potenciales](mejoras-potenciales.md).

## Reservas y seguimiento posterior

1. Cobertura judicial: 705/955 sigue estimado. Falta confirmar movimientos efectivos, juras, habilitaciones y exhaustividad de bajas, incluido Fraga. El cruce de vacantes de agosto corroboró casos ya contemplados y no justifica un nuevo descuento. [Estado de la fuente](cobertura-judicial-pendiente.md), [cotejo adicional](judicial-contraste-vacantes.md).
2. FAL: falta cerrar la comprobación judicial posterior al 21-ago. La consulta PJN tiene un CAPTCHA y la autorización sigue pendiente. [Detalle](fal-estado-judicial-pendiente.md).
3. Privatizaciones: cinco procesos corroborados en CONTRAT.AR, detector de novedades corregido y etapas documentadas; permanece parcial la exhaustividad de novedades y la conciliación de cobros. Un pago individual de Piedra del Águila está respaldado por Central Puerto; no valida el total de la cartera. [Revisión](privatizaciones-revision.md), [pago y cronograma](privatizaciones-cotejo-pago-parcial.md).
4. Lectura editorial de septiembre: se redactó una propuesta de dos párrafos con corte al 8-sep, sustentada en el snapshot y el contraste de agosto. Falta revisión del equipo antes de publicarla; permanece sin firma institucional en `web/src/contenido/lectura-del-mes/borradores/2026-09.md`. La portada conserva la síntesis automática.

La suite y el gate no resuelven estas limitaciones de fuentes. No repetir cotejos cerrados ni integraciones temporales. Consultar el recuento de continuidad en la carpeta de tarea y el uso general antes de cada bloque costoso; detenerse al llegar al 50% restante.

## Revisión futura de las reservas

Las búsquedas alternativas del FAL no aportaron actuaciones posteriores y el catálogo oficial mantiene padrón del 5-jun y movimientos del 13-jul, ya conciliados. Retomar con acceso a la consulta judicial pendiente o evidencia primaria nueva de juras, habilitaciones, bajas y cobertura de privatizaciones. La revisión editorial corresponde al equipo. La etapa se cierra con estas reservas; no se afirma certificación integral de las fuentes ni se mantienen búsquedas equivalentes en ejecución. Último uso general: 44% consumido / 56% restante; el corte solicitado sigue siendo 50% restante.
