# Informe de remediación — las 17 discrepancias

**Auditoría:** externa, 25 de agosto de 2026 · 69 indicadores revisados, 17 discrepantes.
**Remediación:** cinco entregas, 25 de agosto de 2026.
**Corrida:** colectores 18:33–18:41, publicación 18:52. Gate en verde.

## Clasificación de los 17

### `corregido y puntuando` — 7

| Indicador | Antes | Después | Qué estaba mal | ADR |
|---|---:|---:|---|---|
| `costo_financiamiento_tesoro` | 8,07% | **4,93%** (jun) · 5,80% (jul) | La TIREA se reconstruía capitalizando por meses de calendario enteros. Es un dato publicado. | 0238 |
| `iaf_transferencias` | +0,8% | **+1,6%** | Un solo IPC promedio para doce flujos con estacionalidad propia. | 0239 |
| `cobertura_judicial` | 69,63% | **69,63%** | El valor era correcto; el texto lo explicaba con otra definición y otro corte. | 0240 |
| `ratio_dnu` | 1,92 | **1,48** | Contaba coincidencias textuales, no decretos tipificados como DNU. | 0241 |
| `icc_utdt` | 39,9 | **40,2** | Leía la columna 1 por posición: publicaba CABA como total nacional. | 0242 |
| `concesiones_infraestructura` | 28,7% | **100%** | Decidía por el estado de CONTRAT.AR, que se queda viejo. | 0244 |
| `credito_privado` | +2,5% | **−1,5%** | La variable 26 del BCRA es `MEyML`: incluía la cartera en dólares valuada en pesos. | 0251 |

### `renombrado y puntuando con constructo acotado` — 5

| Indicador | Antes | Ahora | ADR |
|---|---|---|---|
| `consumo_supermercados` | «índice 2004 = 100» | base **2017=100**, leída de la fuente | 0243 |
| `trabajo_independiente` | «% del empleo registrado» | **«sin monotributo social»**, con las categorías de cada lado enumeradas | 0250 |
| `subocupacion_demandante` | se llamaba `pluriempleo`, «% de ocupados» | nombre real, **«% de la PEA»** | 0249 |
| `idm` | «Exceso de pesos sobre la demanda» | **«Brecha de crecimiento real M3–M2»** | 0254 |
| `icip` | «Capitalización digital» | **«Pagos de servicios digitales y productividad»** | 0253 |

Y `desequilibrio_monetario`, que conserva su fórmula y pierde toda afirmación de
**«fuera del sistema»**: su componente B pasa a llamarse presión compradora de
divisas (ADR-0252).

### `contextual, fuera del score` — 0

Ninguno. La regla del tablero, cerrada tres veces (ADR-0051/0153/0189), es que
**si no puntúa, no es card**. El handoff pedía conservar cards de contexto
marcadas «no integra el índice»; eso reabriría una excepción que el proyecto ya
cerró dos veces, porque una card sin semáforo se lee como componente igual. Lo
que sobrevive de cada suspendido es su **serie**, que se sigue publicando, y el
motivo documentado en la constante y en la ficha.

### `rediseño pendiente, fuera del score` — 4

| Indicador | Por qué salió | Condición de reingreso | ADR |
|---|---|---|---|
| `apoyo_empresario` | Saldo sobre 7 textos codificados con 14 pendientes (hoy 15) | Corpus cerrado, criterios predeclarados, doble codificación con concordancia | 0246 |
| `reestructuracion_organismos` | `11/45` divide normas por una convención documental | Numerador y denominador en la misma unidad, universo cerrado y publicado | 0247 |
| `sentimiento_digital` | El volumen de búsquedas no tiene valencia; validación adversa en cuatro cortes | Términos predeclarados, vintages congelados, validación fuera de muestra | 0248 |
| `judicializacion` | El corpus de SAIJ no identifica causas contra el Ejecutivo | Universo de causas contra actos del PEN, unidad de expediente | 0255 |

## Impacto sobre el tablero

| Cinturón | Antes | Después | Δ | Paramétrica |
|---|---:|---:|---:|---|
| Macro (ITCM) | 3,6 | **3,6** | +0,0 | 64,1 → 64,1 |
| Política (ITCP) | 3,3 | **2,9** | −0,4 | 67,0 → 70,9 |
| Vida cotidiana (ITCIS) | 6,1 | **6,2** | +0,1 | 94,6 → 93,8 |
| Gestión (ITCG) | 2,7 | **2,0** | −0,7 | 73,0 → 79,6 |
| **Score global** | **3,9** | **3,7** | **−0,2** | |

**El perímetro pasa de 69 a 65 cards**: salieron los cuatro suspendidos y
`pluriempleo` fue renombrado a `subocupacion_demandante`.

### Atribución de cada movimiento

Nueve indicadores cambiaron de valor. **Seis son las correcciones** de la
remediación (tabla de arriba). Los otros **tres son dato fresco ordinario**, no
remediación: `cepo_mulc` 6,0 → 5,91 · `conflictividad_nacional` −24,1 → −24,0 ·
`idm` 4,73 → 4,7.

Los 47 indicadores restantes no se movieron en absoluto. Lo que sí se movió en
muchos es el **peso efectivo**, y siempre por la misma causa mecánica: al salir
un componente, sus pares de dimensión absorbieron el hueco en proporción
(ADR-0245). Ninguna dimensión cambió su peso frente a las otras.

**Una separación que el handoff pide explícitamente**: el costo del
financiamiento del Tesoro tiene las dos cosas a la vez. La *corrección* llevó
junio de 8,07% a **4,93%** —lo que la auditoría verificó, y está en la serie—.
La *actualización* trajo julio, que da **5,80%** sobre dos colocaciones. La card
publica julio; no son el mismo movimiento y no deben leerse como uno.

## Verificación

- **Gate de calidad**: `exit=0`. Dos demoras de fuente, ninguna falla de
  integridad. Las dos son preexistentes y legítimas (`icip` 146d, `mora_familias`
  116d).
- **Suite**: **3008 pasan**, 3 se saltean, **cero fallas**.
- **`npx tsc --noEmit`**: limpio. **`npm run build`**: 83 páginas.
- **Controles de la remediación** (`scripts/verificacion_remediacion.py`): los
  siete pasan — ningún suspendido aporta al índice ni se muestra, los pesos
  suman 1 por dimensión y por cinturón, los seis valores verificados coinciden,
  no reapareció ningún id legado, las unidades corregidas están declaradas, toda
  card con valor tiene fecha.

## Lo que se encontró en el camino y no estaba en la auditoría

1. **La Etapa II-B de las concesiones también estaba adjudicada** desde el
   28-jul (Res. 1149/2026), un mes antes del corte. La auditoría sólo vio la
   Etapa III y estimó ~71,65%; el número correcto es 100%.
2. **`GESTION_OCULTOS` devolvía vacío en silencio** desde hacía meses:
   `cargar_ocultos()` parseaba `publicar.py` con una regex de una línea y esa
   constante había dejado de ser un literal.
3. **La serie de concesiones no seguía a la card** — la atrapó el gate G3 en
   esta misma corrida. Se corrigió usando la fecha de publicación en el Boletín
   para fechar cada escalón, que además es mejor que «el mes en que se detectó».
4. **`MAX_DIAS` seguía indexado por `pluriempleo`**, así que el renombre dejó a
   `subocupacion_demandante` con el tope por defecto y el gate reportaba una
   demora falsa de 236 días.
5. **El archivo histórico conservaba la clave vieja**: es un upsert y nadie
   saca lo que deja de escribirse.

## Deudas anotadas

1. **La asimetría de la matriz de `desequilibrio_monetario`** —degradar B cuesta
   77,5 y degradar A sólo 40— se justificaba con la tesis de la fuga fuera del
   sistema. Esa tesis se cayó; la asimetría quedó en pie sin su fundamento.
2. **La banda de `idm`** se calibró leyendo la brecha como exceso monetario.
3. **`consumo_supermercados` sigue publicando mayo.** El INDEC publicó junio
   (82,1) el 21-ago y la API de series todavía no lo espeja. El informe de prensa
   no es direccionable. El día que la API lo espeje, la card pasa sola.
4. **Dos dimensiones quedan con un solo componente**: sector privado (ITCP) y
   percepción (ITCIS).
5. `icip` combina pagos al exterior con productividad laboral. Es anterior a
   esta remediación y no se tocó.
