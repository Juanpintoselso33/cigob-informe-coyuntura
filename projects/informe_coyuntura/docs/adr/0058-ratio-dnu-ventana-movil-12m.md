---
madr: 4
id: '0058'
estado: 'aceptado'
fecha: 2026-07-15
cinturon: 'politica'
indicadores: [ratio_dnu, poder_legislativo]
relacionado: ['0036', '0045', '0052', '0060']
superado_parcialmente_por: ['0059']
ambito: 'Cinturón política · ITCP · `ratio_dnu` · dimensión `poder_legislativo`'
---

# ADR-0058 — ratio_dnu: ventana móvil de 365 días (reemplaza al acumulado del año calendario)

## Contexto y planteo del problema

`ratio_dnu` (DNUs dictados / leyes sancionadas, InfoLeg) se calculaba desde
ADR-0036 como un **acumulado del año calendario en curso**: `count(DNUs,
1-ene→hoy) / count(leyes, 1-ene→hoy)`. La serie histórica tenía un solo punto
por año (2020→hoy), no un valor por mes.

Esto es exactamente el defecto que ADR-0052 identificó en `movilizacion_cepa`
y usó como motivo para sacarlo del tablero: *"Fórmula no comparable mes a
mes... crece mecánicamente con el calendario y se resetea en enero"*. La
métrica no es una ventana que se desliza — es un contador que arranca de cero
cada 1° de enero. Enero y febrero castigan estructuralmente el ratio (pocas
leyes sancionadas todavía en el año) sin que eso refleje ningún cambio real
de comportamiento del Ejecutivo; para diciembre, el acumulado ya arrastra
once meses de historia y es una medida completamente distinta en composición.

Ese criterio nunca se le aplicó a `ratio_dnu` en ninguna revisión editorial
posterior (ADR-0048 lo confirmó explícitamente en el tablero, sin cuestionar
la fórmula). A diferencia de `movilizacion_cepa` —que no tenía forma de
reconstruirse hacia atrás por falta de historia publicada de la fuente—,
`ratio_dnu` sí puede convertirse a ventana móvil: InfoLeg ya se consulta con
un rango de fechas explícito (`diaPubDesde/mesPubDesde/anioPubDesde` →
`diaPubHasta/mesPubHasta/anioPubHasta`), así que pedir "últimos 365 días"
en vez de "desde el 1° de enero" es el mismo mecanismo, no una fuente nueva.
Es además la norma en su propia dimensión: `eficacia_legislativa` y
`comisiones_caidas` ya usan ventana móvil de 365 días sobre la misma familia
de fuentes públicas (HCDN CKAN); `ratio_dnu` era la excepción.

## Opciones consideradas

- Sacar `ratio_dnu` del tablero, como `movilizacion_cepa`
- Dejarlo como acumulado YTD
- Recalibrar las anclas sin cambiar la ventana
- Mantener las anclas viejas post-cambio de ventana

## Decisión

### 1. `_infoleg_session_count` toma un rango de fechas explícito

`scripts/politica.py`: la función pasa de recibir `year: int` (construía
internamente "1-ene-año → hoy o 31-dic-año") a recibir `desde: date, hasta:
date` explícitos. Es un cambio de firma, no de mecanismo — mismo POST a
`buscarNormas.do`, mismos campos del formulario.

### 2. `fetch_ratio_dnu()` usa ventana móvil de 365 días

```text
hasta = hoy
desde = hoy − 365 días
ratio = count(DNUs, desde→hasta) / count(leyes, desde→hasta)
```

El indicador deja de resetear en enero. El dict devuelto cambia `"periodo":
str(año)` por `"ventana_dias": 365` (mismo campo que ya usan
`eficacia_legislativa` y `comisiones_caidas` para declarar su ventana).

### 3. La serie histórica pasa a un punto por MES, no por año

`scripts/descargar_series.py::fetch_ratio_dnu_serie()` reutiliza
`_hcdn_ventanas_12m()` (genera `(YYYY-MM, cutoff, fin)` desde dic-2023 hasta
hoy — ya usada por `eficacia_legislativa`/`comisiones_caidas`, pese al
nombre heredado de "hcdn": la lógica es genérica, no depende de la fuente) y
consulta InfoLeg **una vez por mes** (una búsqueda de leyes + una de DNUs),
reutilizando la misma sesión. A diferencia del CKAN de HCDN, InfoLeg no
expone un dump con fecha por registro que permita filtrar localmente — no
hay forma de evitar una consulta por mes con esta fuente.

### 4. Recalibrar `BANDAS_ITCP["ratio_dnu"]` con los 32 puntos reales

Las anclas viejas (0,3 / 0,7 / 1,2 / 2,0) se calibraron implícitamente contra
el comportamiento del ratio YTD, que arranca bajo en enero por construcción.
La ventana móvil real (backfill dic-2023→jul-2026, 32 puntos) nunca baja de
**1,176** y llega a **5,545** (mediana 1,89). Con las anclas viejas, **31 de
32 meses caían en las dos bandas del piso** (40 o 10 puntos) y ninguno
alcanzaba nunca 85 o 100 — la misma saturación en espejo que ADR-0045
encontró en `comisiones_caidas`, con el mismo procedimiento de corrección:
anclas nuevas en números redondos, chequeadas contra la serie real.

Anclas nuevas (menor = mejor, tramos extremos abiertos):

| Ratio DNU/leyes (365 días) | Puntaje | Meses reales (de 32) |
|---:|---:|---:|
| ≤ 1,5 | 100 | 7 |
| 1,5 – 2,0 | 85 | 10 |
| 2,0 – 3,0 | 65 | 5 |
| 3,0 – 4,5 | 40 | 4 |
| > 4,5 | 10 | 6 |

Todas las bandas quedan pobladas con la serie real.

### Consecuencias

- `ratio_dnu` deja de resetear en enero: cada corrida mensual produce un
  valor propio, comparable con el mes anterior.
- La serie histórica (`output/series/politica.csv`) pasa de 7 puntos anuales
  a ~32 puntos mensuales tras la regeneración con este ADR.
- El puntaje del indicador cambia materialmente para prácticamente toda la
  serie histórica (antes clavado en 10-40 casi siempre; ahora discrimina
  sobre el rango real) — efecto de metodología, no de coyuntura. La
  dimensión `poder_legislativo` y el ITCP se regeneran en la misma corrida
  scoped (`descargar_series.py --cinturon politica` + `validacion_externa.py`
  + `generar_informe.py` + `publicar.py` + `gate_calidad.py` + pytest).
- `_infoleg_session_count` cambia de firma (`year: int` → `desde: date,
  hasta: date`); no tiene otros llamadores fuera de `politica.py` y
  `descargar_series.py` (verificado).

## Pros y contras de las opciones

### Sacar `ratio_dnu` del tablero, como `movilizacion_cepa`

Rechazada. La diferencia material con `movilizacion_cepa` es que ahí no
existía forma de reconstruir una ventana móvil (la fuente, CEPA, no publica
historia comparable) — acá sí, con la misma fuente y el mismo mecanismo que
ya usa el indicador. Sacarlo sería resignar información recuperable.

### Dejarlo como acumulado YTD

Rechazada por el mismo argumento que sacó a `movilizacion_cepa` del
tablero en ADR-0052: no es comparable mes a mes, y aplicar el criterio a un
indicador sí y a otro no (sin diferencia de fuente que lo justifique) es una
inconsistencia editorial, no una decisión metodológica.

### Recalibrar las anclas sin cambiar la ventana

Rechazada. Habría dejado la comparación mes a mes rota (el problema de fondo)
mientras maquilla la distribución de puntajes. La ventana móvil ataca la
causa; la recalibración de anclas es una consecuencia necesaria de ese
cambio, no un sustituto.

### Mantener las anclas viejas post-cambio de ventana

Rechazada: habría dejado 31/32 meses reales en las dos bandas del piso, la
misma saturación que ADR-0045 corrigió para `comisiones_caidas` — cambiar la
ventana sin recalibrar solo desplaza el problema, no lo resuelve.

## Más información

### Precedentes directos

ADR-0036 (incorpora ratio_dnu a la paramétrica) · ADR-0052 (mismo defecto, corregido en `movilizacion_cepa` sacándolo del tablero) · ADR-0045 (recalibración de bandas por saturación, mismo procedimiento)

### Limitaciones

- Las anclas 1,5/2,0/3,0/4,5 son calibración contra la serie observada (32
  meses), no un umbral institucional — deben someterse al mismo stress test
  que el resto de las bandas de la Paramétrica (ADR-0019).
- InfoLeg no expone un dump con fecha por registro: el backfill mensual
  cuesta una consulta por mes (≈2 min para 32 meses), no una descarga única
  como HCDN CKAN. Un rediseño del buscador de InfoLeg interrumpe tanto el
  indicador como su serie histórica hasta adaptarse.
- Identificar DNU por la frase "necesidad y urgencia" sigue siendo una
  aproximación (limitación heredada, no introducida por este ADR).
