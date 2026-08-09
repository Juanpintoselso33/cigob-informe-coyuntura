---
madr: 4
id: '0187'
estado: 'rechazado'
nota_estado: 'Rechazado por ahora: ver "Condiciones de reapertura" en Más información.'
fecha: 2026-08-09
cinturon: 'gestion'
indicadores: [gasto_funcionamiento]
relacionado: ['0015', '0128']
ambito: 'ITCG · `gasto_funcionamiento` · dimensión `reforma_estado`'
origen: 'CIGOB pidió evaluar sacar personal de FFAA y seguridad de gasto_funcionamiento (revisión de fichas de Gestión, ago-2026); un sondeo previo en la misma ronda (commit 04442d5) encontró Defensa+Seguridad en 44% del gasto en personal SIDIF contra ~10% de la dotación y lo dejó sin resolver, "sin ADR porque no se decidió ningún método".'
---

# ADR-0187 — `gasto_funcionamiento` no migra a SIDIF: el universo no reconcilia con el IMIG

## Contexto y planteo del problema

CIGOB pidió poder sacar el personal de FFAA y de seguridad de
`gasto_funcionamiento` (25% de la dimensión `reforma_estado`, mide la
variación real del gasto de funcionamiento del Estado nacional —salarios +
otros gastos de funcionamiento— contra el mismo mes de 2023). Hoy no se
puede: la fuente (IMIG, datos.gob.ar catálogo "sspm", dataset 452 — Informe
Mensual de Ingresos y Gastos del Sector Público Nacional No Financiero) es un
agregado del SPNF completo sin columna de jurisdicción.

Un sondeo previo, en la misma ronda de revisión (commit `04442d5`), probó la
API SIDIF de Presupuesto Abierto —la misma que usa `fetch_asistencia_directa()`
desde ADR-0015— porque sí expone `jurisdiccion_id` (Defensa = 45, Seguridad =
41). Encontró que Defensa+Seguridad son ~44% del gasto en personal (inciso 1)
de toda la SIDIF en 2025, contra ~10% de la dotación (ADR-0128), y lo dejó
como pregunta abierta: "un desajuste de universo... documentado en el
código, sin ADR porque no se decidió ningún método."

Este ADR retoma esa pregunta con datos en vivo, para decidir si el desajuste
es un artefacto de consulta (arreglable) o una diferencia real de universo
(no arreglable sin reconstruir el indicador desde cero).

## Factores de decisión

- El indicador alimenta un índice paramétrico con historia desde dic-2023;
  un cambio de fuente que no reconcilie con la actual sería un cambio de
  metodología encubierto bajo un pedido de alcance.
- La regla pedida explícitamente para este trabajo: antes de excluir algo,
  la serie SIN excluir tiene que trackear la serie actual. Si no trackea, el
  swap de fuente y la exclusión pedida quedan confundidos en el mismo número
  y nadie puede después atribuirle el movimiento a una sola causa.
- El 44% reportado por el sondeo previo podía deberse a: (a) un artefacto de
  consulta (doble conteo entre dimensiones, nivel de agregación incorrecto);
  (b) fondos de retiro/pensión de FFAA/policía computados como "gasto en
  personal" en vez de como transferencias; (c) que la definición de "fuerzas"
  difiera entre el padrón de dotación y SIDIF; o (d) que SIDIF y el IMIG
  midan universos institucionales distintos. (a) y (b) son arreglables con
  una consulta mejor, (c) es arreglable ajustando qué se excluye, (d) no es
  arreglable sin reconstruir el indicador.

## Opciones consideradas

- **Reconstruir `gasto_funcionamiento` sobre SIDIF, excluyendo jurisdicciones
  41 y 45** — la propuesta de CIGOB. Exige que el universo SIN excluir
  reconcilie primero con el IMIG.
- **Mantener el IMIG, sin exclusión, y declarar la limitación** — la opción
  por defecto si la reconciliación falla.

## Decisión

**Se descarta la migración a SIDIF, por ahora.** `gasto_funcionamiento` sigue
sobre el IMIG, sin exclusión de FFAA/seguridad, exactamente como estaba.

### Qué se verificó, en orden

**1. El 44% se reprodujo en vivo, y no es un artefacto de consulta.**
Consultando `credito` de Presupuesto Abierto (ejercicio 2025, inciso 1,
agrupado por `jurisdiccion_id`): total administración nacional
$13.700.299 M · Defensa $2.629.516 M · Seguridad $3.389.873 M → **43,94%**,
casi exacto al 44% del sondeo previo. El total no cambia si se agrupa por
`jurisdiccion_id`, por `entidad_id` o sin ningún agrupamiento (los tres dan
$13.700.298,91 M al centavo) — la API no duplica filas al cruzar dimensiones,
así que no hay error de conteo en la consulta.

Abrir Defensa y Seguridad por entidad descarta también la hipótesis de
pensiones: el Instituto de Ayuda Financiera para pago de Retiros y Pensiones
Militares ($3.969 M) y la Caja de Retiros de la Policía Federal ($7.376 M)
son ínfimos frente al total. Lo que domina son las fuerzas activas mismas:
Ejército $1.371.366 M, Gendarmería $1.248.234 M, Policía Federal $871.385 M,
Armada $671.390 M, Prefectura $639.469 M, Fuerza Aérea $517.270 M, Servicio
Penitenciario Federal $403.057 M, PSA $172.753 M.

**2. Parte del desajuste sí es de definición — pero no alcanza.** El padrón
de dotación (ADR-0128) define "fuerzas" con siete entes que NO incluyen a la
Policía Federal Argentina ni al Servicio Penitenciario Federal, mientras que
la jurisdicción 41 de SIDIF sí los incluye. Recalculando con la misma
definición de 7 entes, Defensa+Seguridad baja de 43,94% a **34,63%** del
total SIDIF. Sigue siendo 3,5 veces el ~10% de la dotación: la definición de
"fuerzas" explica parte de la brecha, no la brecha.

**3. El universo no reconcilia — el hallazgo decisivo.** SIDIF
(`jurisdiccion`/`entidad`, lo que la Ley 24.156 llama Administración
Nacional) y el IMIG (Sector Público Nacional No Financiero) no miden el
mismo universo, y no es un problema chico:

| | SIDIF (incisos 1+2+3, sin excluir nada) | IMIG (salarios+otros) | SIDIF/IMIG |
|---|---:|---:|---:|
| 2024 (año completo) | $12.890.239 M | $15.628.851 M | 0,825 |
| 2025 (año completo) | $17.071.690 M | $21.406.105 M | 0,798 |

SIDIF capta sistemáticamente ~80% del total que capta el IMIG — un ~20% del
gasto de funcionamiento del SPNF no tiene contraparte en las 14
jurisdicciones que expone `credito`. Defensa y Seguridad, en cambio, SÍ
ejecutan su presupuesto completo como jurisdicciones centrales: están
enteras en el número más chico. Esa asimetría —lo militar/policial entra
completo, una porción grande de lo civil no entra— es lo que infla
mecánicamente su participación en el total de SIDIF, sin que haga falta
ninguna decisión editorial de por medio.

**4. La serie mensual tampoco trackea.** Se reconstruyó la serie completa
dic-2023→jun-2026 de SIDIF (incisos 1+2+3, sin excluir nada) con la MISMA
fórmula que usa hoy el indicador (variación real vs el mismo mes de 2023,
deflactado por IPC) y se comparó mes a mes contra la serie que hoy publica
`gasto_funcionamiento` (IMIG):

- Correlación entre las dos series de variación %: **r = 0,42** (30 meses).
- Diferencia promedio: **5,5 puntos porcentuales**; máxima: **16,4 pp** —
  sobre valores que van de −12% a −34%.
- La razón nominal mes a mes SIDIF/IMIG no es estable: va de **0,55 a
  1,17** según el mes (ene-2025 = 0,55; jun-2025 = 1,11), así que ni
  siquiera hay un factor de escala fijo que corrija el nivel — la DINÁMICA
  mensual difiere, no sólo el nivel anual.

Este punto por sí solo ya cierra la pregunta: la regla pedida para este
trabajo era que la serie SIN excluir nada trackee la actual antes de excluir
algo. No trackea.

**5. El efecto de la exclusión, aislado (para que quede separado del punto
anterior).** Dentro de la serie SIDIF (que ya no reconcilia), excluir las
jurisdicciones 41+45 corre la lectura de variación real, en promedio, **6,0
pp más negativo** (rango 0,3-11,5 pp sobre los mismos 30 meses; en el
último mes común, jun-2026: −27,7% → −32,8%). Es del mismo orden de
magnitud que el ruido que introduce el cambio de fuente (5,5 pp) —
publicar esto no permitiría atribuirle el movimiento a "sacar
FFAA/seguridad" en particular: quedaría mezclado con el cambio de fuente en
una proporción que nadie podría desenredar después.

### Consecuencias

- `gasto_funcionamiento` sigue sin poder aislar el efecto de FFAA/seguridad.
  El pedido de CIGOB queda sin resolver, documentado como limitación
  abierta en el docstring de `fetch_gasto_funcionamiento()` (referencia a
  este ADR) en vez de como una nota de "todavía no se investigó".
- No se tocó ningún score: `itcg.calcular_itcg()` da el mismo resultado
  antes y después de este ADR porque no cambió ningún dato ni ninguna
  fórmula.
- El sondeo previo (commit `04442d5`) queda absorbido por este ADR: la
  sospecha sin verificar que dejó anotada ("probablemente Administración
  Nacional contra SPNF completo, o un problema de fuente de financiamiento
  duplicada") se resuelve acá — descartada la duplicación (punto 1),
  confirmado el desajuste de universo (punto 3), con números.

### Confirmación

Todas las consultas de este ADR corrieron en vivo contra
`https://www.presupuestoabierto.gob.ar/api/v1/credito` y
`https://apis.datos.gob.ar/series/api/series/` con el token vigente de
`PRESUPUESTO_ABIERTO_TOKEN`. Reproducible con las mismas consultas:
`ejercicios`, `columns` (`jurisdiccion_id`/`entidad_id`/`inciso_id`/
`impacto_presupuestario_anio`/`impacto_presupuestario_mes`/
`credito_devengado`) y `filters` citados arriba contra el mismo endpoint. No
se corrió el pipeline ni se regeneró ningún snapshot: `git status --short`
al cierre de esta sesión no tiene cambios en `output/`, `web/src/data/` ni
`data/historico/`.

## Pros y contras de las opciones

**Reconstruir sobre SIDIF, excluyendo 41+45**

- Bueno: es la única fuente pública con dimensión de jurisdicción encontrada
  hasta ahora; si el universo reconciliara, resolvería el pedido de CIGOB.
- Malo: el universo no reconcilia (punto 3) ni la dinámica mensual (punto
  4). Publicarlo igual sería un cambio de metodología escondido detrás de
  un pedido de alcance — exactamente lo que este proyecto evita.

**Mantener el IMIG sin exclusión (elegida)**

- Bueno: el indicador sigue siendo el que se puede vouchear con la fuente
  que ya se validó; no se introduce ruido de fuente disfrazado de señal de
  FFAA.
- Malo: no responde el pedido de CIGOB. La limitación queda abierta y
  documentada, no resuelta.

## Más información

### Qué NO se descartó

Sólo se probó Presupuesto Abierto/SIDIF. Quedan sin evaluar: (a) que el
propio IMIG publique alguna vez una apertura por naturaleza institucional o
jurisdicción dentro del dataset 452 (no existe al momento de este ADR); y
(b) cruzar el padrón de dotación por entidad (que sí identifica a las
fuerzas, ADR-0128) con una fuente de sueldo promedio por fuerza para estimar
el gasto salarial de FFAA/seguridad por fuera de la ejecución presupuestaria
formal — un proxy, no una medición directa, y con su propio riesgo de sesgo
que habría que justificar aparte.

### Condiciones de reapertura

- Si datos.gob.ar publica el IMIG (o un sucesor) desagregado por
  jurisdicción o carácter institucional, la pregunta se puede resolver sin
  cambiar de fuente.
- Si se identifica por qué SIDIF captura sólo ~80% del total IMIG
  (candidato más probable: universidades nacionales y organismos con
  autonomía presupuestaria, que no aparecieron como jurisdicción propia en
  las 14 jurisdicciones relevadas) y ese faltante resulta reconstruible
  dentro de la misma API, se puede reintentar la reconciliación con el
  universo corregido.
- Si ninguna de las dos aparece, la única vía que queda es la (b) de arriba
  (estimación por sueldo promedio), y ahí el debate deja de ser de fuente y
  pasa a ser sobre si un proxy estimado puede reemplazar a una medición de
  ejecución presupuestaria real — una decisión distinta, para otro ADR.
