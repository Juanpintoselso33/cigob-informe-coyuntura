# ADR-0056 — Suavizado del ajuste automático de saldo comercial por composición expo/impo

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-15 |
| **Ámbito** | Cinturón macro · ITCM · `saldo_comercial_12m` · Subcomponente D |
| **Precedentes directos** | ADR-0019 (estudio sombra: los escalones duplicaban la incertidumbre) · ADR-0021 (interpolación sin acantilados) |

## Contexto

El "Subcomponente D" de la Paramétrica CIGOB (mayo 2026) advierte que un
superávit comercial puede reflejar una contracción de la demanda interna
(menos importaciones) en lugar de una mejora exportadora genuina, y que ese
caso debe penalizarse. La implementación original (`ajuste_automatico_saldo`,
`scripts/itcm.py`) traducía esto en una regla binaria: si el superávit era
relevante (>5.000 M USD, banda >60) y la caída de importaciones explicaba más
la mejora del saldo que el aumento de exportaciones, el puntaje se forzaba a
exactamente 60 — el valor del ejemplo del documento fuente (superávit 2024/25).

Esta regla es un acantilado de umbral: un caso apenas por encima de la
condición (la caída de M explica, digamos, 51% de la mejora) recibía el mismo
castigo que un caso extremo (95% explicado por caída de M, superávit
enteramente "defensivo"). Esto contradice la filosofía de interpolación sin
acantilados que el ADR-0021 estableció para el resto del ITCM/ITCG, justamente
porque el estudio sombra del ADR-0019 midió que los escalones de umbral
duplicaban la incertidumbre del índice y truncaban hasta ±13 puntos por
componente.

Además, el gate de activación usaba `puntaje_banda` (el escalonado histórico)
para decidir si el superávit era "relevante" (banda > 60), mientras que el
puntaje que efectivamente entra al índice usa `puntaje_interpolado`
(`parametrica.calcular_indice`). Esa discrepancia dejaba casos límite sin
evaluar: un valor con puntaje interpolado de 61,5 (banda escalonada = 60) no
activaba la regla aunque la mejora del saldo fuera 100% atribuible a la caída
de importaciones.

El contexto de negocio es activo: la prensa económica argentina (Cronista,
feb-2026; Infobae/Ecolatina/BTG, jun-2026) viene documentando exactamente este
patrón para 2026 — superávit comercial histórico con caída de importaciones de
bienes de capital e insumos por demanda interna débil, bajo el marco
"superávit defensivo" (por contracción) vs. "superávit ofensivo" (por
productividad/diversificación exportadora).

## Decisión

Reemplazar el "todo o nada" por una interpolación continua que preserva el
mismo piso de 60 puntos del documento fuente como caso límite, sin acantilado
intermedio.

### 1. Descomponer la mejora del saldo en dos aportes no negativos

Sobre los acumulados 12m vs. los 12m previos que ya produce
`fetch_saldo_comercial_12m` (`expo_delta_12m`, `impo_delta_12m`):

```text
mejora_expo = max(0, Δexpo_12m)
mejora_impo = max(0, −Δimpo_12m)
share_impo  = mejora_impo / (mejora_expo + mejora_impo)
```

`share_impo` es la porción de la mejora total (nunca negativa por
construcción) atribuible a que las importaciones cayeron, en vez de a que las
exportaciones subieron. Si ninguna de las dos mejoró (`mejora_expo +
mejora_impo == 0`), la regla no opina.

### 2. Interpolar el puntaje hacia el piso cuando la caída de M domina

```text
p_banda = puntaje_interpolado(valor, BANDAS_ITCM["saldo_comercial_12m"])

si p_banda ≤ 60 o share_impo ≤ 0,5: no opina (sin cambios de comportamiento
  respecto al gate original en estos dos casos)

si no:
  frac    = (share_impo − 0,5) / 0,5
  puntaje = p_banda − frac × (p_banda − 60)
```

En `share_impo = 0,5` el puntaje coincide con `p_banda` (transición sin
salto). En `share_impo = 1,0` el puntaje es exactamente 60, igual que la regla
original en su caso límite. Entre medio, la penalización crece linealmente con
cuánto domina la contracción de importaciones — el mismo patrón de
interpolación-entre-anclas que ADR-0021 aplicó al resto del sistema, aplicado
acá sobre el eje `share_impo` en vez del eje `valor`.

### 3. Usar el puntaje interpolado, no el escalonado, como gate y como base

El gate de activación (`p_banda ≤ 60` → no opina) y el valor que se penaliza
pasan a usar `parametrica.puntaje_interpolado`, el mismo que
`calcular_indice` aplica en la práctica. Esto cierra la discrepancia descrita
en el contexto: casos con puntaje interpolado >60 pero escalonado =60 ahora sí
se evalúan.

## Opciones consideradas

### Mantener el force-a-60 binario

Rechazada. Es el acantilado que ADR-0021 eliminó en el resto del sistema;
mantenerlo acá para un solo indicador reintroduce la misma patología que el
ADR-0019 midió (duplicación de incertidumbre, truncamiento de hasta ±13
puntos) justo en el componente que la motivó.

### Recalibrar el piso en función de la intensidad de `impo_var_ia`

Rechazada por ahora. Ajustar el piso mismo (no solo la interpolación hacia
él) según qué tan negativa es la variación interanual de importaciones
agregaría un grado de libertad no documentado en la Paramétrica CIGOB — el
piso de 60 es el único valor que el documento fuente fija explícitamente. Se
deja como posible refinamiento futuro si el analista lo pide con
justificación propia.

### Cambiar el indicador titular a una razón de cobertura (X/M) en vez del
nivel del saldo

Rechazada. Cambiaría la métrica que puntúa el ITCM (contrato de bandas,
series históricas, validación externa) para resolver un problema que ya tiene
una vía de ajuste más acotada dentro del subcomponente existente. Queda fuera
de alcance de este ADR.

### Usar una matriz insumo-producto para el "contenido importado" de las
exportaciones (growth accounting, Teixeira 2025 / Serrano-Freitas-Dweck)

Rechazada. Metodológicamente más precisa para atribuir crecimiento, pero
exige datos (matrices insumo-producto actualizadas) que el proyecto no
descarga ni mantiene; desproporcionado para un ajuste de un solo
subcomponente.

## Consecuencias

- `ajuste_automatico_saldo` deja de devolver siempre 60 cuando se activa: el
  puntaje depende de `share_impo` y de `p_banda`, con 60 como piso del caso
  límite (`share_impo = 1,0`).
- Casos límite que antes no activaban la regla (puntaje interpolado >60 con
  puntaje escalonado =60) ahora sí se evalúan y pueden aplicar el piso.
- El dato vigente al momento de este ADR (jun-2026, cache `output/cache/macro.json`:
  `impo_delta_12m = +5193`, importaciones creciendo) no dispara la regla ni
  antes ni después del cambio — no hace falta republicar para reflejar esta
  decisión en el snapshot actual.
- `test_ajuste_automatico_saldo_por_contraccion` se actualiza al nuevo valor
  interpolado (67,1 en vez de 60 para el caso de ejemplo del documento, cuyo
  `share_impo` es 85,7% — no 100%); se agrega
  `test_ajuste_automatico_saldo_interpolado` cubriendo 60%, 80% y 100% de
  `share_impo`.
- El piso de 60 puntos del documento fuente se conserva exactamente como caso
  límite; ningún caso queda peor puntuado que antes (la interpolación solo
  suaviza el camino hacia el mismo piso, nunca lo perfora).
