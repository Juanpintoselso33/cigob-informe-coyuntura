---
madr: 4
id: '0160'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'vida'
cierra: ['0155']
ambito: 'cinturón vida cotidiana, sección de consistencia interna'
---

# ADR-0160 — La dispersión del ITVC se publica junto al neto

- **Relacionados**: ADR-0159 (validación por panel, donde se midió la chatura),
  ADR-0108 (matriz de redundancia), ADR-0018/0024 (escala base-100),
  ADR-0156 (el texto público dice el método, el número se deriva)

## Contexto y planteo del problema

Al revisar por qué «el ITVC casi no se mueve» (ADR-0159) quedó medido que **no es
que los insumos estén planos: es que se compensan**. Si todos los componentes se
movieran juntos el índice oscilaría 37,6 puntos; el rango real es 8,3, así que se
cancela el 78%. El pendiente que quedó anotado fue publicar esa dispersión al
lado del neto, porque **el promedio solo dice «sin cambios» donde el dato dice
«no cambió en neto pero se recompuso fuerte por dentro»**.

## Opciones consideradas

- **Anexar la dispersión a la sección de consistencia interna** — elegida: es donde el lector ya está mirando cómo se relacionan los componentes, y donde la dispersión explica el resultado de esa misma sección.
- **Publicarla como sección aparte** — descartada.

## Decisión

La dispersión se anexa a la **sección de consistencia interna**, que es donde el
lector ya está mirando cómo se relacionan los componentes entre sí — y donde la
dispersión **explica el resultado de esa misma sección**: si se separaron tanto
es porque no repiten la misma señal.

Se publica además la serie mensual completa (`dispersion.serie`: rango, desvío,
mínimo y máximo por mes) para que la lectura no dependa de dos fotos.

Dos decisiones de implementación:

- **la prosa no nombra componentes.** En `publicar.py` rige la convención de
  emitir claves y dejar las etiquetas legibles al front; los nombres van en el
  campo de datos, no en el texto;
- **el «seis veces más separadas» se deriva**, no se escribe. Es una afirmación
  sobre el estado de hoy y caduca sola — exactamente la clase de frase que
  ADR-0156 obliga a computar. Si el cociente baja de 1,5 la frase desaparece.

### Consecuencias

- El cinturón deja de comunicar «sin cambios» a secas. La chatura del índice pasa
  de ser un defecto aparente a ser un hallazgo explicado.
- **No se toca la escala.** Bajar la pendiente de la tensión para que el número
  se mueva más sería recalibrar para que quede mejor, prohibido por ADR-0045. El
  problema no era la escala sino que faltaba la lectura.
- Queda como pendiente editorial si la dispersión merece su propio gráfico: hoy
  viaja como texto y datos dentro de una sección existente, sin componente web
  nuevo.

## Más información

### Lo que muestra el número

| | arranque (dic-2023) | último mes | |
|---|---|---|---|
| componente más bajo | 87,8 | **17,2** | |
| componente más alto | 107,7 | **140,0** | |
| **rango** | **19,9** | **122,8** | ×6,2 |
| desvío estándar | 5,1 | 28,5 | ×5,6 |
| **movimiento NETO del índice** | | | **5,0 puntos** |

En treinta y dos meses el índice se movió cinco puntos y sus componentes pasaron
de estar agrupados en veinte puntos a estar repartidos en ciento veintitrés. Esa
es la recomposición que el neto esconde, y ahora se publica.
