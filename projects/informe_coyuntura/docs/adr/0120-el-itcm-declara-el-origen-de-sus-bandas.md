# ADR-0120 — El ITCM declara el origen de sus bandas, y baja del 83% al 38% de circularidad

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITCM · comentarios de `BANDAS_ITCM` · `procedencia_anclas.py` · trinquete |
| **Fecha** | 2026-07-20 |
| **Cierra** | El backlog de circularidad del ITCM de ADR-0103 |
| **Bajo** | ADR-0045 (no recalibrar para blanquear) · ADR-0105 (trinquete) |

## Contexto

ADR-0103 midió que el ITCM era el índice más circular de los cuatro —83% del
peso— y el único con **cero anclas externas**. Su `sin_declarar` era del 45%:
siete bandas cuyo comentario sólo decía la unidad. ADR-0103 lo dejó como trabajo
pendiente y fue explícito sobre qué clase de trabajo era:

> "Las siete bandas `sin_declarar` del ITCM no requieren recalibrar nada —
> requieren escribir de dónde salieron, y si no se puede reconstruir, decirlo."

Este ADR hace exactamente eso. **Ningún ancla se movió; el ITCM sigue en 62,1.**

## Lo que se descubrió al escribir el origen

Cuatro de las siete bandas tienen serie propia anterior a dic-2023
(`ipc_total`, `emae_ia`, `recaudacion`, `saldo_comercial_12m`), así que la
pregunta natural era: ¿anclarlas a esa historia? Se midió dónde cae cada corte
en la distribución pre-mandato, y la respuesta **no es la misma para todas**:

- **`ipc_total` NO se ancla a su historia, y hacerlo sería un error.** La
  inflación de 2021-2023 promedió 6,1% m/m, de modo que anclar a esos
  percentiles pondría un mes mediano pre-mandato en el peor tramo y haría parecer
  perfecto cualquier mes de hoy —el 1,9% actual saltaría de 77 a ~100 puntos—
  sólo porque el punto de partida era catastrófico. Es el blanqueo de señal que
  ADR-0045 prohíbe. Sus bandas son **normativas**: metas de estabilidad de
  precios (1% m/m ≈ 12,7% anual = éxito; 5% ≈ 80% anual = fracaso).

- **`recaudacion`, `emae_ia`, `saldo_comercial_12m` son conceptuales, ancladas
  al CERO** (empate con la inflación / actividad estancada / comercio
  balanceado), y **además resultan consistentes con la historia**: sus cortes
  centrales caen cerca de la mediana pre-mandato (recaudación 0%→p41, EMAE
  0%→p26, saldo 5000→p53). Discriminan también en la era anterior, no están
  ajustadas a este período.

## La reclasificación

| indicador | antes | ahora | por qué |
|---|---|---|---|
| `ipc_total` | sin declarar | **conceptual** | banda normativa de estabilidad |
| `rem_ipc_12m` | sin declarar | **conceptual** | hereda la vara del IPC |
| `recaudacion` | sin declarar | **conceptual** | anclada al cero, consistente con la historia |
| `emae_ia` | sin declarar | **conceptual** | crecimiento en torno al cero |
| `saldo_comercial_12m` | sin declarar | **conceptual** | equilibrio comercial, techo 85 |
| `reservas_bcra` | sin declarar | **conceptual** | nivel de cobertura, sin dato pre-mandato |
| `ipi_manufacturero` | sin declarar | **conceptual** | ya declaraba herencia del EMAE (ADR-0076/0079); era un falso positivo del clasificador por regex |

## Resultado

| | antes | ahora |
|---|---|---|
| ITCM circular | **83%** | **38%** |
| ITCM sin declarar | 45% | **0%** |
| ITCM conceptual | 3% | 49% |

El 38% que queda es **convención irreducible**: `idm`, `iai`, `icip`,
`costo_financiamiento_tesoro` y `credito_privado`, todos sin serie anterior a
dic-2023. Están calibrados contra el período que miden porque no hay contra qué
otra cosa, y así lo dice cada comentario. No es un pendiente: es el piso que el
dato disponible impone.

## El trinquete hizo su trabajo

Bajar la circularidad disparó `test_el_techo_sigue_a_la_mejora` (ADR-0105): una
mejora no vale hasta que se baja el techo que la fija. El techo del ITCM pasa de
0,83 a **0,38** y el de `sin_declarar` a **0,01**. A partir de acá el ITCM no
puede volver a subir sin que alguien edite ese número a mano y lo justifique.

## Consecuencias

- El único cambio de código son comentarios en `BANDAS_ITCM` y la
  reclasificación en `procedencia_anclas.py`. Cero cambios de puntaje —
  verificado: ITCM 62,1 antes y después.
- El ITCM deja de ser el índice más circular. El orden ahora es ITCP 61% >
  ITCG 51% > ITCM 38%.
- Queda pendiente de otros frentes, no de éste: el ITCM sigue sin ancla
  **externa** (la circularidad conceptual no es externa), y ADR-0071 explicó por
  qué el candidato natural —riesgo país— no puede entrar sin romper la
  validación.
