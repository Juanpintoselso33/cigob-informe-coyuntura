---
madr: 4
id: '0065'
estado: 'aceptado'
fecha: 2026-07-15
cinturon: 'politica'
indicadores: [iaf_transferencias]
archivos: ['_ipc_promedio_indec()']
relacionado: ['0059', '0066']
ambito: 'Cinturón política · ITCP · `iaf_transferencias` · `_ipc_promedio_indec()`'
---

# ADR-0065 — iaf_transferencias: deflactor promedio anual (el dic-dic subdeflactaba sumas anuales)

## Contexto y planteo del problema

Auditoría pedida por el usuario sobre la card "Armonía federal
(transferencias)". Su hipótesis inicial —que el punto fechado en diciembre
representara el presupuesto del año siguiente— **no se confirmó**: la serie
RON de Hacienda (`serie_ron_2003_2025.csv`) es de transferencias
**ejecutadas** por año calendario (coparticipación + leyes especiales
giradas a provincias); no contiene filas del año siguiente ni proyecciones,
y el punto `YYYY-12-01` de la serie es el acumulado de ese año cerrado — una
convención de fin de año correcta para la reconstrucción histórica (el dato
solo es conocible al cierre).

Pero la validación contra fuentes externas destapó un problema real en el
**deflactor**. Publicábamos **+7,0% real** para 2025 vs 2024 (nominal
+40,7%, deflactado por IPC dic-dic 31,5%). Los análisis fiscales de
referencia, con el mismo agregado conceptual:

| Fuente (ene-2026) | Nominal 2025 | Real 2025 | Deflactor |
|---|---:|---:|---|
| OPC (transferencias totales) | +44,3% | +2,7% | promedio |
| IARAF (automáticas) | +43% | +1,6% | promedio |
| Politikon Chaco / La Nación (automáticas) | — | +1,7% | promedio |
| BAE (totales) | +44,4% | +2,6% | promedio |
| **Nuestro indicador (RON)** | **+40,7%** | **+7,0%** | **dic-dic** |

La discrepancia nominal (40,7% vs 43-44%) es de **alcance** y es legítima:
la serie RON no incluye las compensaciones del Consenso Fiscal (que
crecieron ~80% real y empujan el agregado de IARAF/OPC) ni los giros
discrecionales — queda declarada como limitación en la ficha.

La discrepancia **real** (7,0% vs 1,6-2,7%) es un error de método: una suma
anual de flujos se devenga mes a mes a los precios de cada mes, así que el
deflactor correcto es el cociente de índices **promedio** del año (criterio
IARAF/OPC). El dic-dic compara solo las puntas: con inflación descendente
(los meses tempranos de 2024 tenían precios mucho más bajos que su
diciembre), la punta subdeflacta y sobreestima el crecimiento real. Para
2025: dic-dic 31,5% vs promedio ≈40% — cuatro a cinco puntos reales de
diferencia.

## Opciones consideradas

- **Deflactar por la inflación promedio anual del IPC de INDEC** — elegida.
- **Deflactor dic-dic** — descartado: subdeflacta.
- **El fallback hardcodeado `IPC_ANUAL`** — eliminado, por ser de un tipo incompatible con el deflactor nuevo.

## Decisión

1. `_ipc_dicdic_indec()` se reemplaza por `_ipc_promedio_indec()`: inflación
   promedio anual del índice IPC oficial de INDEC (promedio de los 12 meses
   del año ÷ promedio de los 12 del anterior − 1; solo años completos),
   misma fuente y mismo endpoint que antes.
2. `fetch_iaf_transferencias()` y `fetch_iaf_serie()` deflactan con el
   promedio. El fallback hardcodeado `IPC_ANUAL` (dic-dic, ya de tipo
   incompatible) se elimina: si la serie de INDEC no está disponible, aplica
   el mecanismo general de caché del colector.
3. La ficha pública documenta el criterio, la convención de fechado de la
   serie (diciembre = año cerrado, ejecutado, no presupuesto) y la
   limitación de alcance de la serie RON.

### Consecuencias

- La variación real 2025 pasa de +7,0% a ≈0% (consistente con el +1,6-2,7%
  externo, dado que RON excluye las compensaciones que más crecieron).
- El puntaje ITCP del indicador baja (~91 → ~75 interpolado); alianzas
  territoriales y el ITCP se regeneran en la corrida scoped.
- La serie histórica se regenera completa con el deflactor nuevo; pierde su
  primer punto (2017: el promedio exige el año índice completo, disponible
  desde 2017 → primera variación 2018).
- Tercera confirmación del método del día (ratio_dnu/ADR-0059,
  eficacia/ADR-0062): cuando el dato publicado difiere de los análisis de
  referencia, la causa suele ser reproducible y la validación externa la
  encuentra.

## Más información

### Precedentes directos

ADR-0059/0062 (mismo método: validar el dato publicado contra fuentes externas independientes)
