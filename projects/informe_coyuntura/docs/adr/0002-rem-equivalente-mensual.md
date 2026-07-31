---
madr: 4
id: '0002'
estado: 'aceptado'
nota_estado: 'Aceptado (supersede la brecha vs run-rate del commit `8dd8bc0`)'
fecha: 2026-06-26
indicadores: [rem_ipc_12m]
ambito: 'Dimensión Estabilidad monetaria · indicador `rem_ipc_12m`'
commit: '`1016e97`'
---

# ADR-0002 — El REM se puntúa por su equivalente mensual (raíz-12), no por nivel absoluto

## Contexto y planteo del problema

El documento original de la Paramétrica puntúa las **expectativas de inflación a
12 meses (REM)** con una escala de bandas **absolutas** (≤10% → 100, …, >30% → 10).
En el contexto de desinflación argentino, esa escala castiga de más: un REM de 24%
caía en "baja credibilidad" (35 puntos) cuando, comparado con la inflación que
corría, era una expectativa razonable. El analista marcó que "debería ser moderada".

## Opciones consideradas

- **Bandas absolutas del doc original** (≤10→100 … >30→10). Rechazada: miscalibrada
  para la desinflación; castiga expectativas razonables.
- **Brecha vs run-rate del IPC** (`REM − inflación anualizada`, ventana 1 mes).
  Implementada primero (`8parte 8dd8bc0`) y luego **descartada**: dependía de elegir
  una ventana (1/2/3 meses) y era menos autocontenida que la raíz-12.
- **Equivalente mensual (raíz-12) con bandas del IPC.** Elegida: autocontenida (no
  necesita run-rate ni elegir ventana), y pone REM e IPC en la misma escala.

## Decisión

El REM se puntúa por su **equivalente mensual** —la raíz 12 de la expectativa
anual, `(1+REM/100)^(1/12) − 1`— y se bandea con **la misma escala mensual del
IPC** (`BANDAS_ITCM["ipc_total"]`). Así las expectativas y la inflación realizada
quedan en la misma vara: lo que importa es a qué ritmo mensual de inflación apunta
el mercado.

Ej.: REM 23,3% anual → 1,76% mensual → banda 1–2% → 85.

Implementación: `itcm.rem_mensual_equivalente()`; el valor mensual se deriva en
`macro.calcular_itcm_cinturon()` y se sustituye en `valores["rem_ipc_12m"]` antes
de bandear. La fórmula es del documento `260626 aportes para el cinturon macro`.

### Consecuencias

- Se borraron `run_rate_ipc`, `brecha_rem` e `IPC_RUNRATE_MESES` (resabios de la
  brecha).
- El indicador publica `equivalente_mensual` y `nota_scoring` para transparencia:
  el valor mostrado es el nivel anual, pero la banda usa el equivalente mensual.
- Coherencia conceptual: si la inflación esperada mensual ≈ la realizada, la
  credibilidad es alta, sin importar el número anual nominal.
