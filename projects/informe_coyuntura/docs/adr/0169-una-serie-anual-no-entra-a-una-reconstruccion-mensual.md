---
madr: 4
id: '0169'
estado: 'aceptado'
fecha: 2026-07-31
cinturon: 'transversal'
indice: 'ITCP'
indicadores: [judicializacion, velocidad_resolucion]
archivos: ['scripts/validacion_externa.py']
continua: ['0168']
relacionado: ['0086', '0095', '0162', '0167', '0231']
ambito: 'Validación externa · reconstrucción histórica de índices mensuales'
origen: 'La validación del ITCP empeoró al entrar los cuatro indicadores de ADR-0168 y la auditoría encontró por qué'
---

# ADR-0169 — Una serie anual no entra a una reconstrucción mensual

## Contexto y planteo del problema

Al incorporar los cuatro indicadores de ADR-0168, **todas** las métricas de
validación externa del ITCP empeoraron:

| | antes | después |
|---|---:|---:|
| ITCP ↔ EPU, niveles | −0,493 | −0,468 |
| ITCP adelantado 1 mes vs EPU | −0,449 | −0,409 |
| factor común, niveles / diferencias | 0,523 / 0,493 | 0,512 / 0,440 |

La tentación era escribir por qué el empeoramiento es aceptable —"es dilución:
cuatro indicadores nuevos que no correlacionan con el EPU tanto como los
existentes"—. Esa explicación es **cierta en niveles y falsa en diferencias**, y
habría tapado un problema real.

## Factores de decisión

Se corrió el contrafáctico de ADR-0095 —reconstruir el índice sin cada
indicador— **en las dos métricas**, y dan culpables opuestos:

| Variante | r niveles | r diferencias |
|---|---:|---:|
| ITCP completo | −0,458 | −0,366 |
| sin `produccion_legislativa` | −0,473 | — |
| sin los dos **anuales** | −0,466 | **−0,405** |
| sin los cuatro nuevos | −0,491 | −0,402 |

En **niveles** el mayor contribuyente individual es `produccion_legislativa`
(0,015) y los dos anuales aportan 0,008: lectura de dilución repartida, sin
insumo defectuoso. En **primeras diferencias** —el criterio que ADR-0167 fijó
como autoritativo— sacar los dos anuales mejora 0,039, **más que sacar los
cuatro** (0,036), porque los dos mensuales compensan.

**El mecanismo es general.** Una serie anual interpolada dentro de un índice
mensual tiene, en primeras diferencias, **once ceros y un salto por año**.
Contra la variación mensual de cualquier benchmark eso es ruido con forma de
escalón. En niveles el escalón se disimula dentro de la tendencia común
—justamente lo que ADR-0162 midió—; en diferencias queda expuesto.

## Opciones consideradas

- **Sacar las series anuales de la reconstrucción, dejándolas puntuar** —
  elegida.
- **Sacar los indicadores del índice** — descartada: su valor anual es
  legítimo, el bloque judicial los necesita y el problema no es el indicador
  sino su serie dentro de un cálculo mensual.
- **Declarar el empeoramiento y seguir** — descartada: era la justificación que
  la auditoría desmintió.

## Decisión

`judicializacion` y `velocidad_resolucion` salen de la reconstrucción
histórica del ITCP y de su matriz de redundancia. **Siguen puntuando desde su
card**, con su peso completo en la dimensión judicial.

Es el mismo patrón que ADR-0086 aplicó a `rigi_inversiones` en el ITCG, con el
motivo escrito al lado de la exclusión (`ITCP_SERIE_ANUAL`, espejo de
`ITCG_SERIE_NO_COMPARABLE`). La regla general que deja: **la serie de un
indicador entra a la reconstrucción sólo si su frecuencia es la del índice.**

### Consecuencias

- ITCP ↔ EPU en primeras diferencias: **−0,366 → −0,405**, mejor que el −0,397
  que el índice tenía *antes* de incorporar los cuatro. En el criterio que el
  proyecto declaró autoritativo, el cinturón valida mejor que al empezar.
- En niveles queda en −0,466: la dilución sigue ahí y es real. Se publica.
- La reconstrucción pasa de 18 a 16 indicadores; la matriz de redundancia, a
  103 pares.

### Confirmación

`output/validacion_externa.json` publica las dos métricas para cada par, de modo
que la brecha entre niveles y diferencias queda a la vista — que es exactamente
el dato que este ADR usa para decidir.

## Más información

### Limitaciones

- La exclusión es por **frecuencia**, no por calidad: los dos indicadores no
  están bajo sospecha. Si alguna de las dos fuentes empezara a publicar con
  frecuencia mensual, corresponde volver a incluirla.
- La reconstrucción del ITCP queda midiendo 16 de los 18 indicadores que
  puntúan. La validación externa habla, entonces, de una versión del índice
  ligeramente distinta de la publicada — igual que en el ITCG desde ADR-0086.
  Es un costo asumido y preferible a validar contra ruido.
