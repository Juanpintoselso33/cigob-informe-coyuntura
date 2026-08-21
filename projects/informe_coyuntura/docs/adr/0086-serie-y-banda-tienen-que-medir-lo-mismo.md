---
madr: 4
id: '0086'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'gestion'
indicadores: [rigi_inversiones, validacion_externa]
corrige: ['0085']
relacionado: ['0087', '0169', '0231']
ambito: '`rigi_inversiones` · reconstrucción histórica del ITCG · `validacion_externa`'
---

# ADR-0086 — La serie de un indicador tiene que medir lo mismo que puntúa su banda

| **Corrige** | ADR-0085 (atribuyó la correlación +1,000 del ITCG a una causa equivocada) |
| **Familia** | ADR-0082 (quinto caso del mismo error) |

## Contexto y planteo del problema

La serie de `rigi_inversiones` guardaba el pipeline de inversiones en
**millones de dólares** —31.192 en el último punto—, mientras las bandas del
indicador están calibradas para un **porcentaje**: el tramo superior arranca en
60 y el inferior termina en 10.

La card estaba bien: puntuaba 22,0% → 47,5. La **reconstrucción histórica**
puntuaba 31.192 contra esas mismas bandas → 100,0.

En la práctica, la serie del ITCG venía viendo esto:

| período | valor de la serie | puntaje que se le asignaba |
|---|---|---|
| 2024 | 0 | **10** (piso) |
| desde ene-2025 | 8.400 → 31.192 | **100** (techo) |

Un **escalón binario** entre el piso y el techo, que no ocurrió: el indicador
real se movió dentro de un rango estrecho y bajo.

## Opciones consideradas

- **Sacar `rigi_inversiones` de la reconstrucción histórica y de la matriz de redundancia del ITCG** — elegida. Sigue puntuando desde su card, que es correcta.
- **Seguir usando su serie** — descartada: mide en M USD contra una banda en %.

## Decisión

**`rigi_inversiones` sale de la reconstrucción histórica y de la matriz de
redundancia del ITCG.** Sigue puntuando en el índice desde su card, que es
correcta; lo que se retira es el uso de su serie como si midiera lo que puntúa.

La exclusión es explícita y con motivo escrito en el código:

```python
ITCG_SERIE_NO_COMPARABLE = {
    "rigi_inversiones": "serie en M USD vs banda en % (ADR-0086)",
}
```

No es lo mismo que "no tiene serie". La tiene, es correcta y es informativa —
mide el tamaño del pipeline RIGI, que es una señal de compromiso de inversión
privada por derecho propio. Lo que no puede es puntuarse contra bandas
calibradas para otra magnitud.

### La guardia

ADR-0082 creó `Escala` para que hubiera un solo camino de puntuación, y un test
que reproduce el puntaje publicado desde el valor crudo — pero **sólo para el
ITCM**. Este caso vivía en gestión, fuera del alcance del test.

Ahora el test recorre **los tres índices**: para cada indicador puntuable
compara el puntaje del último punto de su serie contra el `puntaje_banda`
publicado, y falla si difieren en más de 20 puntos. La tolerancia es amplia a
propósito: card y serie suelen estar ancladas a fechas distintas y eso produce
diferencias chicas y legítimas. Lo que se busca es una diferencia de
**magnitud**, que es de otro orden. Un segundo test exige que la exclusión siga
declarada con su motivo, para que borrarla no sea silencioso.

### Consecuencias

- ITCG: 14 indicadores en la matriz, 64 pares, \|r\| medio 0,492 en niveles y
  **0,137 en cambios** (1,6% de pares altos, contra el 4% que publicaba ADR-0085).
- El par más alto real del ITCG pasa a ser
  `libertad_opcion_salud × protocolo_antipiquetes` (+0,994) — **éste sí** es el
  artefacto de contadores acumulados que ADR-0085 describe.
- ADR-0085 queda corregido en su atribución, no revocado: su decisión central
  —medir también sobre primeras diferencias— era correcta y de hecho es lo que
  habría que haber mirado antes de explicar el +1,000.

## Más información

### Limitaciones

La serie del pipeline RIGI en dólares **no se reconstruye como porcentaje hacia
atrás**. Podría hacerse (el denominador está en la misma fuente), y hasta que se
haga el ITCG tiene 13 componentes con historia comparable en lugar de 14. Se
deja anotado como deuda, no como imposibilidad.

### Por qué pasó desapercibido

Porque la divergencia estaba **declarada** — como excepción del gate G3:

> `"rigi_inversiones": "card = % de la meta; serie = monto acumulado en M USD"`

La excepción es legítima **para lo que el G3 vigila**, que es la frescura de la
card contra el último punto de su serie. Lo que nadie advirtió es que esa misma
serie alimenta otra cosa: la reconstrucción histórica del índice. Una excepción
correcta en un consumidor se volvió un error silencioso en el otro.

Es la forma general del problema y conviene nombrarla: **declarar una
divergencia no la resuelve, sólo la documenta para un lector**. Si hay dos
consumidores del mismo dato, la excepción tiene que evaluarse contra los dos.

### Impacto medido

| | |
|---|---|
| desvío máximo de la serie reconstruida del ITCG | **5,4 puntos** |
| desvío medio | 1,44 puntos |
| ITCG ↔ Merval USD (niveles) | 0,766 → **0,748** |
| pares "altos" de la matriz publicada que involucraban al indicador | **6 de 26** |

Y el hallazgo más incómodo: **el par de correlación +1,000 que ADR-0085 explicó
como artefacto de contadores acumulados era, en realidad, este bug.** La
explicación publicada era plausible, estaba bien argumentada y era falsa. Al
quitar el indicador, el par desaparece.
