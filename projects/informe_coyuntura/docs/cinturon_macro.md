# Cinturón Macro

| Campo | Valor |
|---|---|
| Script | `scripts/macro.py` (+ `scripts/itcm.py`) |
| Cache | `output/cache/macro.json` |
| Peso en score global | 25% (provisional, 5 cinturones) |
| Barbarismo de riesgo | tecnocrático |

## Encuadre

Marco metodológico: **"Fórmula Paramétrica para Evaluación del Estado de Tensión — Cinturón de la Macroeconomía"** (Fundación CIGOB, mayo 2026; `260602 Parametrica Macro.docx`). Reemplazó en junio 2026 al promedio simple de 11 indicadores (encuadre anterior: Dequino, *Monitor de Sustentabilidad Macroeconómica*).

El cinturón se puntúa con el **ITCM** (Índice de Tensión del Cinturón Macroeconómico), escala 0–100 donde 0 = máxima tensión (cinturón apretado) y 100 = mínima (aflojado). La tensión 0–10 que consume el resto del informe se deriva como `(100 − ITCM) / 10`, así los umbrales globales no cambian: 0–3 estable, 4–6 en tensión, 7–10 tensionado.

### Estructura del ITCM

```
ITCM = 0,35 × (0,5×P_IPC + 0,5×P_REM)
     + 0,30 × (0,6×P_REC + 0,4×P_COM)
     + 0,20 × (0,5×P_RES + 0,5×P_BADLAR)
     + 0,15 × P_EMAE
```

| Dimensión | Peso | Indicadores (peso interno) |
|---|---|---|
| Estabilidad monetaria-inflacionaria | 35% | `ipc_total` (50%) + `rem_ipc_12m` (50%) |
| Viabilidad fiscal-comercial | 30% | `recaudacion` (60%) + `saldo_comercial_12m` (40%) |
| Capacidad de financiamiento | 20% | `reservas_bcra` (50%) + `badlar` (50%) |
| Actividad económica | 15% | `emae_ia` (100%) |

Cada indicador puntúa 0–100 por **tabla de bandas** (sección IV del documento; implementadas en `scripts/itcm.py::BANDAS_ITCM`):

| Indicador | Bandas → puntaje |
|---|---|
| `ipc_total` (% m/m) | ≤1 → 100 · 1–2 → 85 · 2–3 → 65 · 3–5 → 40 · >5 → 10 |
| `rem_ipc_12m` (% anual) | ≤10 → 100 · 10–15 → 85 · 15–20 → 60 · 20–30 → 35 · >30 → 10 |
| `recaudacion` (% m/m) | >10 → 100 · 5–10 → 80 · 0–5 → 60 · −5–0 → 40 · <−5 → 10 |
| `saldo_comercial_12m` (M USD) | >15.000 → 85 · 10–15.000 → 75 · 5–10.000 → 60 · ±5.000 → 50 · −5.000–−15.000 → 30 · <−15.000 → 10 |
| `reservas_bcra` (M USD) | >60.000 → 100 · 50–60.000 → 85 · 40–50.000 → 70 · 30–40.000 → 50 · 20–30.000 → 30 · <20.000 → 10 |
| `badlar` (% anual) | <5 → 100 · 5–10 → 80 · 10–15 → 60 · 15–25 → 35 · >25 → 10 |
| `emae_ia` (% i.a.) | >5 → 100 · 3–5 → 80 · 0–3 → 60 · −2–0 → 40 · −5–−2 → 20 · <−5 → 5 |

Convención de bordes (el doc es ambiguo en los límites exactos): cada banda es `(low, high]` — low exclusivo, high inclusivo — pineada por `tests/test_itcm.py`.

Interpretación del ITCM: 0–20 severamente apretado · 21–40 apretado · 41–60 moderadamente apretado · 61–80 moderadamente aflojado · 81–100 aflojado.

Ante indicadores faltantes los pesos se renormalizan (dentro de la dimensión y, si una dimensión queda vacía, entre dimensiones) — consistente con el "ignorar ausencias" del resto del informe.

### Ajustes sobre la banda

El documento aplica en su ejemplo tres ajustes discrecionales que las tablas no producen (recaudación 80→75, saldo comercial 85→60 "por contracción", EMAE 100→85). El del saldo comercial está **automatizado**; el resto del juicio cualitativo va por override manual.

**Regla automática del saldo comercial** (`itcm.py::ajuste_automatico_saldo`): el colector calcula el saldo como expo − impo de las series ICA y compara los acumulados 12m contra los 12m previos. Si hay superávit con banda > 60, las importaciones **caen**, y esa caída explica más de la mejora del saldo que el aumento de exportaciones (`−Δimpo > max(0, Δexpo)`), el puntaje se ajusta a **60** (el valor del doc), con justificación generada con los números. Si las importaciones crecen —superávit genuino— la regla no opina. Estado jun-2026: NO aplica (expo +14,1% i.a., impo +10,6% i.a.).

**Override manual** en `data/macro/ajustes_itcm.json` (pisa la regla automática), con formato:

```json
{
  "saldo_comercial_12m": {
    "puntaje": 60,
    "justificacion": "Superávit por contracción de importaciones, no por crecimiento exportador",
    "vigente_hasta": "2026-07"
  }
}
```

Un ajuste vencido (`vigente_hasta` < mes corriente) se ignora automáticamente. El output conserva `puntaje_banda` y `puntaje_aplicado`, y la web muestra los ajustes activos con su justificación en la página del cinturón.

### Indicadores de contexto

`tcrm`, `prestamos_privados`, `base_monetaria` y `tc_mayorista` se siguen extrayendo y publicando pero **no integran el ITCM** (`en_indice: false`): la paramétrica no los contempla. Quedan como lectura de contexto.

## Indicadores activos

| Indicador | Qué mide | Fuente | Frecuencia | Estado |
|---|---|---|---|---|
| `ipc_total` | Inflación mensual del IPC nacional | INDEC | Mensual | Automático |
| `reservas_bcra` | Reservas internacionales brutas del BCRA (M USD) | BCRA | Diaria | Automático |
| `badlar` | Tasa para depósitos bancarios mayoristas (% anual) | BCRA | Diaria | Automático |
| `emae_ia` | Variación interanual de la actividad económica | INDEC | Mensual | Automático |
| `saldo_comercial_12m` | Balance exportaciones − importaciones acumulado 12m (M USD) | INDEC | Mensual | Automático |
| `recaudacion` | Variación mensual de la recaudación tributaria total | INDEC/AFIP | Mensual | Automático |
| `tcrm` | Tipo de cambio real multilateral (base 2010=100) | INDEC | Mensual | Automático |
| `rem_ipc_12m` | Expectativas de inflación a 12 meses (mediana REM) | BCRA | Mensual | Automático |
| `prestamos_privados` | Variación mensual del crédito bancario al sector privado | BCRA | Diaria | Automático |
| `base_monetaria` | Variación mensual de la base monetaria | BCRA | Diaria | Automático |
| `tc_mayorista` | Variación mensual del tipo de cambio oficial mayorista | BCRA | Diaria | Automático |

Score actual del cinturón: **2.9 (estable)** — ITCM **71.2 (moderadamente aflojado)**. Última ejecución: 10 de junio de 2026, 11 de 11 indicadores frescos.

## Detalle por indicador

### `ipc_total` — Inflación mensual

- Fuente: `GET https://apis.datos.gob.ar/series/api/series/?ids=148.3_INIVELNAL_DICI_M_26&format=json&limit=2&sort=desc`
- Cálculo: variación porcentual mensual = `(actual / anterior − 1) × 100`.
- Puntaje ITCM: por bandas (≤1 → 100 · 1–2 → 85 · 2–3 → 65 · 3–5 → 40 · >5 → 10). Pesa 50% de la dimensión estabilidad monetaria (17,5% del índice).
- Último valor: 3.38% (marzo 2026).

### `reservas_bcra` — Reservas internacionales brutas

- Fuente: `GET https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/1`
- Cálculo: último valor disponible en millones USD. La API devuelve datos en orden descendente; `detalle[0]` es el dato más reciente.
- Puntaje ITCM: por bandas (>60.000 → 100 · 50–60k → 85 · 40–50k → 70 · 30–40k → 50 · 20–30k → 30 · <20k → 10). Pesa 50% de la dimensión financiamiento (10% del índice).
- Último valor: 46.585 millones USD (mayo 2026).

### `badlar` — Tasa BADLAR bancos privados

- Fuente: `GET https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/7`
- Cálculo: último valor disponible (porcentaje anual).
- Puntaje ITCM: por bandas (<5 → 100 · 5–10 → 80 · 10–15 → 60 · 15–25 → 35 · >25 → 10). Pesa 50% de la dimensión financiamiento (10% del índice).
- Último valor: 22.0% (mayo 2026).

### `emae_ia` — EMAE variación interanual

- Fuente: `GET https://apis.datos.gob.ar/series/api/series/?ids=143.3_ICE_SERVIA_2004_A_25&format=json&limit=2&sort=desc`
- Cálculo: valor directo en decimal multiplicado por 100. Por ejemplo, 0.0188 equivale a 1.88% i.a.
- Puntaje ITCM: por bandas (>5 → 100 · 3–5 → 80 · 0–3 → 60 · −2–0 → 40 · −5–−2 → 20 · <−5 → 5). Única variable de la dimensión actividad (15% del índice).
- Nota técnica: las series `143.1_*` son anuales, `143.2_*` son trimestrales, `143.3_*` son mensuales.
- Último valor: +1.88% i.a. (enero 2026).

### `saldo_comercial_12m` — Balance comercial acumulado 12 meses

- Fuente primaria: series ICA `74.3_IET_0_M_16` (expo totales) y `74.3_IIT_0_M_25` (impo totales), `limit=26`, alineadas por fecha. Saldo 12m = Σexpo − Σimpo de los últimos 12 meses comunes.
- Composición para la regla automática: el indicador expone `expo_12m`, `impo_12m`, `expo_var_ia`, `impo_var_ia`, `expo_delta_12m`, `impo_delta_12m` (acumulado 12m vs 12m previos).
- Fallback: serie de saldo directa `164.3_SOTALTAL_0_0_8` (≈14 meses de rezago observado en jun-2026; sin composición → la regla automática no opina).
- Puntaje ITCM: por bandas (>15.000 → 85 · 10–15k → 75 · 5–10k → 60 · ±5k → 50 · −5/−15k → 30 · <−15k → 10), con la regla automática de ajuste por contracción (ver "Ajustes sobre la banda"). Pesa 40% de la dimensión fiscal-comercial (12% del índice).
- Nota: el acumulado 12 meses elimina estacionalidad energética y sojera.
- Último valor: +18.322 millones USD (12 meses hasta abril 2026); expo +14,1% i.a., impo +10,6% i.a. → ajuste no aplicado.

### `recaudacion` — Recaudación tributaria total

- Fuente: `GET https://apis.datos.gob.ar/series/api/series/?ids=172.3_TL_RECAION_M_0_0_17&format=json&limit=2&sort=desc`
- Cálculo: variación porcentual mensual nominal.
- Puntaje ITCM: por bandas (>10 → 100 · 5–10 → 80 · 0–5 → 60 · −5–0 → 40 · <−5 → 10). Pesa 60% de la dimensión fiscal-comercial (18% del índice).
- Nota: tiene ruido estacional (enero presenta grandes vencimientos). Considerar migrar a variación interanual en futura versión.
- Último valor: −0.99% var. m (marzo 2026).

### `tcrm` — Tipo de cambio real multilateral

- Fuente: `GET https://apis.datos.gob.ar/series/api/series/?ids=116.3_TCRMA_0_M_36&format=json&limit=2&sort=desc`
- Cálculo: último valor índice (base 2010=100).
- Rol: **contexto** — no integra el ITCM (`en_indice: false`).
- Nota: rezago de 2-3 meses en INDEC.
- Último valor: 79.77 (diciembre 2024).

### `rem_ipc_12m` — Expectativas de inflación a 12 meses

- Fuente: `GET https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/29`
- Cálculo: mediana de expectativas de variación interanual del IPC a 12 meses (porcentaje anual).
- Puntaje ITCM: por bandas (≤10 → 100 · 10–15 → 85 · 15–20 → 60 · 20–30 → 35 · >30 → 10). Pesa 50% de la dimensión estabilidad monetaria (17,5% del índice).
- Último valor: 24.2% anual (abril 2026).

### `prestamos_privados` — Préstamos sector privado

- Fuente: `GET https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/26?desde=YYYY-MM-DD`
- Cálculo: variación porcentual mensual nominal (último valor vs. valor de hace 30 días).
- Rol: **contexto** — no integra el ITCM (`en_indice: false`).
- Último valor: +2.13% var. m (mayo 2026).

### `base_monetaria` — Base monetaria

- Fuente: `GET https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/15?desde=YYYY-MM-DD`
- Cálculo: variación porcentual mensual nominal.
- Rol: **contexto** — no integra el ITCM (`en_indice: false`).
- Último valor: +0.7% var. m (mayo 2026).

### `tc_mayorista` — Tipo de cambio mayorista

- Fuente: `GET https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/5?desde=YYYY-MM-DD`
- Cálculo: variación porcentual mensual.
- Rol: **contexto** — no integra el ITCM (`en_indice: false`).
- Último valor: −0.27% var. m (mayo 2026).

## Ejecución

```bash
cd projects/informe_coyuntura
python scripts/macro.py
```

Códigos de salida:

| Código | Significado |
|---|---|
| 0 | Todos los indicadores frescos (11/11) |
| 1 | Al menos uno fresco (algunos fallaron, usó cache) |
| 2 | Ningún indicador fresco (todo desde cache) |

## Notas de mantenimiento

- El BCRA requiere `verify=False` y `urllib3.disable_warnings()` por la configuración SSL del servidor.
- Los datos del BCRA vienen en orden descendente: `detalle[0]` es el dato más reciente; no usar `detalle[-1]`.
- Para series INDEC, los prefijos indican frecuencia: `143.3_*` mensual, `143.2_*` trimestral, `143.1_*` anual.
- Si INDEC reasigna alguna serie, buscar en `https://apis.datos.gob.ar/series/api/search/?q=<nombre>&limit=5&format=json`.
- Si BCRA migra la versión de la API (v4.0 a v5.0), actualizar `BCRA_VARIABLES_BASE` en `macro.py`.
