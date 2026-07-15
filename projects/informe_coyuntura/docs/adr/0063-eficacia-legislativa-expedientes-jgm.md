# ADR-0063 — eficacia_legislativa: los expedientes JGM (Jefatura de Gabinete) son del Ejecutivo — el Presupuesto era invisible

| | |
|---|---|
| **Estado** | Aceptado · complementa ADR-0061/0062 |
| **Ámbito** | Cinturón política · ITCP · `eficacia_legislativa` |
| **Fecha** | 2026-07-15 |
| **Precedentes directos** | ADR-0062 (fuente leyes-sancionadas, mismo día) |

## Contexto

Continuación de la auditoría de ADR-0062 (pregunta del usuario: "¿qué pasa
con los que se aprobaron en menos de 12 meses?"). Al trazar las leyes de
sanción rápida recientes contra el dataset, apareció que la **Ley 27.798
(Presupuesto 2026)** tiene `EXPEDIENTE_INICIAL = 0014-JGM-2025`: el
Presupuesto anual lo envía **siempre la Jefatura de Gabinete de Ministros**
(art. 100 inc. 6 de la Constitución), con sigla de expediente `-JGM-`, no
`-PE-`. El identificador de "proyecto del Ejecutivo" del indicador solo
reconocía `-PE-`.

Consecuencia verificada: los 19 proyectos de ley con expediente JGM del
dataset son exactamente los 19 Presupuestos anuales (2007→2025). El
indicador era ciego a la ley más importante de cada año, en ambas
direcciones:

- **Presupuesto 2025** (0012-JGM-2024, enviado 2024-09-15, nunca aprobado —
  prórroga): pertenece a la cohorte madura vigente y no contaba como
  fracaso.
- **Presupuesto 2026** (0014-JGM-2025, enviado 2025-09-15, Ley 27.798 en
  102 días): no habría contado como éxito cuando su camada madure
  (sep-2026).

El resto de los registros JGM (~630) son remisiones de decisiones
administrativas (`TIPO: MENSAJE`) que el filtro de TIPO de ADR-0062 ya
excluye correctamente.

## Decisión

`_RE_PE_EXP` pasa de `\d+-PE-\d{4}` a `\d+-(?:PE|JGM)-\d{4}`, y los fetch
(titular y serie) consultan el CKAN con ambas siglas (`q="-PE-"` +
`q="-JGM-"`; la búsqueda es full-text por token, una consulta por sigla).
Sin cambios en el filtro de TIPO ni en el numerador.

Efecto en la cohorte vigente: el Presupuesto 2025 entra como fracaso —
**3/17 = 17,6%** (antes 18,8%). Cuando la camada de sep-2025 madure, el
Presupuesto 2026 entrará como éxito.

## Consecuencias

- El indicador deja de ignorar la ley anual políticamente más pesada.
- La serie histórica se regenera: cada punto suma el Presupuesto de su
  camada (aprobado o no) — los años con presupuesto aprobado (p.ej. 2021,
  2022) suben levemente; los de prórroga (2019, 2024, 2025) bajan.
- Pregunta del usuario respondida en el mismo hilo: los éxitos de sanción
  rápida (27.798 en 102 días, 27.800 en 21, 27.802 en 78) cuentan siempre,
  pero recién cuando su camada cumple los 12 meses de maduración — el
  indicador reconoce el presente con ~12 meses de rezago por diseño
  (trade-off de la cohorte madura, ADR-0061). Si el ritmo legislativo del
  nuevo Congreso se sostiene, el indicador lo mostrará entre sep-2026 y
  feb-2027.
