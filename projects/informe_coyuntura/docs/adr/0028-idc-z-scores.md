# ADR-0028 — IdC rediseñado: z-scores de nivel contra la propia historia

| | |
|---|---|
| **Estado** | Aceptado (supersede al ADR-0004; resuelve el ADR-0027 vía su opción a) |
| **Fecha** | 2026-07-04 |
| **Ámbito** | Dimensión Capacidad de financiamiento · indicador `idc` |

## Contexto

La auditoría adversarial del ADR-0027 encontró defectos estructurales en el IdC
del doc `260626 aportes` (ratios mensuales t/t−1): doble conteo de los depósitos
(~70% efectivo), componente de asignación mal condicionado (explota con R→1),
premio a la desaceleración del crédito, medición de derivada y no de estado, sin
estandarización de varianzas ni tratamiento estacional. El editor eligió la
opción (a): rediseño tipo FCI simplificado.

## Decisión

Se conservan los **tres conceptos y los pesos del doc de CIGOB** (precio 30 /
volumen 40 / asignación 30) pero cada componente pasa a ser un **NIVEL mensual
estandarizado contra su propia historia** (z-score, ventana expansiva sobre toda
la muestra disponible, hoy 2017-12 → presente, ~102 meses):

```
IdC = 0,30·z_precio + 0,40·z_volumen + 0,30·z_asignación      (en σ)

precio     = tasa real mensual de la BADLAR (TEM − IPC m/m), en pp
volumen    = depósitos privados, variación INTERANUAL real (%)
asignación = holgura prestable 1 − préstamos/depósitos, en % (nivel)
z          = (nivel − media histórica) / desvío histórico
```

- **Publicación en σ**: 0 = mes histórico típico. Semáforo: > +0,5 σ verde ·
  ±0,5 σ amarillo · < −0,5 σ rojo.
- **Anclas ITCM en percentiles conocidos**: +1σ≈p84→100 · +0,5σ≈p69→85 ·
  ±0,5σ→60 · −1σ≈p16→35 · menor→10 (interpoladas, ADR-0021).
- **El mes publicado es el último con IPC cerrado** — se elimina el nowcast del
  deflactor que mezclaba stocks de junio con IPC de mayo.
- Implementación: `macro._idc_base_mensual()` (niveles) + `_idc_z_series()`
  (estandarización) — fórmula única para el indicador vivo y la serie del modal.

## Cómo resuelve cada hallazgo del ADR-0027

| Hallazgo | Resolución |
|---|---|
| Doble conteo de depósitos | volumen = interanual, asignación = nivel del ratio: un salto mensual de depósitos ya no infla dos ratios m/m a la vez (correlación residual declarada) |
| Asignación explota con R→1 | es un nivel acotado (1−R), sin división por (1−R_prev) |
| Premia la desaceleración | mide el margen COMO ESTADO: la holgura baja cuando el crédito ya creció (jun-2026: −1,18 σ, el boom consumió el margen) — coherente con `credito_privado`, no opuesto |
| Derivada, no estado | los tres componentes son niveles contra la distribución histórica, como los FCI de referencia |
| Sin estandarización | z-scores: cada componente pesa lo que dice su peso, no su varianza |
| Estacionalidad | la interanual de depósitos absorbe aguinaldos/cosecha; tasa real y holgura no tienen estacionalidad relevante |
| Deflactor rezagado | el mes publicado cierra con su propio IPC |
| Anclas mágicas | anclas = percentiles de la muestra (documentados) |

## Consecuencias

- **El valor cambia de escala y de lectura**: jun-2026 pasó de 1,0608 (verde,
  puntaje 100) a **−0,31 σ (amarillo, puntaje ~50)** con fecha may-2026. La
  lectura nueva es más dura y más creíble: la tasa real está apenas sobre su
  media (+0,33 σ), los depósitos crecen a ritmo típico (−0,13 σ) y la holgura
  está baja (−1,18 σ, 17,1%) porque el crédito ya se expandió fuerte.
- El ITCM baja ~3 puntos por este cambio (el IdC pesa 6,4%): el 100 anterior lo
  sostenía un salto mensual de depósitos (aguinaldo incluido).
- La serie del modal queda suave y comparable (misma escala σ toda la historia);
  el histórico previo en escala ~1,0 se purga (regla de métricas redefinidas).
- La volatilidad mensual del diseño anterior desaparece: los últimos 8 meses
  van de −0,03 a −0,41 sin saltos.
- ~~Pendiente de validación externa propia~~ **RESUELTO (04-jul-2026,
  negativo verificado)**: se probó sobre los 102 meses de la muestra si el
  IdC anticipa el crédito real futuro — en niveles (r +0,10 contemporáneo,
  −0,53 a +12 meses) y como aceleración (−0,45 a +12 meses). El IdC NO
  predice el crédito: en la Argentina 2018-2026 la capacidad medida alta fue
  típicamente síntoma de demanda de crédito débil (la liquidez estacionada,
  2020-21), no antesala de expansión — la capacidad nunca fue el cuello de
  botella; la estabilidad macro y la demanda sí. El componente queda como
  descriptor de ESTADO de las condiciones de fondeo (que es lo que su ficha
  dice), sin claim predictivo; la validación operativa del capítulo
  financiamiento es la del ITCM agregado (riesgo país, ADR-0031).
