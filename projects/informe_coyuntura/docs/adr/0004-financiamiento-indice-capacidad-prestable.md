---
madr: 4
id: '0004'
estado: 'superado'
nota_estado: 'SUPERSEDIDO por el [ADR-0028](0028-idc-z-scores.md) el 2026-07-04 (los ratios mensuales pasaron a z-scores de nivel; los tres conceptos y pesos se conservan)'
fecha: 2026-06-26
cinturon: 'macro'
indicadores: [idc]
superado_por: ['0028']
ambito: 'Dimensión Capacidad de financiamiento · indicador `idc`'
commit: '`1016e97`'
---

# ADR-0004 — La dimensión de financiamiento usa el Índice de Capacidad Prestable (IdC)

## Contexto y planteo del problema

La Paramétrica original puntuaba la mitad de la dimensión de financiamiento con la
**tasa BADLAR** en nivel. Problema: la BADLAR alta en términos nominales sólo
refleja la inflación residual, no la (des)confianza en el crédito; castigaba al
cinturón por tener tasas nominales altas. El documento `260626 aportes` propone
reemplazarla por un **Índice de Capacidad Prestable (IdC)** de tres componentes.

## Opciones consideradas

- **BADLAR en nivel** (original). Rechazada: castiga la nominalidad, no mide confianza.
- **Spread de intermediación** (activa adelantos − pasiva depósitos). Implementado
  primero (`8dd8bc0`) y **descartado**: mejoraba sobre la BADLAR pero el doc `260626`
  trae el IdC, más completo (precio + volumen + asignación).
- **IdC con Asignación = nivel `1−R`** (literal del doc). Rechazada: rompe el semáforo.
- **IdC con Asignación = ratio mensual de holgura.** Elegida: coherente con el
  semáforo y reproduce el caso de mayo del doc.

## Decisión

La dimensión de financiamiento usa el **IdC** (50%, junto a reservas netas 50%):

```
IdC = 0,30·Precio + 0,40·Volumen + 0,30·Asignación   (índice centrado en ~1,0)
```

- **Precio** = `1 + tasa real mensual de la BADLAR` (TEM − IPC m/m).
- **Volumen** = ratio mensual de depósitos privados reales (var 100 deflactado por IPC).
- **Asignación** = ratio mensual de holgura prestable `(1−R_t)/(1−R_{t-1})`, con
  `R = préstamos/depósitos` del sector privado (var 117 / var 100).

Semáforo: `>1,02` verde (expansión) · `0,98–1,02` amarillo (neutro) · `<0,98` rojo
(contracción). Bandas en `itcm.py`: `>1,04→100 · 1,02–1,04→85 · 0,98–1,02→60 ·
0,95–0,98→35 · ≤0,95→10`. La BADLAR pasa a **contexto** (se sigue publicando, e
insumo del IdC). Implementación: `macro.fetch_idc()` + `itcm.indice_capacidad_prestable()`.

### Inconsistencia del documento, resuelta

El doc define **Asignación = `1 − R`** (un nivel ~0,14), que rompe el semáforo: con
ese término el índice da ~0,79, nunca centrado en 1,0. Se implementó la Asignación
como el **ratio mensual de holgura** `(1−R_t)/(1−R_{t-1})`, que sí deja el índice en
~1,0 y **reproduce el "amarillo" de mayo 2026** que el propio documento describe
como caso de referencia. La desviación está documentada en el código.

### Consecuencias

- Insumos BCRA: depósitos privados = var 100, préstamos privados = var 117 (NO usar
  104/26: dan ratio > 1, imposible).
- El indicador publica los tres componentes, `badlar_real_mensual` y `semaforo`.
- Hoy IdC ≈ 1,012 → amarillo → 60.
