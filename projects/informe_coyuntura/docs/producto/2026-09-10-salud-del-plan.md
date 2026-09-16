# Mejoras de producto para medir la salud del plan

Propuesta del 10-sep-2026, continuación de la evaluación de producto. No modifica índices, pesos ni la publicación. La auditoría del 8-sep sigue cerrada con reservas; esta propuesta no convierte esas reservas en datos comprobados.

## Qué producto estamos evaluando

El [marco público](../../web/src/components/MarcoTension.astro) define la gobernabilidad como capacidad de procesar tensión entre demandas y recursos. Macro, política, gestión e impacto social observan condiciones distintas de viabilidad. Por eso, mi recomendación anterior de sumar metas y plazos necesita una precisión: esa capa puede fortalecer gestión y explicitar el plan, pero no reemplaza la lectura conjunta de los cuatro cinturones.

Mantengo 7/10 como juicio cualitativo de producto sobre la versión auditada, no como resultado de una escala validada. La utilidad diagnóstica y la trazabilidad son fortalezas; la distancia entre algunos proxies y las capacidades que representan limita la interpretación. Tampoco hay evidencia para prometer que una lista de cambios lo lleve automáticamente a 8,5.

La pregunta de producto que propongo conservar es: **¿qué condiciones sostienen o comprometen la posibilidad de llevar adelante este plan, y con qué evidencia lo afirmamos?** El cumplimiento de hitos aporta una de las respuestas.

## Tres prioridades

| Prioridad | Resultado para el lector | Reutilización y cambio propuesto |
|---|---|---|
| 1. Explicitar el vínculo con el plan | Entender por qué una señal importa para un objetivo y qué inferencia admite. | Reutilizar indicadores y fichas; preparar un registro de objetivos documentados y vínculos razonados. No crear metas numéricas ni plazos que el programa no haya fijado. |
| 2. Hacer visible la solidez de la evidencia | Distinguir una señal favorable de una señal bien comprobada. | Reutilizar fechas, estado de caché, estimaciones y matriz de fuentes. Unificar su presentación junto a la lectura; un dato consultado hoy no queda validado hoy por esa sola razón. |
| 3. Explicar el cambio mensual | Saber si cambió la situación, la cobertura o la reconstrucción de datos. | Reutilizar descomposición ITCP y evidencia de revisiones. Conservar versiones de corte y separar comparación publicada de comparación recalculada con método y componentes comunes, cuando pueda calcularse. |

El orden responde a las brechas encontradas en el propio repositorio. No propone nuevos umbrales universales ni una segunda nota global.

## Piloto concreto con señales existentes

Ejemplos tomados del snapshot local generado el **8-sep-2026**, revisado en disco el 10-sep. No son una actualización de fuentes al 10-sep. Los vínculos con objetivos que siguen son hipótesis de diseño para documentar; no compromisos atribuidos al Gobierno sin fuente.

| Pregunta para la conducción | Señal disponible y fecha | Qué permite leer | Qué falta para afirmar más |
|---|---|---|---|
| ¿La estabilización reduce presión sobre el plan? | IPC 2,11% mensual, julio | Evolución de precios al consumidor. | Vincularla con un objetivo documentado y con actividad e ingresos; no deducir causalidad ni éxito integral del programa. |
| ¿La agenda obtiene validación legislativa? | Eficacia legislativa 14,3%, corte 8-sep | Proporción aprobada de la cohorte definida por el indicador. | Relación nominal entre proyectos y prioridades del plan; cantidad aprobada no mide importancia política por sí sola. |
| ¿Hay capacidad de integrar tribunales? | Cobertura judicial estimada 73,82%, corte 8-sep | Estimación con padrón y movimientos conciliados. | Juras, habilitaciones y bajas exhaustivas; no deducir decisiones judiciales favorables. |
| ¿El FAL está pasando de norma a implementación? | Índice 50, evaluación 8-sep; revisión judicial 21-ago | Etapas documentadas de construcción, vigencia y registro de fondos. | Consulta judicial actual y evidencia de implementación. El registro local prevé vigencia 1-nov; la fecha requiere respaldo y revisión antes de usarse como cronograma vigente. |
| ¿Las privatizaciones avanzan efectivamente? | Avance por etapas 55,6%, revisión parcial 8-sep | Hitos documentados de nueve empresas. | No equivale a 55,6% del valor vendido, recaudado o del plan cumplido. Mantener detalle por operación y novedades pendientes. |
| ¿La presión financiera de los hogares amenaza la sostenibilidad social? | Mora de consumo 14,41%, junio | Cartera irregular de personales y tarjetas. | No representa a todos los hogares ni demuestra voto futuro; cotejar con ingresos, empleo y percepciones. |

Estos ejemplos ya permiten una lectura de conducción sin inventar otro indicador compuesto. Para conectar un objetivo con varios cinturones, un mismo dato puede aparecer como referencia en varias preguntas sin volver a sumarse al puntaje.

## Registro mínimo del vínculo

Cada objetivo piloto necesitaría:

- Identificador, formulación y fuente del compromiso, con fecha y fragmento relevante. Si no se encuentra, estado **vínculo propuesto, compromiso no documentado**.
- Cinturón y dimensión relacionados; indicadores existentes y explicación del vínculo, incluyendo límites de atribución.
- Tipo de evidencia: condición del entorno, capacidad, acto de ejecución o resultado. No son etapas intercambiables.
- Meta y plazo sólo si están documentados; de lo contrario, sin meta o plazo formal. Un campo vacío no significa incumplimiento.
- Hitos observables, fuente primaria y evidencia requerida para declararlos cumplidos. Cada hecho debe tener fecha propia y fecha de revisión.
- Lectura del corte: qué sostiene el plan, qué lo restringe y qué no sabemos. Evitar convertir una opinión editorial en dato automático.

Ejemplo mínimo del FAL: distinguir norma dictada, norma no suspendida según la última revisión, entrada en vigencia y registro de fondos. Los pagos o efectos sobre litigios requieren evidencia adicional de su universo. Una actualización de CNV no debe actualizar la fecha de revisión judicial.

## Evidencia junto a la tensión

La tensión y la calidad de evidencia deben ser dos informaciones separadas. Propuesta de presentación descriptiva, sin puntaje adicional:

| Información | Ejemplo con lo ya auditado |
|---|---|
| Fecha del dato y fecha de revisión | Mora de junio; revisión judicial FAL del 21-ago. |
| Tipo de observación | Dato publicado, estimación reconstruida o registro curado. |
| Cobertura y límite | Cobertura judicial estimada; privatizaciones con revisión parcial. |
| Consecuencia para la lectura | «Permite describir etapas; no permite afirmar cobros efectivos». |

La matriz de fuentes acredita lo que se comprobó, no toda la historia ni la validez causal del indicador. No agrupar todas sus categorías bajo un sello general de «validado». Tampoco castigar el índice con menor puntaje sólo porque haya menos información: eso mezclaría situación con conocimiento de la situación.

## Cómo probar el piloto antes de implementarlo

1. Completar el vínculo documental de tres preguntas: estabilización, validación legislativa y FAL. Si falta compromiso o plazo, conservar el faltante explícito.
2. Preparar una lectura retrospectiva de dos cortes con versiones disponibles. La reconstrucción revisada no debe presentarse como información conocida en aquel momento.
3. Mostrar a lectores del equipo casos que separen señal favorable de evidencia incompleta y cambio observado de revisión metodológica. Pedir que expliquen qué decisión permite la información y qué conclusión no permite.
4. Revisar errores de interpretación y tareas que no pudieron resolver. Ampliar el piloto si agrega claridad; no usar satisfacción general como prueba de validez del índice.

Criterios mínimos de aceptación: ningún compromiso inventado; fechas separadas; una señal no se cuenta dos veces; ausencia de universo no equivale a cero; los ejemplos de FAL y judicial no se leen como fuente exhaustiva; la lectura mensual distingue revisiones. Esta prueba con usuarios todavía no se realizó.

## Alcance de implementación posterior

La preparación documental es el primer entregable. La integración web requeriría acordar el registro y su responsable de revisión; luego un módulo de datos separado del cálculo y una vista vinculada a las fichas. El prototipo no debería recalcular índices ni modificar pesos. No convertir esta propuesta en un ADR aceptado hasta decidir el cambio.

Se mantiene la agenda de [mejoras metodológicas](../auditorias/2026-09-08/mejoras-potenciales.md), especialmente calidad de proxies, validación fuera de muestra y comparaciones con cobertura común. Los pendientes de fuentes permanecen en el [cierre de auditoría](../auditorias/2026-09-08/cierre.md).

## Verificación de esta entrega

Se releyeron el marco, arquitectura, devolución editorial de Babino y decisiones de nomenclatura; se cotejaron los seis ejemplos contra el snapshot local. Su SHA-256 **al momento de esta entrega (10-sep-2026)** era `5e048a7d5eca458ed61d8d4171437f2af7e94cb08f0a8463cdc92319f5638c84`; el snapshot se regenera cada noche, así que el archivo de hoy no coincide y los seis ejemplos hay que leerlos contra esa foto, no contra la vigente. No se consultaron fuentes externas nuevas ni se afirma actualidad al 10-sep. Se corrigió además D7 de la agenda de arquitectura: TDPS describe devengado clasificado, no pago sin intermediarios, conforme a ADR-0296. No se alteraron fórmulas, observaciones, pesos o sitio publicado.

## Piloto documental preparado

Se completó el primer paso con [tres preguntas y fuentes oficiales](piloto-compromisos-2026-09-10.md), más su registro JSON. Son dos objetivos: validación legislativa y FAL comparten la reforma laboral. El ejemplo confirma que la eficacia de cohorte no mide la aprobación de esa iniciativa particular. La prueba con usuarios y la comparación entre versiones permanecen pendientes.
