---
madr: 4
id: '0024'
estado: 'aceptado'
fecha: 2026-07-03
cinturon: 'vida'
relacionado: ['0224']
complementado_por: ['0223']
---

# ADR-0024 — Motos por acumulado móvil de 12 meses (auditoría de estacionalidad)

## Contexto y planteo del problema

Pregunta del editor: ¿hay series que habría que desestacionalizar? La
auditoría concluyó que el diseño ya cubre la estacionalidad **por
construcción** en casi todos los componentes, por tres vías:

1. **Comparaciones interanuales** (mismo mes vs mismo mes): recaudación i.a.
   real, EMAE i.a., crédito real i.a., IDM, IAI/ICIP, litigiosidad 12m-vs-12m.
2. **Ventanas de 12 meses**: saldo comercial 12m, protestas 12m, eficacia
   legislativa 12m, y la carne (CICCRA publica el per cápita ANUALIZADO).
3. **Series desestacionalizadas en la fuente**: ISAC/cemento, EMAE.

**La excepción real: patentamiento de motos.** Flujo mensual crudo (último
mes completo, CAFAM) rebaseado contra el promedio fijo del 4T-2023. La
estacionalidad es fuerte (enero ≈ 2× junio: 60-69 mil vs 33-48 mil), así que
el componente medía calendario además de poder de compra. Medido: el índice
de jun-2026 daba 175,9 crudo vs 166,7 desestacionalizado (~9 puntos de
distorsión estacional).

Exposiciones menores aceptadas (no se tocan): pluriempleo/informalidad (EPH
trimestral vs base fija — sesgo chico), brecha salario/CBT y alimentos (leve
estacionalidad de la canasta; el doc diseñó estos componentes en niveles).

## Opciones consideradas

- **Acumulado móvil de 12 meses para motos** — elegida.
- **Desestacionalizar las series** — evaluado y no hace falta en casi todos los componentes: el diseño ya cubre la estacionalidad por construcción, vía comparaciones interanuales, acumulados de 12 meses y ventanas móviles.

## Decisión

El componente motos del ITVC se rebasea por **acumulado móvil de 12 meses**:
promedio de los últimos 12 meses vs el promedio de las ventanas móviles que
terminan en oct/nov/dic-2023 (la traducción fiel de la base 4T-2023 a una
métrica anualizada — la misma lógica que ya usa la carne). La serie CAFAM se
extendió a nov-2022 para que las ventanas base estén completas. La ventana
exige 12 meses CONSECUTIVOS (sin huecos); si la serie no alcanza, cae al
rebase simple y luego al baseline documentado (cadena de fallbacks
existente). La card del indicador sigue mostrando el flujo mensual crudo
(el dato real); solo cambia la transformación con que entra al índice.

### Consecuencias

- Estado 2026-07-03: motos 175,9 → **166,7** · dimensión confianza 105,3 →
  104,4 · **ITVC 92,1 → 92,0** (tensión 6,6 sin cambio). El componente deja
  de oscilar con el calendario: sube solo si la tendencia anualizada sube.
- `validacion_externa.py` aplica la misma transformación al reconstruir la
  serie mensual del ITVC (consistencia entre el índice vivo y el estudio).
- Sin cambios en el resto de los componentes: la auditoría queda documentada
  acá como referencia de por qué NO se desestacionalizan (ya lo están por
  construcción).
