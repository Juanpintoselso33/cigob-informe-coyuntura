# ADR-0081 — Las recalibraciones no se calendarizan: se detectan

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Todas las paramétricas · `scripts/revision_bandas.py` (nuevo) |
| **Fecha** | 2026-07-18 |
| **Precedentes directos** | **ADR-0045** (cuándo se recalibra una banda y cuándo no) · ADR-0021 (puntaje interpolado) |
| **Origen** | Auditoría de consistencia del cinturón macro (17-jul-2026), observación 9 |

## Contexto

La auditoría pidió **"calendarizar las recalibraciones de bandas de historia
corta"**, señalando al IDM, la presión de dolarización y el crédito privado:
indicadores cuyas anclas se fijaron con pocos meses de datos y que convendría
revisar a medida que la serie crece.

El pedido es razonable pero **un calendario en un documento no funciona**: nadie
lo lee, no sabe qué cambió desde la última vez, y llegado el momento no dice
cuáles bandas mirar ni por qué. Se reemplaza por un diagnóstico ejecutable.

## El criterio, que es lo primero

ADR-0045 ya fijó cuándo se recalibra una banda, y es tajante: **sólo si su techo
o su piso son inalcanzables**. Nunca porque el rango observado quede corto. Si
un indicador se pasó dos años pegado al piso porque el país anduvo mal, correr
el ancla hacia abajo **blanquea la señal** en lugar de mejorarla.

Distinguir un caso del otro exige dos medidas distintas, y el diagnóstico las
separa a propósito:

- **Saturación** — qué fracción de los meses cae exactamente en el puntaje
  extremo. Alta saturación significa que el indicador **dejó de discriminar** en
  ese tramo: doce meses "iguales" que en realidad no lo eran.
- **Alcance** — si el extremo **opuesto** se tocó alguna vez. Un extremo que
  nunca se alcanzó en toda la historia disponible es el candidato legítimo; uno
  que se alcanzó está bien anclado y la saturación es desempeño real.

La alarma se enciende con **saturación alta de un lado + el otro extremo nunca
alcanzado**. Y aun así el resultado se llama **"revisar"**, nunca
"recalibrar": sólo una persona que conozca el indicador puede decir si el
extremo es inalcanzable por construcción o si el período no dio para tanto.

## Decisión

Entra `scripts/revision_bandas.py`, que recorre los indicadores puntuables de
ITCM, ITCG e ITCP y clasifica cada banda en cuatro estados: `revisar`,
`saturado` (discrimina poco pero está bien anclada), `historia_corta` (menos de
18 meses: no se opina) y `ok`. Escribe `output/revision_bandas.json`.

Umbrales: **35%** de saturación para avisar, **18 meses** de historia mínima.
Están puestos holgados a propósito — el costo de un falso positivo es leer una
ficha, el de un falso negativo es una banda mal calibrada durante años sin que
nadie se entere.

### Cadencia

En vez de una fecha en el calendario, el disparador es el propio diagnóstico:
se corre **junto con la revisión editorial del informe** y ante cualquier alta o
cambio de metodología de un indicador. La lista de candidatas viene con el
diagnóstico, así que la revisión empieza sabiendo qué mirar.

## Resultado de la primera corrida

**Ninguna banda del ITCM tiene un extremo inalcanzable**: todas se tocan al
menos de un lado. Bajo el criterio de ADR-0045, hoy **no corresponde recalibrar
nada**.

Quedan **14 candidatas a revisión** en los tres índices, la mayoría en el ITCG
(que tiene varios indicadores de ejecución binaria, clavados en un extremo por
naturaleza). Las tres del ITCM:

| indicador | diagnóstico |
|---|---|
| `reservas_bcra` | 57% de los meses en el piso, techo nunca alcanzado en 23 meses |
| `recaudacion` | 48% en el piso, techo nunca alcanzado en 31 meses |
| `idm` | 35% en el techo, piso nunca alcanzado en 31 meses |

Ninguna se toca en esta tanda: las tres reflejan desempeño real del período.

## Un bug propio, que justifica el test que lo acompaña

La primera versión de este diagnóstico **marcaba `rem_ipc_12m` con el 100% de
los meses en el piso** y lo mandaba a revisar. Era falso: la serie del REM
guarda la expectativa **anual** (24,2%) pero el ITCM puntúa su **equivalente
mensual** (1,82%) contra bandas mensuales. Puntuando el valor crudo, el
indicador caía al piso en todos los meses de la historia.

Habría enviado a un editor a revisar una banda perfectamente calibrada. La
causa es la de siempre: **dos lugares que tienen que estar de acuerdo sobre cómo
se puntúa un indicador**. La corrección es la misma que en los casos anteriores
—el diagnóstico usa la reconstrucción compartida de `validacion_externa`, que ya
aplica la transformación— y viene con un test que compara el puntaje del
diagnóstico contra el `puntaje_banda` publicado para cada indicador del ITCM.

ITCG e ITCP no transforman sus valores antes de puntuar: se verificó.

## Limitaciones declaradas

- El diagnóstico mira **saturación y alcance**, no la forma de la distribución
  en el medio. Una banda con anclas mal espaciadas en el tramo central no
  aparece.
- La historia disponible sigue siendo corta para varios indicadores. Que un
  extremo no se haya alcanzado en 23 meses dice bastante menos que si no se
  alcanzó en 60.
- El ITVC queda afuera: es un índice base-100 continuo, sin bandas que
  recalibrar.
- Los indicadores sin serie histórica (IAI, ICIP) no se pueden diagnosticar.
