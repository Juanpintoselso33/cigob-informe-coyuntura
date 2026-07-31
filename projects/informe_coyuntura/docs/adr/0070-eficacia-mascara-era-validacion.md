---
madr: 4
id: '0070'
estado: 'aceptado'
fecha: 2026-07-16
cinturon: 'politica'
indicadores: [eficacia_legislativa]
archivos: ['validacion_externa.py']
relacionado: ['0061', '0069']
ambito: 'Validación externa del ITCP (`validacion_externa.py`) · `eficacia_legislativa` (solo la serie reconstruida; la card no se toca)'
---

# ADR-0070 — máscara de era para eficacia_legislativa en la reconstrucción del ITCP

## Contexto y planteo del problema

La revisión de la correlación ITCP↔EPU (2026-07-16) localizó el descalce en
2024: r=−0,03 en ese año contra −0,74 en 2025. Al descomponer la
reconstrucción mes a mes apareció un artefacto de transición de gestión en
`eficacia_legislativa`: con cohorte madura de 12-24 meses (ADR-0061), el
valor de CADA mes de 2024 mide expedientes PE publicados en 2022-2023 — es
decir, **la cartera de la gestión anterior muriendo con el cambio de
congreso**, no la eficacia de esta gestión. El puntaje reconstruido caía de
74 (feb-2024) a 26 (sep-2024) por esa vía, arrastrando la dimensión Poder
legislativo en un año en que el dato no hablaba de este gobierno. La
cohorte recién es 100% de la era actual cuando t−730d ≥ 10-dic-2023, o sea
desde **diciembre de 2025**.

Se probaron alternativas de rediseño del indicador (madurez de 4 meses,
cohorte acumulada de la gestión) contra el par EPU: ninguna arregla el r de
2024 (el EPU fue una serie plana ese año — desvío 10 sobre media 85 — y no
hay recomposición que correlacione contra una serie sin varianza), la
madurez corta reintroduce el sesgo que ADR-0061 eliminó, y cambiar la
metodología de la card duplicaría su valor actual sin revisión editorial.

## Opciones consideradas

- Rediseñar el indicador (madurez 4m / cohorte acumulada desde dic-2023)
- No hacer nada (documentar y dejar la serie como estaba)
- Enmascarar solo los meses de cohorte 100% pre-gestión (ene→nov-2024)

## Decisión

En `construir_serie_itcp` (solo la reconstrucción de validación),
`eficacia_legislativa` se excluye de los meses **anteriores a dic-2025**
(constante `EFICACIA_COHORTE_100PCT_MILEI_DESDE`); el motor renormaliza la
dimensión entre los presentes, igual que con cualquier faltante.

El criterio es **a priori** — composición de la cohorte, la misma doctrina
que ya excluye dic-2023 de toda la reconstrucción ("los componentes de
ventana anual que prenden ese mes describen el año 2023 completo de la
gestión anterior") — y no una calibración contra el benchmark: los meses de
cohorte mixta (dic-2024 → nov-2025) también quedan afuera porque siguen
ponderados mayormente por expedientes pre-gestión, aunque un corte más laxo
diera una correlación parecida. La card publicada no cambia: su cohorte
actual ya es 100% de esta gestión.

### Consecuencias

- La reconstrucción del ITCP usa eficacia solo desde dic-2025 (7 de los ~30
  meses); antes, la dimensión Poder legislativo se reparte entre ratio_dnu,
  derrotas, veto_quorum y — desde ADR-0069 — bloqueo_sostenido, que sí
  miden 2024.
- La correlación publicada ITCP↔EPU mejora por remoción de artefacto (no
  por recalibración): el registro del cambio queda en este ADR y el
  docstring de `construir_serie_itcp`.
- El r anual de 2024 sigue ≈0 y está bien que así sea: el EPU no tuvo
  varianza ese año (la incertidumbre de política económica en prensa se
  planchó con la desinflación mientras el capital legislativo se erosionaba
  — divergencia real de constructos, documentada acá para no re-diagnosticarla
  como bug).
- Pendiente declarado: mostrar al editor junto con ADR-0069; si algún día
  se rediseña la cohorte del indicador (variante acumulada), esta máscara
  se vuelve innecesaria y se retira.

## Pros y contras de las opciones

### Rediseñar el indicador (madurez 4m / cohorte acumulada desde dic-2023)

Rechazada por ahora: mueve el valor de la card publicada (22,2% → 38-45%
según variante) y las anclas de ADR-0061 sin pasar por el editor; la
madurez de 4 meses además reintroduce estructuralmente el sesgo de
inmadurez (el defecto de ADR-0050). Si el editor quiere un indicador que
mida la eficacia de la gestión también en su primer año, la variante
honesta es la cohorte acumulada de la era con madurez corta — queda
documentada en la exploración de este ADR para esa conversación.

### No hacer nada (documentar y dejar la serie como estaba)

Rechazada: la serie reconstruida alimenta la validación publicada en el
snapshot (r ITCP↔EPU) y el artefacto deprime esa correlación en toda la
muestra (−0,45 → −0,57 al enmascarar, −0,60 junto con ADR-0069): publicar
un número de validación sabidamente contaminado por un artefacto
identificado no es neutralidad, es ruido conocido sin corregir.

### Enmascarar solo los meses de cohorte 100% pre-gestión (ene→nov-2024)

Rechazada: deja adentro los meses de cohorte mixta, que siguen dominados
por expedientes de la gestión anterior; el corte "100% de la era" es el
único punto no arbitrario de la transición.

## Más información

### Precedentes directos

ADR-0061 (cohorte madura 12-24m) · la exclusión de dic-2023 de la reconstrucción (2026-07-09, documentada en el docstring de `construir_serie_itcp`) · ADR-0069 (mismo diagnóstico, la pata constructiva)
