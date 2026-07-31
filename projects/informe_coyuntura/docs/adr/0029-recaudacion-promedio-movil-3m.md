---
madr: 4
id: '0029'
estado: 'aceptado'
fecha: 2026-07-04
cinturon: 'macro'
indicadores: [recaudacion]
relacionado: ['0072', '0076']
ambito: 'Indicador `recaudacion` (60% de Viabilidad fiscal-comercial = 14,4% del ITCM — el componente más pesado del índice)'
---

# ADR-0029 — Recaudación real: promedio móvil de 3 meses sobre IPC cerrado

| **Disparador** | Barrido uno-por-uno de macro (6/12) |

## Contexto y planteo del problema

El indicador puntuaba la variación i.a. real de UN solo mes. Dos problemas:

1. **Serrucho de calendario tributario**: feb −9,8 → mar −4,8 → abr −3,9 →
   may +1,8 → jun −7,1. El interanual mensual hereda los vencimientos de
   Ganancias, anticipos y bases atípicas del año previo. Con 14,4% de peso,
   el ITCM oscilaba ±7 puntos por ruido de calendario (el puntaje saltó
   10 → 67 → 10 en tres meses sin ningún cambio de política).
2. **Deflactor desalineado sin declarar**: el nominal de junio se deflactaba
   con el IPC interanual de mayo (el de junio no está publicado) — en
   desinflación exagera el negativo ~0,5 pp.

## Factores de decisión

### Prácticas de referencia relevadas

- **IARAF / OPC / CPCE** (los analistas fiscales de referencia): la lectura
  de tendencia se grafica como "variación interanual real del promedio móvil
  de 3 meses" (textual en los reportes de IARAF), acompañada del acumulado
  anual. El mes suelto es titular de prensa, no métrica de evaluación.
- **FMI (Fiscal Monitor)**: cuentas fiscales en acumulados anuales/12 meses.
- **Oficinas estadísticas / academia**: X-13-ARIMA con regresores de
  calendario y tendencia-ciclo — el óptimo técnico, DESCARTADO acá porque
  introduce un modelo estimado (rompe la reproducibilidad simple del
  pipeline y los coeficientes cambian con cada dato nuevo).
- **Handbook JRC/OCDE** (canon del ADR-0019): los insumos ruidosos se tratan
  antes de agregar, documentando la elección.

## Opciones consideradas

- **Promedio móvil de 3 meses sobre IPC cerrado** — elegida.
- **X-13-ARIMA con regresores de calendario y tendencia-ciclo** — el óptimo técnico, descartado acá porque introduce un modelo estimado: rompe la reproducibilidad simple del pipeline y sus coeficientes cambian con cada dato nuevo.

## Decisión

`recaudacion` puntúa el **promedio móvil de 3 meses de la variación
interanual real, calculado solo sobre meses con IPC publicado**:

```
valor = promedio de los últimos 3 meses cerrados de:
        (recaudación_m / recaudación_{m−12}) · (IPC_{m−12} / IPC_m) − 1
```

- Resuelve el serrucho (un vencimiento ya no mueve el ITCM) conservando
  reactividad trimestral — el acumulado 12m habría tardado medio año en
  registrar un cambio de régimen fiscal.
- Resuelve el deflactor: cada mes se deflacta con SU IPC; el mes fresco
  (nominal publicado, IPC pendiente) se muestra en el detalle del modal como
  provisorio, sin puntuar — mismo criterio de mes cerrado que el IdC
  (ADR-0028).
- La serie del modal pasa a la misma métrica (regla de familia: la serie
  grafica el titular). Las anclas del doc no cambian (misma escala de % i.a.
  real).
- Validación externa del ITCM: la reconstrucción usa la serie publicada, así
  que adopta la métrica suavizada automáticamente.

### Consecuencias

- Con los datos del 04-jul-2026: mar −4,8 · abr −3,9 · may +1,8 → **−2,3%**
  (antes: −7,14 del junio provisorio). Puntaje 10 (piso) → **~33**. ITCM
  ~+3 puntos. La señal sigue siendo negativa — pero es la tendencia
  verdadera, no el calendario.
- Validación externa del nivel: IARAF estimó junio −7,4% real i.a. (nuestro
  provisorio: −7,1 ✓) y el semestre −5,3% — el colector reproduce el consenso.
- Candidato a mismo tratamiento: `gasto_funcionamiento` y `masa_salarial` en
  gestión (pendiente #5 — misma volatilidad documentada, pesos menores).
