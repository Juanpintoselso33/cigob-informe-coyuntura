# Piloto: del objetivo del plan a la señal observable

Preparado el 10-sep-2026. Se documentaron tres preguntas sobre dos objetivos; la validación legislativa y el FAL son dos lecturas de una misma reforma. El [registro estructurado](piloto-compromisos-2026-09-10.json) conserva fuentes, fragmentos, fechas, hitos y límites. No se cambian los índices.

## 1. Estabilización

El BCRA define la desinflación como objetivo de actuación para 2026, junto a estabilidad financiera y crecimiento. Esto respalda el vínculo del IPC con el programa; el pasaje no fija una meta mensual cuantificada. Por eso no corresponde convertir el horizonte anual en una promesa de inflación cero en un día concreto. [Objetivos y Planes 2026, publicado el 29-dic-2025](https://www.bcra.gob.ar/noticias/objetivos-y-planes-2026/).

El snapshot conserva IPC de julio de 2,11% mensual. Sirve para seguir precios, pero un punto aislado no prueba desinflación sostenida ni efecto causal del programa. Se mantiene meta numérica sin definir en este piloto, sin inferir que no exista en ningún otro documento.

## 2. Validación legislativa de una prioridad

La remisión de la modernización laboral y el pedido presidencial de tratamiento están documentados. La fuente expresa una prioridad y resultados buscados, no prueba que esos resultados se hayan producido ni fija una tasa de éxito legislativo para toda la agenda. [Comunicado Oficial 122, 11-dic-2025](https://www.argentina.gob.ar/noticias/comunicado-oficial-numero-122).

El hito de sanción está acreditado el 27-feb-2026 y la publicación el 6-mar. [Ficha oficial de Ley 27.802](https://www.argentina.gob.ar/normativa/nacional/ley-27802-423680).

**El 14,3% de eficacia del monitor no evalúa esta reforma.** Al corte del 8-sep observa proyectos ingresados entre 8-sep-2024 y 8-sep-2025. PE 159/2025 ingresó el 11-dic-2025 y queda fuera: [cotejo nominal previo de Senado](../auditorias/2026-09-08/eficacia-cohorte-senado.md). Mostrar el hito al lado del agregado permite leer un avance relevante sin alterar el denominador para mejorar la nota.

## 3. Implementación del FAL

El objeto legal es asistir obligaciones laborales; el artículo 58 conserva el régimen indemnizatorio. No se lo presenta como sustitución general de indemnizaciones ni como pago ya observado. [Ley 27.802, art. 58](https://www.argentina.gob.ar/normativa/nacional/norma-423680/texto).

El decreto documenta la reglamentación y la fecha prevista del 1-nov-2026. También establece 45 días hábiles desde publicación para normas complementarias. Ese plazo es diferente de la entrada en vigencia y del primer pago; queda registrado sin inventar un vencimiento ni declarar incumplimiento sin inventario y calendario. [Decreto 408/2026, arts. 26–27](https://www.boletinoficial.gov.ar/detalleAviso/primera/342622/20260601).

Se agregó al piloto la evidencia de reglas de inversión del 12-ago. Es un hito normativo complementario, no prueba de adopción. [Resolución ME 1276/2026](https://www.boletinoficial.gob.ar/detalleAviso/primera/345836/20260812).

El snapshot conserva FAL 50 y revisión judicial del 21-ago. Leer hoy estas normas no actualiza esa revisión. El estado operativo y los pagos siguen sin verificar en el piloto; no se completa esa falta con un cero ni se declara exhaustiva la revisión normativa.

## Qué permite mostrar el producto

| Pregunta | Evidencia visible | Lectura admisible |
|---|---|---|
| Estabilización | Objetivo documentado; IPC fechado; sin meta mensual extraída | Seguir trayectoria, no calcular porcentaje de promesa cumplida. |
| Validación legislativa | Sanción de la iniciativa; eficacia de otra cohorte | Distinguir el avance concreto del agregado de capacidad. |
| FAL | Normas, fecha prevista y reserva judicial | Separar construcción normativa de operación efectiva. |

Un único hito `laboral_sancion` se referencia desde política y gestión. No se suma dos veces ni se transforma en dos logros independientes. La redacción del Gobierno se conserva como intención declarada; la evaluación de efectos exige evidencia externa.

## Verificación y siguiente paso

Se leyeron las seis fuentes oficiales listadas en el registro; el expediente del Senado se apoya en el cotejo guardado del 8-sep y no se reconsultó. El primer intento de abrir el decreto en el dominio `gob.ar` agotó el tiempo de espera; el texto se leyó en el dominio oficial alternativo `gov.ar` y se cotejó la fecha con la nota de InfoLeg. Fuentes secundarias halladas en búsqueda no se usaron como respaldo del compromiso.

El registro puede alimentar un prototipo de lectura separado del cálculo. Antes de implementarlo faltan la revisión editorial de estos vínculos y una prueba de interpretación con el equipo. La siguiente comparación histórica necesita dos versiones reales de corte: no se simula con la serie revisada ni se confunde la observación del 8-sep con una actualización de datos del 10-sep.
