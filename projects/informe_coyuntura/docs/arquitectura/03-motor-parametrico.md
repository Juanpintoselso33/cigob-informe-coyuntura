# 03 — Motor paramétrico y robustez

## El motor común: `parametrica.py`

Los dos índices con bandas (ITCM, ITCG) comparten el motor de **puntaje
interpolado entre anclas** (ADR-0021): cada indicador define bandas
`(low, high, puntaje)`; el ancla de una banda finita es su punto medio, el de
una banda abierta su borde; entre anclas se interpola linealmente y en los
extremos es plano. Elimina los saltos de escalón del scoring por banda.

`interpolacion_sombra.py` publica el contraste escalón-vs-interpolado que
respaldó esa decisión.

## Los tres índices

### ITCM — `itcm.py` (macro)
- 6 dimensiones (pesos 26/24/16/11/11/12), 12 indicadores puntuables.
- Financiamiento interno 45/40/15 con crédito real (ADR-0022); IdC por
  z-scores de nivel vs historia 2017→ (ADR-0028).
- 4 indicadores nominales ocultos del snapshot pero vivos como insumos.

### ITCG — `itcg.py` (gestión)
- 0-100 de avance de la transformación; apertura = alícuota efectiva,
  litigiosidad al índice 70/30 (ADR-0013/0023).
- Overrides del analista en `data/gestion/ajustes_itcg.json`.

### ITVC-B100 — `itvc.py` + `publicar._itvc_indices` (vida)
- **Sin bandas**: cada componente es su serie rebaseada a 100 = promedio
  4T-2023 (`_itvc_rebase_de_serie`); trimestrales resuelven a 2023-10; motos
  usa acumulado móvil 12m (ADR-0024).
- **Bases declaradas**: si la fuente no midió el 4T-2023, se declara otra
  base (IVI: ene-2024, ADR-0032). Registro central: `base_meses` en el rebase.
- **Winsorización asimétrica (ADR-0033)**: techo 140 por componente (un boom
  no compra compensación ilimitada); **sin piso** — las crisis se señalizan,
  no se recortan.
- Agregación 35/25/10/15/15 con renormalización ante faltantes (dentro de la
  dimensión y entre dimensiones). Confianza: ICC 45 / IVI 30 / sentimiento 10
  / carne 10 / motos 5 (ADR-0034).
- Tensión = 5 − (ITVC − 100) × 0,2, acotada 0-10.

## La batería de robustez (tres pilares, ADR-0019/0020/0031)

Todo corre automáticamente en cada `publicar` o en el pipeline nocturno:

### 1. Monte Carlo — `sensibilidad.py`
Perturba pesos (±20% relativo) e insumos (±5% **del ancho entre anclas** —
scale-free, no multiplicativo) con semilla fija; publica p05-p95 por índice.
Un test verifica que el valor puntual cae dentro del rango.

### 2. Dimensión crítica — flag ADR-0020
Una dimensión bajo el umbral crítico se marca en el snapshot y la web la
señaliza ("el promedio del índice no la compensa"). Hoy: vulnerabilidad
financiera (endeudamiento real×mora).

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

40 tests de pytest sin red: `test_itcm.py` (bandas, interpolación, ejemplo
completo al decimal), `test_itcg.py`, `test_itvc.py` (pesos del doc +
enmiendas ADR, renormalización, ajustes), `test_publicar.py` (reconciliación
del snapshot publicado: suma ponderada = índice, robustez encierra el valor,
tensión = fórmula). Cuando un ADR cambia el motor, los valores esperados se
recalibran **con el engine**, nunca a mano.
