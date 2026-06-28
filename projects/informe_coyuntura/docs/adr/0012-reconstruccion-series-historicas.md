# ADR-0012 — Reconstrucción de series históricas para indicadores sin histórico (backfill)

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-06-30 |
| **Ámbito** | `scripts/descargar_series.py` · `scripts/politica.py` · `scripts/publicar.py` · `docs/backfill-series.md` |

## Contexto

Muchos indicadores de política, vida, espíritu y los "avances" de gestión solo tenían
**un punto** (el valor del mes), así que el modal los mostraba como gauge y no se veía
la trayectoria. La acumulación hacia adelante (`data/historico/indicadores.json`) arma
la serie mes a mes, pero tarda años en ser útil. Para varios indicadores, en cambio, el
**pasado ya existe en la fuente oficial** y se puede reconstruir hoy.

`docs/backfill-series.md` audita, indicador por indicador, qué se puede reconstruir,
desde qué fuente y con qué factibilidad.

## Decisión

Reconstruir la serie de los indicadores de **alta factibilidad** computando la MISMA
métrica que muestra la card, para todo el histórico disponible, vía `descargar_series`
(que ya corre en el pipeline/CI y alimenta `series.json`). Regla de oro: **el último
punto de la serie reconstruida debe coincidir con el valor live** (verificado uno por uno).

- **Votómetro** (`votometro_ventaja_lla`, y `clima_electoral` por alias): la brecha
  ponderada LLA−PJ recalculada a fin de cada mes desde `encuestasRaw` (todos los sondeos
  desde dic-2023), con la misma ponderación recencia×calidad. 31 puntos.
- **Vida** (`ipc_alimentos`, `peso_tarifas`, `mortalidad_pymes`): variación m/m % de la
  serie índice INDEC (`fetch_indec_var_mensual` = `(idxₜ/idxₜ₋₁−1)×100`). 47 puntos c/u.
- **InfoLeg** (`desregulacion_normativa`, `reestructuracion_organismos`): conteo acumulado
  de normas ("deroga"/"disolucion") reconsultado a fin de cada mes. 31 / 24 puntos.
- **`iaf_transferencias`**: variación real i.a. anual (RON Hacienda) deflactada por IPC
  (ver abajo). 9 puntos anuales (2017-2025).

## De-hardcode del deflactor IPC (`iaf_transferencias`)

Al reconstruir `iaf_transferencias` se descubrió que el colector deflactaba con
`IPC_ANUAL` **hardcodeado** (`{2024: 1,1706, 2025: 0,383}`) y que el valor 2025 era una
**proyección vieja**: el dic-dic **real** de INDEC es 0,315 (el 2024 hardcodeado sí
coincidía). Eso violaba el principio del proyecto —*calcular desde la fuente oficial,
nunca hardcodear*— y descuadraba el dato.

Se agregó `politica._ipc_dicdic_indec()`, que deriva el IPC dic-dic por año del **índice
oficial INDEC** (serie 148.3, base dic-2016). El colector lo usa con fallback a
`IPC_ANUAL` solo si la API falla. La serie histórica usa el mismo IPC, así que card y
serie quedan consistentes.

## Consecuencias

- 6 indicadores pasan de gauge (1 punto) a línea + tabla + CSV; la trayectoria real queda
  visible (p. ej. la ventaja LLA−PJ: +16 post-elección → +3 → +13 → +5).
- **Corrección de score:** `iaf_transferencias` 1,8% → **7,0% real** (IPC aplicado 38,3% →
  31,5%); su tensión baja, política 4,8 → **4,6**. Es una corrección, no un cambio de
  criterio: el deflactor pasó de una proyección hardcodeada al dato oficial.
- **Frescura:** todo corre en `descargar_series` (CI diario) con degradación elegante —
  si una fuente falla, esa serie no se actualiza y el indicador cae a la acumulación hacia
  adelante; no se pierde dato.
- **Pendiente:** `sentimiento_digital` (Trends) e `icc_utdt` (UTDT) son el próximo lote;
  el resto del roadmap está en `docs/backfill-series.md`. Los bloqueados (sin dato
  histórico) siguen acumulando hacia adelante.
