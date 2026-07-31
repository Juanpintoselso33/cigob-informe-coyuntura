---
madr: 4
id: '0022'
estado: 'aceptado'
nota_estado: 'aceptada (decisión del editor)'
fecha: 2026-07-03
cinturon: 'macro'
relacionado: ['0071', '0074', '0077']
---

# ADR-0022 — Crédito privado real al ITCM; los monetarios nominales quedan ocultos

## Contexto y planteo del problema

El cinturón macro publicaba cuatro indicadores de contexto (BADLAR, préstamos
privados, base monetaria, TC mayorista) que no integraban el ITCM. El editor
pidió incorporarlos. El análisis mostró que **su señal ya está adentro del
índice, digerida en componentes mejor diseñados**: la BADLAR es el componente
precio del IdC; los préstamos son insumo de la asignación del IdC; la base
monetaria está superada por el IDM (M3 vs M2 real); el TC nominal es el TCRM
en su versión sin deflactar. Incluirlos directo habría reintroducido el doble
conteo recién eliminado (ADR-0021) y el sesgo nominal ya corregido dos veces
en las revisiones del ITCM.

## Opciones consideradas

- *Incluirlos directo con bandas propias*: doble conteo con IdC/IDM/TCRM +
  puntuar niveles nominales sin ancla honesta. Descartada.
- *Panel visual "termómetro monetario" sin puntuar*: cosmética; no responde
  al pedido de que cuenten. Descartada (rehabilitable si se extraña la vista).
- *Eliminarlos de la pipeline*: perdería los insumos de los componentes
  derivados y la trazabilidad. Descartada explícitamente por el editor.

## Decisión

1. **Se rescata la única señal no redundante: el crédito realizado.** Nuevo
   componente `credito_privado` = variación i.a. REAL de los préstamos al
   sector privado (BCRA var. 26, deflactada por IPC). Complementa al IdC:
   el IdC mide la *capacidad* prestable (tasas y ratios); esto mide si el
   crédito efectivamente *llegó* a la economía. Dimensión financiamiento
   repesada: **reservas 0,45 · IdC 0,40 · crédito real 0,15**. Bandas
   calibradas a la remonetización 2024-2026 (el crédito real llegó a +90%
   i.a. desde base ínfima y se normaliza): >40 → 100 · 20-40 → 85 ·
   8-20 → 65 · 0-8 → 45 · −10-0 → 25 · ≤−10 → 10. Serie mensual backfilled
   desde dic-2023 (`fetch_credito_privado_serie`).
2. **Los cuatro nominales quedan OCULTOS del snapshot, no de la pipeline**
   (`publicar.MACRO_OCULTOS`): el colector los sigue computando (cache), las
   series se siguen descargando — son insumos del IdC/IDM/TCRM y auditables —
   pero la web ya no los muestra como tiles. La sección "No integran el
   índice" de macro desaparece (queda vacía).

### Consecuencias

- Estado 2026-07-03: crédito real **+8,1% i.a.** (la remonetización se enfría
  fuerte — información que el índice antes no veía) → puntaje 53,2 →
  dimensión financiamiento 53,6. **ITCM 54,7 → 54,5** (efecto neto mínimo).
  Macro publica 12 indicadores, todos en el índice; contexto vacío.
- Tests repineados (fixture con crédito +26% → 80,0; reconciliación de
  publicar exige contexto macro vacío y los 4 ocultos ausentes del snapshot).
- El histórico del snapshot pierde los 4 tiles pero `data/historico` y las
  series conservan todo (nada se borra).
