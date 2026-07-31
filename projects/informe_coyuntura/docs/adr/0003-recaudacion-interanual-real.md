---
madr: 4
id: '0003'
estado: 'aceptado'
fecha: 2026-06-26
indicadores: [recaudacion]
modificado_por: ['0127']
ambito: 'Dimensión Viabilidad fiscal-comercial · indicador `recaudacion`'
commit: '`1016e97`'
---

# ADR-0003 — La recaudación se mide en variación interanual REAL (deflactada)

## Contexto y planteo del problema

La Paramétrica original tomaba la **variación mensual nominal** de la recaudación
tributaria. Eso tiene dos problemas: (1) el mes a mes nominal está dominado por la
estacionalidad y la inflación, no por la salud fiscal real; (2) una variación
nominal alta puede ser solo inflación, no más recursos. El documento `260626
aportes` indica explícitamente que las variaciones deben corregirse por el IPC del
mismo período.

## Opciones consideradas

- **Variación m/m nominal** (original). Rechazada: estacional y contaminada por
  inflación; el m/m nominal daba 100 (recuperación fuerte) cuando en términos
  reales la recaudación apenas crecía.
- **Variación i.a. nominal** (sin deflactar). Rechazada: sigue inflada por precios.
- **Variación i.a. real (deflactada).** Elegida: aísla la recuperación genuina de
  los ingresos.

## Decisión

La recaudación se mide en **variación INTERANUAL REAL**: la variación nominal
interanual deflactada por el IPC interanual del mismo período.

```
var_real = (1 + var_nominal_ia/100) / (1 + ipc_ia/100) − 1
```

Las bandas (>10→100, 5–10→80, 0–5→60, −5–0→40, <−5→10) se mantienen, pero el
**input** cambia de "% m/m nominal" a "% i.a. real". Implementación:
`macro.fetch_recaudacion()` usa `_indec_yoy()` sobre la serie de recaudación y
sobre el IPC.

Ej. (may-2026): +35,6% nominal i.a. / +33,2% IPC i.a. → **+1,82% real** → banda 0–5 → 60.

### Consecuencias

- El indicador publica `var_ia_nominal` e `ipc_ia` además del valor real, para
  poder auditar la deflactación.
- El score de la dimensión fiscal baja respecto del cálculo nominal (refleja mejor
  la realidad: la recaudación real crece poco).
