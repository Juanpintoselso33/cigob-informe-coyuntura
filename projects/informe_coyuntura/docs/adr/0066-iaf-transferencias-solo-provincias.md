# ADR-0066 — iaf_transferencias: el CSV RON incluye la porción del Tesoro Nacional y la ANSES — se filtra a provincias

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Cinturón política · ITCP · `iaf_transferencias` |
| **Fecha** | 2026-07-15 |
| **Precedentes directos** | ADR-0065 (deflactor promedio, mismo día — este ADR completa esa auditoría con el chequeo de NIVEL) |

## Contexto

Chequeo externo pedido por el usuario tras ADR-0065. La validación de la
VARIACIÓN había cerrado, pero el chequeo de **nivel** no: nuestro total 2025
sumaba **$104 billones** cuando IARAF/DNAP/BAE reportan **~$60,3 billones**
de transferencias automáticas a provincias.

Inspección de la columna `provincia` del CSV: tiene **28 jurisdicciones**,
no 24. La serie RON de Hacienda distribuye los recursos de origen nacional
entre TODOS los destinos del régimen de coparticipación, incluyendo:

| Jurisdicción no provincial | 2025 | Naturaleza |
|---|---:|---|
| `tesoro nacional` | $36,1B | porción de la Nación — no es transferencia |
| `seguridad social` | $6,6B | porción ANSES — no es transferencia a provincias |
| `fondo a.t.n.` | ~$0,9B | retención en la Nación hasta reparto discrecional (los ATN distribuidos son transferencias NO automáticas; en 2025, $740.000M quedaron sin distribuir — BAE) |

El `fdo.compensador` sí se gira mensualmente a provincias y se conserva.

### Semántica del CSV, verificada registro por registro

Pedido explícito del usuario ("investigate bien qué significa cada entrada").
Columnas: `ano` (año de ejecución) · `provincia` (jurisdicción DESTINO del
reparto — las 24 + los destinos no provinciales del régimen) · `impuesto`
(recaudación que se reparte) · `regimen` (ley por la que llega:
coparticipación neta ley 26.075, financiamiento educativo, FONAVI, vialidad,
IVA seg. social, monotributo, consenso fiscal ley 27.429…) · `monto`
(millones de pesos).

**Corrección a ADR-0065**: ese ADR afirmó que la serie RON "no incluye las
compensaciones del Consenso Fiscal" — es incorrecto. Existen como régimen
propio (`consenso fiscal ley 27429 compensacion`): se financian con una fila
**negativa de −$2,5B en el Tesoro Nacional** y se acreditan a las provincias
(+$2,5B en 2025). La serie filtrada es entonces el agregado de transferencias
AUTOMÁTICAS completo (copa neta + financiamiento educativo + leyes especiales
+ compensaciones), el mismo perímetro que IARAF. Lo que no incluye son los
giros discrecionales (no automáticos).

Verificación con el filtro aplicado, en tres niveles:

| Nivel | Nuestro | Externo (IARAF/La Nación, ene-2026) |
|---|---:|---:|
| Por jurisdicción (Buenos Aires 2025) | $13,7B | $13,69B |
| Agregado (24 jurisdicciones, 2025) | $60,0B | $60,28B |
| Variación nominal 2025 | +43,1% | +43% |

La variación sin filtro (+40,7%) venía contaminada por la dinámica distinta
de la porción nacional (la mezcla de impuestos que van al Tesoro/ANSES
creció menos que la que va a provincias). En años con cambios en el reparto
la distorsión era mayor (2019: +51,4% provincias vs +43,1% total).

## Decisión

`RON_NO_PROVINCIA = {"tesoro nacional", "seguridad social", "fondo a.t.n."}`
se excluye de la suma en `fetch_iaf_transferencias()` y `fetch_iaf_serie()`.
La serie histórica se regenera con el alcance corregido.

## Consecuencias

- Variación real 2025: −0,8% → **+0,8%** (nominal +43,0%, deflactor promedio
  41,9%) — entre el 0% de la coparticipación pura y el +1,6% del agregado
  IARAF con compensaciones, exactamente donde el alcance RON debe caer.
- El nivel que expone la card (`total_ref_mm`) pasa a ser el que cualquier
  lector puede contrastar con los informes fiscales públicos.
- Cuarta corrección del día originada en validación externa (ratio_dnu,
  eficacia ×2, iaf ×2): el chequeo de nivel contra fuentes independientes
  queda incorporado como paso obligado de cualquier auditoría de indicador —
  una variación puede cerrar de casualidad con un alcance mal definido.
