# 03 — Motor paramétrico y robustez

## El motor común: `parametrica.py`

Los tres índices con bandas (ITCM, ITCG, ITCP) comparten el motor de **puntaje
interpolado entre anclas** (ADR-0021): cada indicador define bandas
`(low, high, puntaje)`; el ancla de una banda finita es su punto medio, el de
una banda abierta su borde; entre anclas se interpola linealmente y en los
extremos es plano. Elimina los saltos de escalón del scoring por banda.

`interpolacion_sombra.py` publica el contraste escalón-vs-interpolado que
respaldó esa decisión.

## Los cuatro índices

### ITCM — `itcm.py` (macro)
- 6 dimensiones (pesos 26/24/16/11/11/12), 17 indicadores puntuables.
- Estabilidad monetaria 40/25/25/10: IPC, REM, IDM y
  `presion_dolarizacion` (ADR-0053/0055). El cuarto componente mide una presión
  latente 0-100 con observable por régimen: promedio móvil contiguo de 3 meses
  de la brecha CCL/A3500 antes de abril de 2025; desde entonces, compras netas
  de Personas Humanas divididas por M2 privado en USD, con transición 1/2/3
  meses y suma de numeradores y denominadores. Una segunda interpolación común
  convierte presión 0/25/50/75/100 en puntaje ITCM 100/85/60/35/10.
- Financiamiento interno 45/40/15 con crédito real (ADR-0022); IdC por
  z-scores de nivel vs historia 2017→ (ADR-0028).
- 4 indicadores nominales ocultos del snapshot pero vivos como insumos.

### ITCG — `itcg.py` (gestión)
- 0-100 de avance de la transformación; 5 dimensiones (pesos 35/25/15/15/10).
- Apertura = alícuota efectiva, litigiosidad al índice 70/30 (ADR-0013/0023).
- Overrides del analista en `data/gestion/ajustes_itcg.json`.

### ITCP — `itcp.py` (política)
- 7 dimensiones con bandas por indicador (ADR-0036), mismo motor de anclas.
  El cinturón dejó de puntuarse con score directo.

### ITVC-B100 — `itvc.py` + `publicar._itvc_indices` (vida)
- **Sin bandas**: cada componente es su serie rebaseada a 100 = promedio
  4T-2023 (`_itvc_rebase_de_serie`); trimestrales resuelven a 2023-10; la
  motorización (autos + motos per cápita, ADR-0224) usa móvil 12m.
- **Bases declaradas**: si la fuente no midió el 4T-2023, se declara otra
  base (IVI: ene-2024, ADR-0032). Registro central: `base_meses` en el rebase.
- **Winsorización asimétrica (ADR-0033)**: techo 140 por componente (un boom
  no compra compensación ilimitada); **sin piso** — las crisis se señalizan,
  no se recortan. El recorte viaja al snapshot (`indice_itvc_crudo`,
  `recorte_itvc`) para que la nota del modal lo declare. `WINSOR_EXENTOS`
  exime componentes puntuales con el motivo medido en el propio módulo
  (hoy `motorizacion_total`, ADR-0224); cuando un exento pasa de 140 el
  snapshot lo marca con `winsor_exento`.
- Agregación por 6 dimensiones (ingresos 28,06 / precios 25 / empleo 24,19 /
  vulnerabilidad 10 / percepción 8,25 / seguridad 4,5) con renormalización
  ante faltantes, dentro de la dimensión y entre dimensiones. Los pesos
  nominales de dimensión no se tocan en un alta: el que entra cede de los
  internos (`alta_proporcional`).
- Tensión = 5 − (ITVC − 100) × 0,2, acotada 0-10.

## La batería de robustez (tres pilares, ADR-0019/0020/0031)

La robustez compacta se calcula dentro de `publicar.py` para cada snapshot; el
pipeline nocturno regenera además el informe ampliado y la validación externa.

### 1. Monte Carlo — `sensibilidad.py`
Perturba pesos (±20% relativo) e insumos (±5% **del ancho entre anclas** —
scale-free, no multiplicativo) con semilla fija. Hay dos productos coordinados:

- `robustez_compacta()` ejecuta **1.000 simulaciones** durante `publicar.py` y
  embebe p05-p95, mediana y probabilidad de zona en `web/src/data/informe.json`.
- `analizar_bloque()` ejecuta **2.000 simulaciones** después de publicar y
  escribe el análisis ampliado, incluido leave-one-out, en
  `output/sensibilidad.json`.

Un test verifica que el valor puntual cae dentro del rango.

### 2. Dimensión crítica — flag ADR-0020
Una dimensión bajo el umbral crítico se marca en el snapshot y la web la
señaliza ("el promedio del índice no la compensa"). Hoy: vulnerabilidad
financiera (mora materializada 70% y carga del servicio de deuda 30%,
ADR-0232).

### 3. Validación externa — `validacion_externa.py`
Reconstruye las series históricas de los tres índices y las contrasta con
anclas externas que NO alimentan al índice:

| Índice | Par propio | Contrastes cruzados |
|---|---|---|
| ITCM | riesgo país (EMBI, ArgentinaDatos) | Merval USD, ICC |
| ITCG | Merval en USD (Yahoo ^MERV / CCL) | riesgo país, ICG |
| ITVC | ICC UTDT (test también sin-ICC por circularidad) | riesgo país, Merval |

Publica niveles, **primeras diferencias** (la prueba anti-tendencia: en ~30
meses de una sola normalización los niveles correlacionan "gratis") y
lead-lag (resultado documentado: los índices son coincidentes, no
anticipan). `publicar._validacion_cruzada` arma la matriz 3×3 discriminante
que se ve en la web.

> **⚠️ Mantenimiento crítico**: `validacion_externa.py` REPLICA la
> construcción del ITVC (mapa `COMPONENTES`, `BASES_PROPIAS`, `ITVC_TECHO`).
> Cada ADR que toque métricas del ITVC debe actualizar esa réplica — el
> 04-jul-2026 quedó desalineada en silencio y la matriz publicó el índice
> viejo hasta que una pregunta del editor lo destapó.

## Tests — `tests/`

La suite pytest sin red cubre bandas, interpolación y ejemplos completos de
ITCM/ITCG/ITVC; contratos de fuentes; series; y reconciliación del snapshot
publicado (suma ponderada = índice, robustez encierra el valor, tensión =
fórmula). Cuando un ADR cambia el motor, los valores esperados se recalibran
**con el engine**, nunca a mano.
