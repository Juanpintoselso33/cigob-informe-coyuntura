---
madr: 4
id: '0343'
estado: 'aceptado'
fecha: 2026-10-07
cinturon: 'transversal'
archivos: ['web/src/pages/index.astro', 'web/src/components/MarcoTension.astro', 'web/src/components/TensionPanel.astro', 'web/src/components/Recomendaciones.astro', 'web/public/overrides.css']
relacionado: ['0200', '0237', '0320', '0326', '0346']
ambito: 'Portada (`index.astro`) — qué secciones se muestran y cómo se ve el marco conceptual, no qué se calcula'
origen: 'Pedido de Juan del 7-oct-2026: «la card de marco conceptual en el home, que tenga el mismo estilo que la lectura del mes» y «se va toda la parte de lectura cruzada».'
---

# ADR-0343 — La portada sin «Lectura cruzada», y el marco conceptual con formato de lectura

## Contexto y planteo del problema

Después del BLUF («La lectura del mes») la portada tenía el marco conceptual
como una nota lateral: fondo tenue, filete a la izquierda, cuerpo de 14,5 px y
un ancho máximo de 820 px que dejaba media card vacía. Lo que define cómo hay
que leer el Monitor se veía como una nota al pie de la lectura del mes.

Al final de la portada estaba la sección «Lectura cruzada · Tensión sistémica»,
con dos paneles:

- **Tensión sistémica** (`TensionPanel.astro`): los cuatro cinturones con su
  riesgo y su lectura de semáforo, marcando el dominante (ADR-0237) y los
  tensionados, y la regla de lectura «1 cinturón tensionado es manejable; 2 o
  más indican inestabilidad sistémica».
- **Qué vigilar este mes** (`Recomendaciones.astro`): las tres dimensiones con
  más tensión entre los cuatro índices, y cuántos indicadores venían con rezago.

Las dos repetían lo que la portada ya dice más arriba, con menos contexto. El
hero da el riesgo dominante y su cinturón, el BLUF nombra la peor dimensión, y
cada card de cinturón muestra su estado y su dimensión más tensa.

## Factores de decisión

- Acotar lo que muestra la portada (la misma línea que ADR-0320).
- Que las dos lecturas de la portada —la del mes y la del método— se vean como
  un par y no como texto principal y nota.
- No perder ningún dato que no esté publicado en otro lugar.

## Opciones consideradas

1. Sacar la sección entera y dar al marco el formato del BLUF.
2. Dejar sólo «Tensión sistémica» y sacar «Qué vigilar».
3. Dejar todo como estaba.

## Decisión

**Opción 1** (Juan, 7-oct-2026).

- **El marco conceptual** usa la caja y el cuerpo del BLUF (`.cg-bluf`,
  `.cg-bluf-editorial`: 17 px, interlineado 1,7, el filete de colores arriba) y
  ocupa todo el ancho. La cita de Babino (ADR-0326) conserva su filete a la
  izquierda y el texto no cambia. Se borra de `overrides.css` el bloque
  `.cg-marco-home`, que ya no usaba nadie.
- **La sección «Lectura cruzada»** sale de la portada. `TensionPanel.astro` y
  `Recomendaciones.astro` se borraron con ella; si vuelven, salen de `git show`.

### Consecuencias

Lo que sale de la portada y dónde sigue publicado:

| Dato | Dónde sigue |
|---|---|
| Riesgo dominante y su cinturón (ADR-0237) | Hero y BLUF |
| Estado de cada cinturón | Cards de «Los cinturones, hoy» |
| Dimensión con más tensión | BLUF y cada card |
| Regla «2 o más tensionados = inestabilidad sistémica» | `/metodologia`; en datos, `alerta_multicinturon` del snapshot y el aviso de Slack |
| Cantidad de indicadores con rezago | **Sólo en la página de cada cinturón**: la portada ya no da el total |

- Buena: la portada queda en hero → lectura del mes → marco → cinturones →
  evolución, sin repetir ninguna lectura.
- Mala: la regla de lectura multicinturón y el total de rezagados dejan de verse
  en la portada. Si se prende la alerta multicinturón, la portada no la dice
  con esas palabras: hoy la avisa sólo Slack.

### Confirmación

En producción, la portada no muestra «Lectura cruzada» ni «Tensión sistémica»,
y el marco conceptual se ve con la misma caja y el mismo cuerpo que «La lectura
del mes» (verificado el 7-oct-2026).

## Pros y contras de las opciones

### Opción 1 — Sacar la sección y dar formato de lectura al marco

- Bien: menos repetición, y el marco gana peso.
- Mal: la regla multicinturón sale de la portada.

### Opción 2 — Dejar «Tensión sistémica»

- Bien: conserva la regla multicinturón a la vista.
- Mal: repite el riesgo dominante y el estado de cada cinturón, y no es lo que se pidió.

### Opción 3 — Dejar todo

- Mal: no responde al pedido.

## Más información

- ADR-0320: la portada no explica el método, lo enlaza (mismo criterio de acotar).
- ADR-0326: la cita de Babino en el marco.
