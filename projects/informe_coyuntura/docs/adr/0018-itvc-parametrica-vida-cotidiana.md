---
madr: 4
id: '0018'
estado: 'aceptado'
fecha: 2026-07-03
cinturon: 'vida'
relacionado: ['0067', '0190', '0212', '0215', '0217', '0218', '0223', '0224']
origen: 'doc "ITVC — versión base 100" (Fundación CIGOB, 260702, `docs/260702 vida cotidiana finakl.docx`)'
---

# ADR-0018 — ITVC-B100: paramétrica base 100 del cinturón de Vida Cotidiana

## Contexto y planteo del problema

Vida cotidiana se puntuaba con fórmulas de tensión ancladas por indicador
(SCORING en `publicar.py`) promediadas en partes iguales. El doc 260702
reformula el cinturón como **índice de seguimiento de gestión**: no mide un
nivel absoluto "bueno/malo" sino la **mejora o deterioro acumulado desde el
arranque del mandato**. Mantiene las 5 dimensiones, los 12 indicadores y los
pesos del diseño original (35/25/10/15/15); cambia solo el método de
puntuación.

## Opciones consideradas

- **Rebase a 100 = promedio del 4T-2023** — elegida.
- **Diciembre puntual como base** — descartada: el promedio del trimestre amortigua el traspaso a precios de la devaluación de fin de 2023.
- **Bases constantes** — descartadas salvo carne, delitos y el fallback de motos: se calculan dinámicamente de la propia serie (ADR-0001).

## Decisión

1. **Rebase a 100 = promedio del 4T-2023** (oct-nov-dic, no diciembre puntual,
   para amortiguar el traspaso a precios de la devaluación de fin de 2023).
   Componentes "más alto = mejor": `I = V_t/V_base × 100`; "más alto = peor":
   `I = V_base/V_t × 100`. Las bases se calculan **dinámicamente de la propia
   serie** (ADR-0001); solo carne, delitos y el fallback de motos usan
   constantes documentadas en `data/vida/itvc_baselines.json` (con fuente).
2. **ITVC-B100 = promedio ponderado directo** de los 12 índices
   (`scripts/itvc.py`, misma renormalización ante faltantes y overrides
   `data/vida/ajustes_itvc.json` que ITCM/ITCG, pero sin bandas por
   componente: los índices entran continuos). Escala del doc: >110 mejora
   sustancial · 105-110 moderada · 95-105 sin cambios · 85-95 deterioro
   moderado · <85 deterioro sustancial.
3. **Tensión 0-10 = 5 − (ITVC − 100) × 0,2**, topeada a [0, 10] (decisión del
   editor, jul-2026): mapeo lineal que calza exacto con la escala del doc
   (110→3 · 105→4 · 100→5 · 95→6 · 85→8). El score del cinturón y el aporte
   por componente usan el mismo mapeo.
4. **Tasas → niveles** (corrección del doc): alimentos y tarifas puntúan por el
   NIVEL del IPC de la división **relativo al RIPTE** (¿los precios suben más
   o menos que los salarios?); IPI e ISAC por su **nivel desestacionalizado**
   rebaseado (`453.1_SERIE_DESEADA_0_0_24_58` y `33.2_ISAC_SIN_EDAD_0_M_23_56`
   — la serie original del ISAC tiene un desplome estacional en dic-23 que
   contaminaría la base). Las cards siguen mostrando la métrica legible
   (variación m/m, stock); el índice usa la transformación (precedente:
   REM equivalente mensual, ADR-0002).
5. **Endeudamiento con polaridad empírica** (corrección del doc): 
   `I_EC = 100 × (Deuda_real_t/Deuda_real_base) × (Mora_base/Mora_t)`, con
   deuda Y mora del **mismo corte "2. Familias"** del anexo del Informe sobre
   Bancos del BCRA (`InfBanc_Anexo.xlsx`, hoja "Calidad de Cartera (por
   líneas)", personales + tarjetas, mensual 2010→, URL fija, rezago ~2 meses).
   Mora ponderada por saldos. Deflactor: IPC nivel nacional. Más deuda con
   mora estable = acceso al crédito (sube); con mora disparada =
   sobreendeudamiento por necesidad (cae).

### Consecuencias

- Con datos de jul-2026: **ITVC = 92,0 → deterioro moderado → tensión 6,6**
  (antes 3,5 con el promedio de fórmulas ancladas). El driver dominante es
  I_EC = 31,7 (mora de familias ×5,5 desde la base); lo compensan ingresos
  107,4 y motos 175,9. El score global sube ~0,8 puntos.
- `recomputar_vida_y_global()` ya no promedia aportes: el score de vida sale
  del ITVC y el global se repondera igual que antes.
- Tests: `tests/test_itvc.py` (módulo) + reconciliación publicada en
  `tests/test_publicar.py`.

## Más información

### Mapeo componente → indicador

| Doc | Clave | Índice | Fuente de la base |
|---|---|---|---|
| I_SRC salario/CBT (22,75%) | brecha_salario_cbt | rebase serie RIPTE/CBT | dinámica |
| I_IFL informalidad (12,25%) | informalidad | invertido, serie ANUAL 52.1 | dinámica (base = año 2023) |
| I_IA alimentos (10%) | ipc_alimentos | serie `itvc_alimentos` (nivel vs RIPTE) | dinámica |
| I_PT tarifas (15%) | peso_tarifas | serie `itvc_tarifas` (regulados vs RIPTE) | dinámica |
| I_EC endeudamiento (10%) | endeudamiento_familiar | serie `itvc_endeudamiento` (real × mora) | dinámica |
| I_IPI industria (6,75%) | mortalidad_pymes | serie `itvc_ipi` (nivel desest.) | dinámica |
| I_ISC construcción (6%) | despacho_cemento | serie `itvc_isac` (nivel desest.) | dinámica |
| I_SD subocupación (2,25%) | pluriempleo | invertido, serie 47.2 trimestral | dinámica (4T-2023 = un punto) |
| I_ICC confianza (7,5%) | icc_utdt | rebase serie XLS UTDT | dinámica |
| I_HD delitos (4,5%) | inseguridad | invertido, constante | SNIC 2023 = 2.435.858 |
| I_CC carne (1,5%) | consumo_carne | constante | CICCRA 4T-2023 = 53,17 kg |
| I_PM motos (1,5%) | patentamiento_motos | rebase serie CAFAM (histórico mensual) | dinámica (fallback 39.268) |

Contexto (no puntúa): `sentimiento_digital` (ventana Trends de 3 meses, sin
línea base 2023 posible).

### Excepciones y limitaciones declaradas

- **Informalidad**: la serie trimestral pública (303.1) murió en 1T-2020; se
  usa la ANUAL (52.1) con base = año 2023 — actualiza una vez al año.
- **SNIC**: anual con ~1 año de rezago; base anual 2023 (excepción prevista en
  el doc, IV.2.1). El criterio de suma del colector duplica categorías padre y
  subcategorías (~+22% vs el total oficial 1.985.767); numerador y denominador
  usan el MISMO criterio, así el ratio es consistente. El CSV oficial se
  revisa retroactivamente (2024 ya no es 2.501.057 sino 2.542.456).
- **Carne**: CICCRA publica promedio móvil 12m; base = foto provisoria
  contemporánea del 4T-2023 (53,17; el dato revisado es ~52,4).
- **Motos**: el valor corriente es un mes puntual con estacionalidad; la mejora
  pendiente es promediar 12 meses en numerador y base.
- **I_EC**: rezago ~2 meses (Informe sobre Bancos). Si el BCRA discontinúa la
  mora por línea, volver transitoriamente a deuda real sin corrección y
  declararlo (doc IV.2.3).

### Addendum — sweep del mismo día (2026-07-03)

- **SNIC revivido**: el CSV oficial cambió a separador `;` (por eso el parser
  del colector estaba muerto desde 2026); ahora se detecta el separador. Trae
  **2025 completo** (2.418.600) → I_HD = 100,7 con serie anual 2014→2025
  (`fetch_inseguridad_serie`, mismo criterio de suma).
- **Carne con serie real**: `fetch_carne_serie` parsea los informes mensuales
  de CICCRA (PM-12m) desde oct-2023 con caché por mes en
  `data/vida/carne_serie.json` (los de 2023 usan sufijo "b"; se agregó el
  patrón "NN,N kg/hab" al parser del colector). La base dinámica de la serie
  (53,2/53,4/52,9) reproduce la constante documentada; carne e inseguridad
  pasaron a rebase dinámico (constantes quedan de fallback).
- **Cemento/ISAC**: el modal caía por alias a la serie `isac_construccion`
  (insumo cemento 33.4, otra métrica); ahora `despacho_cemento` tiene serie
  propia = ISAC nivel desestacionalizado (la métrica de la card), y el label
  pasó a "Construcción (ISAC)". Ficha de informalidad corregida a frecuencia
  anual.
