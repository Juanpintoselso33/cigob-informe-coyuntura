---
madr: 4
id: '0091'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'politica'
indicadores: [veto_quorum]
ambito: 'ITCP · `veto_quorum` · serie mensual'
origen: 'Auditoría externa del cinturón político, prioridad 6 (techo estructural)'
---

# ADR-0091 — El indicador de quórum contaba mal el fracaso

## Contexto y planteo del problema

### El planteo de la auditoría

> "Mide bien capacidad opositora de bloqueo puro. Riesgo de muestra chica ya
> declarado por CIGOB; **el 0% actual dice más sobre el número de sesiones
> convocadas que sobre ausencia de conflicto**."

La observación era correcta, y al ir a verificarla apareció que el problema de
fondo era otro y más grave.

## Opciones consideradas

- **Numerador: sesiones clasificadas «en minoría»; denominador: sesiones convocadas para tratar temas** — elegida.
- **Ventana del período legislativo** — reemplazada por 12 meses calendario móviles.
- **Incluir informativas, preparatoria y presentación de presupuesto** — quedan afuera: son instancias donde el oficialismo no necesita reunir quórum para avanzar su agenda.

## Decisión

**Numerador**: sesiones clasificadas "en minoría".

**Denominador**: sesiones convocadas para tratar temas — especiales, sus
continuaciones, homenajes y las que quedaron en minoría. Quedan afuera las
informativas, la preparatoria y la presentación de presupuesto, instancias donde
el oficialismo no necesita reunir quórum para avanzar su agenda.

**Ventana**: 12 meses calendario móviles, en lugar del período legislativo.

Las **anclas no cambian** (5/10/20/30). Discriminan bien contra la serie
corregida y no había motivo para tocarlas.

### El indicador corregido

| período | fracasadas / convocadas | |
|---|---|---|
| 2024 | 8/22 = **36,4%** | el año de las sesiones caídas |
| 2025 | 2/16 = 12,5% | |
| 2026 (parcial) | 1/6 = 16,7% | |
| **ventana móvil 12m (hoy)** | 1/12 = **8,3%** | |

Publicado: **0,0 → 8,3** · puntaje **100 → 82,9**.

La serie pasa de **3 puntos anuales a 31 mensuales**, lo que además la vuelve
comparable con el resto del índice y resuelve para este indicador la objeción de
rezagos dispares (prioridad 5 de la misma auditoría).

Es notable que la serie corregida cuenta una historia con sentido —2024 con un
tercio de las sesiones caídas, luego una mejora sostenida— donde la anterior
sólo tenía tres puntos y dos de ellos en cero.

### Consecuencias

- ITCP 68,0 → **68,9**. La dimensión de poder legislativo queda en 39,1.
- Card y serie comparten el cálculo (`_veto_quorum_tasa_12m`), igual que
  `desafios_legislativos` y `brecha_obra_publica`: la card es la ventana al mes
  en curso, la serie a cada mes cerrado.
- El texto público se reescribió entero: la ficha explicaba un criterio de
  conteo que era el equivocado.

## Más información

### Limitaciones

### Limitaciones que siguen en pie

- **El denominador sigue siendo modesto**: 12 a 16 sesiones en la ventana. Es
  mucho mejor que 5, pero lejos de las ~40 que harían robusta una lectura de
  "cero fracasos". El indicador debe leerse por su tendencia, y así está dicho en
  la ficha.
- Las sesiones desactivadas antes de la convocatoria formal no aparecen en el
  registro: el indicador **subestima** el bloqueo. Esta limitación ya estaba
  declarada y no cambia.
- No distingue el quórum frustrado por la oposición del que falla por
  inasistencia propia.

### Lo primero: el problema de muestra era peor de lo declarado

El indicador puntuaba sobre el **período legislativo en curso**, cuyo
denominador se reinicia cada marzo. Al 19-jul-2026 el estado publicado era
**0 fracasos sobre 5 sesiones → puntaje 100 sobre 100**, el máximo posible.

Con 0 éxitos en 5 ensayos, la regla de tres da una cota superior del 60% para la
tasa real, con 95% de confianza:

| n | 0 fracasos → tasa real puede llegar a | puntaje de esa tasa |
|---|---|---|
| 5 | 60,0% | **10** |
| 10 | 30,0% | 10 |
| 20 | 15,0% | 65 |
| 40 | 7,5% | 85 |

**El dato no distinguía el mejor estado posible del peor, y el índice le asignaba
el mejor.** Harían falta unas 40 sesiones para que "cero fracasos" sostuviera un
puntaje alto.

### Lo segundo: el numerador estaba mal

Al auditar los registros crudos del dataset de sesiones —no la metodología, los
registros— apareció que el criterio de conteo era incorrecto. `REUNION_TIPO`
toma estos valores en Diputados (2024-2026):

| tipo | n | `SESION_NO` = 0 | duración mediana |
|---|---|---|---|
| Especial | 29 | 0 de 29 | 11,8 h |
| **Minoría** | **11** | **11 de 11** | **2,0 h** |
| Informativa | 4 | 0 de 4 | 7,0 h |
| Informativa Art. 71 CN — Citada — **Fracasada** | 2 | 2 de 2 | **0,0 h** |
| Preparatoria · Presupuesto · Homenaje | 4 | — | — |

El código buscaba la subcadena `"fracasada"`. Con eso:

- **omitía las once sesiones "Minoría"**, que son el fracaso de quórum
  propiamente dicho: convocadas, esperaron unas dos horas, nunca se
  constituyeron y no recibieron número de sesión;
- **contaba como fracaso las dos "Informativa Art. 71 CN — Citada — Fracasada"**,
  que duran 0,0 h y son otro fenómeno — el jefe de Gabinete que no concurre a dar
  su informe, no el quórum que no se junta.

La evidencia de que "Minoría" es la categoría correcta no es interpretativa: las
once tienen `SESION_NO = 0` (no se les asignó número, o sea que la sesión no
llegó a constituirse) y duran 2 horas medianas, contra las 11,8 h de las que sí
sesionaron.

### Lección de método

Este error sobrevivió a la incorporación del indicador (may-2026), a su paso al
ITCP (jul-2026) y a una auditoría externa que miró el indicador y señaló el
síntoma correcto —"el 0% dice más sobre las sesiones convocadas"— sin llegar a la
causa. Lo encontró **mirar los registros crudos uno por uno**, que es
exactamente el procedimiento que ADR-0062, ADR-0065 y ADR-0068 ya habían dejado
escrito como práctica tras tres casos análogos.

El patrón se repite: un valor sospechosamente extremo —acá un 100 perfecto— casi
nunca es una buena noticia. Es una definición mal escrita.
